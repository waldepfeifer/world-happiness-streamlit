import sys
import os
import duckdb

DB_NAME = "countries.ddb"
CSV_FOLDER = "countries_csv"
POPULATION_CSV = "world_population_data.csv"
HAPPINESS_CSV = "world_happiness.csv"

def recreate_tables():
    """
    Recreates both world_population and world_happiness tables to ensure clean data.
    """
    conn = duckdb.connect(DB_NAME)
    
    # Drop existing tables
    conn.execute("DROP TABLE IF EXISTS world_population;")
    conn.execute("DROP TABLE IF EXISTS world_happiness;")

    # Recreate world_population table
    conn.execute("""
    CREATE TABLE world_population (
        Country VARCHAR,
        Population_2024 BIGINT,
        Yearly_Change VARCHAR,
        Net_Change BIGINT,
        Density_P_Km2 DOUBLE,
        Land_Area_Km2 DOUBLE,
        Fert_Rate DOUBLE,
        Med_Age INTEGER,
        Urban_Pop_Pct VARCHAR,
        World_Share VARCHAR
    );
    """)

    # Recreate world_happiness table
    conn.execute("""
    CREATE TABLE world_happiness (
        Country VARCHAR,
        Year INTEGER,
        Happiness_Index DOUBLE
    );
    """)

    conn.close()

def ingest_population_csv(file_path):
    """
    Reads world population CSV and inserts rows into world_population table.
    Cleans numeric values and standardizes country names.
    """
    conn = duckdb.connect(DB_NAME)
    
    conn.execute(f"""
        INSERT INTO world_population
        SELECT 
            CASE 
                WHEN "Country" = 'United States' THEN 'United States of America'
                WHEN "Country" = 'Congo' THEN 'Republic of the Congo'
                WHEN "Country" = 'Sao Tome & Principe' THEN 'São Tomé and Príncipe'
                WHEN "Country" = 'DR Congo' THEN 'Democratic Republic of the Congo'
                WHEN "Country" = 'Côte d''Ivoire' THEN 'Ivory Coast'  -- Escaped single quote
                WHEN "Country" = 'Czech Republic (Czechia)' THEN 'Czechia'
                ELSE "Country"
            END AS Country,
            CAST(REPLACE("Population (2024)", ',', '') AS BIGINT),
            "Yearly Change",
            CAST(REPLACE("Net Change", ',', '') AS BIGINT),
            CAST(REPLACE("Density (P/Km²)", ',', '') AS DOUBLE),
            CAST(REPLACE("Land Area (Km²)", ',', '') AS DOUBLE),
            CAST("Fert. Rate" AS DOUBLE),
            CAST("Med. Age" AS INTEGER),
            "Urban Pop %",
            "World Share"
        FROM read_csv_auto('{file_path}', header=True);
    """)

    conn.close()

def ingest_happiness_csv(file_path):
    """
    Reads world happiness CSV and inserts rows into world_happiness table.
    Relevant columns: Country, Year, Index. Standardized country names for consistency.
    """
    conn = duckdb.connect(DB_NAME)

    conn.execute(f"""
        INSERT INTO world_happiness
        SELECT 
            CASE 
                WHEN "Country" = 'United States' THEN 'United States of America'
                WHEN "Country" = 'Congo Brazzaville' THEN 'Republic of the Congo'
                WHEN "Country" = 'Congo Kinshasa' THEN 'Democratic Republic of the Congo'
                WHEN "Country" = 'North Cyprus' THEN 'Cyprus'
                WHEN "Country" = 'Turkiye' THEN 'Turkey'
                ELSE "Country"
            END AS Country,
            CAST("Year" AS INTEGER),
            CAST("Index" AS DOUBLE)
        FROM read_csv_auto('{file_path}', header=True);
    """)

    conn.close()

def main():
    # Determine file paths
    population_file_path = os.path.join(CSV_FOLDER, POPULATION_CSV)
    happiness_file_path = os.path.join(CSV_FOLDER, HAPPINESS_CSV)

    # Ensure both files exist
    if not os.path.exists(population_file_path):
        print(f"Error: File '{population_file_path}' not found.")
        sys.exit(1)
    
    if not os.path.exists(happiness_file_path):
        print(f"Error: File '{happiness_file_path}' not found.")
        sys.exit(1)

    # Recreate tables (delete old data)
    recreate_tables()

    # Ingest both datasets
    ingest_population_csv(population_file_path)
    ingest_happiness_csv(happiness_file_path)

    print("Ingestion completed successfully.")

if __name__ == "__main__":
    main()
