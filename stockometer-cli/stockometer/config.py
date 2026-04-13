import os
from pathlib import Path

APP_NAME = "stockometer"

BASE_DIR = Path.home() / f".{APP_NAME}"
EXE_PATH = BASE_DIR / "stockometer.exe"
NEW_EXE_PATH = BASE_DIR / "stockometer_latest.exe"
VERSION_FILE = BASE_DIR / "version.txt"

GITHUB_API = "https://api.github.com/repos/AlvinJoby/stockometer-desktop/releases/latest"
def ensure_dirs():
    BASE_DIR.mkdir(parents=True, exist_ok=True)