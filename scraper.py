import csv

from bs4 import BeautifulSoup, element
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

EXPAND_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/header/button"
VOLUME_INPUT_FIELD = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/div[1]/div[1]/div[3]/div/div[2]/input"
FIND_STOCKS_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[5]/div/div/div/div[2]/div[1]/div[3]/button[1]/span"
CRITERIA_CHANGED = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[2]/div[1]/span"
NUM_RESULTS = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[1]/div[1]/span[2]/span"
NEXT_BUTTON = "/html/body/div[1]/div/div/div[1]/div/div[2]/div/div/div[6]/div/div/section/div/div[2]/div[2]/button[3]"


def get_most_actives(min_volume=2500000, headless=True):
    stocks = []

    # Start Selenium
    options = Options()
    if headless:
        options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)
    driver.get(
        "https://finance.yahoo.com/screener/predefined/most_actives?offset=0&count=100"
    )

    # Wait until we can expand filter options
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, EXPAND_BUTTON))
    )

    # Expand those options
    driver.find_element(By.XPATH, EXPAND_BUTTON).click()

    # Wait until the input field is expanded
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, VOLUME_INPUT_FIELD))
    )

    # Set min movulme field
    volume_el = driver.find_element(By.XPATH, VOLUME_INPUT_FIELD)
    volume_el.clear()
    volume_el.send_keys(str(min_volume))

    # Wait until text "Screening Criteria has changed" appears
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, CRITERIA_CHANGED))
    )

    driver.find_element(By.XPATH, FIND_STOCKS_BUTTON).click()

    # Scrape top stocks using BeautifulSoup to crawl the html
    while True:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, NEXT_BUTTON))
        )

        next_button = driver.find_element(By.XPATH, NEXT_BUTTON)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("tbody")
        if isinstance(table, element.Tag):
            li = list(
                map(lambda x: x.contents[0], table.findChildren("a", recursive=True))
            )
            stocks.extend(li)

        if next_button.is_enabled():
            next_button.click()
        else:
            break

    driver.quit()

    # Write data to csv
    write_to_csv("most_traded.csv", stocks)


def write_to_csv(name: str, elements: list[str]) -> None:
    with open(name, "w", newline="") as csvfile:
        csvwriter = csv.writer(
            csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        csvwriter.writerow(elements)
        csvfile.close()


if __name__ == "__main__":
    try:
        get_most_actives(headless=False)
    except Exception as e:
        print(e)
