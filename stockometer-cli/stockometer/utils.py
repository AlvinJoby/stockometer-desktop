import requests
import threading
import itertools
import sys
import time

def spinner(stop_event, message="Loading"):
    for char in itertools.cycle("|/-\\"):
        if stop_event.is_set():
            break
        sys.stdout.write(f"\r{message} {char}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r")

def download_file(url, path):
    stop_event = threading.Event()
    t = threading.Thread(target=spinner, args=(stop_event, "Downloading"))
    t.start()

    r = requests.get(url, stream=True)
    r.raise_for_status()

    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    stop_event.set()
    t.join()

    print("> Download complete :)")