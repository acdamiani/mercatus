from concurrent.futures import ThreadPoolExecutor, as_completed
import io
import os
import datetime
import json
import requests
import typing
import boto3
from yaspin import yaspin

from enum import Enum

import pandas as pd
import pandas_ta as ta

import dotenv as env


def should_retry(e):
    return 400 <= e.status_code < 500


class TimeFrame(Enum):
    OneMinute = "1Min"
    FifteenMinutes = "15Min"
    OneHour = "1Hour"
    OneDay = "1Day"


class Sorter:
    _secret_key: str
    _api_key: str
    _endpoint: str
    _aws_access_key_id: str
    _aws_secret_access_key: str

    def __init__(self):
        env.load_dotenv()

        print(os.environ)

        self._secret_key = os.environ["ALPACA_SECRET_KEY"]
        self._api_key = os.environ["ALPACA_API_KEY"]
        self._endpoint = os.environ["ALPACA_ENDPOINT"]
        self._aws_access_key_id = os.environ["AWS_KEY_ID"]
        self._aws_secret_access_key = os.environ["AWS_SECRET_KEY"]

    def historical_data(
        self,
        symbol: typing.Union[str, list[str]],
        start: typing.Union[datetime.date, None] = None,
        end: typing.Union[datetime.date, None] = None,
        limit: int = 1000,
        timeframe: typing.Union[TimeFrame, str] = TimeFrame.OneDay,
        adjustment: str = "raw",
    ):
        headers = {}

        if isinstance(timeframe, TimeFrame):
            timeframe = timeframe.value

        payload = {}
        payload["timeframe"] = timeframe
        payload["adjustment"] = adjustment

        if start != None:
            payload["start"] = start.isoformat()

        if end != None:
            payload["end"] = end.isoformat()

        payload["limit"] = limit

        if isinstance(symbol, list):
            # Split symbols into 30 symbol chunks
            symbol_chunks = [symbol[i : i + 30] for i in range(0, len(symbol), 30)]
            r: list[requests.Request] = []

            for chunk in symbol_chunks:
                chunk_s = {"symbols": ",".join(chunk)}
                chunk_p = payload | chunk_s
                r.append(
                    requests.Request(
                        url="https://data.alpaca.markets/v2/stocks/bars",
                        params=chunk_p,
                        headers=headers,
                    ),
                )

            return self.request(r, autosend_credentials=True)
        else:
            url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars"
            return self.request(
                requests.Request(url=url, params=payload, headers=headers),
                autosend_credentials=True,
            )

    def request_simple(
        self,
        url: str,
        payload: typing.Union[dict[str, str], None] = None,
        headers: typing.Union[dict[str, str], None] = None,
        autosend_credentials: bool = False,
    ) -> requests.Response:
        if autosend_credentials:
            if headers == None:
                headers = {}
            headers["APCA-API-KEY-ID"] = self._api_key
            headers["APCA-API-SECRET-KEY"] = self._secret_key

        r = requests.get(url, params=payload, headers=headers, allow_redirects=False)

        return r

    def request(
        self,
        request: typing.Union[requests.Request, list[requests.Request]],
        autosend_credentials: bool = False,
    ) -> typing.Union[list[requests.Response], requests.Response]:
        if isinstance(request, list) and len(request) > 1:
            responses = []
            for r in request:
                print(f"Sending request ({r.url})")
                responses.append(
                    self.request_simple(
                        r.url, r.params, r.headers, autosend_credentials
                    )
                )
                print("Done")
            return responses

        else:
            if isinstance(request, requests.Request):
                s = request
            elif isinstance(request, list):
                s = request[0]

            return self.request_simple(s.url, s.params, s.headers)

    def symbol_ma(self, data: str) -> tuple[float, float, float, float]:
        df = pd.DataFrame.from_dict(data)

        if len(df) < 201:
            return (-1, -1, -1, -1)

        # 200 day moving average
        ema_200 = ta.ema(df["c"], length=200)

        # 50 day moving average
        ema_50 = ta.ema(df["c"], length=50)

        assert ema_200 is not None
        assert ema_50 is not None

        return (ema_50.iloc[-1], ema_50.iloc[-2], ema_200.iloc[-1], ema_200.iloc[-2])


def get_emas(symbols: list[str]):
    sorter = Sorter()

    responses = sorter.historical_data(
        symbols,
        timeframe=TimeFrame.OneDay,
        start=datetime.date(1980, 12, 12),
        end=datetime.date.today() - datetime.timedelta(days=1),
        limit=10000,
    )

    if isinstance(responses, list):
        # x is a list of dictionaries. The dictionaries have 30 keys
        x = [json.loads(x.text)["bars"] for x in responses]
    else:
        x = json.loads(responses.text)["bars"]

    df = pd.DataFrame(columns=["ema_50", "ema_50_y", "ema_200", "ema_200_y"])
    df.index.name = "symbols"

    for s in x:
        for ss in s:
            v = sorter.symbol_ma(s[ss])

            if v != (-1, -1):
                df = df.append(
                    pd.DataFrame(
                        [[v[0], v[1], v[2], v[3]]],
                        columns=["ema_50", "ema_50_y", "ema_200", "ema_200_y"],
                        index=[ss],
                    )
                )

    df_csv = df.to_csv()

    bucket = "pcl-stockdata"
    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=sorter._aws_access_key_id,
        aws_secret_access_key=sorter._aws_secret_access_key,
    )
    s3_resource.Object(bucket, "mt.csv").put(Body=df_csv)
