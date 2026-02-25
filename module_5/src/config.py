"""
This module provides the database configuration and connection logic for the application.

It implements Step 2 SQL Injection Defenses by enforcing query limits and using
psycopg SQL composition to handle dynamic SQL components safely. It also implements 
Step 3 Database Hardening by utilizing environment variables for credentials.
"""
import os
from urllib.parse import quote_plus
import psycopg
from psycopg import sql
from dotenv import load_dotenv

# Load environment variables from the .env file in the root directory
load_dotenv()

class Config:
    """
    Centralized configuration class to manage database credentials and limits.
    
    This class pulls sensitive information from environment variables to 
    adhere to Step 3 Database Hardening requirements.
    """
    # Database credentials (hardcoded postgres user removed for hardening)
    DB_USER = os.getenv("DB_USER", "app_worker")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "gradscrape")

    # Safe password encoding for URL format
    SAFE_PASSWORD = quote_plus(DB_PASSWORD)

    # Inherent Limit enforcement constant
    # Fixed W1508: Changed default to string "100" to match os.getenv expectations
    MAX_ALLOWED_LIMIT = int(os.getenv("MAX_ALLOWED_LIMIT", "100"))

    # Connection string utilizing environment variables
    DATABASE_URL = f"postgresql://{DB_USER}:{SAFE_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_db_connection():
    """
    Establishes a connection to the PostgreSQL database using the DATABASE_URL.

    This fulfills the requirement to avoid environment-specific hard-coded paths
    and utilizes the least-privilege app_worker account for hardening.

    :return: A connection object to the PostgreSQL database.
    :rtype: psycopg.Connection
    :raises psycopg.OperationalError: If the connection to the database fails.
    """
    # Connect using the URL format from the Config class
    connection = psycopg.connect(Config.DATABASE_URL)
    return connection


def clamp_limit(user_limit):
    """
    Enforces a maximum allowed limit for database queries.

    This fulfills the Step 2 requirement to clamp query limits to 1-100.
    It ensures that endpoints handle input safely without returning excessive data.

    :param user_limit: The limit requested by the user or application logic.
    :type user_limit: int or str
    :return: An integer between 1 and 100.
    :rtype: int
    """
    try:
        val = int(user_limit)
        # enforce range 1 to the defined MAX_ALLOWED_LIMIT (Step 3)
        return max(1, min(val, Config.MAX_ALLOWED_LIMIT))
    except (ValueError, TypeError):
        # Default fallback if input is malicious or invalid
        return 10


def compose_query(table_name, columns, limit=10):
    """
    Composes a secure SQL statement using psycopg SQL composition.

    This fulfills the Step 2 requirement to use sql.Identifier and sql.SQL
    instead of f-strings or concatenation. Table and column names are
    safely quoted via sql.Identifier.

    :param table_name: Name of the table to query.
    :type table_name: str
    :param columns: List of column names to select.
    :type columns: list
    :param limit: The number of records to return (will be clamped).
    :type limit: int
    :return: A composed SQL object ready for execution.
    :rtype: psycopg.sql.Composed
    """
    safe_limit = clamp_limit(limit)

    # Use Identifier for dynamic structural parts (table/column names)
    # Use Literal for the clamped limit value (Step 2)
    query = sql.SQL("SELECT {cols} FROM {table} LIMIT {lim}").format(
        cols=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_name),
        lim=sql.Literal(safe_limit)
    )
    return query


if __name__ == "__main__":
    conn = get_db_connection()
    print(f"Connected to {Config.DB_NAME} as {Config.DB_USER}")
    conn.close()
