import requests
import json
import os
import subprocess

BOTS = {"ToromBot", "NimsiluBot"}
MIN_ELO = 2800

def fetch_games(username, filename):
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": 200000,
        "perfType": "antichess",
        "rated": "true",
        "evals": "false",
        "clocks": "false",
        "opening": "true",
        "pgnInJson": "true"
    }
    headers = {"Accept": "application/x-ndjson"}
    with requests.get(url, params=params, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(filename, "w", encoding="utf-8") as f:
            for line in r.iter_lines():
                if line:
                    f.write(line.decode("utf-8") + "\n")

def filter_games(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            game = json.loads(line)
            if "players" not in game: 
                continue
            try:
                white = game["players"]["white"]["user"]["name"]
                black = game["players"]["black"]["user"]["name"]
                w_elo = game["players"]["white"].get("rating", 0)
                b_elo = game["players"]["black"].get("rating", 0)
            except Exception:
                continue

            if white in BOTS and black in BOTS and w_elo >= MIN_ELO and b_elo >= MIN_ELO:
                if "pgn" in game:
                    out.write(game["pgn"] + "\n\n")

def main():
    print("Fetching games...")
    fetch_games("NimsiluBot", "nimsilu_antichess.ndjson")
    fetch_games("ToromBot", "torom_antichess.ndjson")

    print("Filtering...")
    filter_games("nimsilu_antichess.ndjson", "nimsilu_filtered.pgn")
    filter_games("torom_antichess.ndjson", "torom_filtered.pgn")

    print("Merging...")
    with open("torom_nimsilu_2800plus.pgn", "w", encoding="utf-8") as out:
        for f in ["nimsilu_filtered.pgn", "torom_filtered.pgn"]:
            with open(f, "r", encoding="utf-8") as g:
                out.write(g.read())

    print("Building Polyglot book...")
    subprocess.run([
        "./polyglot/make-book",
        "torom_nimsilu_2800plus.pgn",
        "book.bin"
    ], check=True)

    print("Done. book.bin created.")

if __name__ == "__main__":
    main()
