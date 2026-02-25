import pytest 
from bs4 import BeautifulSoup


#creating a list of all app routes except /analysis
#formatting with the path and a unique piece of text on each page so as to make sure the correct page loaded for correct route
other_routes = [
    ('/', 'Shayla Hirji'),
    ('/contact','Contact'),
    ('/projects', 'Projects')
]

@pytest.mark.web
def test_app_routes(app):
    """
    Asserts that a testable Flask app is created with required routes registered.

    :param app: Flask application instance.
    :type app: flask.Flask
    :return: None. Assertions validate route registration.
    :rtype: None
    :raises AssertionError: Raised if any expected route is not registered in the app.
    """
    registered_paths = [str(rule) for rule in app.url_map.iter_rules()] #check all registered paths in flask app

    assert '/analysis' in registered_paths #checking that analysis page exists (is registered) in flask app

    for path, route in other_routes:
        assert path in registered_paths #ensuring routes exist for all pages defined in other_routes list


@pytest.mark.web 
def test_analysis_page_load(client):
    """
    Test that the /analysis page loads correctly with status 200 and contains required elements.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    :return: None. Assertions validate page content and buttons.
    :rtype: None
    :raises AssertionError: Raised if the page does not contain "Analysis", at least one "Answer:", or required buttons.
    """
    response = client.get('/analysis')
    
    # Assert status code is 200
    assert response.status_code == 200
    
    # Parse HTML with BeautifulSoup for cleaner assertions
    soup = BeautifulSoup(response.data, 'html.parser')
    page_text = soup.get_text()
    
    # Assert the page contains the text "Analysis"
    assert "Analysis" in page_text
    
    # Assert at least one "Answer:" label is present
    assert "Answer:" in page_text

    pull_data_btn = soup.find("a", id="pull-data-btn") #creating a variable to find pull data button to verify
    update_analysis_btn = soup.find("a", id="update-analysis-btn") 
    
    assert pull_data_btn is not None, "Pull Data button missing" #asserting that button exists and stopping test if not
    assert update_analysis_btn is not None, "Update Analysis button missing"


@pytest.mark.web
@pytest.mark.parametrize("path, expected_text", other_routes)
def test_other_pages_load(client, path, expected_text):
    """
    Test that other pages load correctly and contain expected text.

    :param client: Flask test client.
    :type client: flask.testing.FlaskClient
    :param path: URL path of the page to test.
    :type path: str
    :param expected_text: Unique expected text on the page to verify correct page loaded.
    :type expected_text: str
    :return: None. Assertions validate page content.
    :rtype: None
    :raises AssertionError: Raised if the page status is not 200 or expected text is missing.
    """
    response = client.get(path)
    # Assert status code is 200
    assert response.status_code == 200
    
    assert expected_text in response.get_data(as_text=True) #make sure correct page loads for each route with correct text
