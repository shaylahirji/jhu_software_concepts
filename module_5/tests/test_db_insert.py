import pytest 

test_table = "test_applicants" #creating empty test table to insert data into for testing

@pytest.fixture
def setup_test_table(db):
    """
    Fixture to create a temporary test table before running tests and drop it afterwards.

    Updated to remove the UNIQUE constraint. Duplicate prevention is now handled 
    programmatically via the SQL query (WHERE NOT EXISTS) to ensure compatibility 
    with databases containing pre-existing duplicate entries.

    :param db: Database connection object.
    :type db: psycopg connection
    :return: Name of the test table.
    :rtype: str
    """
    with db.cursor() as cur:
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {test_table} (
                id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
                term TEXT,
                us_or_international TEXT,
                gpa FLOAT,
                gre FLOAT,
                gre_v FLOAT,
                gre_aw FLOAT,
                degree TEXT,
                llm_generated_program TEXT,
                llm_generated_university TEXT
            )
        """)

        cur.execute(f"DELETE FROM {test_table}") #ensuring table is empty before test
        db.commit()

        yield test_table

        #drop temp table after test
        with db.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {test_table}")
            db.commit()

    
@pytest.mark.db
def test_new_data_insert(db, setup_test_table):
    """
    Test that new rows can be inserted into the test table and contain the required non-null fields.

    Updated to correctly index the PostgreSQL result row where row[0] is the SERIAL ID.

    :param db: Database connection object.
    :type db: psycopg connection
    :param setup_test_table: Name of the temporary test table.
    :type setup_test_table: str
    :return: None. Assertions validate table contents.
    :rtype: None
    :raises AssertionError: Raised if inserted row is missing or table is not empty before insert.
    """
    table = setup_test_table    

    with db.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        assert cur.fetchone()[0] == 0 #asserting table is empty

        cur.execute(f"INSERT INTO {table} (program, comments, date_added, url, status, term, us_or_international, gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    ("Test Program", "Test comment", "January 23, 2026", "https://example.com/1", "Accepted", "Fall 2026", "American", 3.46,  320, 160, 4.5, 'JD', 'LLM Test Program', 'LLM Test University')) #simulate insert

        cur.execute(f"SELECT * FROM {table}")
        row = cur.fetchone()
        assert row is not None
        # In PostgreSQL, row[0] is the ID (1), row[1] is the program
        assert row[1] == "Test Program" 


@pytest.mark.db
def test_idempotency_on_test_table(db, setup_test_table):
    """
    Test that duplicate rows do not create duplicates in the database.

    Updated to use a WHERE NOT EXISTS clause with a 5-column fingerprint (program, 
    date_added, url, status, comments). This manually checks for the existence of 
    the exact record before inserting, preventing redundancy without requiring 
    table-level unique constraints.

    :param db: Database connection object.
    :type db: psycopg connection
    :param setup_test_table: Name of the temporary test table.
    :type setup_test_table: str
    :return: None. Assertions validate duplicate prevention.
    :rtype: None
    :raises AssertionError: Raised if duplicate rows exist after repeated inserts.
    """ 
    table = setup_test_table
    test_data = ("Test Program 2", "Test comment 2", "August 13, 2024", "https://example.com/3", "Rejected", "Summer 2023", "International", 2.7,  270, 175, 4.4, 'PhD', 'LLM Test Program', 'LLM Test University')

    # Manual duplicate check via subquery
    insert_sql = f"""
        INSERT INTO {table} (program, comments, date_added, url, status, term, us_or_international, gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university) 
        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM {table} 
            WHERE program = %s 
              AND date_added = %s 
              AND url = %s 
              AND status = %s 
              AND comments = %s
        )
    """
    # Mapping params: 14 for the SELECT, then 5 for the WHERE clause check
    params = test_data + (test_data[0], test_data[2], test_data[3], test_data[4], test_data[1])

    with db.cursor() as cur:
        # Insert data for the first time
        cur.execute(insert_sql, params)

        # insert data a second time (should be ignored by WHERE NOT EXISTS)
        cur.execute(insert_sql, params)
        db.commit()

        # verify it only counts once, not twice
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        assert cur.fetchone()[0] == 1


@pytest.mark.db
def test_query_function():
    """
    Test that querying data returns a dictionary with the expected keys (required data fields in M3).

    :return: None. Assertions validate returned keys in the results dictionary.
    :rtype: None
    :raises AssertionError: Raised if results are not a dict or expected keys are missing.
    """
    from src.query_data import run_queries #importing the query function to test

    results = run_queries() #running the query function to get results
    assert isinstance(results, dict) #making sure it returns a dict

    expected_keys = ["fall_2026_app_count", "percent_international" , "avg_gpa", "avg_gre", "avg_gre_v", "avg_gre_aw", "avg_gpa_american_fall_2026", "percent_accepted_fall_2025", "avg_gpa_fall_2026_acceptances", "jhu_cs_masters_count", "num_entries_phd_cs_specified_schools", "llm_variance", "rejected_missing_gpa", "top_university", "top_count"]
    for key in expected_keys:
        assert key in results #make sure we have the variables we expect in our results dict