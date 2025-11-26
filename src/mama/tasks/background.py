"""Background tasks for sensor data collection and monitoring"""

import time
import traceback

from mama.models.database import db_connection


def get_lamda_values(lamda_sensor0, lamda_sensor1, number_of_lamda_values: int, sampling_rate: float) -> dict:
    """Gibt die Lamdawerte der beiden Lambdasensoren zurück

    Args:
        lamda_sensor0: Lambda Sensor 0 instance
        lamda_sensor1: Lambda Sensor 1 instance
        number_of_lamda_values (int): Anzahl der Messungen die durchgeführt werden sollen
        sampling_rate (float): Zeitintervall wie lange das Programm schlafen soll nach einem Update

    Returns:
        dict: Lamdawerte der beiden Lambdasensoren
    """
    lamda_values = []
    for _ in range(number_of_lamda_values):
        lamda0_data = lamda_sensor0.get_data()
        lamda1_data = lamda_sensor1.get_data()
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


def get_temp_values(temp_sensor0, temp_sensor1) -> dict:
    """Gibt die Temperaturwerte der beiden Temperatursensoren zurück

    Args:
        temp_sensor0: Temperature Sensor 0 instance
        temp_sensor1: Temperature Sensor 1 instance

    Returns:
        Dict mit den Keys "temp0" und "temp1"
    """
    temp0, voltage0 = temp_sensor0.get_temp()
    temp1, voltage1 = temp_sensor1.get_temp()

    temp_values = {
        "temp0": temp0,
        "temp1": temp1,
        "temp0_voltage": voltage0,
        "temp1_voltage": voltage1,
    }
    return temp_values


def update_data(
    socketio, thread_stop_event, is_recording_func, sensors, update_interval: float, messure_interval: float
):
    """Diese Funktion wird in einem eigenen Thread ausgeführt und sorgt dafür, dass die Daten
    über einen Socket an den Client gesendet werden. Die Daten werden dabei in einem bestimmten
    Intervall aktualisiert. Die Temperaturwerte werden dabei immer gesichert, die Lambda Werte nur
    wenn die Aufzeichnung läuft.

    :param socketio: SocketIO instance
    :param thread_stop_event: Event to signal thread stop
    :param is_recording_func: Function that returns current recording state
    :param sensors: Dictionary containing all sensor instances
    :param update_interval: In welchem Intervall die Daten aktualisiert werden sollen
    :param messure_interval: In welchem Intervall die Messwerte ermittelt werden sollen
    """
    try:
        sampling_rate = messure_interval
        number_of_lamda_values = round(update_interval / sampling_rate)

        while not thread_stop_event.isSet():
            lamda_values = get_lamda_values(sensors["lamda0"], sensors["lamda1"], number_of_lamda_values, sampling_rate)
            temp_values = get_temp_values(sensors["temp0"], sensors["temp1"])

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

            if is_recording_func():
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


def update_lifetime(socketio, sensors) -> None:
    """Aktuallisiert die Lebenszeit der Sensoren

    :param socketio: SocketIO instance
    :param sensors: Dictionary containing all sensor instances
    """
    update_frequency_sec = 60

    while True:
        temp_values = get_temp_values(sensors["temp0"], sensors["temp1"])

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


def check_overheating(socketio, sensors) -> None:
    """Check for overheading. True if the temperature is over 1100°C for more than 2 seconds

    :param socketio: SocketIO instance
    :param sensors: Dictionary containing all sensor instances
    """

    update_frequency_sec = 2
    time0 = 0
    time1 = 0

    while True:
        temp_values = get_temp_values(sensors["temp0"], sensors["temp1"])

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


def check_tmp_sensor_error_state(socketio) -> None:
    """Überprüft ob die Temperattursensoren einen Fehler haben

    :param socketio: SocketIO instance
    """
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
