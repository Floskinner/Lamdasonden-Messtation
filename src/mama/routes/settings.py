"""Settings and configuration routes"""

import json

from flask import Blueprint
from flask import request
from flask import Response

from mama.config import config

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["POST"])
def update_settings():
    """Update der Einstellungen

    :return: Response mit Statuscode 200 wenn erfolgreich. 400 wenn Fehler aufgetreten ist.
    """
    data: dict = request.form
    try:
        for key, value in data.items():
            if value == "":
                return Response(
                    json.dumps({"message": f"Invalid Value. Value of key {key} is empty"}),
                    status=400,
                    mimetype="application/json",
                )
            config.update_setting(key, value)
    except KeyError as error:
        print(error)
        return Response(
            json.dumps({"message": f"Invalid Key. Key {key} is invalid"}), status=400, mimetype="application/json"
        )
    except Exception as error:
        print(error)
        return Response(json.dumps({"message": f"Invalid Settings. {error}"}), status=400, mimetype="application/json")

    return Response("Success", status=200)


@settings_bp.route("/settings", methods=["GET"])
def get_settings():
    """Gibt die aktuellen Einstellungen zurück

    :return: Response mit Statuscode 200 wenn erfolgreich. JSON mit den Einstellungen als Inhalt.
    """
    return config.get_settings()
