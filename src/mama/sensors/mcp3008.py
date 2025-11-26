import random

from spidev import SpiDev


class MCP3008:
    def __init__(self, bus=0, device=0):
        self.spi = SpiDev()
        self.bus, self.device = bus, device
        self.open()
        self.spi.max_speed_hz = 1000000  # 1MHz

    def open(self):
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 1000000  # 1MHz

    def read(self, channel=0):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

    def close(self):
        self.spi.close()


class TestMCP3008:
    def __init__(self, test_summand: int = 1):
        self.current_value = 0
        self.summand = test_summand + random.randint(5, 10)

    def open(self):
        pass

    def read(self, _):
        if self.current_value > 1023:
            self.summand *= -1
        elif self.current_value < 0:
            self.summand *= -1

        self.current_value += self.summand
        return self.current_value

    def close(self):
        pass
