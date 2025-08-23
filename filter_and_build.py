import subprocess

INPUT_PGN = "antichess.pgn"
FILTERED_PGN = "antichess_2800plus.pgn"
BOOK_BIN = "book.bin"

def filter_games(input_pgn, output_pgn, min_elo=2800):
    with open(input_pgn, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    games, game = [], []
    for line in lines:
        if line.strip() == "":
            if check_rating(game, min_elo):
                games.append("".join(game))
            game = []
        else:
            game.append(line)
    if check_rating(game, min_elo):
        games.append("".join(game))

    with open(output_pgn, "w", encoding="utf-8") as f:
        for g in games:
            f.write(g + "\n\n")

    print(f"Filtered: {len(games)} games saved to {output_pgn}")

def check_rating(game_lines, min_elo):
    w = b = 0
    for line in game_lines:
        if line.startswith("[WhiteElo "):
            try: w = int(line.split('"')[1])
            except: pass
        elif line.startswith("[BlackElo "):
            try: b = int(line.split('"')[1])
            except: pass
    return w >= min_elo and b >= min_elo

def make_bin(pgn, output_bin, ply=50):
    cmd = [
        "./polyglot", "make-book",
        "-pgn", pgn,
        "-bin", output_bin,
        "-max-ply", str(ply)
    ]
    subprocess.run(cmd, check=True)
    print(f"Book created: {output_bin}")

if __name__ == "__main__":
    filter_games(INPUT_PGN, FILTERED_PGN)
    make_bin(FILTERED_PGN, BOOK_BIN, ply=50)
