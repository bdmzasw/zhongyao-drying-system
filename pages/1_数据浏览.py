import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 工具函数 =====================
def read_csv_safe(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        return pd.read_csv(path, encoding="gbk")

@st.cache_data
def load_all_data():
    return {
        "herbs": read_csv_safe("data/药材库.csv"),
        "techs": read_csv_safe("data/技术库.csv"),
        "regions": read_csv_safe("data/区域库.csv"),
        "carbon": read_csv_safe("data/区域碳排放因子.csv"),
        "lcc": read_csv_safe("data/LCC经济成本库-干燥设备对比.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
regions_df = data["regions"]

# ===================== 页面样式 =====================
st.set_page_config(page_title="数据浏览", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #f5f9f5; }
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

if st.button("🏠 返回主页"):
    st.switch_page("Home.py")

# ===================== 全局可操作侧边栏（和主页完全一致） =====================
with st.sidebar:
    st.subheader("⚙️ 总操作仪表盘")
    st.markdown("---")

    # 药材
    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox(
        "🌿 药材品种", herb_list,
        index=herb_list.index(st.session_state.get("selected_herb", "请选择")) 
        if st.session_state.get("selected_herb") in herb_list else 0
    )

    # 产区
    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox(
        "📍 产区", region_list,
        index=region_list.index(st.session_state.get("selected_area", "请选择")) 
        if st.session_state.get("selected_area") in region_list else 0
    )

    # 电价
    electricity_price = st.number_input(
        "⚡ 电价（元/kWh）",
        value=st.session_state.get("electricity_price", 0.6), step=0.01
    )

    # 年处理量
    annual_capacity = st.number_input(
        "📦 年处理量（吨/年）",
        value=st.session_state.get("annual_capacity", 400), step=50
    )

    # 写入全局
    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("✅ 全系统同步生效")

# ===================== 主内容 =====================
st.title("📊 基础数据库浏览")
st.markdown("系统内置权威数据库，所有工艺、能耗、碳排放计算均基于标准数据源。")
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌿 药材库",
    "🔥 干燥技术库",
    "📍 产区库",
    "⚖️ 碳排放因子",
    "💰 经济成本库"
])

with tab1:
    st.subheader("药材基础信息")
    st.dataframe(data["herbs"], use_container_width=True)

with tab2:
    st.subheader("干燥技术参数库")
    st.dataframe(data["techs"], use_container_width=True)

with tab3:
    st.subheader("产区信息库")
    st.dataframe(data["regions"], use_container_width=True)

with tab4:
    st.subheader("区域碳排放因子")
    st.dataframe(data["carbon"], use_container_width=True)

with tab5:
    st.subheader("设备经济成本库(LCC)")
    st.dataframe(data["lcc"], use_container_width=True)

st.divider()
st.caption("数据来源：药典、国标、公开发表文献、行业标准")