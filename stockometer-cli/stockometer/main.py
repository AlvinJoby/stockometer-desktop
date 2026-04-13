import subprocess
import sys
import time

from .config import *
from .updater import *


def type_text(text, delay=0.002):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def show_banner():
    banner = r"""
    █████╗ ██╗     ██╗   ██╗██╗███╗   ██╗
   ██╔══██╗██║     ██║   ██║██║████╗  ██║
   ███████║██║     ██║   ██║██║██╔██╗ ██║
   ██╔══██║██║     ╚██╗ ██╔╝██║██║╚██╗██║
   ██║  ██║███████╗ ╚████╔╝ ██║██║ ╚████║
   ╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚═╝╚═╝  ╚═══╝
    """

    print("\n")
    type_text(banner, 0.0015)   # fast typing for big text
    time.sleep(0.3)


def run_exe():
    try:
        subprocess.Popen([str(EXE_PATH)])
    except FileNotFoundError:
        print("[stockometer] Executable not found.")


def main():
    show_banner()

    ensure_dirs()
    first_time_setup()
    replace_exe()

    run_exe()
    start_background_update()


if __name__ == "__main__":
    main()