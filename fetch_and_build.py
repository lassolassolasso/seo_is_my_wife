import requests

def fetch_games(username, min_rating=2800):
    url = f"https://lichess.org/api/games/user/{username}"
    headers = {"Accept": "application/x-chess-pgn"}
    params = {
        "variant": "antichess",
        "rated": "true",
        "perfType": "antichess",
        "clocks": "false",
        "evals": "false",
        "pgnInJson": "false",
        "moves": "true",
        "max": 3000
    }
    r = requests.get(url, params=params, headers=headers, stream=True)
    games = []
    game = ""
    for line in r.iter_lines():
        if line is None:
            continue
        line = line.decode("utf-8") if isinstance(line, bytes) else line
        if not line:
            if check_rating(game, min_rating):
                games.append(game.strip())
            game = ""
        else:
            game += line + "\n"
    if game and check_rating(game, min_rating):
        games.append(game.strip())
    print(f"{username}: {len(games)} games collected")
    return games

def check_rating(pgn, min_rating):
    w = b = 0
    for line in pgn.splitlines():
        if line.startswith("[WhiteElo "):
            w = int(line.split('"')[1])
        elif line.startswith("[BlackElo "):
            b = int(line.split('"')[1])
    return w >= min_rating and b >= min_rating

if __name__ == "__main__":
    all_games = []
    all_games.extend(fetch_games("NimsiluBot"))
    all_games.extend(fetch_games("ToromBot"))
    with open("filtered_960_bots_2200plus.pgn", "w", encoding="utf-8") as f:
        for g in all_games:
            f.write(g + "\n\n")
    print(f"Total collected: {len(all_games)} games")
