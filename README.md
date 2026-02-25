# Grad Cafe Applicant Data & Analytics System
**JHU Modern Concepts in Software - Module 5**

## 📖 Live Documentation
The full technical documentation, including detailed API references, architecture diagrams, and a testing guide, is hosted on Read the Docs:  
👉 **[View Documentation Here](https://jhu-software-concepts-documentation.readthedocs.io/en/latest/)**

## Project Overview
This application is a full-stack data pipeline designed to scrape graduate school admission data from GradCafe, process it via an ETL (Extract, Transform, Load) engine, and visualize the findings through a Flask-based web interface. The system leverages a PostgreSQL database and includes an optional LLM integration for advanced data categorization.

## Architecture
The project is organized into three distinct layers to ensure a separation of concerns:

* **ETL Layer (Processing)**: Handles web scraping (`scrape.py`), data cleaning (`clean.py`), and database ingestion (`load_data.py`).
* **Database Layer (Storage)**: A PostgreSQL relational database for persistent storage and complex data querying (`query_data.py`).
* **Web Layer (Visualization)**: A Flask application providing user dashboards and analytics visualization (`app.py`).

## ⚡ Fresh Install

This section provides instructions to set up the project environment from scratch. You can use either **pip** or **uv** for installation.

### 1️⃣ Using pip
1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd <your-repo-folder>

###  Initialize Virtual Environment 
Create and activate a virtual environment to manage project dependencies.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate

### 2️⃣ Using uv
1. Install uv:
	pip install uv
2. Sync the environment:
	uv sync

##Install dependencies:
	pip install -r requirements.txt


## Running the Application
To start the Flask development server, ensure your virtual environment is active and run:
```bash
python -m src.web_app.run