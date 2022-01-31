import csv
import os
from io import StringIO
import boto3
from tempfile import mkdtemp
from yaspin import yaspin

from bs4 import BeautifulSoup, element
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

from alpaca import get_emas

EXPAND_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/header/button"
VOLUME_INPUT_FIELD = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/div[1]/div[1]/div[3]/div/div[2]/input"
FIND_STOCKS_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/div[1]/div[3]/button[1]"
CRITERIA_CHANGED = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[2]/div[1]/span"
NUM_RESULTS = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[1]/div[1]/span[2]/span"
NEXT_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[2]/div[2]/button[3]"


def handler(event, context):
    return {"status_code": 200, "body": get_most_actives()}


def get_most_actives(min_volume=2500000) -> str:
    stocks = []
    # Start Selenium
    options = webdriver.ChromeOptions()
    options.binary_location = "/opt/chrome/chrome"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")

    with yaspin(text="Spinning up browser") as sp:
        driver = webdriver.Chrome(executable_path="/opt/chromedriver", options=options)

        driver.get(
            "https://finance.yahoo.com/screener/predefined/most_actives?offset=0&count=100"
        )

        sp.write("Headless Chrome driver successfully initialized")

    with yaspin(text="Fetching most actives") as sp:
        # Wait until we can expand filter options
        WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable((By.XPATH, EXPAND_BUTTON))
        )

        # Expand those options
        driver.find_element(By.XPATH, EXPAND_BUTTON).click()

        # Wait until the input field is expanded
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, VOLUME_INPUT_FIELD))
        )

        # Set min movulme field
        volume_el = driver.find_element(By.XPATH, VOLUME_INPUT_FIELD)
        volume_el.clear()
        volume_el.send_keys(str(min_volume))

        # Wait until text "Screening Criteria has changed" appears
        WebDriverWait(driver, 120).until(
            EC.presence_of_element_located((By.XPATH, CRITERIA_CHANGED))
        )

        driver.find_element(By.XPATH, FIND_STOCKS_BUTTON).click()

        # Scrape top stocks using BeautifulSoup to crawl the html
        while True:
            WebDriverWait(driver, 120).until(
                EC.presence_of_element_located((By.XPATH, NEXT_BUTTON))
            )

            next_button = driver.find_element(By.XPATH, NEXT_BUTTON)

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("tbody")
            if isinstance(table, element.Tag):
                li = list(
                    map(
                        lambda x: x.contents[0], table.findChildren("a", recursive=True)
                    )
                )
                stocks.extend(li)

            if next_button.is_enabled():
                next_button.click()
            else:
                break

        driver.quit()
        sp.write(f"Complete! Found {len(stocks)} active stocks")

    get_emas(stocks)

    return ",".join(stocks[:5])
