import json
import tarfile
import traceback
import multiprocessing
import tempfile
from pathlib import Path
import os
from datetime import datetime

SYSTEMD_SERVICE = "mama.service"
UPDATE_STATUS_FILE = Path("/tmp/mama-update-status.json")


def write_update_status(status: str, error: str | None = None, tb: str | None = None):
    """Write update status to JSON file for persistence across restarts"""
    data = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if error:
        data["error"] = error
    if tb:
        data["traceback"] = tb
    UPDATE_STATUS_FILE.write_text(json.dumps(data, indent=2))


# Development mode uses /tmp/mama-test as base path
if os.environ.get("FLASK_ENV") == "development":
    DEV_BASE = Path("/tmp/mama-test")
    APPLICATION_LOCATION = DEV_BASE / "home/pi/mama"
    PYTHON_LOCATION = DEV_BASE
    SYSTEM_LOCATION = DEV_BASE
    IS_DEVELOPMENT = True
else:
    APPLICATION_LOCATION = Path("/home/pi/mama")
    PYTHON_LOCATION = Path("/")
    SYSTEM_LOCATION = Path("/")
    IS_DEVELOPMENT = False


class Updater:
    def __init__(self, source_tar: Path):
        if not (source_tar.exists() and tarfile.is_tarfile(source_tar)):
            raise ValueError(f"Invalid source tar file: {source_tar}")

        self.source_path = source_tar
        self.tempdir = Path(tempfile.mkdtemp())

        with tarfile.open(self.source_path, "r:gz") as tar:
            tar.extractall(path=self.tempdir)

        self.application_tar = Path(self.tempdir) / "application.tar.gz"
        self.system_tar = Path(self.tempdir) / "system.tar.gz"
        self.python_tar = Path(self.tempdir) / "python312.tar.gz"

    def __del__(self):
        self.tempdir.unlink(missing_ok=True)

    def update(self):
        """Starts the update proccess"""
        self.proc = multiprocessing.Process(target=self._update, daemon=False)
        self.proc.start()

        self.proc.join()
        raise RuntimeError("Updater process did not stop the main process as expected. Update failed!")

    def check_validity(self):
        if not (self.application_tar.exists() and tarfile.is_tarfile(self.application_tar)):
            raise FileNotFoundError("application.tar.gz not found in the updater tarball")

        if not (self.system_tar.exists() and tarfile.is_tarfile(self.system_tar)):
            raise FileNotFoundError("system.tar.gz not found in the updater tarball")

        if self.python_tar.exists():
            if not tarfile.is_tarfile(self.python_tar):
                raise FileNotFoundError("python312.tar.gz is not a valid tarball in the updater tarball")

    def _update(self):
        try:
            self.check_validity()

            # In development mode, skip systemd commands and just extract to test location
            if IS_DEVELOPMENT:
                # Ensure base directories exist
                APPLICATION_LOCATION.mkdir(parents=True, exist_ok=True)
                SYSTEM_LOCATION.mkdir(parents=True, exist_ok=True)
                print(f"Development mode: extracting to {DEV_BASE}")
            else:
                # 1. All required files exists. Stop the systemd service
                os.system(f"systemctl stop {SYSTEMD_SERVICE}")

            # 2. Extract the files
            with tarfile.open(self.system_tar, "r:gz") as tar:
                tar.extractall(SYSTEM_LOCATION)

            with tarfile.open(self.application_tar, "r:gz") as tar:
                tar.extractall(APPLICATION_LOCATION)

            # Optional python
            if self.python_tar.exists():
                with tarfile.open(self.python_tar, "r:gz") as tar:
                    tar.extractall(PYTHON_LOCATION)

            # Write success status file before restarting (will be read by new app instance)
            write_update_status("success")

            if not IS_DEVELOPMENT:
                os.system("systemctl daemon-reload")
                os.system(f"systemctl start {SYSTEMD_SERVICE}")
            else:
                print(f"Development mode: update complete. Files extracted to {DEV_BASE}")

        except Exception as error:
            # Write error status with traceback
            write_update_status("error", error=str(error), tb=traceback.format_exc())
            print(f"Update failed: {error}")

            # Try to restart the service even on error so user can see the error
            if not IS_DEVELOPMENT:
                os.system(f"systemctl start {SYSTEMD_SERVICE}")
