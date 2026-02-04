"""
Infos über den Pi bekommen
"""

import platform
import socket
from pathlib import Path
import psutil


def get_cpu_usage() -> float:
    """Gibt die aktuelle CPU auslastung

    Returns:
        float: CPU-Auslastung
    """
    cpu_usage = psutil.cpu_percent(interval=1)
    return cpu_usage


def get_cpu_temp() -> float:
    """Gibt die CPU Temperatur in Celsius

    Returns:
        float: Temperatur auf 2 Nachkommastellen gerundet
    """

    data_temp = psutil.sensors_temperatures()
    cpu_temp = data_temp.get("cpu_thermal", ((0, 0),))[0][1]
    cpu_temp = round(cpu_temp, 2)

    return cpu_temp


def get_os_version() -> str:
    """Gibt den release zurück zB. 5.10.11-v7l+

    Returns:
        str: Release
    """

    version = platform.release()
    return version


def get_hotname_ip() -> str:
    """Liefert den Hostnamenzurück
    Values = Error, wenn ein ein Fehler aufgetreten ist

    Returns:
        str: Hostname
    """

    try:
        host_name = socket.gethostname()

        return host_name
    except IOError as error:
        print(f"Error: {error}")
        return "Error"


def get_ram_info() -> dict:
    """RAM infos ("ram_total", "ram_available", "ram_free_percent")

    Returns:
        dict: Data in MB
    """
    ram_total = round(psutil.virtual_memory().total / (1024 * 1024))
    ram_available = round(psutil.virtual_memory().available / (1024 * 1024))
    ram_free_percent = round((100 / ram_total) * ram_available, 2)

    ram_info = {"ram_total": ram_total, "ram_available": ram_available, "ram_free_percent": ram_free_percent}

    return ram_info


def get_disk_info() -> dict:
    """Freier Speicher vom Pfad "/" in GB

    Returns:
        dict: "total", "used", "free", "percent"
    """

    disk_total = round(psutil.disk_usage("/").total / (1024 * 1024 * 1024), 2)
    disk_used = round(psutil.disk_usage("/").used / (1024 * 1024 * 1024), 2)
    disk_free = round(psutil.disk_usage("/").free / (1024 * 1024 * 1024), 2)
    disk_free_percent = 100 - round(psutil.disk_usage("/").percent, 2)

    data = {"total": disk_total, "used": disk_used, "free": disk_free, "percent": disk_free_percent}

    return data


def get_systemd_journal() -> Path:
    """Returns default path to systemd journal log file"""
    persistent_journal_path = Path("/var/log/journal")
    return persistent_journal_path if persistent_journal_path.exists() else Path("/run/log/journal")
