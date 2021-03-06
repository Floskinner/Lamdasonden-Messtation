# Dokumentation des Projektes "MAMA" / Lamdasonden-Messtation
Dies dient zur nachverfolgung und Dokumentation des Projektes<br>
Logs können mit folgendem Befehl angeschaut werden
```bash
sudo journalctl -u lamda.service -f
```

## Raspberry Pi
Produkte:
- Raspberry Pi W mit Header ([buyzero](https://buyzero.de/products/raspberry-pi-zero-wh-mit-bestucktem-header))
- 16GB microsSD-Karte
- MCP3008

## Installation
Da der Pi W kein Ethernet anschluss besitzt, muss dem Pi zuvor die WLAN Konfiguration übergeben werden -> [Anleitung](https://www.dahlen.org/2017/10/raspberry-pi-zero-w-headless-setup/) <br>
<br>
Folgende Software muss installiert werden:
- Python 3 or newer
- pip
- influxDB
- Grafana
- dnsmasq 
- hostapd

### WLAN
Damit der Pi sein eigenes WLAN erstellt, kann folgende [Anleitung](https://www.elektronik-kompendium.de/sites/raspberry-pi/2002171.htm) bis einschließlich "WLAN-Interface konfigurieren" befolgt werden.

### Grafana & InfluxDB
Mithilfe dieser [Anleitung](https://simonhearne.com/2020/pi-influx-grafana/) kann Grafana und InfluxDB installiert werden. Für Grafana muss anschließend ein Anonymus Zugang eingerichtet werden, damit man auch ohne Login auf den Grafen dann zugreifen kann [Anonymus Authentication](https://grafana.com/docs/grafana/latest/auth/overview/#anonymous-authentication), [Disable login form](https://grafana.com/docs/grafana/latest/auth/overview/#automatic-oauth-login). <br>
<hr>
Um InfluxDB richtig zu konfigurieren folgendes ausführen (influxdb.ini):

```bash
sudo influx

create database lamdawerte
use lamdawerte

create user grafana with password 'password' with all privileges
create user python with password 'password' with all privileges

grant all privileges on lamdawerte to grafana
grant all privileges on lamdawerte to python

show users

; user    admin
; ----    -----
; grafana true
; python  true
```

### Python
Python hat eine virtualenv ([Anleitung](https://bodo-schoenfeld.de/eine-virtuelle-umgebung-fuer-python-erstellen/)) in der alle benötigte Module installiert werden. Alle "requirements" stehen in `requirements.txt`. <br>
Diese können alle über folgendem Befehel installiert werden 
```bash
pip install -r requirements.txt
```

### Service
Der Service muss unter `/etc/systemd/system/lamda.service` liegen -> [Anleitung](https://www.raspberrypi.org/documentation/linux/usage/systemd.md). Wichtig hier, dass `Environment="PATH=/home/pi/lamdaProjekt/lamda_env/bin"` dem Pfad entspricht, wo auch die virtualenv ist, damit sichergestellt ist, das auch alle benötigte vorhaben ist.

### Flask / Gunicorn
Der Webserver wird mithilfe von [Flask](https://flask.palletsprojects.com/en/1.1.x/) erstellt und mit [Gunicorn](https://docs.gunicorn.org/en/stable/run.html) gehosted (Anleitung auch bei Flask-soketIO). Mithilfe von [Flask-soketIO](https://flask.palletsprojects.com/en/1.1.x/api/#blueprint-objects) wird dann ein Socket erstellt, damit die Daten in Echtzeit im Browser erscheinen können. Gunicorn braucht eine `.py`-Datei mit entsprechenden Konfigurationen, die dann beim Service aufruf mit übergebenen werden müssen (`gunicorn.conf.py`)

### MCP3008
Eine Verwendung für den MCP3008 findet man hier -> [Anleitung](https://tutorials-raspberrypi.de/raspberry-pi-mcp3008-analoge-signale-auslesen/)

## Randbemerkungen
- Der Pi wird intern der MAMA direkt mit 5V versorgt
- Die Uhrzeit vom Pi wird mithilfe vom Browser aktuallisiert, jedes mal wenn man die index.html aufruft
- Updates nur mit vorsicht durchführen (never change an running system)