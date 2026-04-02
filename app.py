import streamlit as st
import pymssql
import pandas as pd
import os
import time

# =============================================
# 1. DATABASE CONFIGURATION (VIA ENVIRONMENT)
# =============================================
# Set these in Azure App Service -> Settings -> Environment variables
SERVER   = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

def get_data():
    """Fetches data with retry logic for Serverless Azure SQL wake-up."""
    if not all([SERVER, DATABASE, USERNAME, PASSWORD]):
        st.error("Missing Environment Variables.")
        return None
        
    max_retries = 3
    retry_delay = 20  # Seconds to wait for Azure SQL to resume
    
    for attempt in range(max_retries):
        conn = None
        try:
            # Connect to Azure SQL
            conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE)
            query = "SELECT name, category, average_price, lat, lng, tags_json FROM dbo.FoodPlaces"
            
            # Use pandas to read the table
            df = pd.read_sql(query, conn)
            return df

        except Exception as e:
            error_msg = str(e)
            # If the error is the 40613 "Database not available"
            if "40613" in error_msg and attempt < max_retries - 1:
                with st.spinner(f"😴 Azure SQL is waking up... Please wait ({attempt + 1}/{max_retries})"):
                    time.sleep(retry_delay)
            else:
                st.error(f"❌ Database Error: {e}")
                return None
        finally:
            if conn:
                conn.close()
    return None

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