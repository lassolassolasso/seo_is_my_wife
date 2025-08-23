import os
import json
import subprocess

BOTS = ["NimsiluBot", "ToromBot"]   # ✅ Add more bots if you want
VARIANT = "crazyhouse"
MIN_RATING = 2250

def filter_games(ndjson_file):
    games = []
    with open(ndjson_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            game = json.loads(line)  # ✅ safe JSON parsing

            # filter by variant + rating
            if (
                game.get("variant") == VARIANT
                and "players" in game
                and any(
                    p.get("rating", 0) >= MIN_RATING
                    for p in game["players"].values()
                )
            ):
                if "pgn" in game:
                    games.append(game["pgn"])
    return games


def save_pgn(games, filename):
    with open(filename, "w", encoding="utf-8") as f:
        for g in games:
            f.write(g + "\n\n")


def build_polyglot(pgn_file, book_file):
    subprocess.run([
        "polyglot", "make-book",
        "-pgn", pgn_file,
        "-bin", book_file,
        "-max-ply", "40",   # ✅ deeper lines
        "-min-game", "3"    # only include moves seen in ≥3 games
    ], check=True)


def main():
    all_pgns = []
    for bot in BOTS:
        ndjson_file = f"{bot}_{VARIANT}.ndjson"
        print(f"Fetching games for {bot}...")
        subprocess.run([
            "lichess-cli", "games", bot,
            "--variant", VARIANT,
            "--max", "2000000",   # ✅ fetch A LOT
            "--ndjson", ndjson_file
        ], check=True)

        print(f"Filtering {ndjson_file}...")
        all_pgns.extend(filter_games(ndjson_file))

    print(f"Total games after filtering: {len(all_pgns)}")
    pgn_file = f"{VARIANT}_games.pgn"
    book_file = f"{VARIANT}_book.bin"

    save_pgn(all_pgns, pgn_file)

    print("Building Polyglot book...")
    build_polyglot(pgn_file, book_file)
    print(f"✅ Saved {len(all_pgns)} games to book: {book_file}")


if __name__ == "__main__":
    main()
