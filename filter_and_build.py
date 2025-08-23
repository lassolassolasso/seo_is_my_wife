import requests
import json
import chess.pgn
import io
import subprocess

# Config
BOTS = ["NimsiluBot", "ToromBot"]
VARIANT = "crazyhouse"
MAX_GAMES = 2000000
MIN_RATING = 2250
MAX_PLY = 40

def fetch_games(bot):
    print(f"Fetching games for {bot}...")
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": MAX_GAMES,
        "perfType": VARIANT,
        "rated": "true",
        "clocks": "true",
        "evals": "false",
        "pgnInJson": "true",
    }
    headers = {"Accept": "application/x-ndjson"}
    response = requests.get(url, params=params, headers=headers, stream=True)
    response.raise_for_status()
    filename = f"{bot}_{VARIANT}.ndjson"
    with open(filename, "w", encoding="utf-8") as f:
        for line in response.iter_lines():
            if line:
                f.write(line.decode("utf-8") + "\n")
    return filename

def filter_games(filename):
    print(f"Filtering {filename}...")
    pgns = []
    with open(filename, encoding="utf-8") as f:
        for line in f:
            game = json.loads(line.strip())
            try:
                white_rating = game["players"]["white"]["rating"]
                black_rating = game["players"]["black"]["rating"]
                if white_rating < MIN_RATING or black_rating < MIN_RATING:
                    continue
                if game.get("variant") != VARIANT:
                    continue

                pgn_str = game["pgn"]
                pgn_io = io.StringIO(pgn_str)
                pgn_game = chess.pgn.read_game(pgn_io)
                if pgn_game is None:
                    continue
                if pgn_game.end().board().ply() > MAX_PLY:
                    continue

                pgns.append(pgn_str)
            except Exception:
                continue
    return pgns

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson_file = fetch_games(bot)
        all_pgns.extend(filter_games(ndjson_file))

    # Save PGNs
    pgn_file = "crazyhouse_games.pgn"
    with open(pgn_file, "w", encoding="utf-8") as f:
        for g in all_pgns:
            f.write(g + "\n\n")

    # Build Polyglot book
    print("Building Polyglot book...")
    with open("crazyhouse_games.pgn", "r") as f:
        subprocess.run([
            "polyglot", "make-book",
            "-pgn", "crazyhouse_games.pgn",
            "-bin", "crazyhouse_book.bin",
            "-max-ply", str(MAX_PLY)
        ], check=True)

    print(f"✅ Saved {len(all_pgns)} games to book: crazyhouse_book.bin")

if __name__ == "__main__":
    main()
