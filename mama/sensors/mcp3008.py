import random

from spidev import SpiDev


class MCP3008:
    def __init__(self, bus=0, device=0):
        self.spi = SpiDev()
        self.bus, self.device = bus, device
        self.open()
        self.spi.max_speed_hz = 1000000  # 1MHz

    def __del__(self):
        self.close()

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
    def __init__(self, offset_value: int = 1, min_value: int = 0, max_value: int = 1023):
        self.current_value = min_value
        self.offset_sum = offset_value + random.randint(1, 3)
        self.min_value = min_value
        self.max_value = max_value

    def open(self):
        pass

    def read(self, _):
        self.current_value += self.offset_sum
        if self.current_value > self.max_value:
            self.current_value = self.max_value
            self.offset_sum = -self.offset_sum
        elif self.current_value < self.min_value:
            self.current_value = self.min_value
            self.offset_sum = -self.offset_sum

        return self.current_value

    def close(self):
        pass
