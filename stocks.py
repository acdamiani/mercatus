import os
import time
import json
import pandas as pd
import requests
import main

api_calls = 0
last_minute = time.time()

# Dictionary for stock info accessed by agents
latest_prices = {}

# Gets the latest available price of a given stock
def get_latest_price(symbol: str) -> float:
    global api_calls
    pause_if_limit_reached()

    if (
        latest_prices[symbol] is not None
        and time.time() - latest_prices[symbol]["last_accessed"] < 300
    ):
        return latest_prices[symbol]["price"]

    url = "https://www.alphavantage.co/query"
    payload = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": main.ALPHA_API_KEY,
    }

    response = requests.get(url, params=payload)
    api_calls += 1

    resp = float(response.json()["Global Quote"]["05. price"])
    latest_prices[symbol] = {"price": resp, "last_accessed": time.time()}

    return resp


def get_valid_stocks() -> list[str]:
    files = []
    for x in os.listdir("stock_data/"):
        files.append(os.path.splitext(x)[0])

    return files


def get_stock_into(symbol: str) -> pd.DataFrame:
    return pd.DataFrame(
        pd.read_csv(
            "stock_data/" + symbol + ".csv",
            dayfirst=True,
            parse_dates=True,
            index_col=[0],
        )
    )


def pause_if_limit_reached():
    global api_calls
    global last_minute

    if api_calls - 5 >= 0:
        time.sleep(60 - (time.time() - last_minute))
        api_calls = 0
        last_minute = time.time()

    if time.time() - last_minute >= 60:
        api_calls = 0
        last_minute = time.time()


if __name__ == "__main__":
    print(get_valid_stocks())
