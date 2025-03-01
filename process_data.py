import duckdb

DB_NAME = "countries.ddb"

def create_countries_data_table():
    """
    Creates a new table 'countries_data' as a join of four tables:
    - countries_metadata
    - legatum_prosperity (joined with an INNER JOIN to countries_metadata)
    - gdp_table
    - world_population
    """
    try:
        with duckdb.connect(DB_NAME) as conn:
            # Drop the table if it already exists
            conn.execute("DROP TABLE IF EXISTS countries_data;")
            
            query = """
            CREATE TABLE countries_data AS
            SELECT *
            FROM countries_metadata
            INNER JOIN legatum_prosperity USING (Country)
            JOIN gdp_table USING (Country)
            JOIN world_population USING (Country)
            """
            conn.execute(query)
            print("Table 'countries_data' created successfully.")
    except Exception as e:
        print(f"Error creating countries_data table: {e}")

def preview_countries_data():
    """
    Queries and prints the first few rows from the countries_data table.
    """
    try:
        with duckdb.connect(DB_NAME) as conn:
            df = conn.execute("SELECT * FROM countries_data LIMIT 5;").fetchdf()
            print("Preview of countries_data:")
            print(df)
    except Exception as e:
        print(f"Error previewing countries_data: {e}")

def main():
    create_countries_data_table()
    preview_countries_data()

if __name__ == "__main__":
    main()