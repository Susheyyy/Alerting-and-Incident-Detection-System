import time
import random
import requests

APP_URL = "http://app:8000"

def run_traffic():
    print("Starting background traffic generator targeting:", APP_URL)
    endpoints = ["/", "/api/items", "/health"]
    while True:
        target = random.choice(endpoints)
        try:
            r = requests.get(f"{APP_URL}{target}", timeout=5)
            
        except Exception:
            pass
        time.sleep(random.uniform(0.1, 0.5))

if __name__ == "__main__":
    time.sleep(3) 
    run_traffic()
