import threading
import webbrowser
import time
import sys
import os

# --- define base path FIRST ---
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# --- debug prints ---
print("BASE PATH:", base_path)
print("FILES:", os.listdir(base_path))
print("STOCKOMETER EXISTS:", os.path.exists(os.path.join(base_path, "stockometer")))

# --- fix import paths ---
sys.path.insert(0, base_path)
sys.path.insert(0, os.path.join(base_path, "stockometer"))

# --- import AFTER path fix ---
from stockometer.app import app


def open_browser():
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5050")


if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    app.run(debug=True, use_reloader=False,port=5050)