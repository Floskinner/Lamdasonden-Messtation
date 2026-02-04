"""Main application routes."""

import datetime

from flask import Blueprint
from flask import render_template

from mama.config import config

main_bp = Blueprint("main", __name__)

RECALIBRATION_NEEDED = True


@main_bp.route("/")
def index():
    """Handle the root route ("/").

    Renders and returns the ``index.jinja`` template.
    """
    global RECALIBRATION_NEEDED

    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
        "update_intervall": getattr(config, "UPDATE_INTERVAL") * 1000,  # To convert to ms
        "RECALIBRATION_NEEDED": RECALIBRATION_NEEDED,
    }
    template_data.update(config.get_settings())

    # After the first load, recalibration is no longer needed.
    RECALIBRATION_NEEDED = False

    return render_template("index.jinja", **template_data)


@main_bp.route("/history", methods=["GET"])
def history():
    """Handle the history route ("/history").

    Renders and returns the ``history.jinja`` template.
    """
    now = datetime.datetime.now()
    current_year = now.strftime("%Y")

    template_data = {
        "current_year": current_year,
    }

    return render_template("history.jinja", **template_data)
