import sys
import os
import duckdb

DB_NAME = "countries.ddb"
CSV_FOLDER = "countries_csv"
POPULATION_CSV = "world_population_data.csv"
HAPPINESS_CSV = "world_happiness.csv"
QUALITY_OF_LIFE_CSV = "quality_of_life.csv"

def recreate_tables():
    """
    Recreates both world_population and world_happiness tables to ensure clean data.
    """
    conn = duckdb.connect(DB_NAME)
    
    # Drop existing tables
    conn.execute("DROP TABLE IF EXISTS world_population;")
    conn.execute("DROP TABLE IF EXISTS world_happiness;")
    conn.execute("DROP TABLE IF EXISTS quality_of_life;")

    # Recreate world_population table
    conn.execute("""
    CREATE TABLE world_population (
        Country VARCHAR,
        Population BIGINT,
        PopChange BIGINT,
        DensityKm2 DOUBLE,
        LandAreaKm2 DOUBLE,
        FertRate DOUBLE,
        MedAge INTEGER,
    );
    """)

    # Recreate world_happiness table
    conn.execute("""
    CREATE TABLE world_happiness (
        Country VARCHAR,
        Year INTEGER,
        Happiness DOUBLE
    );
    """)

    # Create quality_of_life table with only the required columns
    conn.execute("""
    CREATE TABLE quality_of_life (
        Country VARCHAR,
        PurchasingPower DOUBLE,
        Climate DOUBLE,
        CostofLiving DOUBLE,
        TrafficCommuteTime DOUBLE,
        Pollution DOUBLE
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
            CAST(REPLACE("Net Change", ',', '') AS BIGINT),
            CAST(REPLACE("Density (P/Km²)", ',', '') AS DOUBLE),
            CAST(REPLACE("Land Area (Km²)", ',', '') AS DOUBLE),
            CAST("Fert. Rate" AS DOUBLE),
            CAST("Med. Age" AS INTEGER),
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

def ingest_quality_of_life_csv(file_path):
    """
    Reads the quality_of_life CSV and inserts rows into the quality_of_life table.
    Only the required columns are kept:
    Purchasing Power Value, Climate Value, Cost of Living Value, 
    Property Price to Income Value, Traffic Commute Time Value, Pollution Value.
    The column 'country' is renamed to 'Country' and standardized.
    """
    conn = duckdb.connect(DB_NAME)
    
    conn.execute(f"""
        INSERT INTO quality_of_life
        SELECT 
            CASE
                WHEN "country" = 'United States' THEN 'United States of America'
                WHEN "country" = 'Sao Tome And Principe' THEN 'São Tomé and Príncipe'
                WHEN "country" = 'Cape Verde' THEN 'Cabo Verde'
                WHEN "country" = 'Trinidad And Tobago' THEN 'Trinidad and Tobago'
                WHEN "country" = 'Czech Republic' THEN 'Czechia'
                WHEN "country" = 'Hong Kong (China)' THEN 'Hong Kong'
                ELSE "country"
            END AS Country,
            CAST("Purchasing Power Value" AS DOUBLE),
            CAST("Climate Value" AS DOUBLE),
            CAST("Cost of Living Value" AS DOUBLE),
            CAST("Traffic Commute Time Value" AS DOUBLE),
            CAST("Pollution Value" AS  DOUBLE)
        FROM read_csv_auto('{file_path}', header=True);
    """)

def main():
    # Determine file paths
    population_file_path = os.path.join(CSV_FOLDER, POPULATION_CSV)
    happiness_file_path = os.path.join(CSV_FOLDER, HAPPINESS_CSV)
    quality_of_life_file_path = os.path.join(CSV_FOLDER, QUALITY_OF_LIFE_CSV)

    # Ensure both files exist
    if not os.path.exists(population_file_path):
        print(f"Error: File '{population_file_path}' not found.")
        sys.exit(1)
    
    if not os.path.exists(happiness_file_path):
        print(f"Error: File '{happiness_file_path}' not found.")
        sys.exit(1)
    
    if not os.path.exists(quality_of_life_file_path):
        print(f"Error: File '{quality_of_life_file_path}' not found.")
        sys.exit(1)

    # Recreate tables (delete old data)
    recreate_tables()

    # Ingest both datasets
    ingest_population_csv(population_file_path)
    ingest_happiness_csv(happiness_file_path)
    ingest_quality_of_life_csv(quality_of_life_file_path)

    print("Ingestion completed successfully.")

if __name__ == "__main__":
    main()