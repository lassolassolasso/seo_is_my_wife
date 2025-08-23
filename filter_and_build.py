import requests
import subprocess
import os

BOTS = ["NimsiluBot", "ToromBot"]
VARIANT = "crazyhouse"
OUTPUT_PGN = "merged.pgn"
BOOK_BIN = "book.bin"
MAX_PLY = "40"
MAX_GAMES = "2000000"

def fetch_games(bot):
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": 5550000,
        "perfType": VARIANT,
        "analysed": "false",
        "clocks": "false",
        "evals": "false",
        "moves": "true",
        "pgnInJson": "false"
    }
    headers = {"Accept": "application/x-chess-pgn"}
    print(f"Fetching {VARIANT} games for {bot}...")
    r = requests.get(url, params=params, headers=headers, stream=True)
    r.raise_for_status()
    fname = f"{bot}.pgn"
    with open(fname, "w", encoding="utf-8") as f:
        for chunk in r.iter_content(chunk_size=1024, decode_unicode=True):
            f.write(chunk)
    return fname

def merge_pgns(files, output):
    print("Merging PGNs...")
    with open(output, "w", encoding="utf-8") as outfile:
        for fname in files:
            with open(fname, "r", encoding="utf-8") as infile:
                outfile.write(infile.read())
                outfile.write("\n")

def build_book():
    print("Building book...")
    subprocess.run([
        "./bookbuilder", "make",
        "-pgn", OUTPUT_PGN,
        "-bin", BOOK_BIN,
        "-max-ply", MAX_PLY,
        "-max-games", MAX_GAMES
    ], check=True)

def main():
    pgn_files = []
    for bot in BOTS:
        pgn_files.append(fetch_games(bot))
    merge_pgns(pgn_files, OUTPUT_PGN)
    build_book()

if __name__ == "__main__":
    main()
