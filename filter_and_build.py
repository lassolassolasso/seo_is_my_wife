import requests
import subprocess

BOTS = ["NimsiluBot", "ToromBot"]
PGN_FILE = "merged.pgn"
BOOK_FILE = "crazyhouse_book.bin"

def fetch_games(bot):
    print(f"Fetching crazyhouse games for {bot}...")
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": 5000,
        "perfType": "crazyhouse",
        "rated": "true",
        "clocks": "false",
        "evals": "false",
        "moves": "true",
        "pgnInJson": "false"
    }
    headers = {"Accept": "application/x-chess-pgn"}
    resp = requests.get(url, params=params, headers=headers, stream=True)

    if resp.status_code != 200:
        print(f"Error fetching {bot}: {resp.status_code}")
        return ""

    return resp.text

def save_pgn(all_games):
    with open(PGN_FILE, "w", encoding="utf-8") as f:
        f.write(all_games)
    print(f"Merged PGN saved: {PGN_FILE}")

def build_book():
    print("Building book...")
    subprocess.run([
        "./bookbuilder",
        "merge",
        "-pgn", PGN_FILE,
        "-bin", BOOK_FILE,
        "-max-ply", "32",
        "-max-games", "5000000"
    ], check=True)
    print(f"Book built: {BOOK_FILE}")

def main():
    all_games = ""
    for bot in BOTS:
        all_games += fetch_games(bot) + "\n"

    save_pgn(all_games)
    build_book()

if __name__ == "__main__":
    main()
