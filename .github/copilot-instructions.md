# MAMA - Lambda Sensor Measurement Station

## Project Overview
MAMA is a Raspberry Pi-based real-time lambda (oxygen) sensor monitoring system for automotive diagnostics. It reads analog sensor data via MCP3008 ADC, calculates air-fuel ratios (AFR), and streams data to a web interface using Flask-SocketIO with WebSocket communication.

**Hardware**: Raspberry Pi Zero W, MCP3008 ADC (SPI interface), Type-K thermocouples, wideband lambda sensors  
**Production deployment**: systemd service running Gunicorn with eventlet workers on port 80  
**Development mode**: Flask dev server on port 8080 with mock sensor data

## Architecture Patterns

### Environment-Based Behavior
The `FLASK_ENV` environment variable controls critical runtime behavior throughout the codebase:
- **Development** (`FLASK_ENV=development`): Uses `settings_example.json`, mock sensors (`TestMCP3008`), port 8080, skips system time sync
- **Production** (default): Uses `settings.json`, real SPI hardware (`MCP3008`), port 80, syncs browser time to system clock

Example from `mama/sensors/gpio.py`:
```python
if os.environ.get("FLASK_ENV") == "development":
    self.adc = TestMCP3008()  # Mock data generator
else:
    self.adc = MCP3008()  # Real SPI hardware
```

### Settings Management (`mama/config.py`)
Global configuration singleton loaded from JSON. Settings are **mutable at runtime** via `config.update_setting()` which persists changes back to the JSON file. All sensor calibration values (correction factors, AFR stoichiometric ratio) come from here.

Access settings: `getattr(config, "SETTING_NAME")` (e.g., `getattr(config, "AFR_STOCH")`)

### Sensor Architecture
Sensors follow inheritance pattern: `LambdaSensor`/`TypKTemperaturSensor` → `GPIO` (base class) → `MCP3008`/`TestMCP3008`

**Key constraint**: Hardware SPI access requires production environment. Development uses sinusoidal mock data generators.

Lambda calculation formula (hardcoded): `lambda = 0.2 * voltage + correction_factor`

### Thread Management & WebSocket Lifecycle
The app uses **connection-counted thread management**: background tasks start on first WebSocket connection and stop when all clients disconnect.

4 background threads managed in `mama/app.py`:
1. `UPDATE_DATA_THREAD` - Samples sensors, emits `newValues` to clients
2. `SENOR_LIFETIME_THREAD` - Tracks sensor runtime hours
3. `SENSOR_OVERHEAD_THREAD` - Temperature monitoring/alerts
4. `SENSOR_CHECK_ERROR_THREAD` - Thermocouple fault detection

All controlled by `THREAD_STOP_EVENT` flag and `CONNECTIONS_COUNTER`.

### Database (SQLite)
Single-file database (`MAMA.sqlite`) with **auto-cleanup** of old records. Thread-safe connection (`check_same_thread=False`) shared across Flask threads. Used for historical data storage during "recording" mode.

Tables: `temps`, `lambda_values`, `temp_sensor_tracking`

## Development Workflows

### Local Development Setup
```bash
# Install dependencies (uses Poetry)
poetry install

# Set development environment
export FLASK_ENV=development

# Run directly (development server on port 8080)
poetry run mama

# Run with Gunicorn (production-like)
gunicorn -c deployment/gunicorn.conf.py mama.app:app
```

### Debugging
Use VS Code launch configuration (`.vscode/launch.json`):
- Configuration: "Python Debugger: Flask"
- Sets `FLASK_APP=mama/app.py` and `FLASK_DEBUG=1`
- Includes Jinja template debugging

**Critical**: Mock sensors generate changing data in development - real sensor readings require production environment on Raspberry Pi.

### Code Quality Tools
- **Ruff** - Linting (Python 3.12 target)
- **Pre-commit hooks** - Configured in `.pre-commit-config.yaml`

Run: `pre-commit run --all-files`

### Testing Production Deployment
The systemd service (`deployment/lamda.service`) runs as root with virtualenv path overrides. To test production behavior locally without hardware:
```bash
# Simulate production environment (will fail on SPI access without hardware)
unset FLASK_ENV
gunicorn -c deployment/gunicorn.conf.py mama.app:app
```

## Key Integration Points

### WebSocket Events (client → server)
- `connected` - Client connects, sends ISO 8601 timestamp for system clock sync
- `disconnect` - Client disconnects, decrements connection counter
- `recording` - Starts/stops database recording mode

### WebSocket Events (server → client)
- `newValues` - Sensor data broadcast (lambda, AFR, voltage, temperature)
- `lifetime` - Sensor runtime tracking updates
- `overheating` - Temperature threshold alerts
- `tempError` - Thermocouple fault states

### Blueprint Structure
- `main_bp` - Template rendering (index, history, system pages)
- `api_bp` - REST endpoints for historical data queries
- `settings_bp` - Configuration updates
- `system_bp` - Raspberry Pi system monitoring (CPU, memory, temp via `psutil`)

## Project-Specific Conventions

### Logging
Uses `write_to_systemd()` helper which calls `print()` + `sys.stdout.flush()` for immediate systemd journal output. **Do not use standard logging module**.

### Naming
Translate all found German terms to English. Take care of these specific terms:
- `lamda` (not lambda - reserved keyword)
- use ASCII quotes (`"`) for strings, not German-style quotes (`„“`)
- use ASCII characters only in code (no umlauts or unicode)

### Sensor Sampling Pattern
Lambda sensors use **averaged sampling**: collect N readings at `MESSURE_INTERVAL` rate, return mean to reduce noise. See `background.get_lamda_values()`.

Temperature sensors read instantaneously (Type-K thermocouples via voltage conversion).

### Frontend Communication
Templates use Jinja2 (`.jinja` extension). JavaScript in `mama/static/javascript/` uses Socket.IO client and Chart.js for real-time plotting. Data updates via `socket.on('newValues')` events.

## Common Pitfalls
- **Settings file mismatch**: Development uses `settings_example.json`, production needs `settings.json`
- **SPI permissions**: Production requires root or SPI group membership for `/dev/spidev0.0`
- **Port conflicts**: Dev uses 8080, prod uses 80 (requires sudo)
- **Thread leaks**: Disconnecting without stopping threads if connection counter logic breaks
- **Hardware dependencies**: Cannot test real sensors in dev environment - use `FLASK_ENV=development` for local work
