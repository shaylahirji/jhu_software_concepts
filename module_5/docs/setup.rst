Overview and Setup
==================

This document provides instructions on how to set up the environment, install 
dependencies, and run the Grad Cafe application and its associated test suite.

How to Run the App
------------------

Follow these steps to get the application running on your local machine:

1. **Clone the Repository**:
   Download the source code from your GitHub repository.

2. **Install Dependencies**:
   It is recommended to use a virtual environment. Install the required packages using:

   .. code-block:: bash

      pip install -r requirements.txt

3. **Initialize the Database**:
   Ensure your PostgreSQL server is running and initialize the schema and base data:

   .. code-block:: bash

      python src/init_db.py
      python src/load_data.py

4. **Start the Flask Application**:
   Run the web interface using the provided run script:

   .. code-block:: bash

      python src/web_app/run.py

Required Environment Variables
------------------------------

The application relies on specific environment variables for database connectivity and security. These should be defined in a ``.env`` file in the project root:

* **DATABASE_URL**: The connection string for your PostgreSQL database (e.g., ``postgresql://user:password@localhost:5432/gradscrape``).
* **FLASK_APP**: Points to the application entry point: ``src/web_app/app/__init__.py``.
* **PYTHONPATH**: Should be set to ``.`` to ensure modules in the ``src`` directory are discoverable.

Testing Guide
-------------

The project uses ``pytest`` and ``coverage`` for automated testing and quality assurance. Tests are categorized using markers.

**Running Marked Tests**
To run specific test suites based on markers:

.. code-block:: bash

   # Run only web-related tests
   pytest -m web

   # Run database and integration tests
   pytest -m "db or integration"

**Code Coverage**
To run the full test suite with coverage reporting:

.. code-block:: bash

   coverage run --source=src -m pytest ../tests -v
   coverage report -m

**Expected Selectors**
The automated web tests interact with the following HTML elements:
* ``#pull-data-btn``: Triggers the background scraping process.
* ``#update-analysis-btn``: Triggers the data aggregation and analysis refresh.
* ``.analysis-table``: The container where results are expected to render.

**Test Doubles and Fixtures**
* **db**: A pytest fixture providing a transacted connection to the PostgreSQL instance.
* **SyncThread**: A custom test double that mocks ``threading.Thread`` to force background ETL tasks to run synchronously during testing.
* **fake_scraper**: A monkeypatch-injected function that simulates web scraping by inserting static test records into the database.