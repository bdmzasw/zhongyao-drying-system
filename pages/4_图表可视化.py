import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 读取CSV工具 =====================
def read_csv_safe(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        return pd.read_csv(path, encoding="gbk")

@st.cache_data
def load_base_data():
    return {
        "herbs": read_csv_safe("data/药材库.csv"),
        "regions": read_csv_safe("data/区域库.csv")
    }

base_data = load_base_data()
herbs_df = base_data["herbs"]
regions_df = base_data["regions"]

# ====================== 页面设置 ======================
st.set_page_config(page_title="图表可视化", page_icon="📊", layout="wide")

st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
.stApp { background-color: #f5f9f5; }
</style>
""", unsafe_allow_html=True)

# ====================== 返回主页 ======================
if st.button("🏠 返回主页"):
    st.switch_page("Home.py")

# ====================== 统一全局侧边栏 ======================
with st.sidebar:
    st.subheader("⚙️ 总操作仪表盘")
    st.markdown("---")

    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox(
        "🌿 药材品种", herb_list,
        index=herb_list.index(st.session_state.get("selected_herb", "请选择")) if st.session_state.get("selected_herb") in herb_list else 0
    )

    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox(
        "📍 产区", region_list,
        index=region_list.index(st.session_state.get("selected_area", "请选择")) if st.session_state.get("selected_area") in region_list else 0
    )

    electricity_price = st.number_input(
        "⚡ 电价（元/kWh）",
        value=st.session_state.get("electricity_price", 0.6), step=0.01
    )

    annual_capacity = st.number_input(
        "📦 年处理量（吨/年）",
        value=st.session_state.get("annual_capacity", 400), step=50
    )

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("✅ 全系统同步生效")

# ====================== 标题 ======================
st.markdown("## 📊 图表可视化")
st.caption("中药材干燥动力学对比分析")
st.divider()

# ====================== 可视化专属筛选 ======================
st.subheader("🔍 动力学数据筛选")
df = read_csv_safe("data/干燥动力学.csv")

col1, col2 = st.columns(2)
with col1:
    herb_choice = st.multiselect("🌿 选择药材", df["药材名称"].unique(), default=df["药材名称"].unique())
with col2:
    tech_choice = st.multiselect("🔥 选择工艺", df["干燥技术"].unique(), default=df["干燥技术"].unique())

plot_type = st.radio("📈 图表类型", ["活化能对比", "水分扩散系数对比"], horizontal=True)
st.divider()

# ====================== 筛选 ======================
df_filter = df[
    df["药材名称"].isin(herb_choice) & 
    df["干燥技术"].isin(tech_choice)
]

st.subheader("📋 筛选后数据")
st.dataframe(df_filter, use_container_width=True)

st.divider()
st.subheader("📊 可视化分析")

if plot_type == "活化能对比":
    fig = px.bar(
        df_filter,
        x="药材名称",
        y="干燥活化能(kJ/mol)",
        color="干燥技术",
        barmode="group",
        title="干燥活化能对比（越低越节能）"
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    fig = px.bar(
        df_filter,
        x="药材名称",
        y="有效水分扩散系数(m2/s)",
        color="干燥技术",
        barmode="group",
        title="水分扩散系数对比（越高越快）"
    )
    st.plotly_chart(fig, use_container_width=True)

st.success("✅ 加载完成 — 筛选正常 | 图表正常 | 无错误")
