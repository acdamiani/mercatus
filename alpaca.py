import os

from alpaca_trade_api.rest import REST, TimeFrame
from alpaca_trade_api.common import URL
import dotenv as env


class Alpaca:
    api: REST

    def __init__(self):
        # Load environment variables
        env.load_dotenv(".env")

        secret_key = os.environ["ALPACA_SECRET_KEY"]
        api_key = os.environ["ALPACA_API_KEY"]
        endpoint = os.environ["ALPACA_ENDPOINT"]

        # Initialize Alpaca
        self.api = REST(api_key, secret_key, URL(endpoint))


if __name__ == "__main__":
    alp = Alpaca()
