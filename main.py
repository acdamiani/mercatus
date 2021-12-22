from bs4.element import NavigableString, Tag
import agent

import time
import os
import math
import requests
from requests_html import HTMLSession
from datetime import date, timedelta
from tqdm import tqdm
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, element
import pandas_ta as ta
import mplfinance as mpf

ALPHA_API_KEY = "ADP8LTSVJ3ZMLIAO"


def main():
    begin_training()


def begin_training() -> None:
    num_stocks = 10

    active_stocks = get_active_stocks(num_stocks)
    raw_data = []
    f = []

    i = 0
    t = time.time()
    for stock in tqdm(active_stocks, desc="Fetching raw data (this may take awhile)"):
        # If one minute has elapsed, reset the timer and counter
        if time.time() - t >= 60:
            print("One minute elapsed")
            t = time.time()
            i = 0

        # If we have reached 5 executions in one minute, wait until the end of the minute
        if i - 5 >= 0:
            tqdm.write("API limit reached. Waiting until end of minute...")
            time.sleep(60 - (time.time() - t))
            tqdm.write("Download resuming")
            t = time.time()
            i = 0
        raw_data.append(download_stock_data(stock, "full"))
        i += 1

    for element in raw_data:
        symbol: str = active_stocks[raw_data.index(element)]
        f.append(get_stock_data(element, symbol))

    if not os.path.exists("stock_data"):
        os.makedirs("stock_data")

    progress = tqdm(range(len(f)))
    progress.set_description("Writing stock data to csv")
    for x in progress:
        for f in os.listdir("stock_data"):
            os.remove(os.path.join("stock_data/", f))
        with open("stock_data/" + active_stocks[x] + ".csv", "w+") as file:
            file.write(f[x].to_csv(date_format="%Y%m%d"))
            file.close()


def get_active_stocks(number: int):
    # writes most active stocks to file
    stocks = []

    def get_content(x):
        return x.contents[0]

    # If we need more results, resend the url
    offset = 0
    iterations = math.ceil(number / 100)
    for x in tqdm(range(iterations), desc="Fetching valuable stocks"):
        url = "https://finance.yahoo.com/screener/predefined/most_actives"
        payload = {"count": "100", "offset": str(offset)}
        session = HTMLSession()
        request = session.get(url, params=payload)
        html = request.text
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("tbody", {"data-reactid": "72"})
        if isinstance(table, element.Tag):
            li = list(map(get_content, table.findChildren("a", recursive=True)))
            stocks.extend(li)
        offset += 100

    l = stocks[:number]
    # Get all stock numbers
    return l


def download_stock_data(symbol: str, output_size: str) -> requests.Response:
    payload = {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "outputsize": output_size,
        "interval": "5min",
        "apikey": ALPHA_API_KEY,
    }

    url = "https://www.alphavantage.co/query"

    r = requests.get(url, params=payload)

    return r


def get_stock_data(r: requests.Response, symbol: str) -> pd.DataFrame:
    date = []
    r_json = r.json()
    interval = "Time Series (5min)"

    df = pd.DataFrame()
    df.index.name = "Date"
    for i in tqdm(r_json[interval].keys(), desc="Sorting data for symbol " + symbol):
        date.append(i)
        row = (
            pd.DataFrame.from_dict(r.json()[interval][i], orient="index")
            .reset_index()
            .T[1:]
            .astype(float)
        )
        df = pd.concat([df, row], ignore_index=True)
    # df.rename(columns={"0": "open", "1": "high", "2": "low", "3": "close", "4": "volume"}, inplace=True)
    df.columns = pd.Index(["Open", "High", "Low", "Close", "Volume"])
    df.index = pd.DatetimeIndex(date)
    df = df[::-1]

    return df


def graph_stock_data(data: pd.DataFrame):
    mpf.plot(data, type="line")


if __name__ == "__main__":
    main()
