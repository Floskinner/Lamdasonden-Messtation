# Documentation of the Project "M.A.M.A" / Lambda Sensor Measurement Station
This serves for tracking and documentation of the project<br>
Logs can be viewed with the following command
```bash
sudo journalctl -u mama.service -f
```

## Hardware
Products:
- Raspberry Pi W with Header ([buyzero](https://buyzero.de/products/raspberry-pi-zero-wh-mit-bestucktem-header))
- 16GB microSD card
- MCP3008

## Installation
The following software must be installed:
- Python 3.12 (use the [deploy script](./deployment/setup.sh))
- pip
- dnsmasq
- hostapd

### WLAN
To set up the Pi to create its own WLAN, the following [Guide](https://www.elektronik-kompendium.de/sites/raspberry-pi/2002171.htm) can be followed up to and including "Configure WLAN Interface".

### Python
This project uses `uv` as package manager. Please see the [uv documentation](https://uv.readthedocs.io/en/latest/) for installation and usage instructions.

TD;LR:
```bash
uv venv
uv sync
```

### Flask / Gunicorn
The web server is created using [Flask](https://flask.palletsprojects.com/en/1.1.x/) and hosted with [Gunicorn](https://docs.gunicorn.org/en/stable/run.html) (instructions also available for Flask-SocketIO). Using [Flask-SocketIO](https://flask.palletsprojects.com/en/1.1.x/api/#blueprint-objects), a socket is created so that data can appear "real-time" in the browser. Gunicorn requires a `.py` file with appropriate configurations, which must be passed when calling the service (`gunicorn.conf.py`)

### MCP3008
Instructions for using the MCP3008 can be found here -> [Guide](https://tutorials-raspberrypi.de/raspberry-pi-mcp3008-analoge-signale-auslesen/)

## Configuration
There is a sample configuration [`settings_example.json`](settings_example.json). This can be used as a template and contains the initial tested best values. When used productively (`FLASK_ENV = "prod"`), a file named `settings.json` with the corresponding values as in the example file must be present.

---

## Notes
- The Pi is powered internally directly by M.A.M.A with 5V
- The Pi's time is updated using the browser each time the index.html is called
- SQLite is used as the database for history tracking

## System configurations
Below the folder `system` are all changed system files. All files inside this folder will be updated / replaced by a self-update.
