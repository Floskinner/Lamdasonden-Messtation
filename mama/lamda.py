from datetime import datetime
from mama.globale_variablen import config
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

bp = Blueprint("lamda", __name__)


@bp.route("/")
def index():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/" aufgerufen wird
    Rendert und gibt das Template index.html zurück
    """
    now = datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
        "update_intervall": config.UPDATE_INTERVAL * 1000,  # To convert to ms
        "correction_bank_1": config.KORREKTURFAKTOR_BANK_1,
        "correction_bank_2": config.KORREKTURFAKTOR_BANK_2,
    }

    return render_template("index.html", **template_data)

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