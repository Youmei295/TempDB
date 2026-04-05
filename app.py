import streamlit as st
import pymssql
import pandas as pd
import os
import time

# =============================================
# 1. DATABASE CONFIGURATION
# =============================================
SERVER   = os.getenv("DB_SERVER")
DATABASE = os.getenv("DB_NAME")
USERNAME = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")

# Lấy TOÀN BỘ dữ liệu 1 lần và lưu Cache trong 5 phút
@st.cache_data(ttl=300)
def get_all_data():
    if not all([SERVER, DATABASE, USERNAME, PASSWORD]):
        st.error("Missing Environment Variables. Please set them in Azure.")
        return None
        
    max_retries = 3
    retry_delay = 20 
    
    for attempt in range(max_retries):
        conn = None
        try:
            conn = pymssql.connect(SERVER, USERNAME, PASSWORD, DATABASE)
            
            # Kéo cả 3 bảng lên cùng lúc
            query = """
                SELECT 'Food' AS type, name, category, average_price, rating, lat, lng, tags_json FROM dbo.FoodPlaces
                UNION ALL
                SELECT 'Drink' AS type, name, category, average_price, rating, lat, lng, tags_json FROM dbo.DrinkPlaces
                UNION ALL
                SELECT 'Activity' AS type, name, category, average_price, rating, lat, lng, tags_json FROM dbo.ActivityPlaces
            """
            
            df = pd.read_sql(query, conn)
            return df

        except Exception as e:
            error_msg = str(e)
            if "40613" in error_msg and attempt < max_retries - 1:
                with st.spinner(f"😴 Azure SQL đang khởi động... Vui lòng đợi ({attempt + 1}/{max_retries})"):
                    time.sleep(retry_delay)
            else:
                st.error(f"❌ Database Error: {e}")
                return None
        finally:
            if conn:
                conn.close()
    return None

# =============================================
# 2. WEB INTERFACE SETUP
# =============================================
st.set_page_config(page_title="VietJourney Data", page_icon="🗺️", layout="wide")

# --- SIDEBAR: ĐIỀU HƯỚNG BẢNG DỮ LIỆU ---
st.sidebar.title("🔍 Menu Điều Hướng")
category = st.sidebar.radio(
    "Chọn Bảng dữ liệu bạn muốn xem chi tiết:",
    ["🍝 Ẩm thực (Food)", "🧋 Đồ uống (Drink)", "⛺ Hoạt động (Activity)"]
)

if st.sidebar.button("🔄 Làm mới dữ liệu từ Database"):
    st.cache_data.clear()

# Mapping dữ liệu
mapping = {
    "🍝 Ẩm thực (Food)": {"type": "Food", "title": "Bảng Chi Tiết: Quán Ăn"},
    "🧋 Đồ uống (Drink)": {"type": "Drink", "title": "Bảng Chi Tiết: Quán Nước / Cafe"},
    "⛺ Hoạt động (Activity)": {"type": "Activity", "title": "Bảng Chi Tiết: Hoạt Động Trải Nghiệm"}
}

selected_type = mapping[category]["type"]
table_title = mapping[category]["title"]

# Tải dữ liệu tổng
df = get_all_data()

if df is not None and not df.empty:
    
    # =============================================
    # PHẦN 1: BẢN ĐỒ TỔNG HỢP (ALL DATA)
    # =============================================
    st.title("📍 Bản đồ Phân Bố Tổng Hợp")
    
    # Chú thích màu sắc
    st.markdown("""
    **Chú thích:**
    🔴 **Food** (Màu Đỏ) &nbsp; | &nbsp; 🔵 **Drink** (Màu Xanh dương) &nbsp; | &nbsp; 🟢 **Activity** (Màu Xanh lá)
    """)
    
    # Định nghĩa màu
    color_mapping = {
        'Food': '#FF4B4B',     
        'Drink': '#1E90FF',    
        'Activity': '#32CD32'  
    }
    
    # Tạo cột màu cho bản đồ
    df['map_color'] = df['type'].map(color_mapping)
    
    # Lọc dữ liệu map và vẽ
    map_data = df[['lat', 'lng', 'map_color']].dropna(subset=['lat', 'lng'])
    map_data = map_data.rename(columns={'lat': 'latitude', 'lng': 'longitude'})
    st.map(map_data, latitude='latitude', longitude='longitude', color='map_color')

    st.divider()

    # =============================================
    # PHẦN 2: BẢNG DỮ LIỆU ĐỘNG (THEO SIDEBAR)
    # =============================================
    st.subheader(f"📋 {table_title}")
    
    # Lọc dataframe chỉ lấy loại người dùng đang chọn ở Sidebar
    table_df = df[df['type'] == selected_type]
    
    # Bỏ các cột không cần thiết khi hiển thị bảng (như cột type và map_color)
    display_df = table_df.drop(columns=['type', 'map_color'])
    
    st.dataframe(display_df, use_container_width=True)
    
    # Tải file CSV chỉ cho bảng đang xem
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {selected_type} Data as CSV",
        data=csv,
        file_name=f'vietjourney_{selected_type.lower()}.csv',
        mime='text/csv',
    )

else:
    st.info("📭 Hiện tại chưa có dữ liệu trong Database hoặc Server đang bận.")