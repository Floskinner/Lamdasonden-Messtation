"""
Modul das von Gunicorn verwendet wird um den Server zu starten
"""
import datetime
import json
import os
import sys
import time
import traceback
from threading import Event

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_socketio import SocketIO

import raspi_status as pi
from database import db_connection
from globale_variablen import config
from lambda_sensor import LambdaSensor
from typ_k_tempreatursensor import TypKTemperaturSensor

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

LAMDA_SENSOR0 = LambdaSensor(getattr(config, "LAMDA0_CHANNEL"))
LAMDA_SENSOR1 = LambdaSensor(getattr(config, "LAMDA1_CHANNEL"))
TEMP_SENSOR0 = TypKTemperaturSensor(getattr(config, "TEMPERATUR0_CHANNEL"))
TEMP_SENSOR1 = TypKTemperaturSensor(getattr(config, "TEMPERATUR1_CHANNEL"))
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


def update_data(update_interval: float, messure_interval: float):
    """Diese Funktion wird in einem eigenen Thread ausgeführt und sorgt dafür, dass die Daten
    über einen Socket an den Client gesendet werden. Die Daten werden dabei in einem bestimmten
    Intervall aktualisiert. Die Temperaturwerte werden dabei immer gesichert, die Lambda Werte nur
    wenn die Aufzeichnung läuft.

    :param update_interval: In welchem Intervall die Daten aktualisiert werden sollen
    :param messure_interval: In welchem Intervall die Messwerte ermittelt werden sollen
    """
    try:
        sampling_rate = messure_interval
        number_of_lamda_values = round(update_interval / sampling_rate)

        while not THREAD_STOP_EVENT.isSet():
            lamda_values = get_lamda_values(number_of_lamda_values, sampling_rate)
            temp_values = get_temp_values()

            data = {
                "lamda1": lamda_values["lamda1"],
                "lamda2": lamda_values["lamda2"],
                "volt1": lamda_values["volt1"],
                "volt2": lamda_values["volt2"],
                "afr1": lamda_values["afr1"],
                "afr2": lamda_values["afr2"],
                "temp1": temp_values["temp0"],
                "temp2": temp_values["temp1"],
                "temp1_voltage": temp_values["temp0_voltage"],
                "temp2_voltage": temp_values["temp1_voltage"],
            }

            socketio.emit("newValues", data, broadcast=True)

            # Ohne warten wird emit nicht zuverlässig durchgeführt
            socketio.sleep(0)

            if temp_values["temp0"] > 100:
                db_connection.insert_temp_value(0, temp_values["temp0"])

            if temp_values["temp1"] > 100:
                db_connection.insert_temp_value(1, temp_values["temp1"])

            if IS_RECORDING:
                db_connection.insert_lambda_value(0, lamda_values["lamda1"])
                db_connection.insert_lambda_value(1, lamda_values["lamda2"])

    except AttributeError:
        socketio.emit(
            "error",
            {
                "type": "config",
                "exc": traceback.format_exc().splitlines()[-1],
                "traceback": traceback.format_exc(),
            },
            broadcast=True,
        )
    except Exception:
        socketio.emit(
            "error",
            {
                "type": "unknown",
                "exc": traceback.format_exc().splitlines()[-1],
                "traceback": traceback.format_exc(),
            },
            broadcast=True,
        )


def get_lamda_values(number_of_lamda_values: int, sampling_rate: float) -> dict:
    """Gibt die Lamdawerte der beiden Lambdasensoren zurück

    Args:
        number_of_lamda_values (int): Anzahl der Messungen die durchgeführt werden sollen
        sampling_rate (float): Zeitintervall wie lange das Programm schlafen soll nach einem Update

    Returns:
        dict: Lamdawerte der beiden Lambdasensoren
    """
    lamda_values = []
    for _ in range(number_of_lamda_values):
        lamda0_data = LAMDA_SENSOR0.get_data()
        lamda1_data = LAMDA_SENSOR1.get_data()
        lamda_values.append(
            {
                "lamda1": lamda0_data["lamda"],
                "lamda2": lamda1_data["lamda"],
                "volt1": lamda0_data["volt"],
                "volt2": lamda1_data["volt"],
                "afr1": lamda0_data["afr"],
                "afr2": lamda1_data["afr"],
            }
        )
        time.sleep(sampling_rate)

    sum_of_lamda1 = 0
    sum_of_lamda2 = 0
    sum_of_volt1 = 0
    sum_of_volt2 = 0
    sum_of_afr1 = 0
    sum_of_afr2 = 0

    for lamda_value in lamda_values:
        sum_of_lamda1 += lamda_value["lamda1"]
        sum_of_lamda2 += lamda_value["lamda2"]
        sum_of_volt1 += lamda_value["volt1"]
        sum_of_volt2 += lamda_value["volt2"]
        sum_of_afr1 += lamda_value["afr1"]
        sum_of_afr2 += lamda_value["afr2"]

    return {
        "lamda1": sum_of_lamda1 / number_of_lamda_values,
        "lamda2": sum_of_lamda2 / number_of_lamda_values,
        "volt1": sum_of_volt1 / number_of_lamda_values,
        "volt2": sum_of_volt2 / number_of_lamda_values,
        "afr1": sum_of_afr1 / number_of_lamda_values,
        "afr2": sum_of_afr2 / number_of_lamda_values,
    }


def get_temp_values() -> dict:
    """Gibt die Temperaturwerte der beiden Temperatursensoren zurück

    Returns: Dict mit den Keys "temp0" und "temp1"
    """
    temp0, voltage0 = TEMP_SENSOR0.get_temp()
    temp1, voltage1 = TEMP_SENSOR1.get_temp()

    temp_values = {
        "temp0": temp0,
        "temp1": temp1,
        "temp0_voltage": voltage0,
        "temp1_voltage": voltage1,
    }
    return temp_values


def update_lifetime() -> None:
    """Aktuallisiert die Lebenszeit der Sensoren"""
    update_frequency_sec = 60

    while True:
        temp_values = get_temp_values()

        current_lifespan0 = db_connection.get_temp_sensor_tracking(0)[0]
        current_lifespan1 = db_connection.get_temp_sensor_tracking(1)[0]

        if temp_values["temp0"] > 100:
            current_lifespan0 += int(update_frequency_sec / 60)
            db_connection.update_temp_sensor_tracking(0, current_lifespan0)

        if temp_values["temp1"] > 100:
            current_lifespan1 += int(update_frequency_sec / 60)
            db_connection.update_temp_sensor_tracking(1, current_lifespan1)

        # Wenn die Lebensdauer der Sensoren überschritten wurde, wird ein Fehler gesetzt
        # dies sind 60min * 100 = 100 Stunden
        if current_lifespan0 > 60 * 100:
            db_connection.set_error_state(
                0,
                True,
                f"Maximale Lebensdauer überschritten! Er wurde bereits {int(current_lifespan1 / 60)} Stunden betrieben. Bitte ersetzen!",
            )

        if current_lifespan1 > 60 * 100:
            db_connection.set_error_state(
                1,
                True,
                f"Maximale Lebensdauer überschritten! Er wurde bereits {int(current_lifespan1 / 60)} Stunden betrieben. Bitte ersetzen!",
            )

        socketio.sleep(update_frequency_sec)


def check_overheating() -> None:
    """Check for overheading. True if the temperature is over 1100°C for more than 2 seconds"""

    update_frequency_sec = 2
    time0 = 0
    time1 = 0

    while True:
        temp_values = get_temp_values()

        if temp_values["temp0"] > 1100:
            time0 += update_frequency_sec
        else:
            time0 = 0

        if temp_values["temp1"] > 1100:
            time1 += update_frequency_sec
        else:
            time1 = 0

        if time0 > 2:
            db_connection.set_error_state(
                0,
                True,
                f"Überhitzung! Die Temperatur betrug {temp_values['temp0']}°C. Bitte ersetzen!",
            )

        if time1 > 2:
            db_connection.set_error_state(
                1,
                True,
                f"Überhitzung! Die Temperatur betrug {temp_values['temp1']}°C. Bitte ersetzen!",
            )

        socketio.sleep(update_frequency_sec)


def check_tmp_sensor_error_state() -> None:
    """Überprüft ob die Temperattursensoren einen Fehler haben"""
    update_frequency_sec = 30

    while True:
        error_state0, error_msg0 = db_connection.get_error_state(0)
        error_state1, error_msg1 = db_connection.get_error_state(1)

        if error_state0:
            socketio.emit(
                "info",
                {
                    "msg": f"Achtung der Temperatursensor 0 hat einen Fehler! Fehlermeldung: {error_msg0}",
                },
                broadcast=True,
            )

        if error_state1:
            socketio.emit(
                "info",
                {
                    "msg": f"Achtung der Temperatursensor 1 hat einen Fehler! Fehlermeldung: {error_msg1}",
                },
                broadcast=True,
            )

        socketio.sleep(update_frequency_sec)


@app.route("/")
def index():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/" aufgerufen wird
    Rendert und gibt das Template index.jinja zurück
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
        "update_intervall": getattr(config, "UPDATE_INTERVAL") * 1000,  # To convert to ms
    }
    template_data.update(config.get_settings())

    return render_template("index.jinja", **template_data)


@app.route("/history", methods=["GET"])
def history():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/history" aufgerufen wird
    Rendert und gibt das Template history.jinja zurück
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
    }

    return render_template("history.jinja", **template_data)


@app.route("/settings", methods=["POST"])
def update_settings():
    """Update der Einstellungen

    :return: Response mit Statuscode 200 wenn erfolgreich. 400 wenn Fehler aufgetreten ist.
    """
    data: dict = request.form
    try:
        for key, value in data.items():
            if value == "":
                return Response(json.dumps({"message":f"Invalid Value. Value of key {key} is empty"}), status=400, mimetype="application/json")
            config.update_setting(key, value)
    except KeyError as error:
        print(error)
        return Response(json.dumps({"message":f"Invalid Key. Key {key} is invalid"}), status=400, mimetype="application/json")
    except Exception as error:
        print(error)
        return Response(json.dumps({"message":f"Invalid Settings. {error}"}), status=400, mimetype="application/json")

    return Response("Success", status=200)


@app.route("/settings", methods=["GET"])
def get_settings():
    """Gibt die aktuellen Einstellungen zurück

    :return: Response mit Statuscode 200 wenn erfolgreich. JSON mit den Einstellungen als Inhalt.
    """
    return config.get_settings()


def add_temp_data(sensor_id: int, value: float):
    """Fügt Temperaturdaten in die Datenbank ein

    Args:
        sensor_id (int): ID des Sensors
        value (float): Temperaturwert
    """
    db_connection.insert_temp_value(sensor_id, value)


@app.route("/tempdata", methods=["GET"])
def get_temp_data_between():
    """Gibt Temperaturdaten zwischen zwei Zeitpunkten zurück

    :return: Response mit Statuscode 200 wenn erfolgreich. 400 wenn Fehler aufgetreten ist.
    """
    data: dict = request.args
    try:
        start_time = data["start_time"]
        end_time = data["end_time"]
    except KeyError as error:
        print(error)
        return Response("{'message':'Invalid values'}", status=400, mimetype="application/json")

    return Response(
        json.dumps(db_connection.get_temp_values_between(start_time, end_time)),
        status=200,
        mimetype="application/json",
    )


@app.route("/reset_temp_sensors", methods=["POST"])
def reset_temp_sensors():
    """Setzt die Lebensdauer der Temperatursensoren zurück

    :return: Response mit Statuscode 200 wenn erfolgreich. 400 wenn Fehler aufgetreten ist.
    """
    data: dict = request.form
    db_connection.update_temp_sensor_tracking(int(data["sensor"]), 0)
    db_connection.reset_error_state(int(data["sensor"]))
    return Response("Success", status=200)


def add_lambda_data(sensor_id: int, value: float):
    """Fügt Lambdadaten in die Datenbank ein

    Args:
        sensor_id (int): ID des Sensors
        value (float): Wert des Sensors
    """
    db_connection.insert_lambda_value(sensor_id, value)


@app.route("/lambdadata", methods=["GET"])
def get_lambda_data_between():
    """Gibt Lambdadaten zwischen zwei Zeitpunkten zurück

    :return: Response mit Statuscode 200 wenn erfolgreich. 400 wenn Fehler aufgetreten ist.
    """
    data: dict = request.args
    try:
        start_time = data["start_time"]
        end_time = data["end_time"]
    except KeyError as error:
        print(error)
        return Response("{'message':'Invalid values'}", status=400, mimetype="application/json")

    return Response(
        json.dumps(db_connection.get_lambda_values_between(start_time, end_time)),
        status=200,
        mimetype="application/json",
    )


@app.route("/system")
def system():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/system" aufgerufen wird
    Rendert und gibt das Template system.jinja zurück
    """

    system_data = {
        "os_version": pi.get_os_version(),
        "os_name": pi.get_hotname_ip(),
        "os_cpu": pi.get_cpu_usage(),
        "os_temperatur": pi.get_cpu_temp(),
        "os_ram_total": pi.get_ram_info().get("ram_total"),
        "os_ram_available": pi.get_ram_info().get("ram_available"),
        "os_ram_percent": pi.get_ram_info().get("ram_free_percent"),
        "os_disk_total": pi.get_disk_info().get("total"),
        "os_disk_used": pi.get_disk_info().get("used"),
        "os_disk_free": pi.get_disk_info().get("free"),
        "os_disk_free_percent": pi.get_disk_info().get("percent"),
    }

    return render_template("system.jinja", **system_data)


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
    time_befehl = "/usr/bin/date -s " + str(date_string)
    os.system(time_befehl)

    write_to_systemd("Client connected")
    CONNECTIONS_COUNTER += 1

    if UPDATE_DATA_THREAD is None or not UPDATE_DATA_THREAD.is_alive():
        write_to_systemd("Starting Thread")
        THREAD_STOP_EVENT.clear()
        UPDATE_DATA_THREAD = socketio.start_background_task(
            update_data,
            getattr(config, "UPDATE_INTERVAL"),
            getattr(config, "MESSURE_INTERVAL"),
        )

    if SENOR_LIFETIME_THREAD is None or not SENOR_LIFETIME_THREAD.is_alive():
        SENOR_LIFETIME_THREAD = socketio.start_background_task(update_lifetime)

    if SENSOR_OVERHEAD_THREAD is None or not SENSOR_OVERHEAD_THREAD.is_alive():
        SENSOR_OVERHEAD_THREAD = socketio.start_background_task(check_overheating)

    if SENSOR_CHECK_ERROR_THREAD is None or not SENSOR_CHECK_ERROR_THREAD.is_alive():
        SENSOR_CHECK_ERROR_THREAD = socketio.start_background_task(check_tmp_sensor_error_state)


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


if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080, host="0.0.0.0")
