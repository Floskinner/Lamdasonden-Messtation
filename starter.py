"""
Modul das von Gunicorn verwendet wird um den Server zu starten
"""
import datetime
import os
import sys
import time
from threading import Event
from threading import Thread
from typing import Dict

from flask import Flask
from flask import render_template
from flask import request
from flask import Response
from flask_socketio import SocketIO
from influxdb import InfluxDBClient

import raspi_status as pi
from globale_variablen import config
from GPIO import GPIO_Reader

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)

GPIO = GPIO_Reader()
THREAD = Thread()
THREAD_STOP_EVENT = Event()

CONNECTIONS_COUNTER = 0
IS_RECORDING = False

# fmt:off
client = InfluxDBClient(
    host="127.0.0.1",
    port=8086,
    username="python",
    password="password",
    database="lamdawerte",
)
# fmt:on


def write_to_systemd(message: str):
    """Übergebene Nachrichten werden auf die Konsole ausgegeben mit print und anschließend
    erfolgt sys.stdout.flush(). Dadurch werden alle Ausgaben direkt in die systemd Logs eingetragen

    Args:
        message (str): Nachricht welche auf der Konsole / systemd Log erscheinen soll
    """
    print(message)
    sys.stdout.flush()


def update_data(update_interval: float, messure_interval: float):
    """Daten werden vom GPIO neu ausgelesen und zur Webseite übertragen
    Ist aktuell eine Aufnahme am start, so wird  0.5 Sekunden geschlafen

    Args:
        interval (float): Zeitintervall wie lange das Programm schlafen soll nach einem Update
    """

    sampling_rate = messure_interval
    number_of_lamda_values = round(update_interval / sampling_rate)

    while not THREAD_STOP_EVENT.isSet():

        lamda_values = []
        for _ in range(number_of_lamda_values):
            data = GPIO.getData()
            lamda_values.append(data)
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

        data = {
            "lamda1": sum_of_lamda1 / number_of_lamda_values,
            "lamda2": sum_of_lamda2 / number_of_lamda_values,
            "volt1": sum_of_volt1 / number_of_lamda_values,
            "volt2": sum_of_volt2 / number_of_lamda_values,
            "afr1": sum_of_afr1 / number_of_lamda_values,
            "afr2": sum_of_afr2 / number_of_lamda_values,
        }

        socketio.emit("newValues", data, broadcast=True)

        # Ohne warten wird emit nicht zuverlässig durchgeführt
        socketio.sleep(0.01)

        if IS_RECORDING:
            record_thread = Thread(target=write_to_db, args=(data,), daemon=True)
            record_thread.start()


def write_to_db(data: dict):
    """Erstellt einen neuen Eintrag in der Datenbank

    Args:
        data (dict): Folgende Keys müssen vorhaben sein: ["lamda1"], ["lamda2"], ["afr1"], ["afr2"]
    """

    json_body = [
        {
            "measurement": "lamdawerte",
            "tags": {"Car": "IEinAutoTag"},
            "fields": {
                "Lamda_1": data["lamda1"],
                "AFR_1": data["afr1"],
                "Lamda_2": data["lamda2"],
                "AFR_2": data["afr2"],
            },
        }
    ]

    client.write_points(json_body, time_precision="ms")
    # result = client.query('select Lamda_1 from lamdawerte;')
    # print("Result: {0}".format(result))


@app.route("/")
def index():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/" aufgerufen wird
    Rendert und gibt das Template index.html zurück
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
        "update_intervall": config.UPDATE_INTERVAL * 1000,  # To convert to ms
        "correction_bank_1": config.KORREKTURFAKTOR_BANK_1,
        "correction_bank_2": config.KORREKTURFAKTOR_BANK_2,
    }

    return render_template("index.html", **template_data)


@app.route("/correction", methods=["GET", "POST"])
def update_correction():
    if request.method == "GET":
        return {"correction_bank_1": config.KORREKTURFAKTOR_BANK_1, "correction_bank_2": config.KORREKTURFAKTOR_BANK_2}

    else:
        data: dict = request.form
        try:
            correction_bank_1 = float(data["correction_bank_1"])
            correction_bank_2 = float(data["correction_bank_2"])

            config.update_setting("KORREKTURFAKTOR_BANK_1", correction_bank_1)
            config.update_setting("KORREKTURFAKTOR_BANK_2", correction_bank_2)
        except Exception as e:
            print(e)
            return Response("{'message':'Invalid settings'}", status=400, mimetype="application/json")

        return Response("Success", status=200)


@app.route("/system")
def system():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/system" aufgerufen wird
    Rendert und gibt das Template system.html zurück
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

    return render_template("system.html", **system_data)


@socketio.on("connected")
def connected(json: dict):
    """Sobald eine Verbindung mit dem Socket aufgebaut wird, startet die Methode den Thread für das
    updaten der Daten. Zudem setzt sie die Systemzeit gleich der Browserzeit,
    damit beim aufzeichnen der Daten die richtigen Uhrzeiten verwendet werden

    Args:
        json (dict): Key ["data"] welcher die Uhrzeit als ISO 8601 String enthält
    """

    global THREAD
    global THREAD_STOP_EVENT
    global CONNECTIONS_COUNTER

    date_string = json["data"]
    time_befehl = "/usr/bin/date -s " + str(date_string)
    os.system(time_befehl)

    write_to_systemd("Client connected")
    CONNECTIONS_COUNTER += 1

    if not THREAD.is_alive():
        write_to_systemd("Starting Thread")
        THREAD_STOP_EVENT.clear()
        THREAD = socketio.start_background_task(update_data, config.UPDATE_INTERVAL, config.MESSURE_INTERVAL)


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
    """Startet oder stoppt die Aufnahem von Daten, welche in der InfluxDB gespeichert werden

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

# Clean data from DB older than 6 Months
if os.environ.get("FLASK_ENV") != "development":
    db_delete_time_string = (datetime.datetime.now() - datetime.timedelta(days=config.DB_DELETE_AELTER_ALS)).strftime(
        "%Y-%m-%d"
    )
    query = "DELETE WHERE time < '" + db_delete_time_string + "'"
    write_to_systemd(f"Delete Data older than {db_delete_time_string}")
    result = client.query(query)

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080, host="0.0.0.0")
