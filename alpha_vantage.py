import requests
import time
import math
import sys
from tqdm import tqdm

class AlphaVantage:
    api_key: str
    num_requests: int
    last_request: float

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.num_requests = 0
        self.last_request = 0

    def send_request(self, url: str, payload="") -> requests.Response:
        if not payload:
            raise ValueError("Url must be a valid string")

        if self.num_requests >= 5:
            print(
                    "Request limit reached. Waiting until end of minute to continue execution."
                    )

            seconds_since_last = math.floor(time.time() - self.last_request)

            for x in reversed(range(60 - seconds_since_last)):
                print(x, end="\r", flush=True)
                time.sleep(1)

                if x > 0:
                    sys.stdout.write("\033[K")

            print("")

            self.num_requests = 0

        self.num_requests += 1
        self.last_request = time.time()

        return requests.get(url, params=payload)

    def time_series_daily(
            self, symbol: str, datatype="json", compact=True, adjusted=True
            ):
        if not symbol:
            raise ValueError("Symbol must be a valid string")

        payload = {
                "function": "TIME_SERIES_DAILY_ADJUSTED"
                if adjusted
                else "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact" if compact else "full",
                "apikey": self.api_key,
                "datatype": "json" if datatype != "csv" else "csv",
                }
        url = "https://www.alphavantage.co/query"

        r = self.send_request(url, payload=payload)

        return r

if __name__ == "__main__":
    t = AlphaVantage("ADP8LTSVJ3ZMLIAO")

    for x in range(6):
        print(t.time_series_daily("IBM").json())
