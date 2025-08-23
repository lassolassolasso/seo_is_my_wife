import os
import json
import subprocess

# ========== CONFIG ==========
BOTS = ["NimsiluBot", "ToromBot"]  # add more if needed
VARIANT = "crazyhouse"
MAX_GAMES = 2000000
MAX_PLY = 40
OUTPUT_PGN = "all_games.pgn"
BOOK_FILE = "book.bin"

# ========== FUNCTIONS ==========

def fetch_games(bot):
    """Fetch games from Lichess API using lichess-cli"""
    print(f"Fetching games for {bot}...")
    ndjson_file = f"{bot}_{VARIANT}.ndjson"
    subprocess.run([
        "lichess-cli", "games", bot,
        "--variant", VARIANT,
        "--max", str(MAX_GAMES),
        "--rated", "true",
        "--out", ndjson_file,
        "--moves", "--evals", "--pgnInJson"
    ], check=True)
    return ndjson_file


def filter_games(ndjson_file):
    """Filter and convert NDJSON to PGN"""
    print(f"Filtering {ndjson_file}...")
    pgns = []
    with open(ndjson_file, "r", encoding="utf-8") as f:
        for line in f:
            try:
                game = json.loads(line)
                if game.get("variant") != VARIANT:
                    continue
                if not game.get("moves"):
                    continue
                if len(game["moves"].split()) > MAX_PLY:
                    continue
                pgn = game.get("pgn")
                if pgn:
                    pgns.append(pgn)
            except Exception:
                continue
    return pgns


def compile_polyglot():
    """Compile book_make.cpp into polyglot binary"""
    if not os.path.exists("book_make.cpp"):
        print("Downloading book_make.cpp...")
        subprocess.run([
            "wget", "https://raw.githubusercontent.com/ddugovic/polyglot/master/book_make.cpp",
            "-O", "book_make.cpp"
        ], check=True)
    print("Compiling polyglot...")
    subprocess.run(["g++", "book_make.cpp", "-o", "polyglot"], check=True)


def build_book(pgn_file, book_file):
    """Build .bin Polyglot book"""
    print("Building Polyglot book...")
    subprocess.run([
        "./polyglot", "make-book",
        "-pgn", pgn_file,
        "-bin", book_file,
        "-max-ply", str(MAX_PLY),
        "-games", str(MAX_GAMES)
    ], check=True)


# ========== MAIN ==========
def main():
    all_pgns = []
    for bot in BOTS:
        ndjson = fetch_games(bot)
        all_pgns.extend(filter_games(ndjson))

    print(f"Writing {len(all_pgns)} games to {OUTPUT_PGN}...")
    with open(OUTPUT_PGN, "w", encoding="utf-8") as f:
        for pgn in all_pgns:
            f.write(pgn.strip() + "\n\n")

    compile_polyglot()
    build_book(OUTPUT_PGN, BOOK_FILE)
    print(f"✅ Done! Book saved to {BOOK_FILE}")


if __name__ == "__main__":
    main()
