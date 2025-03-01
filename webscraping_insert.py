import requests
import pandas as pd
from bs4 import BeautifulSoup
import duckdb

DB_NAME = "countries.ddb"

def fetch_soup(url):
    """
    Fetch content of URL and return BeautifulSoup object
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def read_table_from_soup(table):
    """
    Converts HTML table element to pandas DataFrame.
    """
    try:
        return pd.read_html(str(table))[0]
    except ValueError as e:
        print(f"Error parsing table into DataFrame: {e}")
        return None

def create_and_ingest_data(df, table_name):
    """
    Connect to the DuckDB database, clean existing table,
    and create table populated with the data from the DataFrame.
    """
    conn = duckdb.connect(DB_NAME)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {table_name};")
        conn.register('df_temp', df)
        conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df_temp;")
        conn.unregister('df_temp')
        print(f"Data successfully ingested into DuckDB table '{table_name}'.")
    except Exception as e:
        print(f"Error creating or inserting into DuckDB table '{table_name}': {e}")
    finally:
        conn.close()

# --------------------- Legatum Prosperity Index Functions --------------------- #
def extract_legatum_table(soup):
    """
    Extract target table from Legatum Prosperity Index page.
    Prefers the table that contains the keyword 'Rank'
    """
    tables = soup.find_all('table', class_='wikitable')
    if not tables:
        print("No tables found on the page.")
        return None
    target_table = None
    for table in tables:
        if 'Rank' in table.get_text():
            target_table = table
            break
    if target_table is None:
        print("Relevant table not found by keyword; defaulting to the first table.")
        target_table = tables[0]
    return target_table

def process_legatum_df(df):
    """
    Process the scraped Legatum DataFrame:
    Drops 'Rank' column, renames 'Country[1]' to 'Country', and adjusts country names.
    """
    if 'Rank' in df.columns:
        df = df.drop(columns='Rank')
    if 'Country[1]' in df.columns:
        df = df.rename(columns={'Country[1]': 'Country'})
    if 'Average Score' in df.columns:
        df = df.rename(columns={'Average Score': 'Average Prosperity Score'})
    
    # Adjust country names as specified
    if 'Country' in df.columns:
        adjustments = {
            'United States': 'United States of America',
            'Congo': 'Republic of the Congo',
            'Democratic Republic of Congo': 'Democratic Republic of the Congo',
            'Czech Republic': 'Czechia',
            "Côte d'Ivoire": 'Ivory Coast',
            'Swaziland': 'Eswatini'
        }
        df['Country'] = df['Country'].replace(adjustments)
    return df

def scrape_legatum_index(url):
    """
    Scrape and processe the Legatum Prosperity Index table from the given Wikipedia URL.
    """
    soup = fetch_soup(url)
    if soup is None:
        return None
    table = extract_legatum_table(soup)
    if table is None:
        return None
    df = read_table_from_soup(table)
    if df is None:
        return None
    return process_legatum_df(df)

# --------------------- Worldometers GDP Functions --------------------- #
def extract_worldometers_table(soup):
    """
    Extracts the GDP table from the Worldometers page.
    Attempts to find the table by its known ID ("example2")
    """
    table = soup.find("table", {"id": "example2"})
    if table is None:
        table = soup.find("table")
        if table is None:
            print("No table found on the page.")
            return None
    return table

def process_worldometers_df(df):
    """
    Processes the scraped Worldometers GDP DataFrame:
    Filters to required columns, adjusts country names, and converts columns to numeric.
    """
    df.columns = df.columns.str.strip()
    required_columns = ['Country', 'GDP  (nominal, 2023)', 'GDP growth', 'GDP per capita']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Missing columns in the scraped table: {missing_columns}")
        return None
    df = df[required_columns]
    df = df.rename(columns={'GDP  (nominal, 2023)': 'GDP'})
    adjustments = {
        "United States": "United States of America",
        "Czech Republic (Czechia)": "Czechia",
        "Sao Tome & Principe": "São Tomé and Príncipe",
        "Côte d'Ivoire": "Ivory Coast",
        "Congo": "Republic of the Congo",
        "DR Congo": "Democratic Republic of the Congo"
    }
    df['Country'] = df['Country'].replace(adjustments)
    
    # Convert numeric columns to decimals (floats)
    # Remove "$" and commas from 'GDP' and 'GDP per capita'; remove "%" from 'GDP growth'
    df['GDP'] = pd.to_numeric(df['GDP'].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')
    df['GDP growth'] = pd.to_numeric(df['GDP growth'].astype(str).str.replace('[%,]', '', regex=True), errors='coerce')
    df['GDP per capita'] = pd.to_numeric(df['GDP per capita'].astype(str).str.replace('[$,]', '', regex=True), errors='coerce')
    
    return df

def scrape_worldometers_gdp(url):
    """
    Scrape and processes the GDP by country table from Worldometers URL.
    """
    soup = fetch_soup(url)
    if soup is None:
        return None
    table = extract_worldometers_table(soup)
    if table is None:
        return None
    df = read_table_from_soup(table)
    if df is None:
        return None
    return process_worldometers_df(df)

# --------------------- Main Function --------------------- #
def main():
    # URLs for the respective data sources.
    legatum_url = "https://en.wikipedia.org/wiki/Legatum_Prosperity_Index"
    gdp_url = "https://www.worldometers.info/gdp/gdp-by-country/"
    
    # Scrape and ingest Legatum Prosperity Index data.
    df_legatum = scrape_legatum_index(legatum_url)
    if df_legatum is not None:
        print("Legatum Prosperity Index data loaded successfully!")
        print(df_legatum.head())
        create_and_ingest_data(df_legatum, "legatum_prosperity")
    else:
        print("Failed to load Legatum Prosperity Index data.")
    
    # Scrape and ingest Worldometers GDP data.
    df_gdp = scrape_worldometers_gdp(gdp_url)
    if df_gdp is not None:
        print("Worldometers GDP data loaded successfully!")
        print(df_gdp.head())
        create_and_ingest_data(df_gdp, "gdp_table")
    else:
        print("Failed to load Worldometers GDP data.")

if __name__ == "__main__":
    main()
