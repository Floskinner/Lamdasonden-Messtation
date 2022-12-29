"""
Hier weden grundelgende Einstellungen / Variablen definiert, die im ganzen Programm verwendet werden
"""
import json
from pathlib import Path
from typing import Dict

setting_path = Path("settings.json")


def read_settings(file_path: Path) -> Dict:
    with file_path.open(mode="r", encoding="utf8") as file:
        settings = json.load(file)
    return settings


def save_settings(file_path: Path, values: Dict) -> None:
    with file_path.open(mode="w", encoding="utf8") as file:
        json.dump(values, file, indent=4, sort_keys=True)


class Config:

    def __init__(self):
        self.MESSURE_INTERVAL: float
        self.UPDATE_INTERVAL: float
        self.DB_DELETE_AELTER_ALS: float
        self.AFR_STOCH: float
        self.KORREKTURFAKTOR_BANK_1: float
        self.KORREKTURFAKTOR_BANK_2: float
        self.NACHKOMMASTELLEN: int
        self.WARNUNG_BLINKEN: bool
        self.ANZEIGEN_BANK_1: bool
        self.ANZEIGEN_BANK_2: bool

        self.__load_settings()

    def __load_settings(self):
        settings = read_settings(setting_path)
        try:
            self.MESSURE_INTERVAL = settings["MESSURE_INTERVAL"]
            self.UPDATE_INTERVAL = settings["UPDATE_INTERVAL"]
            self.DB_DELETE_AELTER_ALS = settings["DB_DELETE_AELTER_ALS"]
            self.AFR_STOCH = settings["AFR_STOCH"]
            self.KORREKTURFAKTOR_BANK_1 = settings["KORREKTURFAKTOR_BANK_1"]
            self.KORREKTURFAKTOR_BANK_2 = settings["KORREKTURFAKTOR_BANK_2"]
            self.NACHKOMMASTELLEN = settings["NACHKOMMASTELLEN"]
            self.WARNUNG_BLINKEN = settings["WARNUNG_BLINKEN"]
            self.ANZEIGEN_BANK_1 = settings["ANZEIGEN_BANK_1"]
            self.ANZEIGEN_BANK_2 = settings["ANZEIGEN_BANK_2"]
        except KeyError as error:
            raise Exception("Missing Setting") from error

    def update_setting(self, name: str, value: any):
        """ Aktualisiert eine Einstellung

        :param name: Name der Einstellung
        :param value: Wert der Einstellung
        """
        settings = read_settings(setting_path)
        settings[name] = value
        save_settings(setting_path, settings)
        self.__load_settings()

    def get_settings(self) -> Dict:
        """ Gibt die aktuellen Einstellungen zurück

        :return: Dict mit den Einstellungen als Inhalt.
        """
        return self.__dict__


config = Config()
