"""
This module scrapes survey data from The GradCafe Website.

This module serves as the initial data ingestion point. It collects raw data 
that will be cleaned and subsequently inserted into the database using 
secure SQL composition methods defined in the database module. It adheres to
Step 3 requirements by externalizing data collection from the application core.
"""
import json
import os
from urllib import parse, request, error
from bs4 import BeautifulSoup

URL = "https://www.thegradcafe.com/survey/"


def _parse_row_content(row, results, current_index):
    """
    Helper to extract text from a row and its subsequent rows if they are comments.

    Resolves R0914 by reducing local variable count in the main loop.

    :param row: The current BeautifulSoup tag object for a table row.
    :type row: bs4.element.Tag
    :param results: The list of all BeautifulSoup row objects.
    :type results: list
    :param current_index: The current index within the results list.
    :type current_index: int
    :return: A tuple containing the data dictionary and the next index to process.
    :rtype: tuple[dict or None, int]
    """
    cells = row.find_all("td")
    if len(cells) < 4 or not cells[0].get_text(strip=True):
        return None, current_index + 1

    university = cells[0].get_text(strip=True)
    program_name = cells[1].get_text(separator=" ", strip=True)
    date_added = cells[2].get_text(strip=True)
    decision = cells[3].get_text(strip=True)
    full_text = row.get_text(separator=" ", strip=True)

    j = current_index + 1
    while j < len(results):
        next_cells = results[j].find_all("td")
        if len(next_cells) >= 4 and next_cells[0].get_text(strip=True):
            break
        full_text += " " + results[j].get_text(separator=" ", strip=True)
        j += 1

    data = {
        "university": university,
        "program": program_name,
        "date_added": date_added,
        "decision": decision,
        "text": full_text
    }
    return data, j


def scrape_data(start_page=1, end_page=2500):
    """
    Scrapes survey data from The GradCafe website for a range of pages.

    :param start_page: The first page to start scraping from.
    :type start_page: int
    :param end_page: The last page to scrape.
    :type end_page: int
    :return: Dictionary containing all scraped entries keyed by entry ID.
    :rtype: dict
    """
    raw_entries = {}
    entry_id = 0

    for page_num in range(start_page, end_page + 1):
        page_url = parse.urljoin(URL, f"?page={page_num}")
        try:
            req = request.Request(
                page_url,
                headers={"User-Agent": "Mozilla/5.0 ShaylaHirjiScraper/1.0"}
            )
            # Using 'with' to handle resource allocation (R1732)
            with request.urlopen(req) as page:
                soup = BeautifulSoup(page.read().decode("utf-8"), "html.parser")

            results = soup.select("tr")
            idx = 0
            while idx < len(results):
                row_data, next_idx = _parse_row_content(results[idx], results, idx)
                if row_data:
                    entry_id += 1
                    row_data.update({"page": page_num, "url": page_url})
                    raw_entries[entry_id] = row_data
                idx = next_idx

        except error.HTTPError as err:
            print(f"HTTP Error {err.code} on page {page_num}: {err.reason}")

    return raw_entries


def save_data(data, filename="raw_data/raw.json"):
    """
    Saves the scraped data to a JSON file.

    Ensures the target directory exists to prevent runtime errors in a 
    hardened environment (Step 3).

    :param data: Dictionary of scraped entries to save.
    :type data: dict
    :param filename: File path where the JSON data will be saved.
    :type filename: str
    """
    # Create directory if it does not exist (Defensive Programming)
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    scraped_results = scrape_data(start_page=1, end_page=5)
    save_data(scraped_results)