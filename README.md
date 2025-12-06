# North Atlantic Migration Pattern Explorer (1880–1914)

North Atlantic Migration Patterns Explorer (1880–1914) is an interactive Streamlit application that explores UK–US migration during the late 19th and early 20th centuries.
Using digitized passenger lists and contextual historical event data, the project visualizes temporal trends, demographic patterns, and factors influencing long-distance travel.
The goal is to create a clear, data-driven narrative of who migrated, when they traveled, and how major events shaped these movements.

## Table of Contents
- [About](#about)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)

---

## About

Between 1880 and 1914, millions of people crossed the Atlantic in search of new opportunities.
This project investigates migration from the United Kingdom to the United States during the ocean liner era by analyzing passenger records, voyage dates, ship information, and related historical events.

The project:

- Integrates structured passenger-list data with contextual historical information.
- Identifies demographic and temporal patterns in migration flows.
- Provides interactive visualizations to support exploration and interpretation.
- Highlights correlations between travel patterns and major socio-political events.

All analysis is conducted within the Streamlit app, which handles datasets and processing automatically, so users can explore the data entirely in their browser without local files or database setup.

---

## Features

- Interactive visualizations using Altair, Plotly, and Streamlit.
- Timeline of major historical events that correspond to migration trends.
- Demographic analysis including age, gender, occupation, and origin/destination.
- Ship and voyage exploration (routes, departure ports, travel timing).
- Clustering and pattern detection using scikit-learn techniques.
- Automatic dataset integration: all data is handled internally by the app.

---

## Installation

We recommend exploring the dataset via the live Streamlit app.
If you choose to run the app locally, note that some functionality or behavior may differ from the deployed version.

Clone the repository:

git clone https://github.com/cwilburn-dev/INFO698Capstone.git  
cd INFO698Capstone  


Install required packages:  
pip install -r requirements.txt

## Usage

Visit the live Streamlit app at https://wilburn-capstone.streamlit.app/.
The app runs entirely in your browser — no local setup is required.
All necessary Python packages and datasets are handled automatically by Streamlit.

Explore the migration data through the interactive interface, including:

- Temporal migration trends
- Demographic analysis (age, gender, occupation, origin/destination)
- Ship and voyage information
- Historical event correlations and patterns

No additional configuration or downloads are necessary.

For local usage:  
From a terminal window, execute the command:  
streamlit run streamlit_app.py

Once running, the Streamlit app should open in your browser automatically.  

If not, navigate to:  
http://localhost:8501

## Configuration

No manual configuration is required.
The Streamlit app automatically manages dependencies and dataset integration.
Simply open the app link and start exploring.