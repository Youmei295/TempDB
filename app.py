import streamlit as st
import pymssql
import pandas as pd
import json
import os

# =============================================
# 1. DATABASE CONFIGURATION (VIA ENVIRONMENT)
# =============================================
# These must be set in Azure App Service -> Settings -> Environment variables
SERVER   = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASS")

def get_data():
    """Fetches food place data from Azure SQL."""
    if not all([SERVER, DATABASE, USERNAME, PASSWORD]):
        st.error("⚠️ Missing Database Configuration. Please set Environment Variables in Azure.")
        return None
        
    conn = None
    try:
        # Connect to Azure SQL
        conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE)
        
        # Query the table
        query = "SELECT name, category, average_price, lat, lng, tags_json FROM dbo.FoodPlaces"
        
        # Load into a Pandas DataFrame
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"❌ Database Connection Error: {e}")
        return None
    finally:
        if conn:
            conn.close()

# =============================================
# 2. STREAMLIT UI SETUP
# =============================================
st.set_page_config(
    page_title="VietJourney | Food Explorer",
    page_icon="🍴",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_index=True)

st.title("🍴 VietJourney: Food Explorer")
st.info("Dữ liệu được cập nhật thời gian thực từ hệ thống phân tích Gemini AI.")

# Sidebar for Filters
st.sidebar.header("Bộ lọc tìm kiếm")
if st.sidebar.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()

# Load Data
data = get_data()

if data is not None and not data.empty:
    # --- METRICS ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng số địa điểm", len(data))
    with col2:
        avg_p = data['average_price'].dropna().mean()
        st.metric("Giá trung bình", f"{int(avg_p):,} VNĐ" if not pd.isna(avg_p) else "N/A")
    with col3:
        top_cat = data['category'].value_counts().idxmax()
        st.metric("Loại hình phổ biến", top_cat.capitalize())

    # --- TABS FOR VIEWING ---
    tab1, tab2 = st.tabs(["📍 Bản đồ vị trí", "📋 Danh sách chi tiết"])

    with tab1:
        st.subheader("Bản đồ quán ăn quanh bạn")
        # Streamlit expects 'latitude' and 'longitude' names
        map_df = data[['lat', 'lng']].dropna().rename(columns={'lat': 'latitude', 'lng': 'longitude'})
        st.map(map_df)

    with tab2:
        st.subheader("Chi tiết thông tin")
        
        # Filter by Price Sidebar
        max_price = st.sidebar.slider("Ngân sách tối đa (VNĐ)", 0, 500000, 200000, step=10000)
        
        # Display the table (filtering out prices higher than slider if price exists)
        display_df = data[data['average_price'].fillna(0) <= max_price]
        st.dataframe(display_df, use_container_width=True)

else:
    st.warning("📭 Hiện tại chưa có dữ liệu trong Database hoặc Database đang bận.")
    if st.button("Kiểm tra lại kết nối"):
        st.rerun()