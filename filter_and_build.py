import requests
import json
import chess
import chess.pgn
import chess.polyglot
import subprocess
import os

BOTS = ["ToromBot", "NimsiluBot"]
MIN_ELO = 2770
MAX_BOOK_PLIES = 50
MAX_BOOK_WEIGHT = 10000

# ---------- POLYGLOT BOOK CLASSES ----------
def format_zobrist_key_hex(zobrist_key):
    return f"{zobrist_key:016x}"

def get_zobrist_key_hex(board):
    return format_zobrist_key_hex(chess.polyglot.zobrist_hash(board))

class BookMove:
    def __init__(self):
        self.weight = 0
        self.move = None

class BookPosition:
    def __init__(self):
        self.moves = {}

    def get_move(self, uci):
        return self.moves.setdefault(uci, BookMove())

class Book:
    def __init__(self):
        self.positions = {}

    def get_position(self, zobrist_key_hex):
        return self.positions.setdefault(zobrist_key_hex, BookPosition())

    def normalize_weights(self):
        for pos in self.positions.values():
            total_weight = sum(bm.weight for bm in pos.moves.values())
            if total_weight > 0:
                for bm in pos.moves.values():
                    bm.weight = int(bm.weight / total_weight * MAX_BOOK_WEIGHT)

    def save_as_polyglot(self, path):
        with open(path, 'wb') as outfile:
            entries = []
            for key_hex, pos in self.positions.items():
                zbytes = bytes.fromhex(key_hex)
                for uci, bm in pos.moves.items():
                    if bm.weight <= 0 or bm.move is None:
                        continue
                    move = bm.move
                    mi = move.to_square + (move.from_square << 6)
                    if move.promotion:
                        mi += ((move.promotion - 1) << 12)
                    mbytes = mi.to_bytes(2, byteorder="big")
                    wbytes = bm.weight.to_bytes(2, byteorder="big")
                    lbytes = (0).to_bytes(4, byteorder="big")
                    entries.append(zbytes + mbytes + wbytes + lbytes)

            entries.sort(key=lambda e: (e[:8], e[10:12]))
            for entry in entries:
                outfile.write(entry)
            print(f"✅ Saved {len(entries)} moves to book: {path}")

# ---------- FETCH + FILTER GAMES ----------
def fetch_games(username, filename):
    """Fetch all Antichess games for a bot (any opponent)"""
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
    print(f"Fetching games for {username}...")
    with requests.get(url, params=params, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(filename, "w", encoding="utf-8") as f:
            for line in r.iter_lines():
                if line:
                    f.write(line.decode("utf-8") + "\n")

def filter_games(input_file, output_file):
    """Filter PGN: Antichess, rated ≥MIN_ELO"""
    print(f"Filtering {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f, open(output_file, "w", encoding="utf-8") as out:
        for line in f:
            game = json.loads(line)
            if "players" not in game:
                continue
            try:
                white_name = game["players"]["white"]["user"]["name"]
                black_name = game["players"]["black"]["user"]["name"]
                white_rating = game["players"]["white"].get("rating", 0)
                black_rating = game["players"]["black"].get("rating", 0)
            except Exception:
                continue

            if white_name in BOTS or black_name in BOTS:
                if max(white_rating, black_rating) >= MIN_ELO:
                    if "pgn" in game:
                        out.write(game["pgn"] + "\n\n")

def merge_pgns(files, output_file):
    print("Merging PGNs...")
    with open(output_file, "w", encoding="utf-8") as out:
        for f in files:
            with open(f, "r", encoding="utf-8") as g:
                out.write(g.read())
    print(f"✅ Saved merged PGN to {output_file}")

# ---------- BUILD BOOK ----------
def build_polyglot_book(pgn_path, book_path):
    print("Building Polyglot book...")
    book = Book()
    with open(pgn_path, "r", encoding="utf-8") as pgn_file:
        for i, game in enumerate(iter(lambda: chess.pgn.read_game(pgn_file), None), start=1):
            if game is None:
                break
            if game.headers.get("Variant", "").lower() != "antichess":
                continue

            board = game.board()
            # Antichess: score depends on who should lose pieces
            result = game.headers.get("Result", "*")
            for ply, move in enumerate(game.mainline_moves()):
                if ply >= MAX_BOOK_PLIES:
                    break
                key_hex = get_zobrist_key_hex(board)
                position = book.get_position(key_hex)
                bm = position.get_move(move.uci())
                bm.move = move
                # Assign weight: win = 2 for losing side, draw = 1
                if result == "1-0":
                    bm.weight += 2 if board.turn == chess.WHITE else 0
                elif result == "0-1":
                    bm.weight += 2 if board.turn == chess.BLACK else 0
                elif result == "1/2-1/2":
                    bm.weight += 1
                board.push(move)

            if i % 100 == 0:
                print(f"Processed {i} games")
    book.normalize_weights()
    book.save_as_polyglot(book_path)

# ---------- MAIN ----------
def main():
    ndjson_files = []
    pgn_files = []

    # Fetch and filter each bot
    for bot in BOTS:
        ndjson_file = f"{bot}_antichess.ndjson"
        pgn_file = f"{bot}_filtered.pgn"
        fetch_games(bot, ndjson_file)
        filter_games(ndjson_file, pgn_file)
        ndjson_files.append(ndjson_file)
        pgn_files.append(pgn_file)

    # Merge all PGNs
    merged_pgn = "antichess_games.pgn"
    merge_pgns(pgn_files, merged_pgn)

    # Build book
    build_polyglot_book(merged_pgn, "anti_book.bin")

if __name__ == "__main__":
    main()
