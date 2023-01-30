from typing import Tuple

from GPIO import GPIO


class TypKTemperaturSensor(GPIO):
    """Klasse womit der Temperaturwert am GPIO Einglang ausgelesen werden kann.
    Als Sensor wird ein Typ K Temperatursensor verwendet.
    Referenz: https://www.sensorshop24.de/kabelthermoelement-mit-nicr-ni-typ-k-durchmesser-6mm
    """

    def __init__(self, channel: int):
        """Klasse womit der Temperaturwert am ADC Einglang ausgelesen werden kann.

        :param channel: ADC Pin an dem der Temperatursensor angeschlossen ist
        """
        super().__init__(test_summand=100)
        self.channel = channel

    @staticmethod
    def calculate_temp(voltage: float) -> int:
        """Gibt die Temperatur in Grad Celsius zurück

        :param voltage: Spannungswert des Typ K Temperatursensors (0-5V)
        :return: Temperatur in Grad Celsius (0-1360°C)
        """
        # Formel für die Umrechnung von Spannung in Grad Celsius
        # Referenz: https://www.turbozentrum.de/turbozentrum/pdf/Anleitungen/EGT-DE_mit_CANchecked_Info.pdf
        # T [C] = 250 * OUT [V]
        temp = int(250 * voltage)
        return temp

    def get_temp(self) -> Tuple[int, float]:
        """Gibt die Temperatur in Grad Celsius zurück

        :param channel: GPIO Pin an dem der Temperatursensor angeschlossen ist
        :return: Temperatur in Grad Celsius (0-1360°C) und Spannungswert (0-5V)
        """
        voltage = self.get_voltage(self.channel)
        temp = self.calculate_temp(voltage)
        return (temp, voltage)
