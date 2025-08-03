import requests
import time
import json

BOTS = [
    "NimsiluBot",
    "MaggiChess16",
    "NNUE_Drift",
    "Endogenetic-Bot",
    "AttackKing_Bot"
]

OUTPUT_PGN = "filtered_960_bots_2200plus.pgn"
MAX_GAMES_PER_BOT = 200

def fetch_games(username):
    url = f"https://lichess.org/api/games/user/{username}"
    headers = {"Accept": "application/x-ndjson"}
    params = {
        "max": MAX_GAMES_PER_BOT,
        "variant": "chess960",
        "pgnInJson": "true",
        "clocks": "false",
        "evals": "false",
        "opening": "false"
    }

    print(f"Fetching games for {username}...")
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        print(f"  Failed to fetch games for {username} - Status: {response.status_code}")
        return []

    return [line for line in response.text.strip().split('\n') if line]

def parse_rating(player):
    rating = player.get("rating", 0)
    provisional = player.get("provisional", False)
    return rating, provisional

def extract_valid_games(games_ndjson):
    valid_pgns = []
    for line in games_ndjson:
        try:
            game = json.loads(line)
        except json.JSONDecodeError:
            continue

        if game.get("variant") != "chess960":
            continue

        players = game.get("players", {})
        white = players.get("white", {})
        black = players.get("black", {})

        white_user = white.get("user", {})
        black_user = black.get("user", {})

        # Ensure both players are bots
        if not white_user.get("bot") or not black_user.get("bot"):
            continue

        white_rating, white_prov = parse_rating(white)
        black_rating, black_prov = parse_rating(black)

        white_ok = white_prov or white_rating >= 2400
        black_ok = black_prov or black_rating >= 2400

        if white_ok and black_ok and "pgn" in game:
            valid_pgns.append(game["pgn"].strip())

    return valid_pgns

def main():
    all_pgns = []
    for bot in BOTS:
        ndjson = fetch_games(bot)
        time.sleep(1.5)  # Respect rate limits
        filtered = extract_valid_games(ndjson)
        print(f"  → {len(filtered)} valid games for {bot}")
        all_pgns.extend(filtered)

    print(f"\nTotal games collected: {len(all_pgns)}")
    with open(OUTPUT_PGN, "w", encoding="utf-8") as f:
        f.write("\n\n".join(all_pgns))
    print(f"PGN saved to {OUTPUT_PGN}")

if __name__ == "__main__":
    main()
