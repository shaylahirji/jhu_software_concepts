"""
This module contains the Config class which holds data pulling status and DB settings.

This configuration handles environment-based database settings and enforces 
application-wide security constraints such as query result limits to defend 
against resource exhaustion and data leaks. It implements Step 3 requirements 
by loading secrets from a protected .env file.
"""
import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the root directory
load_dotenv()

class Config:
    """
    Application configuration and private app state.

    :cvar IS_PULLING_DATA: Flag indicating if a background data pull is in progress.
    :cvar DB_HOST: The hostname for the PostgreSQL database.
    :cvar DB_PORT: The port number for the PostgreSQL database.
    :cvar DB_NAME: The name of the database to connect to.
    :cvar DB_USER: The least-privilege database user.
    :cvar DB_PASS: The password for the database user.
    :cvar MAX_ALLOWED_LIMIT: The maximum result limit allowed for any query.
    """

    # Private app state flag
    IS_PULLING_DATA = False

    # Module 5 Step 2 Requirement: Enforce a maximum allowed limit (example: 1-100)
    # Cast to int to ensure it can be used in SQL composition clamping logic
    MAX_ALLOWED_LIMIT = int(os.getenv("MAX_ALLOWED_LIMIT", "100"))

    # Step 3 Requirement: Read DB connection values from environment variables
    # No hard-coded credentials: values are pulled from the .env file.
    # Defaults are provided for non-sensitive structural settings only.
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "gradscrape")

    # Credentials must be set in .env; no default strings are left in-code.
    DB_USER = os.getenv("DB_USER", "app_worker")
    DB_PASS = os.getenv("DB_PASSWORD")

    def get_db_url(self):
        """
        Constructs the database DSN/URL from environment variables.

        :return: A formatted PostgreSQL connection string.
        :rtype: str
        """
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    def get_pull_status(self):
        """
        Retrieves the current background data pulling status.

        :return: True if a pull is in progress, False otherwise.
        :rtype: bool
        """
        return self.IS_PULLING_DATA