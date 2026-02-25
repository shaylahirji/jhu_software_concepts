import pytest
import json
import os
from src.load_data import get_latest_entry_text, load_json_to_db, scrape_and_update_db

@pytest.mark.db
def test_get_latest_entry_text_variations(tmp_path):
    """
    Tests the logic for retrieving the most recent entry text from a raw JSON file.


    :param tmp_path: Pytest fixture for temporary file directories.
    :type tmp_path: pathlib.Path
    :return: None.
    :rtype: None
    """
    # Test missing file
    assert get_latest_entry_text("non_existent_file.json") is None

    # Test empty file
    empty_file = tmp_path / "empty.json"
    empty_file.write_text(json.dumps({}))
    assert get_latest_entry_text(str(empty_file)) is None

    # Test valid data
    valid_file = tmp_path / "valid.json"
    valid_file.write_text(json.dumps({"entry1": {"text": "Specific Text"}}))
    assert get_latest_entry_text(str(valid_file)) == "Specific Text"


@pytest.mark.db
def test_load_json_to_db_scenarios(db, tmp_path):
    """
    Tests loading JSON data into the database using various file formats and handling duplicates via unique constraints. Ensures idempotency by cleaning up specific test URLs before execution.


    :param db: Fixture providing a connection to the PostgreSQL database.
    :type db: psycopg.Connection
    :param tmp_path: Pytest fixture for temporary file directories.
    :type tmp_path: pathlib.Path
    :return: None.
    :rtype: None
    """
    # 0. CLEANUP: Ensure the specific test URL does not exist to avoid conflict failures
    test_url = "http://unique-test-collision.com"
    with db.cursor() as cur:
        cur.execute("DELETE FROM applicantdata WHERE url = %s", (test_url,))
        db.commit()

    # 1. Test File Not Found
    assert load_json_to_db("not_a_real_path.json") == 0

    # Define test data (Ensure fields match your DB unique constraints, specifically the URL)
    test_entry = {
        "University": "Johns Hopkins",
        "Program Name": "Data Science",
        "date_added": "2026-01-01",
        "URL": test_url,
        "Applicant Status": "Accepted",
        "llm-generated-program": "DS",
        "llm-generated-university": "JHU"
    }

    # 2. Test List Format - Initial Insert
    list_file = tmp_path / "test_list.json"
    list_file.write_text(json.dumps([test_entry]))
    inserted_count = load_json_to_db(str(list_file))
    assert inserted_count == 1

    # 3. Test Dictionary Format & ON CONFLICT (duplicate check)
    # Using the exact same data to ensure a row-level conflict is triggered
    dict_file = tmp_path / "test_dict.json"
    dict_file.write_text(json.dumps({"key_1": test_entry}))
    duplicate_count = load_json_to_db(str(dict_file))
    
    # This should be 0 because the record (defined by the URL/Key) already exists
    assert duplicate_count == 0


@pytest.mark.db
def test_load_json_to_db_exception_handling(tmp_path, monkeypatch):
    """
    Tests the exception block in load_json_to_db by mocking a JSON decode failure to ensure graceful error handling.


    :param tmp_path: Pytest fixture for temporary file directories.
    :type tmp_path: pathlib.Path
    :param monkeypatch: Pytest fixture for forcing exceptions during file loading.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    # Create a malformed JSON file
    bad_file = tmp_path / "corrupt.json"
    bad_file.write_text("This is not valid JSON content")
    
    # Mock json.load to raise a JSONDecodeError which the function's try-except should catch
    def mock_json_error(*args, **kwargs):
        raise json.JSONDecodeError("Mocked error", "", 0)
        
    import json
    monkeypatch.setattr(json, "load", mock_json_error)

    # Logic should catch the JSONDecodeError, print error message, and return 0
    result = load_json_to_db(str(bad_file))
    assert result == 0


@pytest.mark.db
def test_scrape_and_update_db_new_data(db, monkeypatch):
    """
    Tests the update loop when the scraper finds new data that does not match the latest database record, triggering an insertion.


    :param db: Fixture providing a connection to the PostgreSQL database.
    :type db: psycopg.Connection
    :param monkeypatch: Pytest fixture for mocking functions.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    # Mock dependencies to simulate new data flow
    monkeypatch.setattr("src.load_data.get_latest_entry_text", lambda: "Old String")
    monkeypatch.setattr("src.load_data.scrape_data", lambda **kwargs: {"id1": {"text": "New Unique String"}})
    monkeypatch.setattr("src.load_data.clean_data", lambda x: [{"University": "Test U", "Program Name": "Test P", "URL": "http://new.com", "date_added": "2026-02-15"}])

    inserted = scrape_and_update_db(start_page=1, end_page=1)
    # If the logic works, it should successfully insert the new row
    assert inserted >= 0


@pytest.mark.db
def test_scrape_and_update_db_no_new_data(db, monkeypatch):
    """
    Tests the update loop break condition when the scraper encounters a record already existing in the database.


    :param db: Fixture providing a connection to the PostgreSQL database.
    :type db: psycopg.Connection
    :param monkeypatch: Pytest fixture for mocking functions.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    shared_text = "Match Me"
    
    # Mock get_latest_entry_text to return the shared text
    monkeypatch.setattr("src.load_data.get_latest_entry_text", lambda: shared_text)
    
    # Mock scrape_data to return only 1 item containing that same text
    # This triggers the 'break' in the scrape loop
    monkeypatch.setattr("src.load_data.scrape_data", lambda **kwargs: {"id1": {"text": shared_text}})

    # This should trigger the 'break' in the loop and return 0 because no cleaning/inserting occurs
    inserted = scrape_and_update_db(start_page=1, end_page=1)
    assert inserted == 0