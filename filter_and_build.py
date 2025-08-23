import requests
import subprocess
import os
import json

# Bots to fetch games from
BOTS = ["NimsiluBot", "ToromBot"]

# Config
MAX_GAMES = 2000000   # max games per bot
VARIANT = "crazyhouse"
MAX_PLY = 40          # book depth

def fetch_games(bot):
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": MAX_GAMES,
        "perfType": VARIANT,
        "moves": "true",
        "pgnInJson": "true",
    }
    headers = {"Accept": "application/x-ndjson"}

    out_file = f"{bot}.ndjson"
    print(f"Fetching {VARIANT} games for {bot}...")
    r = requests.get(url, params=params, headers=headers, stream=True)
    r.raise_for_status()
    with open(out_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    return out_file

def ndjson_to_pgn(ndjson_file):
    pgn_file = ndjson_file.replace(".ndjson", ".pgn")
    print(f"Converting {ndjson_file} -> {pgn_file}...")
    with open(ndjson_file, "r", encoding="utf-8") as f_in, open(pgn_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            if line.strip():
                game = json.loads(line)
                if "pgn" in game:
                    f_out.write(game["pgn"] + "\n\n")
    return pgn_file

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson_file = fetch_games(bot)
        pgn_file = ndjson_to_pgn(ndjson_file)
        all_pgns.append(pgn_file)

    merged_pgn = f"{VARIANT}_games.pgn"
    print(f"Merging all PGNs into {merged_pgn}...")
    with open(merged_pgn, "w", encoding="utf-8") as out:
        for pgn in all_pgns:
            with open(pgn, "r", encoding="utf-8") as f:
                out.write(f.read())

    print("Compiling Polyglot book builder...")
    subprocess.run(["g++", "-O2", "book_make.cpp", "-o", "bookbuilder"], check=True)

    output_bin = f"{VARIANT}_book.bin"
    print(f"Building {output_bin} (depth {MAX_PLY})...")
    subprocess.run(["./bookbuilder", "make-book", merged_pgn, output_bin, str(MAX_PLY)], check=True)

    print("Done! Book saved as", output_bin)

if __name__ == "__main__":
    main()
