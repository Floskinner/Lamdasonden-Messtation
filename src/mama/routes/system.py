"""System information routes"""
from flask import Blueprint
from flask import render_template
from mama.utils import raspi_status as pi

system_bp = Blueprint("system", __name__)


@system_bp.route("/system")
def system():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/system" aufgerufen wird
    Rendert und gibt das Template system.jinja zurück
    """

    system_data = {
        "os_version": pi.get_os_version(),
        "os_name": pi.get_hotname_ip(),
        "os_cpu": pi.get_cpu_usage(),
        "os_temperatur": pi.get_cpu_temp(),
        "os_ram_total": pi.get_ram_info().get("ram_total"),
        "os_ram_available": pi.get_ram_info().get("ram_available"),
        "os_ram_percent": pi.get_ram_info().get("ram_free_percent"),
        "os_disk_total": pi.get_disk_info().get("total"),
        "os_disk_used": pi.get_disk_info().get("used"),
        "os_disk_free": pi.get_disk_info().get("free"),
        "os_disk_free_percent": pi.get_disk_info().get("percent"),
    }

    return render_template("system.jinja", **system_data)
