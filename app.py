import streamlit as st
import pymssql
import pandas as pd
import os

# =============================================
# 1. DATABASE CONFIGURATION (VIA ENVIRONMENT)
# =============================================
# Set these in Azure App Service -> Settings -> Environment variables
SERVER   = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

def get_data():
    """Fetches data from Azure SQL and returns a DataFrame."""
    if not all([SERVER, DATABASE, USERNAME, PASSWORD]):
        st.error("Missing Environment Variables: DB_SERVER, DB_NAME, DB_USER, or DB_PASS.")
        return None
        
    conn = None
    try:
        # Connect using pymssql
        conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE)
        
        # SQL Query to pull your food data
        query = "SELECT name, category, average_price, lat, lng, tags_json FROM dbo.FoodPlaces"
        
        # Read directly into Pandas
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Database Connection Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

# =============================================
# 2. WEB INTERFACE
# =============================================
st.set_page_config(page_title="VietJourney Data", layout="wide")

st.title("🍴 VietJourney Database View")
st.write("This table shows all records currently stored in your Azure SQL Server.")

# Fetch the data
df = get_data()

if df is not None:
    # 1. Show the Map at the top for quick context
    if 'lat' in df.columns and 'lng' in df.columns:
        st.subheader("Map Overview")
        map_data = df[['lat', 'lng']].dropna().rename(columns={'lat': 'latitude', 'lng': 'longitude'})
        st.map(map_data)

    # 2. Show the Data Table
    st.subheader("Raw Data Table")
    st.dataframe(df, use_container_width=True)
    
    # Simple Download Button for CSV
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='vietjourney_data.csv',
        mime='text/csv',
    )
else:
    st.info("No data found or connection could not be established.")