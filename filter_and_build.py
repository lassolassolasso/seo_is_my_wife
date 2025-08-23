import requests
import json
import subprocess
import os

# Config
BOTS = ["NimsiluBot", "ToromBot"]
MAX_PLY = 40
MAX_GAMES = 2000000
VARIANT = "crazyhouse"

def fetch_games(bot):
    print(f"Fetching games for {bot}...")
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": 1000,
        "perfType": VARIANT,
        "rated": "true",
        "analysed": "true",
        "pgnInJson": "true",
        "clocks": "false",
        "evals": "false"
    }
    headers = {"Accept": "application/x-ndjson"}
    r = requests.get(url, params=params, headers=headers, stream=True)
    filename = f"{bot}_{VARIANT}.ndjson"
    with open(filename, "w", encoding="utf-8") as f:
        for line in r.iter_lines():
            if line:
                f.write(line.decode("utf-8") + "\n")
    return filename

def filter_games(ndjson_file):
    print(f"Filtering {ndjson_file}...")
    pgns = []
    with open(ndjson_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                game = json.loads(line)
            except json.JSONDecodeError:
                continue
            if game.get("variant") != VARIANT:
                continue
            moves = game.get("moves", "").split()
            if len(moves) > MAX_PLY:
                continue
            pgn = game.get("pgn")
            if pgn:
                pgns.append(pgn)
            if len(pgns) >= MAX_GAMES:
                break
    return pgns

def build_polyglot(pgn_file, book_file):
    print("Building Polyglot book...")
    cpp_code = r'''
    #include <iostream>
    #include <fstream>
    #include "polyglot.h"
    int main(int argc, char** argv) {
        if (argc < 3) {
            std::cerr << "Usage: book_make <pgn> <bin>\n";
            return 1;
        }
        std::ifstream pgn(argv[1]);
        if (!pgn) {
            std::cerr << "Cannot open PGN file\n";
            return 1;
        }
        std::ofstream bin(argv[2], std::ios::binary);
        if (!bin) {
            std::cerr << "Cannot open BIN file\n";
            return 1;
        }
        // minimal polyglot book creation (stub)
        // in production, use full polyglot code
        bin << "POLYGLOTBOOK";
        return 0;
    }
    '''
    with open("book_make.cpp", "w") as f:
        f.write(cpp_code)
    # Compile
    subprocess.run(["g++", "book_make.cpp", "-o", "bookbuilder"], check=True)
    # Run
    subprocess.run(["./bookbuilder", pgn_file, book_file], check=True)

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson_file = fetch_games(bot)
        all_pgns.extend(filter_games(ndjson_file))
    # Save PGNs
    pgn_file = "all_games.pgn"
    with open(pgn_file, "w", encoding="utf-8") as f:
        for pgn in all_pgns:
            f.write(pgn + "\n\n")
    # Build Polyglot
    build_polyglot(pgn_file, "book.bin")
    print("Done! book.bin created.")

if __name__ == "__main__":
    main()
