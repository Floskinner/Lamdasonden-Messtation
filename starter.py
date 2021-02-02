from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

from GPIO import GPIO_Reader
from threading import Thread, Event
from influxdb import InfluxDBClient

import time
import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

gpio = GPIO_Reader()
thread = Thread()
thread_stop_event = Event()

connectionsCounter = 0
isRecording = False
messInterval = 0.01     # in Sekunden

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

        if isRecording:
            recordThread = Thread(target=writeToDB, args=(data,), daemon=True)
            recordThread.start()
            time.sleep(0.5)         #Bei aufnahme nurnoch alle 0,5 Sekunden

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
        'currentYear': timeString
    }

    return render_template('index.html', **templateData)


@socketio.on('connected')
def connected(json, methods=['GET', 'POST']):

    global thread
    global thread_stop_event
    global connectionsCounter

    dateString = json['data']
    timeBefehl = "/usr/bin/date -s " + str(dateString)
    os.system(timeBefehl)

    print('Client connected')
    connectionsCounter += 1

    if not thread.isAlive():
        print("Starting Thread")
        thread_stop_event.clear()
        thread = socketio.start_background_task(updateData, messInterval)


@socketio.on('disconnect')
def disconnect():

    global connectionsCounter

    print('Client disconnected')
    connectionsCounter -= 1

    if connectionsCounter == 0:
        # Stop Thread
        # Stop Aufnahme
        global thread_stop_event
        global isRecording

        thread_stop_event.set()
        isRecording = False

        print('Stopped thread')


@socketio.on('recording')
def recording(json):
    global isRecording
    
    if json["recording"]:
        isRecording = True
        print("start aufnahme")
    else:
        # stoppen
        isRecording = False
        print("stoppe Aufnahme")


if __name__ == "__main__":
    #socketio.run(app, debug=True, port=8080, host='0.0.0.0')
    pass
