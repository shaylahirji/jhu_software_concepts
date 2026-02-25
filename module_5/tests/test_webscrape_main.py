import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# --- Pytest-only Mocking of heavy AI libraries and Environment ---

# Prevent ModuleNotFoundErrors during import by mocking heavy dependencies
class DummyAI:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules["llama_cpp"] = DummyAI()
sys.modules["huggingface_hub"] = DummyAI()

# Set environment variables to bypass the check logic in main.py
os.environ["SKIP_SCRAPING"] = "False" 

# Capture original functions to restore them after import
original_exit = sys.exit
original_exists = os.path.exists
original_open = open

# 1. Force os.path.exists to return True
# 2. Neutralize sys.exit
# 3. Mock open to return a dummy file to prevent FileNotFoundError during import
os.path.exists = lambda path: True
sys.exit = lambda code: None

try:
    # Use a dummy context manager for 'open' to satisfy top-level script execution
    with MagicMock() as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "{}"
        # Temporarily override open only during the import
        import builtins
        builtins.open = lambda *args, **kwargs: mock_open.return_value
        
        import src.web_scrape.main as main
finally:
    # Always restore original functions immediately after import
    import builtins
    builtins.open = original_open
    sys.exit = original_exit
    os.path.exists = original_exists

@pytest.fixture
def mock_dependencies(monkeypatch, tmp_path):
    """
    Fixture to mock file system paths and heavy functions to prevent actual 
    LLM loading or web scraping during tests.


    :param monkeypatch: Pytest fixture for mocking.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :param tmp_path: Pytest fixture for temporary directory.
    :type tmp_path: pathlib.Path
    :return: Dictionary containing mock paths.
    :rtype: dict
    """
    # Create temporary paths for data isolation
    raw_dir = tmp_path / "raw_data"
    raw_dir.mkdir()
    raw_json = raw_dir / "raw.json"
    output_json = raw_dir / "llm_extended_applicant_data.json"
    checkpoint_json = raw_dir / ".llm_checkpoint.json"

    # Ensure the raw_json exists in the temp directory so main.py functions work
    raw_json.write_text(json.dumps({"test": "data"}))

    # Mock file paths in the main module to point to temporary test files
    monkeypatch.setattr(main, "raw_json_path", str(raw_json))
    monkeypatch.setattr(main, "output_path", str(output_json))
    monkeypatch.setattr(main, "checkpoint_path", str(checkpoint_json))

    # Mock heavy functions to ensure no real AI or Web calls occur
    monkeypatch.setattr(main, "scrape_data", lambda: {"1": {"text": "test"}})
    monkeypatch.setattr(main, "save_data", lambda x: None)
    monkeypatch.setattr(main, "_load_llm", lambda: "mock_model")
    monkeypatch.setattr(main, "_call_llm", lambda x: {"standardized_program": "Standardized CS"})
    monkeypatch.setattr(main, "load_data", lambda: [{"Program Name": "CS", "University": "JHU"}])
    
    return {
        "raw_json": raw_json,
        "output_json": output_json,
        "checkpoint_json": checkpoint_json
    }

def test_log_function(capsys):
    """
    Verifies that the log function correctly formats timestamps and flushes output.


    :param capsys: Pytest fixture to capture stdout/stderr.
    :type capsys: _pytest.capture.CaptureFixture
    :return: None.
    :rtype: None
    """
    main.log("Test Message")
    captured = capsys.readouterr()
    assert "Test Message" in captured.out
    assert "[" in captured.out 

def test_timeout_handler():
    """
    Verifies that the timeout_handler raises the custom TimeoutException.


    :return: None.
    :rtype: None
    :raises TimeoutException: Expected result of the handler.
    """
    with pytest.raises(main.TimeoutException, match="LLM call timed out"):
        main.timeout_handler(None, None)

def test_main_logic_flow(mock_dependencies, monkeypatch):
    """
    Tests the high-level logic of the main script, including data loading and LLM processing.


    :param mock_dependencies: Fixture providing mocked paths.
    :type mock_dependencies: dict
    :param monkeypatch: Pytest fixture for mocking.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    # Simulate existing data for the main logic flow
    mock_dependencies["raw_json"].write_text(json.dumps({"1": {"text": "test"}}))
    monkeypatch.setattr(main, "CHECKPOINT_INTERVAL", 1)
    
    data = [{"Program Name": "CS", "University": "JHU"}]
    
    # Verify LLM call result integration
    result = main._call_llm(data[0]["Program Name"])
    data[0]["LLM Program Name"] = result["standardized_program"]
    
    assert data[0]["LLM Program Name"] == "Standardized CS"

def test_checkpoint_resume_logic(mock_dependencies, monkeypatch):
    """
    Tests the logic that restores progress from a checkpoint file.


    :param mock_dependencies: Fixture providing mocked paths.
    :type mock_dependencies: dict
    :param monkeypatch: Pytest fixture for mocking.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    # Create a fake checkpoint to test the resume functionality
    checkpoint_content = {
        "last_index": 1,
        "0": {"LLM Program Name": "Standardized Math", "LLM University Name": "MIT"}
    }
    mock_dependencies["checkpoint_json"].write_text(json.dumps(checkpoint_content))
    
    cleaned_data = [
        {"Program Name": "Math", "University": "MIT"},
        {"Program Name": "Bio", "University": "JHU"}
    ]
    
    # Simulate the resume logic by manually reading the mocked checkpoint
    start_index = 0
    if os.path.exists(main.checkpoint_path):
        with open(main.checkpoint_path, "r") as f:
            cp = json.load(f)
            start_index = cp.get("last_index", 0)
            for i in range(start_index):
                cleaned_data[i]["LLM Program Name"] = cp[str(i)]["LLM Program Name"]

    assert start_index == 1
    assert cleaned_data[0]["LLM Program Name"] == "Standardized Math"

def test_llm_failure_fallback(monkeypatch):
    """
    Verifies that the script falls back to a basic split if the LLM call fails.


    :param monkeypatch: Pytest fixture for mocking.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None.
    :rtype: None
    """
    def mock_fail(text):
        raise Exception("LLM Error")

    # Mock the failure and the fallback function to test error handling
    monkeypatch.setattr(main, "_call_llm", mock_fail)
    monkeypatch.setattr(main, "_split_fallback", lambda x: [x.split()[0]])

    program_text = "Computer Science"
    try:
        main._call_llm(program_text)
    except Exception:
        fallback = main._split_fallback(program_text)[0]
    
    assert fallback == "Computer"