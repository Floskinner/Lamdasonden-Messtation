"""
Modul das von Gunicorn verwendet wird um den Server zu starten
"""
import time
import datetime
import os

from threading import Thread, Event


from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

from influxdb import InfluxDBClient
from GPIO import GPIO_Reader

import raspi_status as pi

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

gpio = GPIO_Reader()
thread = Thread()
thread_stop_event = Event()

CONNECTIONS_COUNTER = 0
IS_RECORDING = False
MESSINTERVAL = 0.3     # in Sekunden

client = InfluxDBClient(host='127.0.0.1', port=8086, username='python',
                        password='password', database='lamdawerte')


# Clean data from DB older than 6 Months
timeString = (datetime.datetime.now() - datetime.timedelta(days=180)).strftime("%Y-%m-%d")
query = "DELETE WHERE time < '" + timeString + "'"
print("Delete Data older than ", timeString)
result = client.query(query)


def updateData(interval):
    while not thread_stop_event.isSet():
        data = gpio.getData()
        socketio.emit("newValues", data, broadcast=True)
        # print(data)

        if IS_RECORDING:
            record_thread = Thread(target=writeToDB, args=(data,), daemon=True)
            record_thread.start()
            time.sleep(0.5)  # Bei aufnahme nurnoch alle 0,5 Sekunden

        else:
            time.sleep(interval)


def writeToDB(data):
    json_body = [
        {
            "measurement": "lamdawerte",
            "tags": {
                "Car": "IEinAutoTag"
            },
            "fields": {
                "Lamda_1": data["lamda1"],
                "Voltage_1": data["voltage1"],
                "Lamda_2": data["lamda2"],
                "Voltage_2": data["voltage2"]
            }
        }
    ]

    client.write_points(json_body, time_precision="ms")
    # result = client.query('select Lamda_1 from lamdawerte;')
    # print("Result: {0}".format(result))


@app.route("/")
def index():

    now = datetime.datetime.now()
    timeString = now.strftime("%Y")

    templateData = {
        'current_year': timeString
    }

    return render_template('index.html', **templateData)


@app.route("/system")
def system():
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
    return render_template('system.html', **system_data)


@socketio.on('connected')
def connected(json, methods=['GET', 'POST']):

    global thread
    global thread_stop_event
    global CONNECTIONS_COUNTER

    date_string = json['data']
    time_befehl = "/usr/bin/date -s " + str(date_string)
    os.system(time_befehl)

    print('Client connected')
    CONNECTIONS_COUNTER += 1

    if not thread.isAlive():
        print("Starting Thread")
        thread_stop_event.clear()
        thread = socketio.start_background_task(updateData, MESSINTERVAL)


@socketio.on('disconnect')
def disconnect():

    global CONNECTIONS_COUNTER

    print('Client disconnected')
    CONNECTIONS_COUNTER -= 1

    if CONNECTIONS_COUNTER == 0:
        # Stop Thread
        # Stop Aufnahme
        global thread_stop_event
        global IS_RECORDING

        thread_stop_event.set()
        IS_RECORDING = False

        print('Stopped thread')


@socketio.on('recording')
def recording(json):
    global IS_RECORDING

    if json["recording"]:
        IS_RECORDING = True
        print("start aufnahme")
    else:
        # stoppen
        IS_RECORDING = False
        print("stoppe Aufnahme")


if __name__ == "__main__":
    #socketio.run(app, debug=True, port=8080, host='0.0.0.0')
    pass
