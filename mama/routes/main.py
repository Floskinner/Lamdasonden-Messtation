"""Main application routes"""

import datetime

from flask import Blueprint
from flask import render_template

from mama.config import config

# No need to import template directories; Flask resolves by name

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/" aufgerufen wird
    Rendert und gibt das Template index.jinja zurück
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
        "update_intervall": getattr(config, "UPDATE_INTERVAL") * 1000,  # To convert to ms
    }
    template_data.update(config.get_settings())

    return render_template("index.jinja", **template_data)


@main_bp.route("/history", methods=["GET"])
def history():
    """Funktion wird aufgerufen wenn auf dem Webserver der Pfad "/history" aufgerufen wird
    Rendert und gibt das Template history.jinja zurück
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
    }

    return render_template("history.jinja", **template_data)
