import threading
import subprocess
import os
import requests

from .config import *
from .utils import download_file


def get_latest_release():
    res = requests.get(GITHUB_API)
    res.raise_for_status()
    data = res.json()

    version = data["tag_name"]

    for asset in data["assets"]:
        if asset["name"].endswith(".exe"):
            return version, asset["browser_download_url"]

    raise Exception("No .exe found in release assets")

def get_local_version():
    if not VERSION_FILE.exists():
        return None
    return VERSION_FILE.read_text().strip()


def save_version(version):
    VERSION_FILE.write_text(version)


def replace_exe():
    if NEW_EXE_PATH.exists():
        try:
            os.replace(NEW_EXE_PATH, EXE_PATH)
        except Exception:
            pass  # will retry next run


def update_if_needed():
    try:
        latest_version, url = get_latest_release()
        local_version = get_local_version()

        if local_version == latest_version:
            return

        print("[stockometer] Updating in background...")

        download_file(url, NEW_EXE_PATH)

        replace_exe()
        save_version(latest_version)

        print("[stockometer] Updated to", latest_version)

    except Exception:
        pass  # silent fail


def start_background_update():
    thread = threading.Thread(target=update_if_needed, daemon=True)
    thread.start()


def first_time_setup():
    if EXE_PATH.exists():
        return

    print("[yourtool] First time setup: downloading tool...")

    latest_version, url = get_latest_release()
    download_file(url, EXE_PATH)
    save_version(latest_version)