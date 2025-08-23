# filter_and_build.py
# Fetch ALL Crazyhouse games for NimsiluBot & ToromBot with rating >= 2250,
# merge to PGN, and build a Polyglot book (no external C++ needed).

import requests
import json
import time
import io
import chess
import chess.pgn
import chess.polyglot
import chess.variant

# --------- CONFIG ---------
BOTS = ["NimsiluBot", "ToromBot"]
VARIANT = "crazyhouse"
MIN_ELO = 2250
CHUNK_SIZE = 5000          # lichess max per request
REQUEST_TIMEOUT = 120
SLEEP_BETWEEN_CHUNKS = 0.4 # be polite to API
MAX_PLY = 60
MAX_BOOK_WEIGHT = 10000

PGN_OUTPUT = f"{VARIANT}_games.pgn"
BOOK_OUTPUT = f"{VARIANT}_book.bin"

# --------- FETCH ALL NDJSON (PAGINATED) ---------
def fetch_all_games_for_bot(bot: str) -> list[str]:
    """
    Returns a list of PGN strings (already filtered by rating >= MIN_ELO).
    Uses 'until' pagination to walk back through the user's entire history.
    """
    print(f"Fetching {VARIANT} games for {bot} (rating >= {MIN_ELO})...")
    base_url = f"https://lichess.org/api/games/user/{bot}"
    headers = {"Accept": "application/x-ndjson"}
    params = {
        "max": CHUNK_SIZE,
        "perfType": VARIANT,
        "rated": "true",
        "moves": "true",
        "pgnInJson": "true",
        "clocks": "false",
        "evals": "false",
        "opening": "false",
    }

    all_pgns: list[str] = []
    # Walk backwards in time. Start with no 'until', then set to earliest timestamp seen - 1.
    until_ts: int | None = None
    total_lines = 0
    kept = 0

    while True:
        if until_ts is not None:
            params["until"] = until_ts  # milliseconds since epoch
        else:
            params.pop("until", None)

        resp = requests.get(base_url, params=params, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        batch_count = 0
        earliest_ts = None

        for raw in resp.iter_lines():
            if not raw:
                continue
            batch_count += 1
            total_lines += 1

            try:
                game = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            # Track earliest createdAt to paginate further back
            created_at = game.get("createdAt")
            if isinstance(created_at, int):
                if earliest_ts is None or created_at < earliest_ts:
                    earliest_ts = created_at

            # Filter by rating >= MIN_ELO
            try:
                w = game["players"]["white"]
                b = game["players"]["black"]
                white_rating = int(w.get("rating", 0) or 0)
                black_rating = int(b.get("rating", 0) or 0)
            except Exception:
                continue

            if max(white_rating, black_rating) < MIN_ELO:
                continue

            # Keep only games that involve the target bot (redundant but safe) and correct variant
            # API is already filtered by perfType, but double-check:
            variant = (game.get("variant") or "").lower()
            if variant and variant != VARIANT:
                continue

            # Accept PGN
            pgn = game.get("pgn")
            if pgn:
                all_pgns.append(pgn)
                kept += 1

        print(f"  chunk: got {batch_count} games, kept {kept} total so far")

        if batch_count == 0 or earliest_ts is None:
            break  # no more data

        # Prepare next page further back in time
        until_ts = earliest_ts - 1
        time.sleep(SLEEP_BETWEEN_CHUNKS)

    print(f"Finished {bot}: processed {total_lines} lines, kept {kept} games ≥ {MIN_ELO}")
    return all_pgns

# --------- MERGE & SAVE PGN ---------
def save_merged_pgn(pgn_list: list[str], out_path: str) -> None:
    print("Merging PGNs...")
    with open(out_path, "w", encoding="utf-8") as f:
        for p in pgn_list:
            f.write(p)
            if not p.endswith("\n"):
                f.write("\n")
            f.write("\n")
    print(f"Saved merged PGN to {out_path} ({len(pgn_list)} games)")

# --------- PYTHON POLYGLOT BUILDER ---------
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
                # scale to MAX_BOOK_WEIGHT
                bm.weight = max(1, int(bm.weight / s * MAX_BOOK_WEIGHT))
    def save_polyglot(self, path):
        entries = []
        for key_hex, pos in self.positions.items():
            zbytes = bytes.fromhex(key_hex)
            for uci, bm in pos.moves.items():
                if bm.weight <= 0 or bm.move is None:
                    continue
                m = bm.move
                # Skip drop-style moves (not representable in classic polyglot)
                if "@" in m.uci():
                    continue
                mi = m.to_square + (m.from_square << 6)
                if m.promotion:
                    mi += ((m.promotion - 1) << 12)
                mbytes = mi.to_bytes(2, "big")
                wbytes = bm.weight.to_bytes(2, "big")
                lbytes = (0).to_bytes(4, "big")
                entries.append(zbytes + mbytes + wbytes + lbytes)
        # Sort by key then move bytes as in Polyglot
        entries.sort(key=lambda e: (e[:8], e[10:12]))
        with open(path, "wb") as f:
            for e in entries:
                f.write(e)
        print(f"Saved {len(entries)} moves to book: {path}")

def key_hex(board):
    return f"{chess.polyglot.zobrist_hash(board):016x}"

def build_book_from_pgn(pgn_path, bin_path):
    print("Building book...")
    book = Book()
    with open(pgn_path, "r", encoding="utf-8") as f:
        data = f.read()
    stream = io.StringIO(data)

    processed = 0
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        # Ensure variant
        if (game.headers.get("Variant", "") or "").lower() != VARIANT:
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

        processed += 1
        if processed % 200 == 0:
            print(f"Processed {processed} games")

    book.normalize()
    book.save_polyglot(bin_path)

# --------- MAIN ---------
def main():
    all_pgns = []
    for bot in BOTS:
        all_pgns.extend(fetch_all_games_for_bot(bot))
    save_merged_pgn(all_pgns, PGN_OUTPUT)
    build_book_from_pgn(PGN_OUTPUT, BOOK_OUTPUT)
    print("Done.")

if __name__ == "__main__":
    main()
