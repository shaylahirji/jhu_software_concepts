Testing Guide
=============

This document provides a detailed overview of the testing procedures for the Grad Cafe Application, including execution instructions, coverage reporting, and the use of specialized test fixtures.

Running Marked Tests
--------------------

The project utilizes ``pytest`` markers to categorize tests, allowing developers to run specific subsets of the suite depending on the focus of development.

* **Web Tests**: Validates Flask routes, page loading, and UI elements.
  .. code-block:: bash

     pytest -m web

* **Database Tests**: Focuses on CRUD operations and schema integrity.
  .. code-block:: bash

     pytest -m db

* **Integration Tests**: Executes end-to-end workflows, including simulated ETL processes.
  .. code-block:: bash

     pytest -m integration

Expected Selectors
------------------

The automated web and integration tests (using the Flask test client) look for specific HTML identifiers and classes to validate that the application state has updated correctly:

* **#pull-data-btn**: The primary button on the main dashboard used to initiate the scraper.
* **#update-analysis-btn**: The button used to trigger the ``query_data.py`` logic and refresh the analytics view.
* **#analysis-results**: The container ID used to verify that rounding and labels are applied correctly to the data.
* **.status-message**: A class used to detect "Busy" or "Success" feedback after a user action.

Test Doubles and Fixtures
-------------------------

To ensure tests are deterministic and do not depend on external network state or persistent database changes, the following doubles and fixtures are used:

* **db Fixture**: A ``psycopg`` connection fixture that manages the lifecycle of the database connection. It ensures that any data modified during a test is cleaned up or isolated via transactions.
* **SyncThread (Mock Object)**: Because the production app uses ``threading.Thread`` to prevent the UI from freezing during scraping, the test suite injects a ``SyncThread`` double. This forces the background task to run in the foreground, allowing the test to wait for the data to be inserted before running assertions.
* **fake_scraper**: A mock function that replaces the real web scraper. It returns a predefined set of records, ensuring the integration tests validate the **loading** and **querying** logic rather than actual internet connectivity.

Code Coverage
-------------

Code coverage is tracked using ``pytest-cov``. The goal for the core logic (ETL and Query) is high coverage to ensure all edge cases in data cleaning are met.

To generate a coverage report:

.. code-block:: bash

   coverage run --source=src -m pytest ../tests -v
   coverage report -m