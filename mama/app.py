"""
Modul das von Gunicorn verwendet wird um den Server zu starten
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
from mama.sensors.lambda_sensor import LambdaSensor
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
LAMDA_SENSOR0 = LambdaSensor(getattr(config, "LAMDA0_CHANNEL"))
LAMDA_SENSOR1 = LambdaSensor(getattr(config, "LAMDA1_CHANNEL"))
TEMP_SENSOR0 = TypKTemperaturSensor(getattr(config, "TEMPERATUR0_CHANNEL"))
TEMP_SENSOR1 = TypKTemperaturSensor(getattr(config, "TEMPERATUR1_CHANNEL"))

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
    """Übergebene Nachrichten werden auf die Konsole ausgegeben mit print und anschließend
    erfolgt sys.stdout.flush(). Dadurch werden alle Ausgaben direkt in die systemd Logs eingetragen

    Args:
        message (str): Nachricht welche auf der Konsole / systemd Log erscheinen soll
    """
    print(message)
    sys.stdout.flush()


def get_is_recording():
    """Returns the current recording state"""
    return IS_RECORDING


@socketio.on("connected")
def connected(json: dict):
    """Sobald eine Verbindung mit dem Socket aufgebaut wird, startet die Methode den Thread für das
    updaten der Daten. Zudem setzt sie die Systemzeit gleich der Browserzeit,
    damit beim aufzeichnen der Daten die richtigen Uhrzeiten verwendet werden

    Args:
        json (dict): Key ["data"] welcher die Uhrzeit als ISO 8601 String enthält
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

    write_to_systemd("Client connected")
    CONNECTIONS_COUNTER += 1

    if UPDATE_DATA_THREAD is None or not UPDATE_DATA_THREAD.is_alive():
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

    if SENOR_LIFETIME_THREAD is None or not SENOR_LIFETIME_THREAD.is_alive():
        SENOR_LIFETIME_THREAD = socketio.start_background_task(background.update_lifetime, socketio, SENSORS)

    if SENSOR_OVERHEAD_THREAD is None or not SENSOR_OVERHEAD_THREAD.is_alive():
        SENSOR_OVERHEAD_THREAD = socketio.start_background_task(background.check_overheating, socketio, SENSORS)

    if SENSOR_CHECK_ERROR_THREAD is None or not SENSOR_CHECK_ERROR_THREAD.is_alive():
        SENSOR_CHECK_ERROR_THREAD = socketio.start_background_task(background.check_tmp_sensor_error_state, socketio)


@socketio.on("disconnect")
def disconnect():
    """Falls keiner mehr mit dem Socket verbunden ist,
    werden alle Threads (update Data und aufnahme) gestoppt
    """
    global CONNECTIONS_COUNTER

    write_to_systemd("Client disconnected")
    CONNECTIONS_COUNTER -= 1

    if CONNECTIONS_COUNTER == 0:
        # Stop Thread
        # Stop Aufnahme
        global THREAD_STOP_EVENT
        global IS_RECORDING

        THREAD_STOP_EVENT.set()
        IS_RECORDING = False

        write_to_systemd("Stopped thread")


@socketio.on("recording")
def recording(json: dict):
    """Startet oder stoppt die Aufnahem von Daten, welche in der db gespeichert werden

    Args:
        json (dict): Key ["recording"] mit true oder false
    """
    global IS_RECORDING

    if json["recording"]:
        IS_RECORDING = True
        write_to_systemd("start aufnahme")
    else:
        # stoppen
        IS_RECORDING = False
        write_to_systemd("stoppe Aufnahme")


def main():
    """Main entry point for the application"""
    import os

    port = 8080 if os.environ.get("FLASK_ENV") == "development" else 80
    host = "0.0.0.0"
    debug = os.environ.get("FLASK_ENV") == "development"

    socketio.run(app, debug=debug, port=port, host=host)


if __name__ == "__main__":
    main()
