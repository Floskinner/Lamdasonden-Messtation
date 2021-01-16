from MCP3008 import MCP3008

adc = MCP3008()
value = adc.read( channel = 0 ) # Den auszulesenden Channel kannst du natürlich anpassen
print("Anliegende Spannung: %.2f" % (value / 1023.0 * 3.3) )