Architecture
============

The Grad Cafe Application is designed using a multi-layered architecture to ensure 
separation of concerns between data acquisition, storage, and user presentation. 
The system follows a modular design where each component communicates through 
defined interfaces and database schemas.

System Overview
---------------

The application follows a standard Web-ETL-DB pattern:

1. **Web Layer**: Handles user requests, visualizes analytics, and triggers background tasks.
2. **ETL Layer**: Manages data extraction, LLM-based transformation, and cleaning.
3. **DB Layer**: Provides persistent PostgreSQL storage and manages data integrity.



Web Layer (Flask)
-----------------
The presentation layer is built with the Flask web framework. Its primary 
responsibilities include:

* **Routing**: Mapping URLs to specific Python functions (views) located in ``src/web_app/app/views.py``.
* **State Management**: Using threading to trigger data pulls without blocking the user interface.
* **Visualization**: Rendering Jinja2 HTML templates that display processed metrics and applicant trends.

ETL & Processing Layer
----------------------
The ETL process is the engine of the application, responsible for moving data 
from external web sources into the local system:

* **Extraction (src/web_scrape/scrape.py)**: Programmatically fetches raw applicant data from GradCafe.
* **Transformation & Intelligence**:
    * **Cleaning (src/web_scrape/clean.py)**: Handles missing values, standardizes date formats, and validates GPA/GRE ranges.
    * **LLM Integration (src/web_scrape/llm_hosting/)**: Utilizes a local LLM service to categorize and extract structured program names from unstructured comments.
* **Loading (src/load_data.py)**: Inserts cleaned data into PostgreSQL while enforcing ``url`` uniqueness to ensure idempotency.

Database Layer (PostgreSQL)
---------------------------
The storage layer utilizes a PostgreSQL relational database. Its role includes:

* **Persistence**: Securely storing the ``applicantdata`` table containing thousands of records.
* **Querying (src/query_data.py)**: Executing complex SQL aggregations to calculate acceptance rates and admission statistics.
* **Integrity**: Maintaining data quality through primary keys and transaction-based inserts to prevent partial data corruption during bulk loads.