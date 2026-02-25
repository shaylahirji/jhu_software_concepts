"""
This module initialized database and creates a flask app instance.

It manages the application lifecycle, including blueprint registration and
initial database verification using secure SQL composition. It implements
Step 3 requirements by loading configuration from environment-based settings.
"""
import os
import sys
from flask import Flask
import psycopg
from psycopg import sql
from src.config import get_db_connection
from load_data import load_json_to_db
from web_app.config import Config  # Import hardened configuration
from .views import bp

# Add Project Root to sys.path so Python can see Module_3
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

# Corrected line length for Pylint C0301
RAW_DATA_DIR = os.path.join("Web_Scrape", "raw_data")
JSON_FILE = "llm_extended_applicant_data.json"
JSON_PATH = os.path.abspath(os.path.join(project_root, RAW_DATA_DIR, JSON_FILE))


def create_app():
    """
    Create and configure the Flask application instance.

    :return: Configured Flask application instance.
    :rtype: Flask
    :raises RuntimeError: If database verification fails during startup.
    """
    app = Flask(__name__)  # Flask constructor

    # Load configuration from the hardened Config class (Step 3)
    app.config.from_object(Config)

    app.register_blueprint(bp)  # render blueprints in views, register blueprints here

    # Only load JSON if database is empty (first run)
    try:
        connection = get_db_connection()
        with connection.cursor() as cur:
            # Step 2: Use psycopg SQL composition for query construction
            # Even for static queries, we use Identifier for table names to maintain pattern
            stmt = sql.SQL("SELECT COUNT(*) FROM {table};").format(
                table=sql.Identifier("applicantdata")
            )
            # Separation of construction and execution
            cur.execute(stmt)
            count = cur.fetchone()[0]
        connection.close()

        if count == 0:
            # Database is empty, load initial data
            if os.path.exists(JSON_PATH):
                load_json_to_db(JSON_PATH)
                print("[OK] Initial JSON data loaded successfully.")
            else:
                print("[SKIP] JSON file not found - database may need initialization")
        else:
            print(f"[OK] Database already initialized with {count} records")

    except (psycopg.errors.UndefinedTable, psycopg.errors.InsufficientPrivilege):
        # Database Hardening (Step 3): app_worker cannot create tables.
        # This catch handles cases where init_db.py hasn't been run yet.
        print("[WARNING] Database table 'applicantdata' does not exist or access denied.")
        print("[ACTION] Please run 'python init_db.py' with superuser credentials.")

    except (psycopg.Error, AttributeError, KeyError) as e:
        print(f"[WARNING] Could not verify database during startup: {e}")

    return app
