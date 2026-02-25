import pytest
import json
import io
from src.web_scrape.clean import (
    extract_decision_and_date,
    extract_comments,
    extract_program_start,
    extract_citizenship,
    extract_gre_score,
    extract_gre_v_score,
    extract_degree_type,
    extract_gpa,
    extract_gre_aw,
    clean_data,
    load_data
)

def test_extract_decision_and_date():
    """
    Verifies that decision status and dates are correctly parsed from raw strings.
    Covers variants like Wait listed, Interview, and Withdrawn.


    :return: None.
    :rtype: None
    """
    # Standard formats
    assert extract_decision_and_date("Accepted on 15 Jan 2026") == ("Accepted", "15 Jan 2026")
    assert extract_decision_and_date("Rejected on 2 Feb") == ("Rejected", "2 Feb")
    
    # Coverage for lines 45-50 and 67-74 (alternative statuses and date cleaning)
    assert extract_decision_and_date("Waitlisted on 10 Mar 2026") == ("Waitlisted", "10 Mar 2026")
    assert extract_decision_and_date("Wait listed on 11 Mar 2026") == ("Wait listed", "11 Mar 2026")
    assert extract_decision_and_date("Interview on 12 Feb") == ("Interview", "12 Feb")
    assert extract_decision_and_date("Withdrawn on 20 Jan") == ("Withdrawn", "20 Jan")
    
    # Test "Other" status
    assert extract_decision_and_date("Other on 05 Mar") == ("Other", "05 Mar")
    
    # Test no match
    assert extract_decision_and_date("Pending Review") == (None, None)


def test_extract_comments():
    """
    Verifies that comments are extracted and GPA references are stripped from the raw text.


    :return: None.
    :rtype: None
    """
    text = "Fall 2026 International This is my comment GPA 3.85"
    assert extract_comments(text) == "This is my comment"
    
    # Coverage for line 94 (comment becomes empty after cleaning)
    assert extract_comments("Fall 2026 International GPA 4.0") is None
    
    # Test no comment text after metadata
    assert extract_comments("Fall 2026 International") is None


def test_extract_program_start():
    """
    Verifies extraction of the start term and year from text.


    :return: None.
    :rtype: None
    """
    assert extract_program_start("I want to start in Fall 2026") == "Fall 2026"
    assert extract_program_start("Spring 2025 entry") == "Spring 2025"
    
    # Coverage for other terms (Summer/Winter)
    assert extract_program_start("Summer 2024") == "Summer 2024"
    assert extract_program_start("Winter 2023") == "Winter 2023"
    assert extract_program_start("No date mentioned") is None


def test_extract_citizenship():
    """
    Verifies the categorization of applicant citizenship into American, International, or Other.


    :return: None.
    :rtype: None
    """
    assert extract_citizenship("I am American") == "American"
    assert extract_citizenship("Status: international") == "International"
    assert extract_citizenship("Other") == "Other"
    
    # Coverage for line 128-129 (Unknown or missing citizenship)
    assert extract_citizenship("Unknown") is None
    assert extract_citizenship("") is None


def test_extract_gre_scores():
    """
    Tests extraction of various GRE score components (Total, Verbal, and Analytical Writing).


    :return: None.
    :rtype: None
    """
    sample = "My scores: GRE 320, GRE V 160, GRE AW 4.5"
    assert extract_gre_score(sample) == 320
    assert extract_gre_v_score(sample) == 160
    assert extract_gre_aw(sample) == 4.5
    
    # Coverage for line 165 and 181-184 (AW as integer conversion and score cleanup)
    assert extract_gre_aw("GRE AW 5") == 5.0
    assert extract_gre_aw("GRE AW n/a") is None
    
    # Test missing scores
    assert extract_gre_score("No GRE") is None


def test_extract_degree_type():
    """
    Verifies that degree objectives (PhD, Masters, MFA, etc.) are identified correctly.


    :return: None.
    :rtype: None
    """
    assert extract_degree_type("Applying for a PhD") == "PhD"
    assert extract_degree_type("Masters program") == "Masters"
    
    # Coverage for additional degree types (Line 113)
    assert extract_degree_type("MFA in Studio Art") == "MFA"
    assert extract_degree_type("PsyD candidate") == "PsyD"
    assert extract_degree_type("Bachelors") is None


def test_extract_gpa():
    """
    Verifies extraction of GPA as a float and handling of non-numeric entries.


    :return: None.
    :rtype: None
    """
    assert extract_gpa("My GPA 3.98") == 3.98
    assert extract_gpa("GPA 4.0") == 4.0
    
    # Coverage for line 144-147 (Invalid GPA strings)
    assert extract_gpa("GPA is n/a") is None
    assert extract_gpa("No GPA provided") is None


def test_clean_data_comprehensive():
    """
    Tests the clean_data function for mapping keys and handling entries with missing data fields.


    :return: None.
    :rtype: None
    """
    # Test valid entry
    raw_input = {
        "id1": {
            "program": "CS",
            "university": "JHU",
            "text": "Fall 2026 American GPA 4.0",
            "decision": "Accepted on 1 Jan",
            "date_added": "2026-01-01",
            "url": "http://test.com"
        },
        # Coverage for line 259-267 (Entry missing 'text' or critical fields)
        "id2": {
            "program": "Math",
            "university": "MIT"
        }
    }
    
    cleaned = clean_data(raw_input)
    assert len(cleaned) >= 1
    assert cleaned[0]["University"] == "JHU"
    assert cleaned[0]["GPA"] == 4.0


def test_load_data_io_failure_and_success(monkeypatch):
    """
    Tests the load_data function's file I/O operations and JSON parsing.


    :param monkeypatch: Pytest fixture for mocking built-ins.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    # 1. Test Success
    raw_content = {"1": {"text": "Fall 2026 American", "university": "JHU"}}
    
    # Mocking open for both reading raw.json and writing applicant_data.json
    mock_file = io.StringIO(json.dumps(raw_content))
    monkeypatch.setattr("builtins.open", lambda p, m="r", encoding=None: mock_file)
    monkeypatch.setattr("json.dump", lambda data, file, indent=None: None)

    result = load_data()
    assert isinstance(result, list)
    
    # 2. Coverage for load_data exceptions (Line 200-203)
    def mock_open_error(*args, **kwargs):
        raise FileNotFoundError()
    
    monkeypatch.setattr("builtins.open", mock_open_error)
    assert load_data() == []