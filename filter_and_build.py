import requests
import json
import chess
import chess.pgn
import chess.polyglot
import chess.variant
import io

BOTS = ["NimsiluBot", "ToromBot"]
VARIANT = "crazyhouse"
MAX_GAMES = 2000000
MAX_PLY = 40
MAX_BOOK_WEIGHT = 10000

PGN_OUTPUT = f"{VARIANT}_games.pgn"
BOOK_OUTPUT = f"{VARIANT}_book.bin"

def fetch_bot_pgn(bot):
    url = f"https://lichess.org/api/games/user/{bot}"
    params = {
        "max": MAX_GAMES,
        "perfType": VARIANT,
        "rated": "true",
        "moves": "true",
        "pgnInJson": "true",
        "clocks": "false",
        "evals": "false",
        "opening": "true",
    }
    headers = {"Accept": "application/x-ndjson"}
    r = requests.get(url, params=params, headers=headers, stream=True, timeout=120)
    r.raise_for_status()
    out_pgn = f"{bot}_{VARIANT}.pgn"
    with open(out_pgn, "w", encoding="utf-8") as out:
        for line in r.iter_lines():
            if not line:
                continue
            game = json.loads(line.decode("utf-8"))
            pgn = game.get("pgn")
            if pgn:
                out.write(pgn)
                if not pgn.endswith("\n"):
                    out.write("\n")
                out.write("\n")
    return out_pgn

def merge_pgns(pgn_files, merged_file):
    with open(merged_file, "w", encoding="utf-8") as out:
        for p in pgn_files:
            with open(p, "r", encoding="utf-8") as f:
                out.write(f.read())
                if not f.read().endswith("\n\n"):
                    out.write("\n")

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
    def get_position(self, key_hex):
        return self.positions.setdefault(key_hex, BookPosition())
    def normalize(self):
        for pos in self.positions.values():
            s = sum(bm.weight for bm in pos.moves.values())
            if s <= 0:
                continue
            for bm in pos.moves.values():
                bm.weight = max(1, int(bm.weight / s * MAX_BOOK_WEIGHT))
    def save_polyglot(self, path):
        entries = []
        for key_hex, pos in self.positions.items():
            zbytes = bytes.fromhex(key_hex)
            for uci, bm in pos.moves.items():
                if bm.weight <= 0 or bm.move is None:
                    continue
                m = bm.move
                u = m.uci()
                if "@" in u:
                    continue
                mi = m.to_square + (m.from_square << 6)
                if m.promotion:
                    mi += ((m.promotion - 1) << 12)
                mbytes = mi.to_bytes(2, "big")
                wbytes = bm.weight.to_bytes(2, "big")
                lbytes = (0).to_bytes(4, "big")
                entries.append(zbytes + mbytes + wbytes + lbytes)
        entries.sort(key=lambda e: (e[:8], e[10:12]))
        with open(path, "wb") as f:
            for e in entries:
                f.write(e)
        print(f"Saved {len(entries)} moves to book: {path}")

def key_hex(board):
    return f"{chess.polyglot.zobrist_hash(board):016x}"

def build_book_from_pgn(pgn_path, bin_path):
    book = Book()
    with open(pgn_path, "r", encoding="utf-8") as f:
        data = f.read()
    stream = io.StringIO(data)
    cnt = 0
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        variant = game.headers.get("Variant", "").lower()
        if variant != VARIANT:
            continue
        board = chess.variant.CrazyhouseBoard()
        for ply, move in enumerate(game.mainline_moves()):
            if ply >= MAX_PLY:
                break
            k = key_hex(board)
            pos = book.get_position(k)
            bm = pos.get_move(move.uci())
            bm.move = move
            bm.weight += 1
            board.push(move)
        cnt += 1
        if cnt % 200 == 0:
            print(f"Processed {cnt} games")
    book.normalize()
    book.save_polyglot(bin_path)

def main():
    pgns = []
    for b in BOTS:
        print(f"Fetching {VARIANT} games for {b}...")
        pgns.append(fetch_bot_pgn(b))
    print("Merging PGNs...")
    merge_pgns(pgns, PGN_OUTPUT)
    print("Building book...")
    build_book_from_pgn(PGN_OUTPUT, BOOK_OUTPUT)
    print("Done.")

if __name__ == "__main__":
    main()
