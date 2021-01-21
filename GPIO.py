from MCP3008 import MCP3008

class GPIO_Reader(object):
    """
    Klasse womit der Aktuelle Lamdawert am GPIO Einglang ausgelesen werden kann
    """
    pass

    def __init__ (self):
        self.adc = MCP3008()

    def getVoltage(self, channel):
        value = self.adc.read( channel )
        voltage = value / 1023.0 * 3.3
        return round(voltage, 3)

    def getLamda(self, channel):
        
        lamda = self.getVoltage(channel) * 3
        return round(lamda, 3)
    
    def getData(self):
        data = {
            "lamda1" : self.getLamda(channel = 0),
            "lamda2" : self.getLamda(channel = 1),
            "voltage1" : self.getVoltage(channel = 0),
            "voltage2" : self.getVoltage(channel = 1)
        }
        return data