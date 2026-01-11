"""API routes for data retrieval"""

import json

from flask import Blueprint
from flask import request
from flask import Response

from mama.models.database import db_connection

api_bp = Blueprint("api", __name__)


@api_bp.route("/tempdata", methods=["GET"])
def get_temp_data_between():
    """Returns temperature data between two timestamps

    :return: Response with status code 200 if successful. 400 if an error occurred.
    """
    data: dict = request.args
    try:
        start_time = data["start_time"]
        end_time = data["end_time"]
    except KeyError as error:
        print(error)
        return Response("{'message':'Invalid values'}", status=400, mimetype="application/json")

    return Response(
        json.dumps(db_connection.get_temp_values_between(start_time, end_time)),
        status=200,
        mimetype="application/json",
    )


@api_bp.route("/reset_temp_sensors", methods=["POST"])
def reset_temp_sensors():
    """Resets the lifespan of the temperature sensors

    :return: Response with status code 200 if successful. 400 if an error occurred.
    """
    data: dict = request.form
    db_connection.update_temp_sensor_tracking(int(data["sensor"]), 0)
    db_connection.reset_error_state(int(data["sensor"]))
    return Response("Success", status=200)


@api_bp.route("/lambdadata", methods=["GET"])
def get_lambda_data_between():
    """Returns lambda data between two timestamps
    :return: Response with status code 200 if successful. 400 if an error occurred.
    """
    data: dict = request.args
    try:
        start_time = data["start_time"]
        end_time = data["end_time"]
    except KeyError as error:
        print(error)
        return Response("{'message':'Invalid values'}", status=400, mimetype="application/json")

    return Response(
        json.dumps(db_connection.get_lambda_values_between(start_time, end_time)),
        status=200,
        mimetype="application/json",
    )
