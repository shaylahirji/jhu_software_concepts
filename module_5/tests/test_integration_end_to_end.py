import pytest
import threading

@pytest.mark.integration
def test_end_to_end(client, db, monkeypatch):
    """
    End-to-end test: Injects a fake scraper, pulls data into the database via app routes,
    updates analysis, checks analysis page rendering, and ensures idempotency.

    This version ensures that the application's internal state is updated by
    triggering the /pull_data and /update_analysis endpoints through the Flask
    test client. To prevent race conditions and ensure the mock is used, 
    the scraper is patched directly in the views module and threading is 
    forced to be synchronous.


    :param client: Flask test client for simulating requests.
    :type client: flask.testing.FlaskClient
    :param db: Database connection object.
    :type db: psycopg.Connection
    :param monkeypatch: Pytest monkeypatch fixture to replace functions temporarily.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None. Assertions validate full end-to-end workflow.
    :rtype: None
    :raises AssertionError: Raised if data is not inserted or duplicates are created.
    """
    # 1. SETUP: Define mock test data
    test_url_1 = "https://example.com/unique-integration-test-1"
    test_url_2 = "https://example.com/unique-integration-test-2"
    test_univ = "Integration Test University"

    # 2. CLEANUP: Clear old test data
    with db.cursor() as cur:
        cur.execute("DELETE FROM applicantdata WHERE url IN (%s, %s)", (test_url_1, test_url_2))
        db.commit()

    def fake_scraper(*args, **kwargs):
        """
        Fake scraper function injected via monkeypatch. Inserts test records 
        directly into the database.


        :param args: Positional arguments.
        :param kwargs: Keyword arguments.
        :return: Number of entries successfully processed.
        :rtype: int
        """
        test_entries = [
            (f'{test_univ} 1', 'Test Comments 1', '2024-02-26', test_url_1, 'Applied', 'Fall 2024', 'International', 3.5, 320, 160, 4.5, 'JD', 'LLM Test Program', 'LLM Test University'),
            (f'{test_univ} 2', 'Test Comments 2', '2026-02-23', test_url_2, 'Rejected', 'Fall 2026', 'US', 3.8, 330, 165, 5.0, 'JD', 'LLM Test Program 2', 'LLM Test University 2')
        ]
        
        with db.cursor() as cur:
            for entry in test_entries:
                cur.execute("""
                    INSERT INTO applicantdata (
                        program, comments, date_added, url, status, term, 
                        us_or_international, gpa, gre, gre_v, gre_aw, 
                        degree, llm_generated_program, llm_generated_university
                    )
                    SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM applicantdata WHERE url = %s
                    )
                """, entry + (entry[3],))
            db.commit()
        
        # This print will appear in 'Captured stdout call' if successful
        print(f"MOCK SCRAPER: Inserted {len(test_entries)} rows.")
        return len(test_entries)

    class SyncThread:
        """
        Mock Thread class to force background tasks to run synchronously.
        """
        def __init__(self, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}
            self.daemon = True

        def start(self):
            """Execute immediately."""
            self.target(*self.args, **self.kwargs)

    # 3. CRITICAL MONKEYPATCHING
    # We must patch the reference INSIDE views.py because it was imported as:
    # from src.load_data import scrape_and_update_db
    monkeypatch.setattr("src.web_app.app.views.scrape_and_update_db", fake_scraper)
    # Also patch the Threading class in views to stop it from going to background
    monkeypatch.setattr("src.web_app.app.views.threading.Thread", SyncThread)

    # 4. EXECUTION
    pull_response = client.post('/pull_data', follow_redirects=True)
    assert pull_response.status_code == 200

    # 5. VERIFICATION
    db.commit() # Sync transaction
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicantdata WHERE url IN (%s, %s)", (test_url_1, test_url_2))
        count = cur.fetchone()[0]
        assert count == 2

    # 6. ANALYSIS CHECK
    client.post('/update_analysis', follow_redirects=True)
    analysis_page = client.get('/analysis')
    html_content = analysis_page.data.decode('utf-8')
    assert "Fall 2026" in html_content

    # 7. IDEMPOTENCY
    client.post('/pull_data', follow_redirects=True)
    db.commit()
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM applicantdata WHERE url IN (%s, %s)", (test_url_1, test_url_2))
        assert cur.fetchone()[0] == 2