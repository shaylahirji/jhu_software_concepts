"""
Configuration script for the module_5_app package.

This script uses setuptools to make the project installable, ensuring consistent 
import behavior across local, test, and CI environments. It supports editable 
installs to mitigate path-related issues and allows tools like uv to extract 
runtime requirements efficiently. Packaging the project in this manner 
transforms the source directory into a distributable module, facilitating 
automated dependency management and environment synchronization.

:setup_name: module_5_app
:version: 0.1.0
"""
from setuptools import setup, find_packages

setup(
    name="module_5_app",
    version="0.1.0",
    # This tells Python to look for code inside the 'src' directory
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # This mirrors your requirements.txt for the 'uv' tool to extract
    install_requires=[
        "Flask==2.3.2",
        "psycopg[binary]==3.3.2",
        "python-dotenv==1.2.1",
        "beautifulsoup4==4.14.3",
    ],
    # These are only needed for development/CI (Steps 1, 4, 6, 7)
    extras_require={
        "dev": [
            "pylint==4.0.4",
            "pydeps==3.0.2",
            "pytest==8.0.2",
            "pytest-cov==4.1.0",
            "snyk",
        ],
    },
)