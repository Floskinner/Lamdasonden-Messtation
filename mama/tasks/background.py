"""Background tasks for sensor data collection and monitoring"""

import time
import traceback
from dataclasses import dataclass

from mama.models.database import db_connection
from mama.sensors.temp_sensor import TypKTemperaturSensor
from mama.sensors.lamda_sensor import LambdaSensor


@dataclass
class AveragedLamdaValues:
    """Container for averaged lambda sensor readings from both sensors"""

    lamda1: float
    lamda2: float
    volt1: float
    volt2: float
    afr1: float
    afr2: float


@dataclass
class TempValues:
    """Container for temperature sensor readings from both sensors"""

    temp0: float
    temp1: float
    temp0_voltage: float
    temp1_voltage: float


def get_lamda_values(
    lamda_sensor0: LambdaSensor, lamda_sensor1: LambdaSensor, number_of_lamda_values: int, sampling_rate: float
) -> AveragedLamdaValues:
    """Returns the averaged lambda values from both lambda sensors

    Args:
        lamda_sensor0: Lambda Sensor 0 instance
        lamda_sensor1: Lambda Sensor 1 instance
        number_of_lamda_values: Number of measurements to perform for averaging
        sampling_rate: Sleep interval between measurements in seconds

    Returns:
        AveragedLamdaValues: Averaged lambda values from both sensors
    """
    if number_of_lamda_values <= 0:
        raise ValueError("number_of_lamda_values must be greater than 0")

    # Collect samples
    lamda1_samples = []
    lamda2_samples = []
    volt1_samples = []
    volt2_samples = []
    afr1_samples = []
    afr2_samples = []

    for _ in range(number_of_lamda_values):
        lamda0_data = lamda_sensor0.get_data()
        lamda1_data = lamda_sensor1.get_data()

        lamda1_samples.append(lamda0_data.lamda)
        lamda2_samples.append(lamda1_data.lamda)
        volt1_samples.append(lamda0_data.volt)
        volt2_samples.append(lamda1_data.volt)
        afr1_samples.append(lamda0_data.afr)
        afr2_samples.append(lamda1_data.afr)

        time.sleep(sampling_rate)

    assert len(lamda1_samples) == number_of_lamda_values

    # Calculate averages
    return AveragedLamdaValues(
        lamda1=sum(lamda1_samples) / number_of_lamda_values,
        lamda2=sum(lamda2_samples) / number_of_lamda_values,
        volt1=sum(volt1_samples) / number_of_lamda_values,
        volt2=sum(volt2_samples) / number_of_lamda_values,
        afr1=sum(afr1_samples) / number_of_lamda_values,
        afr2=sum(afr2_samples) / number_of_lamda_values,
    )


def get_temp_values(temp_sensor0: TypKTemperaturSensor, temp_sensor1: TypKTemperaturSensor) -> TempValues:
    """Gibt die Temperaturwerte der beiden Temperatursensoren zurück

    Args:
        temp_sensor0: Temperature Sensor 0 instance
        temp_sensor1: Temperature Sensor 1 instance

    Returns:
        TempValues: Temperature values from both sensors
    """
    temp0_data = temp_sensor0.get_data()
    temp1_data = temp_sensor1.get_data()

    return TempValues(
        temp0=temp0_data.temp,
        temp1=temp1_data.temp,
        temp0_voltage=temp0_data.volt,
        temp1_voltage=temp1_data.volt,
    )


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
                "lamda1": lamda_values.lamda1,
                "lamda2": lamda_values.lamda2,
                "volt1": lamda_values.volt1,
                "volt2": lamda_values.volt2,
                "afr1": lamda_values.afr1,
                "afr2": lamda_values.afr2,
                "temp1": temp_values.temp0,
                "temp2": temp_values.temp1,
                "temp1_voltage": temp_values.temp0_voltage,
                "temp2_voltage": temp_values.temp1_voltage,
            }

            socketio.emit("newValues", data)

            # without sleep, the emit does not work properly
            # socketio.sleep(0.1)

            if temp_values.temp0 > 100:
                db_connection.insert_temp_value(0, temp_values.temp0)

            if temp_values.temp1 > 100:
                db_connection.insert_temp_value(1, temp_values.temp1)

            if is_recording_func():
                db_connection.insert_lambda_value(0, lamda_values.lamda1)
                db_connection.insert_lambda_value(1, lamda_values.lamda2)

    except AttributeError:
        socketio.emit(
            "error",
            {
                "type": "config",
                "exc": traceback.format_exc().splitlines()[-1],
                "traceback": traceback.format_exc(),
            },
        )
    except Exception:
        socketio.emit(
            "error",
            {
                "type": "unknown",
                "exc": traceback.format_exc().splitlines()[-1],
                "traceback": traceback.format_exc(),
            },
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

        if temp_values.temp0 > 100:
            current_lifespan0 += int(update_frequency_sec / 60)
            db_connection.update_temp_sensor_tracking(0, current_lifespan0)

        if temp_values.temp1 > 100:
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

        if temp_values.temp0 > 1100:
            time0 += update_frequency_sec
        else:
            time0 = 0

        if temp_values.temp1 > 1100:
            time1 += update_frequency_sec
        else:
            time1 = 0

        if time0 > 2:
            db_connection.set_error_state(
                0,
                True,
                f"Überhitzung! Die Temperatur betrug {temp_values.temp0}°C. Bitte ersetzen!",
            )

        if time1 > 2:
            db_connection.set_error_state(
                1,
                True,
                f"Überhitzung! Die Temperatur betrug {temp_values.temp1}°C. Bitte ersetzen!",
            )

        socketio.sleep(update_frequency_sec)


def check_tmp_sensor_error_state(socketio) -> None:
    """Checks the error state of the temperature sensors and notifies the client if an error is present

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
            )

        if error_state1:
            socketio.emit(
                "info",
                {
                    "msg": f"Achtung der Temperatursensor 1 hat einen Fehler! Fehlermeldung: {error_msg1}",
                },
            )

        socketio.sleep(update_frequency_sec)
