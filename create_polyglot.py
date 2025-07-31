import chess.pgn
import polyglot
from polyglot import book
import os

PGN_FILE = "filtered_960_bots_2200plus.pgn"
BOOK_FILE = "book.bin"
MAX_PLY = 20  # Edit as needed

def create_book():
    book_entries = []

    with open(PGN_FILE, encoding="utf-8") as pgn:
        game_count = 0
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            if game.headers.get("Variant") != "Chess960":
                continue
            if "FEN" not in game.headers or "SetUp" not in game.headers:
                continue

            board = game.board()
            game_count += 1

            try:
                for i, move in enumerate(game.mainline_moves()):
                    if i >= MAX_PLY:
                        break
                    entry = book.Entry.from_board(board, move, weight=1, learn=0)
                    book_entries.append(entry)
                    board.push(move)
            except Exception as e:
                continue

    if book_entries:
        with open(BOOK_FILE, "wb") as f:
            for entry in book_entries:
                f.write(entry.encode())
        print(f"✅ Saved {len(book_entries)} moves to book: {BOOK_FILE}")
    else:
        print("⚠️ No valid moves found. Book not created.")

if __name__ == "__main__":
    create_book()
