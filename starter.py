from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit

from GPIO import GPIO_Reader

from threading import Thread, Event

import time
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

gpio = GPIO_Reader()
thread = Thread()
thread_stop_event = Event()

connectionsCounter = 0


def updateData(interval):
    while not thread_stop_event.isSet():
        data = gpio.getData()
        socketio.emit("newValues", data, broadcast=True)
        print(data)
        time.sleep(interval)
        
        

@app.route("/")
def index():
    
    now = datetime.datetime.now()
    timeString = now.strftime("%m.%Y")

    templateData = {
      'currentMonthYear' : timeString
      }

    return render_template('index.html', **templateData)


@socketio.on('connected')
def connected(json, methods=['GET', 'POST']):

    global thread
    global thread_stop_event
    global connectionsCounter


    print('Client connected')
    connectionsCounter += 1

    if not thread.isAlive():
        print("Starting Thread")
        thread_stop_event.clear()
        thread = socketio.start_background_task(updateData, 1)

@socketio.on('disconnect')
def disconnect():

    global connectionsCounter
    
    print('Client disconnected')
    connectionsCounter -= 1

    if connectionsCounter == 0:
        # Stop Thread
        global thread_stop_event
        thread_stop_event.set()

        print('Stopped thread')


@socketio.on('recording')
def recording(json):
    if json["recording"]:
        #aufnehmen
        print("start aufnahme")
    else:
        #stoppen
        print("stoppe Aufnahme")
    

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8081, host='192.168.0.30')
