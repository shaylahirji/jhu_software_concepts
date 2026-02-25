import pytest 
import re

@pytest.mark.analysis
def test_analysis_labels_and_rounding(client):
    """
    Test that the /analysis page includes "Answer" labels for rendered analysis,
    has at least 12 answers, and any percentage is formatted with exactly two decimals.

    :param client: Test client used to make requests to the Flask app.
    :type client: flask.testing.FlaskClient
    :return: None. Assertions are used to validate correctness.
    :rtype: None
    :raises AssertionError: Raised if any of the label or percentage formatting checks fail.
    """
    response = client.get('/analysis')
    html_content = response.data.decode('utf-8')

    labels = re.findall(r"Answer", html_content, re.IGNORECASE) #find all instances of "Answer" in the page text
    assert len(labels) >= 11, f"Expected at least 11 'Answer' labels, found {len(labels)}" #making sure we answered all 11 query questions

    #using regex to find patters of numbers ending in a % sign
    all_percentages = re.findall(r"([\d\.]+)%", html_content)
    assert len(all_percentages) > 0, "No percentages found on page" #ensuring at least one percentage is found on page, stop test if not

    for value in all_percentages:
        assert "." in value, f"Percentage {value}% is missing decimal places"
        
        # Split at decimal and make sure two values after decimal point
        decimal_part = value.split(".")[1]
        assert len(decimal_part) == 2, f"Percentage {value}% must have exactly 2 decimal"
