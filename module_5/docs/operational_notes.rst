Operational Notes & Troubleshooting
====================================

.. contents:: Table of Contents
   :local:

Operational Policies
--------------------

Busy-State Policy
~~~~~~~~~~~~~~~~~
To prevent race conditions and database corruption, the system implements a **Busy Gate**. 
* While a "Pull Data" task is active, the system sets an internal state.
* Any subsequent ``POST /pull-data`` or ``POST /update-analysis`` requests will return a **409 Conflict** status with ``{"busy": true}``.
* This ensures that the ETL process is atomic and non-overlapping.

Idempotency Strategy
~~~~~~~~~~~~~~~~~~~~
The system is designed to be idempotent, meaning multiple executions of the same scraper results will not change the database state beyond the initial application.
* We utilize a "Check-before-Insert" logic.
* If the data already exists, the record is ignored or updated rather than duplicated.

Uniqueness Keys
~~~~~~~~~~~~~~~
To identify unique Grad Cafe entries, we use a composite key consisting of:
* ``institution``
* ``program``
* ``decision_date``
* ``applicant_stats``

Troubleshooting
---------------

Local Setup Issues
~~~~~~~~~~~~~~~~~~
* **Database Connection Refused**: Ensure PostgreSQL is running and your ``DATABASE_URL`` environment variable matches your local credentials.
* **ModuleNotFound**: Ensure you have activated your virtual environment (``.venv``) and ran ``pip install -r requirements.txt``.

CI (GitHub Actions) Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~
* **Postgres Service Failure**: If tests fail in CI but pass locally, verify the ``tests.yml`` has the correct service container configuration.
* **100% Coverage Failure**: If the build fails with a coverage error, check ``coverage_summary.txt`` to identify which lines in ``src/`` are not being exercised by your Pytest suite.