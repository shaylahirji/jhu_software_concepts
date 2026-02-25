import pytest
import os
import src.init_db as init_db

@pytest.mark.db
def test_init_db_calls_loader(monkeypatch):
    """
    Verifies that run_init calls the load_json_to_db function with the correct path.


    :param monkeypatch: Pytest fixture used to mock the database loader function and file system checks.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    :raises AssertionError: If the function is not called with the expected file path.
    """
    called_with_path = None

    # Define a mock function to replace the real one
    def mock_load(path):
        nonlocal called_with_path
        called_with_path = path

    # Mock os.path.exists to return True so the function proceeds to call the loader
    # This prevents the function from returning early when the file isn't physically there
    monkeypatch.setattr(os.path, "exists", lambda x: True)

    # Replace the real load_json_to_db with our mock
    monkeypatch.setattr("src.init_db.load_json_to_db", mock_load)

    # Execute the function
    init_db.run_init()

    # Assertions
    assert called_with_path == "Web_Scrape/raw_data/llm_extended_applicant_data.json"