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
    def __init__(self):
        pass

    def open(self):
        pass

    def read(self, channel=0):
        # Lamda 1 = 500
        return 900

    def close(self):
        pass
