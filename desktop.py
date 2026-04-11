import threading
import sys
import os
import webview

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


def start_flask():
    app.run(
        host="127.0.0.1",
        port=5050,
        debug=False,
        use_reloader=False
    )


if __name__ == "__main__":
    # start flask in background
    threading.Thread(target=start_flask, daemon=True).start()

    # create native desktop window
    webview.create_window(
        "Stockometer",
        "http://127.0.0.1:5050",
        width=1200,
        height=800
    )

    # start GUI loop
    webview.start()