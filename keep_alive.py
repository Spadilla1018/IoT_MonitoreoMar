import threading
import requests
import time

def keep_alive():
    while True:
        try:
            requests.get("https://simmar-iot.onrender.com")
        except:
            pass
        time.sleep(840)

def start():
    t = threading.Thread(target=keep_alive)
    t.daemon = True
    t.start()