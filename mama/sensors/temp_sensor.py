from dataclasses import dataclass

from mama.sensors.gpio import ADC, TestMCP3008


@dataclass
class TempData:
    temp: float
    volt: float


class TypKTemperaturSensor(ADC):
    """Class to read temperature values from a GPIO input.
    Uses a Type-K thermocouple sensor.
    Reference: https://www.sensorshop24.de/kabelthermoelement-mit-nicr-ni-typ-k-durchmesser-6mm
    """

    def __init__(self, channel: int):
        """Class to read temperature values from an ADC input.

        :param channel: ADC pin to which the temperature sensor is connected
        """
        # TODO: Remove the following line when the implementation is complete
        self.adc = TestMCP3008(min_value=0, max_value=1023)
        self.channel = channel

    @staticmethod
    def calculate_temp(voltage: float) -> int:
        """Returns the temperature in degrees Celsius.

        :param voltage: Voltage from the Type-K thermocouple (0-5V)
        :return: Temperature in degrees Celsius (0-1360°C)
        """
        # Conversion formula from voltage to degrees Celsius
        # Reference: https://www.turbozentrum.de/turbozentrum/pdf/Anleitungen/EGT-DE_mit_CANchecked_Info.pdf
        # T [C] = 250 * OUT [V]
        temp = int(250 * voltage)
        return temp

    def get_data(self) -> TempData:
        """Returns the temperature in degrees Celsius.

        :param channel: GPIO pin to which the temperature sensor is connected
        :return: Temperature in degrees Celsius (0-1360°C) and voltage (0-5V)
        """
        voltage = self.get_voltage(self.channel)
        temp = self.calculate_temp(voltage)
        return TempData(temp=temp, volt=voltage)
