import requests
import time


def safeGet(url, params):
    waitTime = 65
    attempts = 3
    for attempt in range(attempts):
        try:
            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 429:
                print(f"Rate limit reached: Attempt {attempt + 1} of {attempts}")
                time.sleep(waitTime)
                continue

            if response.status_code >= 500 and response.status_code < 600:
                print(f"Server error: Attempt {attempt + 1} of 2")
                time.sleep(waitTime)
                continue

            return response
        except:
            pass