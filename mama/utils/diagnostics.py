from pathlib import Path
from tempfile import TemporaryDirectory
import tarfile
from typing import Generator
from mama.utils import raspi_status
import shutil
import json
from contextlib import contextmanager


@contextmanager
def diagnostic_tar() -> Generator[Path, None, None]:
    """Create a tar file of all logs and system information for diagnostics and later debugging."""

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "diagnostics"
        temp_path.mkdir(parents=True, exist_ok=True)

        # 1. Collect system informations and save them to a temp file
        system_info_file = temp_path / "system_info.json"
        system_info = {
            "os_version": raspi_status.get_os_version(),
            "hostname": raspi_status.get_hotname_ip(),
            "cpu_usage": raspi_status.get_cpu_usage(),
            "cpu_temp": raspi_status.get_cpu_temp(),
            "ram_info": raspi_status.get_ram_info(),
            "disk_info": raspi_status.get_disk_info(),
        }
        with system_info_file.open("w") as f:
            json.dump(system_info, f, indent=4)

        # 2. Collect systemd journal logs
        journald_folder = temp_path / "journald_logs"
        journald_folder.mkdir(parents=True, exist_ok=True)

        systemd_journal_path = raspi_status.get_systemd_journal()
        if systemd_journal_path.exists():
            for item in systemd_journal_path.iterdir():
                if item.is_dir():
                    dest = journald_folder / item.name
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, journald_folder / item.name)

        # 3. Create tar file
        tar_path = Path(temp_dir) / "diagnostics.tar.gz"
        with tarfile.open(tar_path, "x:gz") as tar:
            tar.add(temp_path, arcname="diagnostics")

        yield tar_path
