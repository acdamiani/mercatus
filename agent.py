import numpy as np
import pandas as pd
import pandas_ta as ta
import stocks
from tqdm import tqdm


class Agent:
    buying_power: float = 0
    stocks: list[str] = []

    def __init__(self) -> None:
        self.set_attr(np.random.rand(8))

    def __str__(self) -> str:
        s = "Agent " + str(id(self)) + ":" + "\n"
        s += "EMA 50 Wegiht: " + str(self.ema_50_w) + "\n"
        s += "EMA 200 Weight: " + str(self.ema_200_w) + "\n"
        s += "MACD Weight: " + str(self.macd_w) + "\n"
        s += "MACD_S Weight: " + str(self.macd_w) + "\n"
        s += "MACD_H Weight: " + str(self.macd_w) + "\n"
        s += "RSI Weight: " + str(self.rsi_w) + "\n"
        s += "Buy Threshold: " + str(self.buy_t) + "\n"
        s += "Sell Threshold: " + str(self.sell_t) + "\n"

        return s

    # Gets agent composite score, which is simply the value of the agent's buying power plus the value of all of the stocks
    def calculate_composite_score(self) -> float:
        total_value = 0

        for stock in self.stocks:
            total_value += stocks.get_latest_price(stock)

        return self.buying_power + total_value

    def set_attr(self, attributes: list[float]) -> None:
        self.ema_50_w = attributes[0]
        self.ema_200_w = attributes[1]
        self.macd_w = attributes[2]
        self.macd_s_w = attributes[3]
        self.macd_h_w = attributes[4]
        self.rsi_w = attributes[5]
        self.buy_t = attributes[6]
        self.sell_t = attributes[7]

    def get_attr(self):
        attributes = np.empty(4, dtype=float)
        attributes[0] = self.ema_50_w
        attributes[1] = self.ema_200_w
        attributes[2] = self.macd_w
        attributes[3] = self.macd_s_w
        attributes[4] = self.macd_h_w
        attributes[5] = self.rsi_w
        attributes[6] = self.buy_t
        attributes[7] = self.sell_t

        return list(attributes)

    def get_composite(self, date: pd.DatetimeIndex, stock: str) -> float:
        df = stocks.get_stock_into(stock)
        ema_50 = ta.ema(df["Close"], length=50).loc[date]
        ema_200 = ta.ema(df["Close"], length=50).loc[date]
        macd_df = pd.DataFrame(ta.macd(df["Close"], fast=12, slow=26, signal=9)).loc[date]
        macd = macd_df["MACD_12_26_9"]
        macd_s = macd_df["MACDs_12_26_9"]
        macd_h = macd_df["MACDh_12_26_9"]
        rsi = ta.rsi(df["Close"], length=14).loc[date]

        return (
                ema_50 * self.ema_50_w
                + ema_200 * self.ema_200_w
                + macd * self.macd_w
                + macd_s * self.macd_s_w
                + macd_h * self.macd_h_w
                + rsi * self.rsi_w
                )

    def buy(self, symbol: str):
        price = stocks.get_latest_price(symbol)

        if self.buying_power < price:
            return

        self.buying_power -= price
        self.stocks.append(symbol)

    def sell(self, symbol: str):
        if symbol not in self.stocks:
            return
      price = stocks.get_latest_price(symbol)

        self.buying_power += price
        self.stocks.remove(symbol)

    def tick(self, date: pd.DatetimeIndex):
        all_stocks = np.array(stocks.get_valid_stocks())
        composites = []

        # Calculate composite score for each stock
        # for stock in all_stocks:
        for stock in all_stocks:
            composites.append(self.get_composite(date, stock))

        for x in range(len(composites)):
            # If score is greater than the buy threshold, buy the stock
            # If score is less than the sell threshold, sell the stock
            if composites[x] > self.buy_t:
                self.buy(all_stocks[x])
            elif composites[x] < self.sell_t:
                self.sell(all_stocks[x])


def cross(parent_one: Agent, parent_two: Agent) -> Agent:
    agent = Agent()
    cross_point = np.random.randint(0, 5)
    parent_one_attributes = parent_one.get_attr()
    parent_two_attributes = parent_two.get_attr()

    parent_one_sliced = parent_one_attributes[:cross_point]
    parent_two_sliced = parent_two_attributes[cross_point:]

    # Generate child array
    child_attributes = np.concatenate([parent_one_sliced, parent_two_sliced])
    agent.set_attr(child_attributes)

    return agent


def mutate(agent: Agent) -> Agent:
    # Mutate a random attribute slightly
    attributes = agent.get_attr()
    attributes[np.random.randint(0, len(attributes))] += (
            2 * np.random.rand() - 1
            ) * 0.1
    agent.set_attr(attributes)

    return agent


def main():
    prev_agents = []

    # Create our inital pool of agents
    for x in tqdm(range(100)):
        prev_agents = loop(x, prev_agents)

    print(prev_agents[0])


def loop(genration_num, prev_agents) -> list[Agent]:
    needed_agents = 10 - len(prev_agents)
    new_agents = [Agent() for i in range(needed_agents)]
    agents = np.concatenate([prev_agents, new_agents])
    hours = 0

    while hours < 168:
        for agent in agents:
            agent.tick(pd.to_datetime("today"))

    # def get_score(a: Agent):
    #    return a.calculate_composite_score()

    # Sort by highest score
    # agents.sort(reverse=True, key=get_score())

    # The best agent is carried over to the next generation
    next_agents = []
    next_agents.append(agents[0])

    # The next best four are mated with each other to produce two children
    child_one = cross(agents[1], agents[2])
    child_two = cross(agents[3], agents[4])

    next_agents.append(child_one)
    next_agents.append(child_two)

    # 10% chance that an agent will mutate slightly
    for agent in next_agents:
        if np.random.rand() >= 0.9:
            agent = mutate(agent)

    return next_agents


if __name__ == "__main__":
    main()
