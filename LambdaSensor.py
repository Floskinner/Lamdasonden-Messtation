from globale_variablen import config
from GPIO import GPIO


class LambdaSensor(GPIO):
    """
    Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann
    """

    def get_lamda(self, voltage: float, correction: float) -> float:
        lamda = round(0.2 * voltage + correction, 3)
        return lamda

    def get_afr(self, lamda: float) -> float:
        afr = lamda * getattr(config, "AFR_STOCH")
        return afr

    def getData(self):
        voltage_1 = self.get_voltage(0)
        voltage_2 = self.get_voltage(1)

        lamda_1 = round(self.get_lamda(voltage_1, getattr(config, "KORREKTURFAKTOR_BANK_1")), 3)
        lamda_2 = round(self.get_lamda(voltage_2, getattr(config, "KORREKTURFAKTOR_BANK_2")), 3)

        afr_1 = self.get_afr(lamda_1)
        afr_2 = self.get_afr(lamda_2)

        data = {
            "lamda1": lamda_1,
            "lamda2": lamda_2,
            "afr1": afr_1,
            "afr2": afr_2,
            "volt1": voltage_1,
            "volt2": voltage_2,
        }
        return data
