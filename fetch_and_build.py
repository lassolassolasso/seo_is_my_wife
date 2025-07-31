import requests, time, chess, chess.pgn, chess.polyglot, datetime

BOTS = ["SoggiestShrimp", "AttackKing_Bot", "PositionalAI", "mayhem23111", "InvinxibleFlxsh", "YoBot_v2", "VEER-OMEGA-BOT", "MaggiChess16", "NimsiluBot"]
PGN_OUT = "filtered_960_bots_2200plus.pgn"
BIN_OUT = "book.bin"

# Lichess token if available to improve rate limits
TOKEN = None
HEADERS = {"Accept":"application/x-ndjson"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

def fetch():
    url = "https://lichess.org/api/games/user/{}"
    params = {"perfType": "chess960", "rated": "true", "moves":"true", "opening":"true"}
    games = []
    for bot in BOTS:
        print("Fetching games for", bot)
        resp = requests.get(url.format(bot), headers=HEADERS, params=params, stream=True)
        if resp.status_code != 200:
            print("Failed for", bot, resp.status_code)
            continue
        for line in resp.iter_lines():
            if not line: continue
            g = requests.utils.json.loads(line)
            pw = g.get("players", {})
            w = pw.get("white",{}); b = pw.get("black",{})
            if (w.get("user",{}).get("title")=="BOT" and b.get("user",{}).get("title")=="BOT" and
                w.get("rating",0)>=2200 and b.get("rating",0)>=2200):
                games.append(g.get("pgn",""))
        time.sleep(2)
    with open(PGN_OUT,"w",encoding="utf-8") as f:
        for p in games: f.write(p+"\n\n")
    print("Saved games:", len(games))

# (Insert your corrected create_polyglot.py logic here...)
from create_polyglot import build_book_file
def build():
    build_book_file(PGN_OUT, BIN_OUT)

if __name__=="__main__":
    fetch()
    build()
