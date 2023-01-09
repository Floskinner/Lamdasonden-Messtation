import os

from MCP3008 import MCP3008
from MCP3008 import TestMCP3008


class GPIO(object):
    """Basis Klasse für die GPIO Schnittstelle"""

    def __init__(self):
        """Handelt es sich um eine Testumgebung wird ein TestMCP3008 Objekt erstellt, ansonsten ein MCP3008 Objekt"""
        if os.environ.get("FLASK_ENV") == "development":
            self.adc = TestMCP3008()
        else:
            self.adc = MCP3008()

    def get_voltage(self, channel: int) -> float:
        """Gibt den Spannungswert des angegebenen Kanals zurück

        :param channel: Kanalnummer (0-7)
        :return: Spannungswert (0-5V)
        """
        value = self.adc.read(channel)
        voltage = value / 1023.0 * 5.0
        return voltage
