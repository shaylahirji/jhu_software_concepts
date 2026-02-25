import pytest 
import psycopg
from src.web_app.app import create_app
from src.config import get_db_connection

@pytest.fixture
def app():
    """
    Creates and configures a Flask app instance for testing.

    This fixture initializes the Flask application and sets it in testing mode.

    :return: Configured Flask app instance.
    :rtype: flask.Flask
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture
def client(app):
    """
    Provides a test client for the Flask app.

    This fixture depends on the `app` fixture and returns a test client
    that can be used to simulate requests to the application.

    :param app: Flask app instance created by the `app` fixture.
    :type app: flask.Flask
    :return: Test client for the Flask app.
    :rtype: flask.testing.FlaskClient
    """
    return app.test_client()


@pytest.fixture
def db():
    """
    Provides a PostgreSQL database connection for testing.

    This fixture utilizes the get_db_connection function from the project 
    config, yields the connection, and ensures it is closed after the test.

    :return: psycopg.Connection object.
    :rtype: psycopg.Connection
    """
    conn = get_db_connection()
    yield conn
    if conn.info.transaction_status == psycopg.pq.TransactionStatus.INERROR: 
        conn.rollback()
    conn.close()


@pytest.fixture
def setup_test_table(db):
    """
    Ensures the necessary tables exist for database tests.

    :param db: The database connection provided by the db fixture.
    """
    # No changes needed here; db is the connection object from get_db_connection()
    db.commit()
    return db