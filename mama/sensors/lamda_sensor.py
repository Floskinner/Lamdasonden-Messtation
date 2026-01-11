from mama.config import config
from mama.sensors.gpio import ADC, TestMCP3008
from dataclasses import dataclass


@dataclass
class LamdaData:
    lamda: float
    afr: float
    volt: float


class LambdaSensor(ADC):
    """
    Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann
    """

    def __init__(self, channel: int, correction_factor_key: str = "KORREKTURFAKTOR_BANK_1"):
        """Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann

        :param channel: ADC Pin an dem der Lambda Sensor angeschlossen ist
        :param correction_factor_key: Korrekturfaktor für den Lamdawert
        """
        super().__init__()
        self.channel = channel
        self.correction_factor_key = correction_factor_key

        if isinstance(self.adc, TestMCP3008):
            self.adc = TestMCP3008(min_value=0, max_value=1023)

    @staticmethod
    def calculate_lamda(voltage: float, correction: float) -> float:
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

    def get_data(self) -> LamdaData:
        """Gibt den aktuellen Lamdawert, den aktuellen AFR Wert und den aktuellen Spannungswert zurück

        :return: Aktueller Lamdawert, Aktueller AFR Wert und Aktueller Spannungswert
        """
        voltage = self.get_voltage(self.channel)
        lamda = LambdaSensor.calculate_lamda(voltage, getattr(config, self.correction_factor_key))
        afr = self.get_afr(lamda)

        return LamdaData(lamda=lamda, afr=afr, volt=voltage)
