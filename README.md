# Signal Intelligence Dashboard

This system collects, processes, and interprets real-time news signals relevant to Sri Lanka's socio-economic and operational environment. It visualizes data across three key strategic dimensions: **National Activity**, **Operational Environment**, and **Risk & Opportunity Insights**.

## Features

- **Live News Feed**: Real-time aggregation of news from multiple sources.
- **Strategic Indicators**:
    - **National Activity**: Major events and emerging topics.
    - **Operational Environment**: Business and operational impact signals.
    - **Risk & Opportunity**: High-impact alerts and positive development tracking.
- **Interactive Visualizations**: Impact distribution and operational category breakdown.
- **Automated Processing**: Backend pipeline for scraping, clustering, and scoring news items.

## Prerequisities

- Python 3.8+
- pip

## Installation

1. Clone or download the repository.
2. Navigate to the project directory:
   ```bash
   cd news_SIGNALS-main
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask server:
   ```bash
   python run.py
   ```
2. Open your browser and navigate to:
   `http://localhost:5111`

## Project Structure

- `app/`: Main application source code.
    - `routes.py`: API endpoints and page routes.
    - `services/`: Data processing logic.
    - `static/`: Frontend assets (CSS, JS).
    - `templates/`: HTML templates.
- `data/`: Data storage (CSVs).
- `run.py`: Entry point for the application.
