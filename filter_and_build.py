# ---------- FETCH + FILTER GAMES ----------
def fetch_games(username, filename):
    """Fetch all Three-Check games for a bot (any opponent)"""
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": 200000,
        "perfType": "threeCheck",  # <-- changed from "antichess"
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

# ---------- BUILD BOOK ----------
def build_polyglot_book(pgn_path, book_path):
    print("Building Polyglot book...")
    book = Book()
    with open(pgn_path, "r", encoding="utf-8") as pgn_file:
        for i, game in enumerate(iter(lambda: chess.pgn.read_game(pgn_file), None), start=1):
            if game is None:
                break
            # <-- filter variant Three-Check instead of Antichess
            if game.headers.get("Variant", "").lower() != "three-check":
                continue

            board = game.board()
            result = game.headers.get("Result", "*")
            for ply, move in enumerate(game.mainline_moves()):
                if ply >= MAX_BOOK_PLIES:
                    break
                key_hex = get_zobrist_key_hex(board)
                position = book.get_position(key_hex)
                bm = position.get_move(move.uci())
                bm.move = move
                # Keep same weight logic as original
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
