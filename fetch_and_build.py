import requests
import json
import collections
import time
import os

TOKEN = os.getenv("LICHESS_TOKEN") 
bots = [
    "SoggiestShrimp",
    "AttackKing_Bot",
    "PositionalAI",
    "mayhem23111",
    "InvinxibleFlxsh",
    "YoBot_v2",
    "VEER-OMEGA-BOT",
    "MaggiChess16",
    "NimsiluBot",
    "pangubot",
    "Loss-Not-Defined",
    "Alexnajax_Fan",
    "strain-on-veins",
    "BOTTYBADDY11",
    "ChampionKitten",
    "LeelaMultiPoss",
    "ToromBot",
    "Ayaangamerzbot",
    "Lili-ai",
    "BOT_DeChess",
    "Moment-That-Inspires"
]

def fetch():
    headers = {
        "Accept": "application/x-ndjson"
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    fen_to_pgns = collections.defaultdict(list)

    for bot in bots:
        print(f"🔍 Fetching games for {bot}")
        url = f"https://lichess.org/api/games/user/{bot}"
        params = {
            "max": 3000,
            "perfType": "chess960",
            "rated": "true",
            "analysed": "false",
            "pgnInJson": "true",
            "clocks": "false",
            "opening": "false",
            "moves": "true"
        }

        try:
            response = requests.get(url, headers=headers, params=params, stream=True, timeout=30)
        except Exception as e:
            print(f"Error while fetching {bot}: {e}")
            continue

        if response.status_code != 200:
            print(f"Failed to fetch games for {bot}, status {response.status_code}")
            time.sleep(3)
            continue

        for line in response.iter_lines():
            if not line:
                continue

            g = json.loads(line)
            white = g.get("players", {}).get("white", {})
            black = g.get("players", {}).get("black", {})
            white_name = white.get("user", {}).get("name", "")
            black_name = black.get("user", {}).get("name", "")
            white_rating = white.get("rating", 0)
            black_rating = black.get("rating", 0)

            if white_name not in bots or black_name not in bots:
                continue
            if white_rating < 2350 or black_rating < 2350:
                continue
            if g.get("variant") != "chess960":
                continue

            fen = g.get("initialFen", "")
            pgn = g.get("pgn", "")

            if fen and pgn and len(fen_to_pgns[fen]) < 11:
                fen_to_pgns[fen].append(pgn.strip())

    total_games = 0
    with open("filtered_960_bots_2200plus.pgn", "w", encoding="utf-8") as f:
        for pgns in fen_to_pgns.values():
            for pgn in pgns:
                f.write(pgn + "\n\n")
                total_games += 1

    print(f"Saved {total_games} games from {len(fen_to_pgns)} unique FENs to filtered_960_bots_2200plus.pgn")

if __name__ == "__main__":
    fetch()
