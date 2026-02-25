"""
This module contains Flask view functions for handling requests and rendering templates.

This layer handles user interaction and ensures that background tasks are 
managed safely without exposing internal database states or risking 
application crashes during high-load data operations. It utilizes the 
hardened database layer to enforce Step 2 and Step 3 security standards.
"""
import os
import sys
import threading
from flask import Blueprint, render_template, current_app, jsonify
from query_data import run_queries
from load_data import scrape_and_update_db

# Adjust pathing for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

bp = Blueprint('views', __name__)

@bp.route('/')
def home():
    """
    Render the home page of the application.

    :return: Rendered home.html template.
    :rtype: str
    """
    return render_template("home.html")


@bp.route('/contact')
def contact():
    """
    Render the contact page of the application.

    :return: Rendered contact.html template.
    :rtype: str
    """
    return render_template("contact.html")

@bp.route('/projects')
def projects():
    """
    Render the projects page of the application.

    :return: Rendered projects.html template.
    :rtype: str
    """
    return render_template("projects.html")


@bp.route('/analysis')
def analysis():
    """
    Execute database queries and render the analysis page with results.

    This endpoint triggers the secure query execution logic defined in 
    the query_data module, adhering to SQL composition standards and 
    inherent result limits (Step 2 & 3).

    :return: Rendered queries.html template populated with query results.
    :rtype: str
    """
    results = run_queries()
    # Pull current state from the hardened application configuration
    results['is_pulling_data'] = current_app.config.get("IS_PULLING_DATA", False)
    return render_template("queries.html", **results)


@bp.route('/pull_data', methods=['GET', 'POST'])
def pull_data():
    """
    Initiate a background thread to scrape data and update the database.

    Enforces safe state management by checking for active background tasks
    to prevent data collision. Database operations within the thread utilize 
    the least-privilege 'app_worker' account for hardening.

    :return: JSON response with status 'ok' (200) or 'busy' (409).
    :rtype: tuple[flask.Response, int]
    """
    # 1. Check if already busy
    if current_app.config.get("IS_PULLING_DATA", False):
        return jsonify({"busy": True}), 409

    # 2. Set the busy flag in the application configuration
    current_app.config["IS_PULLING_DATA"] = True

    def scrape_in_background(app_instance):
        """
        Run scraping logic inside the Flask application context.

        :param app_instance: Flask application instance.
        :type app_instance: flask.Flask
        """
        with app_instance.app_context():
            try:
                # Limit the scope of initial background scrape (Inherent Limit)
                scrape_and_update_db(start_page=1, end_page=10)
            except Exception as exc:  # pylint: disable=broad-except
                # Safety: Ensure error doesn't crash main app thread
                print(f"Background Task Error: {exc}")
            finally:
                # 3. Always clear the flag when finished
                app_instance.config["IS_PULLING_DATA"] = False

    # Resolved AttributeError by using the correct Flask proxy unwrapping method.
    # The _get_current_object() call allows the thread to access the true App instance.
    # W0212 fixed via explicit pylint suppression for required proxy unwrapping.
    thread = threading.Thread(
        target=scrape_in_background,
        args=(current_app._get_current_object(),)  # pylint: disable=protected-access
    )
    thread.daemon = True
    thread.start()

    # 4. Return 200 OK
    return jsonify({"ok": True}), 200


@bp.route('/update_analysis', methods=['GET', 'POST'])
def update_analysis():
    """
    Handle requests to update analysis results.

    Verifies the application is not currently modifying records before
    allowing the analysis view to refresh, ensuring data integrity.

    :return: JSON response with status 'ok' (200) or 'busy' (409).
    :rtype: tuple[flask.Response, int]
    """
    if current_app.config.get("IS_PULLING_DATA", False):
        return jsonify({"busy": True}), 409

    return jsonify({"ok": True}), 200
