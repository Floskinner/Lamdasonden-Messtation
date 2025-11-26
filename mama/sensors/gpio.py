import os

from mama.sensors.mcp3008 import MCP3008
from mama.sensors.mcp3008 import TestMCP3008


class ADC(object):
    """Base class for the ADC interface"""

    def __init__(self, bus: int = 0, device: int = 0):
        """If it is a test environment, a TestMCP3008 object is created, otherwise an MCP3008 object"""
        if os.environ.get("FLASK_ENV") == "development":
            print("Create TestMCP3008 Object")
            self.adc = TestMCP3008(bus, device)
        else:
            self.adc = MCP3008(bus, device)

    def get_voltage(self, channel: int) -> float:
        """Returns the voltage value of the specified channel

        :param channel: Channel of the ADC (0-7)
        :return: Voltage value (0-5V)
        """
        value = self.adc.read(channel)
        voltage = value / 1023.0 * 5.0
        return voltage
