import requests
import chess.pgn
import io
import os
import subprocess

# Settings
BOTS = ["NimsiluBot", "ToromBot"]
VARIANT = "crazyhouse"
MIN_RATING = 2250

MERGED_PGN = f"{VARIANT}_games.pgn"
BOOK_FILE = f"{VARIANT}_book.bin"

def fetch_games(bot):
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": 5000,
        "perfType": VARIANT,
        "rated": "true",
        "analysed": "false",
        "pgnInJson": "true",
    }
    headers = {"Accept": "application/x-ndjson"}
    print(f"Fetching games for {bot}...")
    r = requests.get(url, params=params, headers=headers, stream=True)
    fname = f"{bot}_{VARIANT}.ndjson"
    with open(fname, "wb") as f:
        for line in r.iter_lines():
            if line:
                f.write(line + b"\n")
    return fname

def filter_games(ndjson_file):
    print(f"Filtering {ndjson_file}...")
    pgns = []
    with open(ndjson_file, "r", encoding="utf-8") as f:
        for line in f:
            game = eval(line)  # JSON object
            if "players" not in game:
                continue
            white = game["players"].get("white", {})
            black = game["players"].get("black", {})
            wr = white.get("rating", 0)
            br = black.get("rating", 0)
            if wr >= MIN_RATING and br >= MIN_RATING:
                if "pgn" in game:
                    pgns.append(game["pgn"])
    return pgns

def merge_and_save(pgns, filename):
    print(f"Merging PGNs...")
    with open(filename, "w", encoding="utf-8") as f:
        for pgn in pgns:
            f.write(pgn.strip() + "\n\n")
    print(f"✅ Saved merged PGN to {filename}")

def build_polyglot(pgn_file, book_file):
    print("Building Polyglot book...")
    cmd = f"./bookbuilder make-book -pgn {pgn_file} -bin {book_file} -max-ply 20"
    subprocess.run(cmd, shell=True, check=True)
    print(f"✅ Saved book: {book_file}")

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson_file = fetch_games(bot)
        all_pgns.extend(filter_games(ndjson_file))

    if not all_pgns:
        print("❌ No games found above rating filter.")
        return

    merge_and_save(all_pgns, MERGED_PGN)
    build_polyglot(MERGED_PGN, BOOK_FILE)

if __name__ == "__main__":
    main()
