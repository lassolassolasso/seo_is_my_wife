import requests
import json
import chess.pgn
from io import StringIO

# Bot usernames to include
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
]

def fetch():
    headers = {
        "Accept": "application/x-ndjson"
    }

    out_pgns = []

    for bot in bots:
        print(f"Fetching games for {bot}")
        url = f"https://lichess.org/api/games/user/{bot}"
        params = {
            "max": 100,
            "perfType": "chess960",
            "rated": "true",
            "analysed": "false",
            "pgnInJson": "true",
            "clocks": "false",
            "opening": "false",
            "moves": "true"
        }

        response = requests.get(url, headers=headers, params=params, stream=True)

        if response.status_code != 200:
            print(f"Failed to fetch games for {bot}")
            continue

        for line in response.iter_lines():
            if not line:
                continue
            g = json.loads(line)

            # Filter: must be against another bot, both 2200+
            white = g.get("players", {}).get("white", {})
            black = g.get("players", {}).get("black", {})
            white_name = white.get("user", {}).get("name", "")
            black_name = black.get("user", {}).get("name", "")
            white_title = white.get("user", {}).get("title", "")
            black_title = black.get("user", {}).get("title", "")
            white_rating = white.get("rating", 0)
            black_rating = black.get("rating", 0)

            if white_name not in bots or black_name not in bots:
                continue

            if white_rating < 2350 or black_rating < 2350:
                continue

            if g.get("variant") != "chess960":
                continue

            pgn = g.get("pgn", "")
            if pgn:
                out_pgns.append(pgn.strip())

    # Save filtered PGNs
    with open("filtered_960_bots_2200plus.pgn", "w", encoding="utf-8") as f:
        for pgn in out_pgns:
            f.write(pgn + "\n\n")

    print(f"✅ Saved {len(out_pgns)} games to filtered_960_bots_2200plus.pgn")

if __name__ == "__main__":
    fetch()
