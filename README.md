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
- Python 3.7
- pip
- dnsmasq 
- hostapd

### WLAN
Damit der Pi sein eigenes WLAN erstellt, kann folgende [Anleitung](https://www.elektronik-kompendium.de/sites/raspberry-pi/2002171.htm) bis einschließlich "WLAN-Interface konfigurieren" befolgt werden.

### Python
Python hat eine virtualenv ([Anleitung](https://bodo-schoenfeld.de/eine-virtuelle-umgebung-fuer-python-erstellen/)) in der alle benötigte Module installiert werden. Alle "requirements" stehen in `requirements.txt`. <br>
Diese können alle über folgendem Befehel installiert werden 
```bash
pip install -r requirements.txt
```

### Service
Der Service muss unter `/etc/systemd/system/lamda.service` liegen -> [Anleitung](https://www.raspberrypi.org/documentation/linux/usage/systemd.md). Wichtig hier, dass `Environment="PATH=/home/pi/lamdaProjekt/venv/bin"` dem Pfad entspricht, wo auch die virtualenv ist, damit sichergestellt ist, das auch alle benötigte vorhaben ist.

### Flask / Gunicorn
Der Webserver wird mithilfe von [Flask](https://flask.palletsprojects.com/en/1.1.x/) erstellt und mit [Gunicorn](https://docs.gunicorn.org/en/stable/run.html) gehosted (Anleitung auch bei Flask-soketIO). Mithilfe von [Flask-soketIO](https://flask.palletsprojects.com/en/1.1.x/api/#blueprint-objects) wird dann ein Socket erstellt, damit die Daten in Echtzeit im Browser erscheinen können. Gunicorn braucht eine `.py`-Datei mit entsprechenden Konfigurationen, die dann beim Service aufruf mit übergebenen werden müssen (`gunicorn.conf.py`)

### MCP3008
Eine Verwendung für den MCP3008 findet man hier -> [Anleitung](https://tutorials-raspberrypi.de/raspberry-pi-mcp3008-analoge-signale-auslesen/)

## Konfigurationen
Es gibt eine Beispielkonfiguration [`settings_example.json`](settings_example.json). Diese kann als Vorlage verwendet werden und beinhaltet die Initialen ertesteten besten Werte. Wird das ganze Produtktiv verwendet (`FLASK_ENV = "prod"`), so muss eine Datei namens `settings.json` mit den entsprechenden Werten wie in der Beispieldatei vorhanden sein.

```json
{
    "AFR_STOCH": 14.68, // Wert zum ausrechnen des AFR = lamda * AFR_STOCH 
    "KORREKTURFAKTOR_BANK_1": 0.511, // Korrekturfaktor des Lamdawertes Bank 1
    "KORREKTURFAKTOR_BANK_2": 0.511, // Korrekturfaktor des Lamdawertes Bank 1
    "MESSURE_INTERVAL": 0.01, // Messintervall in Sekunden
    "UPDATE_INTERVAL": 1.5, // Updateintervall in Sekunden der Anzeige
    "DB_DELETE_AELTER_ALS": 180, // Löschen in Tage der DB Einträge
    "ANZEIGEN_BANK_1": true, // Bank 1 wird beim aufruf angezeigt
    "ANZEIGEN_BANK_2": true, // Bank 2 wird beim aufruf angezeigt
    "NACHKOMMASTELLEN": 2, // Initiale Anzeige der Nachkommastellen
    "WARNUNG_BLINKEN": false // Blinken im roten Bereich aktivieren
}
```

---

## Randbemerkungen
- Der Pi wird intern der MAMA direkt mit 5V versorgt
- Die Uhrzeit vom Pi wird mithilfe vom Browser aktuallisiert, jedes mal wenn man die index.html aufruft
- SQLite wird als Datenbank verwendet