"""
Application entry point for running the Flask development server.

This module initializes the Flask application using the factory pattern. 
While this entry point does not handle database queries directly, it 
instantiates the app context where SQL Injection defenses, such as 
psycopg SQL composition and parameter binding, are enforced across 
all endpoints.
"""

import os
from src.web_app.app import create_app

# Initialize the Flask application instance
app = create_app()

if __name__ == '__main__':
    # Main entry point for execution. Runs the Flask development server
    server_host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
    server_port = int(os.getenv("FLASK_RUN_PORT", "8080"))

    app.run(host=server_host, port=server_port)
