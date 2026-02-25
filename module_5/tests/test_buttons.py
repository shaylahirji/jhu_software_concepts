import pytest 

views_path = "src.web_app.app.views" #creating a variable for the path to views.py to use in monkeypatching

@pytest.mark.buttons
def test_pull_data_button(client, app, monkeypatch):
    """
    Test that the pull data button returns 200 and triggers the data scrape.

    Uses monkeypatch to mock the `scrape_and_update_db` function and the app's busy status.
    Wraps the configuration patch within an application context to avoid RuntimeError.

    :param client: Test client for sending requests to the Flask app.
    :type client: flask.testing.FlaskClient
    :param app: Flask application instance for context management.
    :type app: flask.Flask
    :param monkeypatch: Pytest fixture for dynamically modifying objects for testing.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None. Assertions validate the HTTP response and JSON body.
    :rtype: None
    :raises AssertionError: Raised if response status code is not 200 or JSON is incorrect.
    """
    # mock scrape function -- need to import from views.py
    monkeypatch.setattr(f"{views_path}.scrape_and_update_db", lambda **kwargs: None)
    
    with app.app_context():
        # make sure app is not busy by patching app.config directly
        monkeypatch.setitem(app.config, "IS_PULLING_DATA", False)

        response = client.post('/pull_data') # triggering pull data button route using POST
        assert response.status_code == 200 # asserting we get a response of 200 when not busy
        assert response.get_json() == {"ok": True} # verify JSON payload

@pytest.mark.buttons
def test_update_analysis_button(client, app, monkeypatch): 
    """
    Test that the update analysis button returns 200 when the app is not busy.

    Wraps the configuration patch within an application context to avoid RuntimeError.

    :param client: Test client for sending requests to the Flask app.
    :type client: flask.testing.FlaskClient
    :param app: Flask application instance for context management.
    :type app: flask.Flask
    :param monkeypatch: Pytest fixture for dynamically modifying objects for testing.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None. Assertions validate the HTTP response and JSON body.
    :rtype: None
    :raises AssertionError: Raised if response status code is not 200 or JSON is incorrect.
    """
    with app.app_context():
        # make sure app is not busy
        monkeypatch.setitem(app.config, "IS_PULLING_DATA", False)
        
        response = client.post('/update_analysis') # using POST as per requirements
        assert response.status_code == 200 # assert that update_analysis is 200 if not busy
        assert response.get_json() == {"ok": True} # verify JSON payload


@pytest.mark.buttons
def test_busy_gating(client, app, monkeypatch): 
    """
    Test that when a pull is in progress, both /pull_data and /update_analysis return 409.

    Uses monkeypatch to simulate the app being busy. 
    Wraps the configuration patch within an application context to avoid RuntimeError.

    :param client: Test client for sending requests to the Flask app.
    :type client: flask.testing.FlaskClient
    :param app: Flask application instance for context management.
    :type app: flask.Flask
    :param monkeypatch: Pytest fixture for dynamically modifying objects for testing.
    :type monkeypatch: _pytest.monkeypatch.MonkeyPatch
    :return: None. Assertions validate the HTTP responses and JSON busy status.
    :rtype: None
    :raises AssertionError: Raised if response status codes are not 409 or JSON is incorrect.
    """
    with app.app_context():
        # make busy status true using monkeypatch
        monkeypatch.setitem(app.config, "IS_PULLING_DATA", True)

        # test both buttons return 409 and {"busy": True} using POST
        response_pull = client.post('/pull_data')
        assert response_pull.status_code == 409
        assert response_pull.get_json() == {"busy": True}

        response_update = client.post('/update_analysis')
        assert response_update.status_code == 409
        assert response_update.get_json() == {"busy": True}