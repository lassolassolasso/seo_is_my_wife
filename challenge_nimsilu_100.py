import os
import requests
import time

TOKEN = os.getenv("TOKEN")  # Read from GitHub Actions secrets securely
BOT_NAME = "NimsiluBot"
TOTAL_GAMES = 100
SLEEP_BETWEEN = 1.5  # Delay between challenges

if not TOKEN:
    raise ValueError("TOKEN environment variable not set!")

def challenge_nimsilu():
    url = f"https://lichess.org/api/challenge/{BOT_NAME}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "clock.limit": 30,         # 30 seconds = ½ minute
        "clock.increment": 0,
        "rated": False,
        "color": "random",
        "variant": "chess960"
    }

    for i in range(1, TOTAL_GAMES + 1):
        print(f"Sending challenge {i}/{TOTAL_GAMES} to {BOT_NAME}...")
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            print(f"  ✅ Challenge {i} sent.")
        else:
            print(f"  ❌ Challenge {i} failed! Status: {response.status_code} | {response.text}")

        time.sleep(SLEEP_BETWEEN)

if __name__ == "__main__":
    challenge_nimsilu()
