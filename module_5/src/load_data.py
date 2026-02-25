"""
This module contains functions to load scraped and cleaned data into a PostgreSQL database.

It utilizes psycopg SQL composition to prevent SQL injection and enforces inherent
limits on all database operations as per the Module 5 security requirements by
utilizing environment-based configuration and least-privilege database access.
"""
import os
import json
import psycopg
from psycopg import sql
from config import get_db_connection, Config
from web_scrape.scrape import scrape_data
from web_scrape.clean import clean_data

# Max allowed limit for queries retrieved from environment variables (Step 3)
MAX_ALLOWED_LIMIT = Config.MAX_ALLOWED_LIMIT


def get_latest_entry_text(raw_json_path="Web_Scrape/raw_data/raw.json"):
    """
    Returns the text of the most recent entry stored in a raw JSON file.

    :param raw_json_path: Path to the raw JSON file containing scraped entries.
    :type raw_json_path: str
    :return: Text content of the most recent entry, or None if the file doesn't exist.
    :rtype: str or None
    """
    if not os.path.exists(raw_json_path):
        return None
    with open(raw_json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except (json.JSONDecodeError, ValueError):
            return None

        if not data:
            return None

        first_key = next(iter(data))
        return data[first_key].get("text")


def _get_insert_statement():
    """Helper to generate composed SQL and reduce local variable count."""
    fields = [
        "program", "comments", "date_added", "url", "status", "term",
        "us_or_international", "gpa", "gre", "gre_v", "gre_aw", "degree",
        "llm_generated_program", "llm_generated_university"
    ]
    return sql.SQL("""
        INSERT INTO {table} ({fields})
        VALUES ({placeholders})
        ON CONFLICT (url) DO NOTHING;
    """).format(
        table=sql.Identifier("applicantdata"),
        fields=sql.SQL(", ").join(map(sql.Identifier, fields)),
        placeholders=sql.SQL(", ").join([sql.Placeholder()] * len(fields))
    )


def scrape_and_update_db(start_page=1, end_page=50):
    """
    Scrapes new data, cleans it, and inserts entries into the PostgreSQL database.

    :param start_page: Page number to start scraping from.
    :type start_page: int
    :param end_page: Page number to stop scraping at.
    :type end_page: int
    :return: Number of new rows successfully inserted into the database.
    :rtype: int
    """
    latest_text = get_latest_entry_text()
    scraped = scrape_data(start_page=start_page, end_page=end_page)
    new_raw_entries = {}

    for entry_id, entry in scraped.items():
        if latest_text and entry["text"] == latest_text:
            break
        new_raw_entries[entry_id] = entry

    if not new_raw_entries:
        print("No new data found.")
        return 0

    cleaned_rows = clean_data(new_raw_entries)
    connection = get_db_connection()
    new_rows = 0
    insert_stmt = _get_insert_statement()

    with connection.cursor() as cur:
        for row in cleaned_rows:
            try:
                univ, prog = row.get('University', ''), row.get('Program Name', '')
                combined = f"{univ} - {prog}" if univ and prog else prog
                params = (
                    combined, row.get("Comments"), row.get("date_added"),
                    row.get("URL"), row.get("Applicant Status"),
                    row.get("Program Start Date"), row.get("Citizenship"),
                    row.get("GPA"), row.get("GRE Score"), row.get("GRE V Score"),
                    row.get("GRE AW"), row.get("Degree Program"),
                    row.get("llm-generated-program", "Unknown"),
                    row.get("llm-generated-university", "Unknown")
                )
                cur.execute(insert_stmt, params)
                if cur.rowcount == 1:
                    new_rows += 1
            except (psycopg.Error, KeyError, ValueError) as e:
                print(f"Error inserting row: {e}")
                continue

    connection.commit()
    connection.close()
    print(f"[OK] {new_rows} new rows inserted.")
    return new_rows


def load_json_to_db(json_file_path):
    """
    Loads applicant data from a JSON file and inserts it into the database.
    This function uses sql.Identifier for table names and parameter binding
    for data values to defend against SQL injection.

    :param json_file_path: Path to the JSON file containing applicant data.
    :type json_file_path: str
    :return: Number of rows successfully inserted into the database.
    :rtype: int
    """
    if not os.path.exists(json_file_path):
        print(f"JSON file not found: {json_file_path}")
        return 0

    connection = get_db_connection()
    new_rows = 0

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        entries = json_data.values() if isinstance(json_data, dict) else json_data
        insert_stmt = _get_insert_statement()

        with connection.cursor() as cur:
            for entry in entries:
                univ, prog = entry.get('University', ''), entry.get('Program Name', '')
                combined = f"{univ} - {prog}" if univ and prog else prog
                cur.execute(insert_stmt, (
                    combined, entry.get("Comments"), entry.get("date_added"),
                    entry.get("URL"), entry.get("Applicant Status"),
                    entry.get("Program Start Date"), entry.get("Citizenship"),
                    entry.get("GPA"), entry.get("GRE Score"), entry.get("GRE V Score"),
                    entry.get("GRE AW"), entry.get("Degree Program"),
                    entry.get("llm-generated-program"),
                    entry.get("llm-generated-university")
                ))
                if cur.rowcount == 1:
                    new_rows += 1

        connection.commit()
        print(f"[OK] {new_rows} rows inserted from JSON.")
        return new_rows

    except (json.JSONDecodeError, ValueError, psycopg.Error) as error:
        print(f"[ERROR] Error loading JSON: {error}")
        return 0
    finally:
        connection.close()
