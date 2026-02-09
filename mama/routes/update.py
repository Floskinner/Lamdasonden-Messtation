"""Update routes for uploading and applying system updates"""

import datetime
import json
import tempfile
import traceback
from pathlib import Path

from flask import Blueprint, jsonify, render_template, request

from mama.utils.update import Updater, UPDATE_STATUS_FILE

update_bp = Blueprint("update", __name__)

# Store the updater instance between upload and start requests
_current_updater: Updater | None = None


def get_update_status() -> dict | None:
    """Read and clear update status file, returns status dict or None"""
    if UPDATE_STATUS_FILE.exists():
        try:
            data = json.loads(UPDATE_STATUS_FILE.read_text())
            UPDATE_STATUS_FILE.unlink()
            return data
        except (json.JSONDecodeError, OSError):
            UPDATE_STATUS_FILE.unlink()
            return None
    return None


@update_bp.route("/update")
def update_page():
    """Render the update page"""
    update_status = get_update_status()
    template_data = {
        "current_year": datetime.datetime.now().year,
        "update_status": update_status,
    }
    return render_template("update.jinja", **template_data)


@update_bp.route("/update/health")
def update_health():
    """Health check endpoint for pinging after update (doesn't consume status file)"""
    return jsonify({"status": "ok"})


@update_bp.route("/update/upload", methods=["POST"])
def update_upload():
    """Handle file upload and validate the update tarball"""
    global _current_updater

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided", "traceback": ""}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected", "traceback": ""}), 400

    if not file.filename.endswith((".tar.gz", ".gz")):
        return jsonify(
            {"success": False, "error": "Invalid file type. Please upload a .tar.gz file", "traceback": ""}
        ), 400

    try:
        # Save uploaded file to temp location
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / file.filename
        file.save(temp_path)

        # Create updater and validate
        _current_updater = Updater(temp_path)
        _current_updater.check_validity()

        return jsonify({"success": True, "message": "File uploaded and validated successfully"})

    except FileNotFoundError as e:
        _current_updater = None
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 400

    except ValueError as e:
        _current_updater = None
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 400

    except Exception as e:
        _current_updater = None
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@update_bp.route("/update/start", methods=["POST"])
def update_start():
    """Start the update process"""
    global _current_updater

    if _current_updater is None:
        return jsonify({"success": False, "error": "No valid update file uploaded", "traceback": ""}), 400

    try:
        # Start the update process (this will restart the service)
        _current_updater.update()

        # This line should not be reached if update succeeds
        return jsonify({"success": True, "message": "Update started"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500
