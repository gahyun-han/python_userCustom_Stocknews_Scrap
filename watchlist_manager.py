import json
import os
from pathlib import Path

WATCHLIST_FILE = Path(__file__).parent / "user_watchlist.json"


def load_watchlists():
    if not os.path.exists(WATCHLIST_FILE):
        return {}

    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)


def save_watchlists(data):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(data, f, indent=4)


def add_ticker(user_id, ticker):
    data = load_watchlists()

    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = []

    if ticker not in data[user_id]:
        data[user_id].append(ticker)

    save_watchlists(data)


def remove_ticker(user_id, ticker):
    data = load_watchlists()

    user_id = str(user_id)

    if user_id in data:
        if ticker in data[user_id]:
            data[user_id].remove(ticker)

    save_watchlists(data)


def get_tickers(user_id):
    data = load_watchlists()
    return data.get(str(user_id), [])


def reset_watchlist(user_id):
    data = load_watchlists()
    data[str(user_id)] = []
    save_watchlists(data)