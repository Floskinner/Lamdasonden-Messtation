from MCP3008 import MCP3008

from globale_variablen import AFR_STOCH


class GPIO_Reader(object):
    """
    Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann
    """

    def __init__(self):
        self.adc = MCP3008()

    def get_voltage(self, channel: int) -> float:
        value = self.adc.read(channel)
        voltage = value / 1023.0 * 5.0
        return voltage

    def get_lamda(self, voltage: float) -> float:
        lamda = round(0.2 * voltage + 0.511, 3)
        return lamda

    def get_afr(self, voltage: float) -> float:
        afr = round( 3.018 * voltage + 7.361 , 2)
        return afr

    def getData(self):
        voltage_1 = self.get_voltage(0)
        voltage_2 = self.get_voltage(1)

        lamda_1 = round(self.get_lamda(voltage_1), 3)
        lamda_2 = round(self.get_lamda(voltage_2), 3)

        afr_1 = self.get_afr(voltage_1)
        afr_2 = self.get_afr(voltage_2)

        data = {
            "lamda1": lamda_1,
            "lamda2": lamda_2,
            "afr1": afr_1,
            "afr2": afr_2,
            "volt1": voltage_1,
            "volt2": voltage_2
        }
        return data
