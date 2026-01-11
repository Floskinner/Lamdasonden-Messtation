"""
Module used by Gunicorn to start the server
"""

import os
import sys
from threading import Event

from flask import Flask
from flask_socketio import SocketIO

from mama.config import config
from mama.routes.api import api_bp
from mama.routes.main import main_bp
from mama.routes.settings import settings_bp
from mama.routes.system import system_bp
from mama.sensors.lamda_sensor import LambdaSensor
from mama.sensors.temp_sensor import TypKTemperaturSensor
from mama.tasks import background

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(system_bp)

# Initialize sensors
LAMDA_SENSOR0 = LambdaSensor(channel=getattr(config, "LAMDA0_CHANNEL"), correction_factor_key="KORREKTURFAKTOR_BANK_1")
LAMDA_SENSOR1 = LambdaSensor(channel=getattr(config, "LAMDA1_CHANNEL"), correction_factor_key="KORREKTURFAKTOR_BANK_2")
TEMP_SENSOR0 = TypKTemperaturSensor(channel=getattr(config, "TEMPERATUR0_CHANNEL"))
TEMP_SENSOR1 = TypKTemperaturSensor(channel=getattr(config, "TEMPERATUR1_CHANNEL"))

SENSORS = {
    "lamda0": LAMDA_SENSOR0,
    "lamda1": LAMDA_SENSOR1,
    "temp0": TEMP_SENSOR0,
    "temp1": TEMP_SENSOR1,
}

# Thread management
UPDATE_DATA_THREAD = None
SENOR_LIFETIME_THREAD = None
SENSOR_OVERHEAD_THREAD = None
SENSOR_CHECK_ERROR_THREAD = None
THREAD_STOP_EVENT = Event()

CONNECTIONS_COUNTER = 0
IS_RECORDING = False


def write_to_systemd(message: str):
    """print message and flush stdout to force the system to write the log immediately

    Args:
        message (str): Message to be printed
    """
    print(message)
    sys.stdout.flush()


def is_task_running(task) -> bool:
    """Check if a background task is still running.

    Handles both standard threads (is_alive) and eventlet greenthreads (dead property).

    Args:
        task: The background task to check (Thread or EventletThread/GreenThread)

    Returns:
        bool: True if the task is running, False otherwise
    """
    if task is None:
        return False

    # Standard threading.Thread uses is_alive()
    if hasattr(task, "is_alive"):
        return task.is_alive()

    # Eventlet greenthreads use 'dead' property
    if hasattr(task, "dead"):
        return not task.dead

    return False


def get_is_recording():
    """Returns the current recording state"""
    return IS_RECORDING


@socketio.on("connected")
def connected(json: dict):
    """When a socket connection is established this handler starts the data update thread.
    It also sets the system time to the browser time so recorded data uses correct timestamps.

    Args:
        json (dict): Key ["data"] containing the time as an ISO 8601 string
    """

    global UPDATE_DATA_THREAD
    global SENOR_LIFETIME_THREAD
    global SENSOR_OVERHEAD_THREAD
    global SENSOR_CHECK_ERROR_THREAD
    global THREAD_STOP_EVENT
    global CONNECTIONS_COUNTER

    date_string = json["data"]

    if os.environ.get("FLASK_ENV") != "development":
        time_befehl = "/usr/bin/date -s " + str(date_string)
        os.system(time_befehl)
    else:
        write_to_systemd("Development mode: Skipping setting system time")

    write_to_systemd("Client connected")
    CONNECTIONS_COUNTER += 1

    if not is_task_running(UPDATE_DATA_THREAD):
        write_to_systemd("Starting Thread")
        THREAD_STOP_EVENT.clear()
        UPDATE_DATA_THREAD = socketio.start_background_task(
            background.update_data,
            socketio,
            THREAD_STOP_EVENT,
            get_is_recording,
            SENSORS,
            getattr(config, "UPDATE_INTERVAL"),
            getattr(config, "MESSURE_INTERVAL"),
        )

    if not is_task_running(SENOR_LIFETIME_THREAD):
        SENOR_LIFETIME_THREAD = socketio.start_background_task(background.update_lifetime, socketio, SENSORS)

    if not is_task_running(SENSOR_OVERHEAD_THREAD):
        SENSOR_OVERHEAD_THREAD = socketio.start_background_task(background.check_overheating, socketio, SENSORS)

    if not is_task_running(SENSOR_CHECK_ERROR_THREAD):
        SENSOR_CHECK_ERROR_THREAD = socketio.start_background_task(background.check_tmp_sensor_error_state, socketio)


@socketio.on("disconnect")
def disconnect():
    """When no one is connected to the socket anymore,
    all threads (update data and recording) are stopped
    """
    global CONNECTIONS_COUNTER

    write_to_systemd("Client disconnected")
    CONNECTIONS_COUNTER -= 1

    if CONNECTIONS_COUNTER == 0:
        # Stop Thread
        # Stop Recording
        global THREAD_STOP_EVENT
        global IS_RECORDING

        THREAD_STOP_EVENT.set()
        IS_RECORDING = False

        write_to_systemd("Stopped thread")


@socketio.on("recording")
def recording(json: dict):
    """Starts or stops the recording of data, which is stored in the db

    Args:
        json (dict): Key ["recording"] with true or false
    """
    global IS_RECORDING

    if json["recording"]:
        IS_RECORDING = True
        write_to_systemd("start recording")
    else:
        # stop
        IS_RECORDING = False
        write_to_systemd("stop recording")


def main():
    """Main entry point for the application"""
    import os

    port = 8080 if os.environ.get("FLASK_ENV") == "development" else 80
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_ENV") == "development"

    socketio.run(app, debug=debug, port=port, host=host)


if __name__ == "__main__":
    main()
