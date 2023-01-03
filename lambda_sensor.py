from globale_variablen import config
from GPIO import GPIO


class LambdaSensor(GPIO):
    """
    Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann
    """

    def __init__(self, channel: int):
        """Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann

        :param channel: ADC Pin an dem der Lambda Sensor angeschlossen ist
        """
        super().__init__()
        self.channel = channel

    def calculate_lamda(self, voltage: float, correction: float) -> float:
        """Gibt den aktuellen Lamdawert zurück

        :param voltage: Spannungswert des Lambda Sensors (0-5V)
        :param correction: Korrekturfaktor für den Lamdawert
        :return: Aktueller Lamdawert
        """
        lamda = round(0.2 * voltage + correction, 3)
        return lamda

    def get_afr(self, lamda: float) -> float:
        """Gibt den aktuellen AFR Wert zurück

        :param lamda: Aktueller Lamdawert
        :return: Aktueller AFR Wert
        """
        afr = lamda * getattr(config, "AFR_STOCH")
        return afr

    def get_data(self) -> dict:
        """Gibt den aktuellen Lamdawert, den aktuellen AFR Wert und den aktuellen Spannungswert zurück

        :return: Aktueller Lamdawert, Aktueller AFR Wert und Aktueller Spannungswert
        """
        voltage = self.get_voltage(self.channel)
        lamda = self.calculate_lamda(voltage, getattr(config, "KORREKTURFAKTOR_BANK_1"))
        afr = self.get_afr(lamda)
        data = {
            "lamda": lamda,
            "afr": afr,
            "volt": voltage,
        }
        return data
