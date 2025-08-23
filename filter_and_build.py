# crazyhouse_book.py
import requests
import os
import subprocess

BOTS = ["NimsiluBot", "ToromBot"]   # you can add more bots here
VARIANT = "crazyhouse"
PGN_FILE = "crazyhouse_games.pgn"
BOOK_FILE = "crazyhouse_book.bin"


def fetch_games(bot):
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": 500,   # number of games per bot
        "perfType": VARIANT,
        "rated": "true",
        "moves": "true",
        "pgnInJson": "false"
    }
    headers = {"Accept": "application/x-ndjson"}

    r = requests.get(url, params=params, headers=headers, stream=True)
    pgn_file = f"{bot}_{VARIANT}.pgn"
    with open(pgn_file, "w", encoding="utf-8") as f:
        for line in r.iter_lines():
            if line:
                f.write(line.decode("utf-8") + "\n")

    return pgn_file


def merge_pgns(pgn_files):
    with open(PGN_FILE, "w", encoding="utf-8") as outfile:
        for fname in pgn_files:
            with open(fname, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())


def build_book():
    # assumes polyglot is already installed in your repo
    subprocess.run([
        "polyglot",
        "make-book",
        "-pgn", PGN_FILE,
        "-bin", BOOK_FILE,
        "-max-ply", "40",
        "-max-games", "2000000"
    ], check=True)


def main():
    pgns = []
    for bot in BOTS:
        print(f"Fetching {VARIANT} games for {bot}...")
        pgns.append(fetch_games(bot))

    print("Merging PGNs...")
    merge_pgns(pgns)

    print("Building book...")
    build_book()
    print("Done! Book saved as", BOOK_FILE)


if __name__ == "__main__":
    main()
