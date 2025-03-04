import streamlit as st
import duckdb
import pandas as pd
import numpy as np
import altair as alt
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import seaborn as sns
import statsmodels.api as sm


# 1. Configuration -----------------------------------------------------------
st.set_page_config(
    page_title="Global Happiness Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main Title of the Dashboard
st.title("Global Happiness Dashboard")

# Brief Description and Key Objectives
st.markdown("""
Analyzes happiness drivers across countries using datasets:
- **World Happiness**: [Happiness Index scores](https://worldhappiness.report/).
- **Legatum Prosperity**: [Prosperity scores](https://index.prosperity.com/) (e.g., Safety, Freedom).
- **Quality of Life**: Metrics like healthcare, education, and environment.
- **GDP Data**: GDP, growth, and per capita figures.
- **Country Metadata**: Region, population, languages.
- **World Population**: Population metrics.
""")

# 2. Data Loading ------------------------------------------------------------

# Connect to the DuckDB database using a context manager for automatic cleanup
try:
    with duckdb.connect("countries.ddb") as conn:
        # Load the joined data directly from DuckDB with a SQL query
        query = """
        SELECT *
        FROM world_happiness AS wh
        INNER JOIN countries_data AS cd
        USING (Country)
        """
        # Execute the query and fetch the result directly into a pandas DataFrame
        joined_data = conn.execute(query).fetchdf()

except Exception as e:
    st.error(f"Error loading data from DuckDB: {e}")

# 3. Sidebar: Filters, Navigation & Sorting Options ---------------------------

# Static Sidebar Elements
st.sidebar.image("BTS_Logo.png", use_container_width=True)
st.sidebar.header("Filters & Sorting Options")

# Happiness Filters 
# Year Selection: Choose the year for which happiness data is displayed
if not joined_data.empty and "Year" in joined_data.columns:
    unique_years = sorted(joined_data["Year"].unique())
    selected_year = st.sidebar.selectbox("Select Happiness Data Year", options=unique_years, index=len(unique_years) - 1)
else:
    selected_year = None

# Happiness Index Range Slider: Based on the selected year
if selected_year is not None:
    df_year = joined_data[joined_data["Year"] == selected_year]
    if not df_year.empty and "Happiness" in df_year.columns:
        happiness_min = float(df_year["Happiness"].min())
        happiness_max = float(df_year["Happiness"].max())
        happiness_range = st.sidebar.slider(
            "Happiness Index Range",
            min_value=happiness_min,
            max_value=happiness_max,
            value=(happiness_min, happiness_max),
            step=0.1,
            format="%.2f"
        )
    else:
        happiness_range = None
else:
    happiness_range = None

# Country Selection Filter 
if "selected_countries" not in st.session_state:
    if not joined_data.empty:
        st.session_state.selected_countries = sorted(joined_data["Country"].unique())
    else:
        st.session_state.selected_countries = []

with st.sidebar.expander("Country Selection"):
    col1, col2 = st.columns(2)
    
    def select_all_countries():
        if not joined_data.empty:
            st.session_state.selected_countries = sorted(joined_data["Country"].unique())
    
    def reset_country_selection():
        st.session_state.selected_countries = []
    
    col1.button("Select All", on_click=select_all_countries)
    col2.button("Reset", on_click=reset_country_selection)
    
    if not joined_data.empty:
        st.multiselect(
            "Select Countries",
            options=sorted(joined_data["Country"].unique()),
            default=st.session_state.selected_countries,
            key="selected_countries",
            help="Filter the dashboard by country"
        )
    else:
        st.write("No country data available.")

# ---------- Additional Sidebar Filters ----------

# Region Filter: Based on countries_metadata (merged into joined_data)
if "Region" in joined_data.columns:
    unique_regions = sorted(joined_data["Region"].dropna().unique())
    selected_regions = st.sidebar.multiselect(
        "Select Region(s)",
        options=unique_regions,
        default=unique_regions,
        help="Filter the dashboard by Region"
    )
else:
    selected_regions = None

# Store additional filters in session_state for further use in the application
st.session_state.selected_year = selected_year
st.session_state.selected_regions = selected_regions

# Create filtered_data based on sidebar selections
filtered_data = joined_data.copy()

# Filter by the selected year (for Happiness data)
if selected_year is not None and "Year" in filtered_data.columns:
    filtered_data = filtered_data[filtered_data["Year"] == selected_year]

# Filter by selected Countries
if "Country" in joined_data.columns and st.session_state.selected_countries:
    filtered_data = filtered_data[filtered_data["Country"].isin(st.session_state.selected_countries)]

# Filter by Region if available
if "Region" in joined_data.columns and st.session_state.selected_regions:
    filtered_data = filtered_data[filtered_data["Region"].isin(st.session_state.selected_regions)]

# Filter by Happiness Index range
if happiness_range is not None and "Happiness" in filtered_data.columns:
    filtered_data = filtered_data[
        (filtered_data["Happiness"] >= happiness_range[0]) &
        (filtered_data["Happiness"] <= happiness_range[1])
    ]

# ---------- Subregion Filter (Expander based) ----------
if "Subregion" in joined_data.columns:
    if "selected_subregions" not in st.session_state:
        st.session_state.selected_subregions = sorted(joined_data["Subregion"].dropna().unique())
    
    with st.sidebar.expander("Subregion Selection"):
        sub_col1, sub_col2 = st.columns(2)
        
        def select_all_subregions():
            st.session_state.selected_subregions = sorted(joined_data["Subregion"].dropna().unique())
        
        def reset_subregion_selection():
            st.session_state.selected_subregions = []
        
        sub_col1.button("Select All", on_click=select_all_subregions, key="select_all_subregions")
        sub_col2.button("Reset", on_click=reset_subregion_selection, key="reset_subregions")
        
        st.multiselect(
            "Select Subregions",
            options=sorted(joined_data["Subregion"].dropna().unique()),
            default=st.session_state.selected_subregions,
            key="selected_subregions",
            help="Filter the dashboard by subregion"
        )
    
    filtered_data = filtered_data[filtered_data["Subregion"].isin(st.session_state.selected_subregions)]
else:
    st.sidebar.write("Subregion data not available.")

# GDP per Capita Range Filter
if "GDP per capita" in joined_data.columns:
    gdp_min = float(joined_data["GDP per capita"].min())
    gdp_max = float(joined_data["GDP per capita"].max())
    selected_gdp_range = st.sidebar.slider(
        "GDP per Capita Range",
        min_value=gdp_min,
        max_value=gdp_max,
        value=(gdp_min, gdp_max),
        step=1.0,
        format="%.0f",
        help="Filter countries by GDP per Capita."
    )
    filtered_data = filtered_data[
        (filtered_data["GDP per capita"] >= selected_gdp_range[0]) &
        (filtered_data["GDP per capita"] <= selected_gdp_range[1])
    ]

# Average Prosperity Score Range Filter
if "Average Prosperity Score" in joined_data.columns:
    prosperity_min = float(joined_data["Average Prosperity Score"].min())
    prosperity_max = float(joined_data["Average Prosperity Score"].max())
    selected_prosperity_range = st.sidebar.slider(
        "Average Prosperity Score Range",
        min_value=prosperity_min,
        max_value=prosperity_max,
        value=(prosperity_min, prosperity_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by Average Prosperity Score."
    )
    filtered_data = filtered_data[
        (filtered_data["Average Prosperity Score"] >= selected_prosperity_range[0]) &
        (filtered_data["Average Prosperity Score"] <= selected_prosperity_range[1])
    ]

# Population Range Filter
if "Population" in joined_data.columns:
    pop_min = float(joined_data["Population"].min())
    pop_max = float(joined_data["Population"].max())
    selected_population_range = st.sidebar.slider(
        "Population Range",
        min_value=int(pop_min),
        max_value=int(pop_max),
        value=(int(pop_min), int(pop_max)),
        step=100000,
        format="%d",
        help="Filter countries by population size."
    )
    filtered_data = filtered_data[
        (filtered_data["Population"] >= selected_population_range[0]) &
        (filtered_data["Population"] <= selected_population_range[1])
    ]

# Fertility Rate Range Filter
if "Fert_Rate" in joined_data.columns:
    fert_min = float(joined_data["FertRate"].min())
    fert_max = float(joined_data["FertRate"].max())
    selected_fert_range = st.sidebar.slider(
        "Fertility Rate Range",
        min_value=fert_min,
        max_value=fert_max,
        value=(fert_min, fert_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by fertility rate."
    )
    filtered_data = filtered_data[
        (filtered_data["FertRate"] >= selected_fert_range[0]) &
        (filtered_data["FertRate"] <= selected_fert_range[1])
    ]

# Median Age Range Filter
if "Med_Age" in joined_data.columns:
    age_min = float(joined_data["MedAge"].min())
    age_max = float(joined_data["MedAge"].max())
    selected_age_range = st.sidebar.slider(
        "Median Age Range",
        min_value=age_min,
        max_value=age_max,
        value=(age_min, age_max),
        step=1.0,
        format="%.0f",
        help="Filter countries by median age."
    )
    filtered_data = filtered_data[
        (filtered_data["MedAge"] >= selected_age_range[0]) &
        (filtered_data["MedAge"] <= selected_age_range[1])
    ]

# Population Density Range Filter (per Km²)
if "DensityKm2" in joined_data.columns:
    density_min = float(joined_data["DensityKm2"].min())
    density_max = float(joined_data["DensityKm2"].max())
    selected_density_range = st.sidebar.slider(
        "Population Density Range (per Km²)",
        min_value=density_min,
        max_value=density_max,
        value=(density_min, density_max),
        step=1.0,
        format="%.0f",
        help="Filter countries by population density (per Km²)."
    )
    filtered_data = filtered_data[
        (filtered_data["DensityKm2"] >= selected_density_range[0]) &
        (filtered_data["DensityKm2"] <= selected_density_range[1])
    ]

# ---------- Purchasing Power Range Filter ----------
if "PurchasingPower" in joined_data.columns:
    pp_min = float(joined_data["PurchasingPower"].min())
    pp_max = float(joined_data["PurchasingPower"].max())
    selected_pp_range = st.sidebar.slider(
        "Purchasing Power Range",
        min_value=pp_min,
        max_value=pp_max,
        value=(pp_min, pp_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by purchasing power."
    )
    filtered_data = filtered_data[
        (filtered_data["PurchasingPower"] >= selected_pp_range[0]) &
        (filtered_data["PurchasingPower"] <= selected_pp_range[1])
    ]

# ---------- Climate Range Filter ----------
if "Climate" in joined_data.columns:
    climate_min = float(joined_data["Climate"].min())
    climate_max = float(joined_data["Climate"].max())
    selected_climate_range = st.sidebar.slider(
        "Climate Range",
        min_value=climate_min,
        max_value=climate_max,
        value=(climate_min, climate_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by climate index."
    )
    filtered_data = filtered_data[
        (filtered_data["Climate"] >= selected_climate_range[0]) &
        (filtered_data["Climate"] <= selected_climate_range[1])
    ]

# ---------- Cost of Living Range Filter ----------
if "CostofLiving" in joined_data.columns:
    cost_min = float(joined_data["CostofLiving"].min())
    cost_max = float(joined_data["CostofLiving"].max())
    selected_cost_range = st.sidebar.slider(
        "Cost of Living Range",
        min_value=cost_min,
        max_value=cost_max,
        value=(cost_min, cost_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by cost of living index."
    )
    filtered_data = filtered_data[
        (filtered_data["CostofLiving"] >= selected_cost_range[0]) &
        (filtered_data["CostofLiving"] <= selected_cost_range[1])
    ]

# ---------- Pollution Range Filter ----------
if "Pollution" in joined_data.columns:
    pollution_min = float(joined_data["Pollution"].min())
    pollution_max = float(joined_data["Pollution"].max())
    selected_pollution_range = st.sidebar.slider(
        "Pollution Range",
        min_value=pollution_min,
        max_value=pollution_max,
        value=(pollution_min, pollution_max),
        step=0.1,
        format="%.2f",
        help="Filter countries by pollution index."
    )
    filtered_data = filtered_data[
        (filtered_data["Pollution"] >= selected_pollution_range[0]) &
        (filtered_data["Pollution"] <= selected_pollution_range[1])
    ]

# 4. Main Navigation & Dashboard Layout -------------------------------------

# Create navigation tabs
tabs = st.tabs([
    "Data Overview & Summary",
    "Geopandas Map",
    "Trend Analysis & Time Series",
    "Correlation & Statistical Analysis", 
    "Predictive Modeling & Simulation",
    "Documentation & Data Sources",
])

# Tab 1: Data Overview & Summary
with tabs[0]:
    st.subheader("Data Overview & Summary")
    filtered_data = filtered_data.sort_values(by="Happiness", ascending=False)
    
    # 1. Display the raw merged data in an interactive table
    st.write("#### Raw Merged Data")
    st.dataframe(filtered_data)

    # 2. Bar Chart: Regions ranked by Happiness
    st.markdown("#### Regions ranked by Happiness")

    # Aggregate Happiness Index by Subregion (using mean, sum, or max)
    regions_ranked = (
        filtered_data.groupby("Region", as_index=False)["Happiness"].mean()
        .nlargest(10, "Happiness")
    )

    # Create the bar chart
    bar_chart = alt.Chart(regions_ranked).mark_bar().encode(
        x=alt.X("Region:N", sort='-y', title="Region"),
        y=alt.Y("Happiness:Q", title="Happiness Index"),
        tooltip=["Region", "Happiness"]
    ).properties(width=700, height=400)

    # Display the chart
    st.altair_chart(bar_chart, use_container_width=True)

    # 3. Provide a summary section (mean, median, range) for key variables
    st.write("#### Summary Statistics")
    key_columns = []
    for col in ["Happiness", "Average Prosperity Score", "GDP per capita", "Population", "LandAreaKm2", "FertRate", "MedAge"]:
        if col in filtered_data.columns:
            key_columns.append(col)
    
    if key_columns:
        # Compute descriptive statistics for selected key variables
        summary_df = filtered_data[key_columns].describe().T
        summary_df["range"] = summary_df["max"] - summary_df["min"]
        st.dataframe(summary_df[["count","mean", "std", "min","25%","50%","75%","max","range"]])
    else:
        st.write("Key variables not available for summary statistics.")

    # 4. Bar Chart: Top 15 Subregions by Happiness
    st.markdown("#### Top 15 Subregions by Happiness")

    # Aggregate Happiness Index by Subregion (using mean)
    top15_subregions = (
        filtered_data.groupby("Subregion", as_index=False)["Happiness"].mean()
        .nlargest(15, "Happiness")
    )

    # Create a horizontal bar chart:
    # - The y-axis shows Subregions, sorted by descending Happiness
    # - The x-axis shows the Happiness values.
    bar_chart = alt.Chart(top15_subregions).mark_bar().encode(
        x=alt.X("Happiness:Q", title="Happiness Index"),
        y=alt.Y("Subregion:N", 
                sort=alt.EncodingSortField(field="Happiness", op="mean", order="descending"),
                title="Subregion"),
        tooltip=["Subregion", "Happiness"]
    ).properties(width=700, height=400)

    # Display the chart
    st.altair_chart(bar_chart, use_container_width=True)

    # 5. Scatter Plot: Happiness vs. GDP per Capita
    st.markdown("#### Happiness Index vs. GDP per capita")
    scatter_plot = alt.Chart(filtered_data).mark_circle(size=60).encode(
        x=alt.X("GDP per capita:Q", title="GDP per capita"),
        y=alt.Y("Happiness:Q", title="Happiness"),
        color=alt.Color("Region:N", title="Region"),
        tooltip=["Country", "Region", "Happiness", "GDP per capita"]
    ).interactive().properties(width=700, height=400)
    st.altair_chart(scatter_plot, use_container_width=True)

    # 6. Option to download/export the combined dataset
    st.write("#### Download Dataset")
    csv_data = filtered_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Data as CSV",
        data=csv_data,
        file_name="global_happiness_data.csv",
        mime="text/csv"
    )

# Tab 2: Map Visualizations
with tabs[1]:
    st.subheader("Geopandas Map")
    
    # Load world boundaries GeoDataFrame from a remote URL
    try:
        world = gpd.read_file(
            "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
        )
    except Exception as e:
        st.error(f"Error loading world boundaries: {e}")
        world = gpd.GeoDataFrame()

    # Check that both map data and filtered_data are available
    if not world.empty and not filtered_data.empty and "Happiness" in filtered_data.columns:
        # To avoid duplicate entries (if a country appears more than once in filtered_data),
        # we drop duplicates based on 'Country'
        map_data = filtered_data[["Country", "Happiness"]].drop_duplicates()
        
        # Merge the world boundaries with our filtered happiness data.
        # Note: 'ADMIN' in world data corresponds to the country name.
        merged = world.merge(
            map_data,
            left_on="ADMIN",
            right_on="Country",
            how="left"
        )
        
        # --- Apply country filter explicitly (to ensure the map reflects the sidebar selection) ---
        merged_filtered = merged[merged["Country"].isin(st.session_state.selected_countries)]
        
        # --- Interactive Map Visualization ---
        st.markdown("#### Interactive Choropleth Map")
        try:
            interactive_map = merged_filtered.explore(
                column="Happiness",            # Use Happiness for choropleth coloring
                tooltip=["Country", "Happiness"],# Show a concise tooltip on hover
                popup=["Country", "Happiness"],  # Display only these two fields on click
                tiles="CartoDB positron",            # Use CartoDB Positron tiles
                cmap="YlGnBu",                       # Use the YlGnBu colormap
                style_kwds=dict(color="black")       # Black outlines
            )
            components.html(interactive_map._repr_html_(), height=600, width=1000)
        except Exception as e:
            st.error(f"Error generating interactive map: {e}")
        
        # --- Static Map Visualization as fallback ---
        st.markdown("#### Static Map")
        try:
            fig, ax = plt.subplots(1, 1, figsize=(15, 10))
            world.boundary.plot(ax=ax, linewidth=1, color="black")
            merged_filtered.plot(
                column="Happiness",
                ax=ax,
                cmap="YlGnBu",
                legend=True,
                missing_kwds={
                    "color": "lightgrey",
                    "edgecolor": "red",
                    "hatch": "///",
                    "label": "Missing values"
                }
            )
            ax.set_title("World Happiness Index", fontsize=15)
            ax.set_axis_off()
            st.pyplot(fig)
        except Exception as e:
            st.error(f"Error generating static map: {e}")
    else:
        st.write("Map data is not available.")

# Tab 3: Trend Analysis & Time Series
with tabs[2]:
    st.subheader("Time Series & Country Analysis")
    st.write("Standard Filter won't apply here.")
    
    if "Year" in joined_data.columns:
        # Ensure the Year column is numeric and convert if necessary
        joined_data["Year"] = joined_data["Year"].astype(int)
        
        # Line Chart: Happiness Index Trends over years per country
        st.write("#### Happiness Index Trends")
        pivot_happiness = joined_data.pivot_table(
            index="Year", 
            columns="Region", 
            values="Happiness", 
        )
        st.line_chart(pivot_happiness)
        
    else:
        st.write("Year data is not available for trend analysis.")
    
    st.markdown("### Detailed Country View")
    if not joined_data.empty:
        # Allow user to select a country from the full joined dataset
        selected_country_detail = st.selectbox(
            "Select a Country for Detailed View",
            options=sorted(joined_data["Country"].unique())
        )
        
        # Display detailed metrics for the selected country from the joined data
        country_details = joined_data[joined_data["Country"] == selected_country_detail][["Year", "Happiness"]]
        if not country_details.empty:
            st.markdown(f"#### Detailed Metrics for {selected_country_detail}")
            # Transpose the DataFrame for better readability
            st.dataframe(country_details.T, use_container_width=True)
        else:
            st.info("No detailed data available for the selected country.")
        
        # Display historical happiness trends using the happiness_data table
        country_happiness_history = joined_data[joined_data["Country"] == selected_country_detail]
        if not country_happiness_history.empty:
            st.markdown("#### Happiness History Over the Years")
            trend_chart = alt.Chart(country_happiness_history).mark_line(point=True).encode(
                x=alt.X("Year:O", title="Year"),
                y=alt.Y("Happiness:Q", title="Happiness Index"),
                tooltip=["Year", "Happiness"]
            ).properties(width=700, height=400)
            st.altair_chart(trend_chart, use_container_width=True)
        else:
            st.info("No happiness history available for the selected country.")
    else:
        st.info("No country data available for drill-down view.")
    
        st.markdown("### Trends in Happiness Over Multiple Years")
    if not joined_data.empty:
        # Allow user to select countries for trend analysis
        countries_for_trend = st.multiselect(
            "#### Select Countries for Happiness Trend Analysis",
            options=sorted(joined_data["Country"].unique()),
            default=sorted(joined_data["Country"].unique())[:5]
        )
        if countries_for_trend:
            trend_data = joined_data[joined_data["Country"].isin(countries_for_trend)]
            line_chart = alt.Chart(trend_data).mark_line(point=True).encode(
                x=alt.X("Year:O", title="Year"),
                y=alt.Y("Happiness:Q", title="Happiness Index"),
                color=alt.Color("Country:N"),
                tooltip=["Country", "Year", "Happiness"]
            ).properties(width=700, height=400)
            st.altair_chart(line_chart, use_container_width=True)
        else:
            st.write("Select at least one country to view happiness trends.")
    else:
        st.write("No historical happiness data available.")

# Tab 4: Correlation & Statistical Analysis
with tabs[3]:
    st.subheader("Correlation & Statistical Analysis")
    # Define columns for correlation analysis:

    corr_columns = []
    if "Happiness" in filtered_data.columns:
        corr_columns.append("Happiness")
    
    # Legatum Prosperity sub-indicators (if present)
    legatum_cols = [
        "Safety & Security", "Personal Freedom", "Governance", "Social Capital", 
        "Investment Environment", "Enterprise Conditions", "Market Access & Infrastructure", 
        "Economic Quality", "Living Conditions", "Healthcare", "Education", "Natural Environment"
    ]
    for col in legatum_cols:
        if col in filtered_data.columns:
            corr_columns.append(col)
    
    # GDP variables
    gdp_cols = ["GDP", "GDP growth", "GDP per capita"]
    for col in gdp_cols:
        if col in filtered_data.columns:
            corr_columns.append(col)
    
    # Population metrics (using common naming conventions)
    pop_cols = ["Population","NetChange","DensityKm2", "LandAreaKm2", "FertRate", "MedAge"]
    for col in pop_cols:
        if col in filtered_data.columns:
            corr_columns.append(col)
    
    # Population metrics (using common naming conventions)
    qual_cols = ["PurchasingPower","Climate","CostofLiving", "TrafficCommuteTime", "Pollution"]
    for col in qual_cols:
        if col in filtered_data.columns:
            corr_columns.append(col)
    
    # Prepare the dataset for correlation analysis
    corr_data = filtered_data[corr_columns].dropna()
    
    st.write("#### Correlation Matrix Heatmap")
    if not corr_columns:
        st.error("No candidate variables for happiness drivers are available in the dataset.")
    else:
        selected_vars = st.multiselect(
            "Select candidate variables to analyze as drivers of Happiness",
            options=corr_columns,
            default=corr_columns,
            help="These variables are believed to impact the Happiness Index. Choose one or more for analysis."
        )
        
        if not selected_vars:
            st.warning("Please select at least one candidate variable to proceed with the analysis.")
        else:
            # Prepare data: drop rows with missing values for Happiness and selected variables
            model_data = filtered_data.dropna(subset=["Happiness"] + selected_vars)
            if model_data.empty:
                st.error("Insufficient data after dropping missing values for the selected variables.")
            else:
                # ------------------ Correlation Analysis ------------------
                st.markdown("#### Correlation Heatmap")
                corr_cols = selected_vars
                corr_matrix = model_data[corr_cols].corr()
                fig_corr, ax_corr = plt.subplots(figsize=(16, 8))
                sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", ax=ax_corr)
                st.pyplot(fig_corr)
    
    st.write("#### Scatter Plot Analysis")
    # Get numeric columns from the filtered dataset for user selection
    numeric_options = corr_data.columns.tolist()

    if len(numeric_options) >= 2:
        scatter_x = st.selectbox("Select X-axis variable", options=numeric_options, key="scatter_x")
        scatter_y = st.selectbox("Select Y-axis variable", options=numeric_options, key="scatter_y")
        
        # Use the full filtered_data to include Region and Country information
        chart_data = filtered_data.copy()
        
        scatter_chart = alt.Chart(chart_data).mark_circle(size=60).encode(
            x=alt.X(scatter_x, title=scatter_x),
            y=alt.Y(scatter_y, title=scatter_y),
            # Color by Region if available; otherwise, use a default color
            color=alt.Color("Region:N", title="Region") if "Region" in chart_data.columns else alt.value("steelblue"),
            # Tooltip shows Country, Region, and the two selected numeric variables
            tooltip=["Country", "Region", scatter_x, scatter_y] 
                    if ("Country" in chart_data.columns and "Region" in chart_data.columns) 
                    else [scatter_x, scatter_y]
        ).interactive()
        
        st.altair_chart(scatter_chart, use_container_width=True)
    else:
        st.write("Not enough numeric data available for scatter plot analysis.")

with tabs[4]:
    st.subheader("Predictive Modeling & Simulation")
    st.markdown("""
    In this tab, we build a linear regression model to predict the **Happiness Index** based on selected predictor variables.
    Choose one or more predictors from the available numeric features (excluding **Happiness**) and examine the model summary.
    If a single predictor is selected, you can interactively simulate how changes in its value affect the predicted Happiness Index.
    """)
    
    # Get list of numeric columns from the filtered dataset
    #numeric_columns = filtered_data.select_dtypes(include=np.number).columns.tolist()
    
    if "Happiness" not in corr_columns:
        st.error("Happiness not found among corr columns.")
    else:
        # Exclude the dependent variable from predictors
        available_predictors = [col for col in corr_columns if col != "Happiness"]
        if not available_predictors:
            st.error("No predictor variables available in the dataset.")
        else:
            # Allow the user to select one or more predictor variables
            selected_predictors = st.multiselect(
                "Select Predictor Variable(s)",
                options=available_predictors,
                default=available_predictors[:1],
                help="Choose one or more numeric predictors (other than Happiness) to build the model."
            )
            
            if not selected_predictors:
                st.warning("Please select at least one predictor variable.")
            else:
                # Prepare data: drop missing values in the dependent variable and selected predictors
                regression_data = filtered_data.dropna(subset=["Happiness"] + selected_predictors).copy()
                
                # Build X and y for regression
                X = regression_data[selected_predictors]
                X = sm.add_constant(X)  # Add intercept term
                y = regression_data["Happiness"]
                
                # Fit the regression model using OLS
                model = sm.OLS(y, X).fit()
                
                # Display coefficients in a tidy table
                coeff_df = pd.DataFrame({
                    "Coefficient": model.params,
                    "P-value": model.pvalues
                })
                st.markdown("### Regression Coefficients")
                st.dataframe(coeff_df)
                
                # If exactly one predictor is selected, enable an interactive simulation
                if len(selected_predictors) == 1:
                    predictor = selected_predictors[0]
                    st.markdown("#### Interactive Simulation")
                    
                    # Determine the range and mean of the predictor
                    min_val = regression_data[predictor].min()
                    max_val = regression_data[predictor].max()
                    default_val = regression_data[predictor].mean()
                    
                    sim_value = st.slider(
                        f"Set value for {predictor}",
                        min_value=float(min_val),
                        max_value=float(max_val),
                        value=float(default_val)
                    )
                    
                    # Create a DataFrame for simulation (with constant term)
                    sim_df = pd.DataFrame({
                        "const": [1],
                        predictor: [sim_value]
                    })
                    
                    # Predict the Happiness Index based on the simulation value
                    predicted_happiness = model.predict(sim_df)[0]
                    st.markdown(f"**Predicted Happiness Index for {predictor} = {sim_value:.2f}: {predicted_happiness:.2f}**")
                    
                    # Plot: Scatter plot with regression line and the simulation point highlighted
                    scatter = alt.Chart(regression_data).mark_circle(size=60).encode(
                        x=alt.X(f"{predictor}:Q", title=predictor),
                        y=alt.Y("Happiness:Q", title="Happiness Index"),
                        tooltip=["Happiness", predictor]
                    ).properties(width=700, height=400)
                    
                    # Generate a regression line by predicting across a range of predictor values
                    line_data = pd.DataFrame({predictor: np.linspace(min_val, max_val, 100)})
                    line_data["predicted"] = model.predict(sm.add_constant(line_data))
                    regression_line = alt.Chart(line_data).mark_line(color="red").encode(
                        x=alt.X(f"{predictor}:Q", title=predictor),
                        y=alt.Y("predicted:Q", title="Predicted Happiness Index")
                    )
                    
                    # Highlight the simulation point
                    sim_point = alt.Chart(pd.DataFrame({predictor: [sim_value], "Happiness": [predicted_happiness]})).mark_circle(size=100, color="green").encode(
                        x=alt.X(f"{predictor}:Q", title=predictor),
                        y=alt.Y("Happiness:Q", title="Happiness Index")
                    )
                    
                    combined_chart = scatter + regression_line + sim_point
                    st.altair_chart(combined_chart, use_container_width=True)
                else:
                    st.markdown("#### Multi-Predictor Model")
                    st.info("Interactive simulation is available when a single predictor variable is selected. For multiple predictors, please review the regression summary and coefficients above.")

# Tab 6: Documentation & Data Sources
with tabs[5]:
    st.subheader("Documentation & Data Sources")
    st.markdown(
        """
        ### Key Objectives
        - **Dynamic Filtering**: Filter by country, year, region.
        - **Visualizations**: Charts, maps, and tables.
        - **Statistical Analysis**: Correlation matrices, scatter plots, regression.
        
        ### Methodology
        - **Data Joining:** Datasets were merged using the common `Country` column, with time-series data aligned on `Year` where applicable.
        - **Data Cleaning:** Standardized country names, handled missing values, and converted data types as needed.
        - **Analytical Techniques:**
          - Correlation matrices and heatmaps to explore relationships.
          - Scatter plots and regression analyses to quantify the influence of various factors.
        
        ### Disclaimers
        - This dashboard is intended for exploratory analysis and insights.
        - Data accuracy is dependent on the original source datasets; inherent limitations may exist.
        - All analyses are performed solely on the provided datasets.
        
        ### Update Logs
        - **Version 1.0:** Initial release including merged data, filters, visualizations, and basic statistical analyses.
        - **Future Updates:** Additional datasets and enhanced analytical methods may be incorporated.
        
        ### Contact Information
        - **Email:** info@globalhappinessdashboard.com
        - **Website:** [Global Happiness Dashboard](https://www.globalhappinessdashboard.com)
        - **Github:** Visit our [GitHub repository](https://github.com/waldepfeifer/world-happiness-streamlit) for source code and updates.
        """
    )