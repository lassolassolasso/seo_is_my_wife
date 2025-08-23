import requests
import json
import os
import subprocess

BOTS = [
    "NimsiluBot",
    "ToromBot"
]

MAX_GAMES = 2000000
MAX_PLY = 40

def fetch_games(bot):
    print(f"Fetching games for {bot}...")
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": MAX_GAMES,
        "perfType": "crazyhouse",
        "rated": "true",
        "analysed": "false",
        "clocks": "false",
        "evals": "false",
        "opening": "true",
        "moves": "true",
        "pgnInJson": "true",
    }
    headers = {"Accept": "application/x-ndjson"}
    resp = requests.get(url, params=params, headers=headers, stream=True)

    filename = f"{bot}_crazyhouse.ndjson"
    with open(filename, "w", encoding="utf-8") as f:
        for line in resp.iter_lines():
            if line:
                f.write(line.decode("utf-8") + "\n")
    return filename

def filter_games(ndjson_file):
    pgn_file = ndjson_file.replace(".ndjson", ".pgn")
    print(f"Filtering {ndjson_file} -> {pgn_file}...")
    with open(ndjson_file, "r", encoding="utf-8") as fin, open(pgn_file, "w", encoding="utf-8") as fout:
        for line in fin:
            game = json.loads(line)
            if "moves" not in game or "players" not in game:
                continue
            moves = game["moves"].split()
            if len(moves) > MAX_PLY:
                moves = moves[:MAX_PLY]
            fout.write(game["pgn"] + "\n")
    return pgn_file

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson = fetch_games(bot)
        pgn = filter_games(ndjson)
        all_pgns.append(pgn)

    merged_pgn = "crazyhouse_games.pgn"
    with open(merged_pgn, "w", encoding="utf-8") as fout:
        for pgn in all_pgns:
            with open(pgn, "r", encoding="utf-8") as fin:
                fout.write(fin.read())
    print(f"Merged all PGNs -> {merged_pgn}")

    print("Compiling Polyglot book builder...")
    subprocess.run(["g++", "-O2", "book_make.cpp", "-o", "bookbuilder"], check=True)

    print("Building Polyglot book...")
    subprocess.run(["./bookbuilder", "make", "crazyhouse_games.pgn", "crazyhouse_book.bin"], check=True)

    print("✅ Done! Book saved as crazyhouse_book.bin")

if __name__ == "__main__":
    main()
