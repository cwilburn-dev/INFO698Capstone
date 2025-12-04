# Transatlantic Migration Patterns During the Ocean Liner Era (1880–1914)

Transatlantic Migration Patterns During the Ocean Liner Era (1880–1914) is an interactive Streamlit application that explores UK–US migration during the late 19th and early 20th centuries.
Using digitized passenger lists and contextual historical event data, the project visualizes temporal trends, demographic patterns, and factors influencing long-distance travel.
The goal is to create a clear, data-driven narrative of who migrated, when they traveled, and how major events shaped these movements.

## Table of Contents
- [About](#about)
- [Features](#features)
- [Demo](#demo)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Acknowledgements](#acknowledgements)

---

## About

Between 1880 and 1914, millions of people crossed the Atlantic in search of new opportunities.
This project investigates migration from the United Kingdom to the United States during the ocean liner era by analyzing passenger records, voyage dates, ship information, and related historical events.

The project:

- Integrates structured passenger-list data with contextual historical information.
- Identifies demographic and temporal patterns in migration flows.
- Provides interactive visualizations to support exploration and interpretation.
- Highlights correlations between travel patterns and major socio-political events.

All analysis is conducted directly on local datasets (no external database required), and results are presented through a Streamlit interface for ease of use and accessibility.

---

## Features

- Interactive visualizations using Altair, Plotly, and Streamlit.
- Timeline of major historical events that correspond to migration trends.
- Demographic analysis including age, gender, occupation, and origin/destination.
- Ship and voyage exploration (routes, departure ports, travel timing).
- Clustering and pattern detection using scikit-learn techniques.
- Local dataset integration — no database setup required.

---

## Installation

Clone the repository:

git clone https://github.com/cwilburn-dev/INFO698Capstone.git  
cd INFO698Capstone  


Install required packages:  
pip install -r requirements.txt

## Usage

Run the Streamlit app:  
streamlit run streamlit_app.py  

Once running, the Streamlit app should open in your browser automatically.  
If not, navigate to:  
http://localhost:8501


## Configuration

streamlit.py  
migration_analysis_ready_clean.csv  
historical_events.json  

## Acknowledgements

pending.

