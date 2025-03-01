import requests
import duckdb

# Constants
API_URL = "https://restcountries.com/v3.1/all"
DB_NAME = "countries.ddb"

def create_db_and_table_if_not_exists():
    """
    Creates the DuckDB database (if it doesn't exist) and the 'countries_metadata' table.
    """
    conn = duckdb.connect(DB_NAME)

    conn.execute("DROP TABLE IF EXISTS countries_metadata;")  # Ensures a fresh start

    create_table_query = """
    CREATE TABLE IF NOT EXISTS countries_metadata (
        Country VARCHAR,
        Region VARCHAR,
        Subregion VARCHAR,
        Currencies VARCHAR,
        Languages VARCHAR,
        Flag_URL VARCHAR
    );
    """
    conn.execute(create_table_query)
    conn.close()

def fetch_countries_data(url):
    """
    Fetches country data from the given API URL.
    Returns the JSON response or an empty list on failure.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def transform_data(data):
    """
    Transforms raw API data into a structured list of tuples suitable for
    insertion into the DuckDB 'countries_metadata' table.
    
    Adjusts specific country names as instructed:
      - 'United States' is changed to 'United States of America'
      - 'DR Congo' is changed to 'Democratic Republic of the Congo'
    """
    transformed = []
    for country in data:
        # Get the common name and adjust if necessary
        country_name = country.get("name", {}).get("common", "Unknown")
        if country_name == "United States":
            country_name = "United States of America"
        elif country_name == "DR Congo":
            country_name = "Democratic Republic of the Congo"
        
        region = country.get("region", "Unknown")
        subregion = country.get("subregion", "Unknown")
        # Process currencies: join each currency as "Name (Symbol)"
        currencies = ", ".join(
            f"{cur.get('name', 'Unknown')} ({cur.get('symbol', '')})"
            for cur in country.get("currencies", {}).values()
        )
        # Process languages: join the language names
        languages = ", ".join(country.get("languages", {}).values())
        flag_url = country.get("flags", {}).get("png", None)
        
        transformed.append((country_name, region, subregion, currencies, languages, flag_url))
    return transformed

def insert_into_duckdb(data):
    """
    Inserts the transformed country data directly into the DuckDB 'countries_metadata' table.
    """
    if not data:
        print("No data available for insertion.")
        return
    conn = duckdb.connect(DB_NAME)
    insert_query = """
        INSERT INTO countries_metadata (Country, Region, Subregion, Currencies, Languages, Flag_URL)
        VALUES (?, ?, ?, ?, ?, ?);
    """
    conn.executemany(insert_query, data)
    conn.close()
    print("Data successfully inserted into DuckDB.")

def main():
    # Create the database and table if they do not exist
    create_db_and_table_if_not_exists()
    
    # Fetch data from the API
    raw_data = fetch_countries_data(API_URL)
    if not raw_data:
        print("No data fetched from API. Exiting.")
        return
    
    # Transform the API data to match our table schema
    transformed_data = transform_data(raw_data)
    
    # Insert the data into the DuckDB table
    insert_into_duckdb(transformed_data)

if __name__ == "__main__":
    main()