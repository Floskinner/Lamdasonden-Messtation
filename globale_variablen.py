"""
Hier weden grundelgende Einstellungen / Variablen definiert, die im ganzen Programm verwendet werden
"""
import json
import os
from pathlib import Path
from typing import Dict

setting_path = Path("settings_example.json") if os.environ.get("FLASK_ENV") == "development" else Path("settings.json")


def read_settings(file_path: Path) -> Dict:
    with file_path.open(mode="r", encoding="utf8") as file:
        settings = json.load(file)
    return settings


def save_settings(file_path: Path, values: Dict) -> None:
    with file_path.open(mode="w", encoding="utf8") as file:
        json.dump(values, file, indent=4, sort_keys=True)


class Config:
    def __init__(self):
        self.__load_settings()

    def __load_settings(self):
        settings = read_settings(setting_path)
        # Add dynmaic attributes from sttings json
        for name, value in settings.items():
            setattr(self, name, value)

    def update_setting(self, name: str, value: any):
        """Aktualisiert eine Einstellung

        :param name: Name der Einstellung
        :param value: Wert der Einstellung
        """
        settings = read_settings(setting_path)
        settings[name] = json.loads(value)
        save_settings(setting_path, settings)
        self.__load_settings()

    def get_settings(self) -> Dict:
        """Gibt die aktuellen Einstellungen zurück

        :return: Dict mit den Einstellungen als Inhalt.
        """
        return self.__dict__


config = Config()
