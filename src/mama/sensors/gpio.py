import os

from mama.sensors.mcp3008 import MCP3008
from mama.sensors.mcp3008 import TestMCP3008


class GPIO(object):
    """Basis Klasse für die GPIO Schnittstelle"""

    def __init__(self, *args, **kwargs):
        """Handelt es sich um eine Testumgebung wird ein TestMCP3008 Objekt erstellt, ansonsten ein MCP3008 Objekt"""
        if os.environ.get("FLASK_ENV") == "development":
            print("Create TestMCP3008 Object")
            self.adc = TestMCP3008(*args, **kwargs)
        else:
            self.adc = MCP3008(*args, **kwargs)

    def get_voltage(self, channel: int) -> float:
        """Gibt den Spannungswert des angegebenen Kanals zurück

        :param channel: Kanalnummer (0-7)
        :return: Spannungswert (0-5V)
        """
        value = self.adc.read(channel)
        voltage = value / 1023.0 * 5.0
        return voltage
