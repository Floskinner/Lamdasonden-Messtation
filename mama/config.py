"""
Configuration settings for MAMA application.
Settings are loaded from JSON file and can be updated at runtime.
"""

import json
import os
import threading
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any

# Get the project root directory
_project_root = Path(__file__).parent.parent
setting_path = (
    _project_root / "settings_example.json"
    if os.environ.get("FLASK_ENV") == "development"
    else _project_root / "settings.json"
)


def _read_settings(file_path: Path) -> dict:
    with file_path.open(mode="r", encoding="utf8") as file:
        return json.load(file)


def _save_settings(file_path: Path, values: dict) -> None:
    with file_path.open(mode="w", encoding="utf8") as file:
        json.dump(values, file, indent=4, sort_keys=True)


@dataclass
class Config:
    """Thread-safe configuration container for MAMA settings."""

    # Lambda sensor settings
    AFR_STOCH: float = 14.68
    KORREKTURFAKTOR_BANK_1: float = 0.511
    KORREKTURFAKTOR_BANK_2: float = 0.511
    LAMDA0_CHANNEL: int = 0
    LAMDA1_CHANNEL: int = 1

    # Temperature sensor settings
    TEMPERATUR0_CHANNEL: int = 2
    TEMPERATUR1_CHANNEL: int = 3

    # Display settings
    ANZEIGEN_BANK_1: bool = True
    ANZEIGEN_BANK_2: bool = True
    ANZEIGEN_TEMP_1: bool = True
    ANZEIGEN_TEMP_2: bool = True
    NACHKOMMASTELLEN: int = 2
    WARNUNG_BLINKEN: bool = True

    # Timing settings
    MESSURE_INTERVAL: float = 0.01
    UPDATE_INTERVAL: float = 1.5

    # Database settings
    DB_DELETE_AELTER_ALS: int = 180

    # Internal lock (excluded from serialization)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Load settings from file after initialization."""
        self._reload_from_file()

    def _reload_from_file(self) -> None:
        """Reload all settings from the JSON file."""
        settings = _read_settings(setting_path)
        for key, value in settings.items():
            if hasattr(self, key) and not key.startswith("_"):
                setattr(self, key, value)

    def update_setting(self, name: str, value: str) -> None:
        """Update a single setting and persist to file.

        Args:
            name: Setting name (must be a valid config attribute)
            value: JSON-encoded value string
        """
        if not hasattr(self, name) or name.startswith("_"):
            raise ValueError(f"Unknown setting: {name}")

        with self._lock:
            settings = _read_settings(setting_path)
            settings[name] = json.loads(value)
            _save_settings(setting_path, settings)
            setattr(self, name, settings[name])

    def get_settings(self) -> dict[str, Any]:
        """Get all settings as a dictionary.

        Returns:
            Dictionary containing all configuration values.
        """
        with self._lock:
            return {f.name: getattr(self, f.name) for f in fields(self) if not f.name.startswith("_")}


config = Config()
