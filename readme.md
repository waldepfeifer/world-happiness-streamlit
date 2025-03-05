# Global Happiness Dashboard

<img width="727" alt="image" src="https://github.com/user-attachments/assets/0f1df926-03a5-4d1c-964d-03e28e89b2bb" />

A **Streamlit** application that analyzes and visualizes global happiness and prosperity metrics. The dashboard integrates multiple datasets—ranging from the [World Happiness Report](https://worldhappiness.report/) to [Legatum Prosperity](https://index.prosperity.com/)—and offers interactive filters, visualizations, and statistical summaries to help users explore happiness drivers across different countries and regions.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Data Sources](#data-sources)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Overview

The Global Happiness Dashboard is designed to empower users with data insights by:
- Allowing dynamic filtering by year, region, country, and various economic and social indicators.
- Displaying key statistics such as the average happiness index, GDP per capita, population, and more.
- Visualizing trends and comparisons through interactive bar charts, scatter plots, and map visualizations.
- Providing a user-friendly interface built with Streamlit, making it easy for both technical and non-technical users to explore the data.

## Features

- **Interactive Data Filtering:**  
  Users can filter data by:
  - Happiness year
  - Happiness Index range
  - Country, region, and subregion
  - Economic indicators (e.g., GDP per capita, Average Prosperity Score)
  - Demographic metrics (e.g., Population, Median Age)
  - Additional indexes such as Cost of Living, Pollution, and Climate

- **Data Visualization:**  
  - **Bar Charts** to rank regions or subregions by happiness.
  - **Scatter Plots** comparing happiness with GDP per capita.
  - **Altair charts** for interactive visual exploration.
  - **Geopandas Map:** Visual mapping of countries with happiness scores.

- **Statistical Summary:**  
  Generates descriptive statistics (mean, median, range, etc.) for key variables.

- **Data Export:**  
  Option to download the filtered dataset as a CSV file for further analysis.

## Data Sources

The dashboard leverages various datasets, including:
- **World Happiness Report:** Provides global happiness scores.
- **Legatum Prosperity Index:** Offers prosperity scores and other socioeconomic metrics.
- **Quality of Life Metrics:** Includes data on healthcare, education, and environmental factors.
- **GDP and Population Data:** Key economic and demographic indicators.
- **Country Metadata:** Information on regions, subregions, languages, etc.

*(For more details, please refer to the in-app documentation and data source links provided in the code.)*

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/waldepfeifer/world-happiness-streamlit.git
   cd world-happiness-streamlit
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Data Files:**
Ensure that the provided data files (e.g., countries.ddb and data in the countries_csv folder) are in place. These files are used by the app to join and filter datasets.



1. **Run the Streamlit Application:**
   ```bash
   streamlit run streamlit_app.py
   ```

## License
MIT License

Copyright (c) 2025 waldepfeifer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

