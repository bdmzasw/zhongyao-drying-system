import streamlit as st
import pandas as pd
import os

# ===================== 安全读取CSV =====================
def read_csv_safe(path):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        return pd.read_csv(path, encoding="gbk")

# ===================== 加载数据库 =====================
@st.cache_data
def load_all_data():
    return {
        "herbs": read_csv_safe("data/药材库.csv"),
        "regions": read_csv_safe("data/区域库.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
regions_df = data["regions"]

# ===================== 页面配置 + 精致排版 =====================
st.set_page_config(page_title="中药材低碳干燥智能决策系统", layout="wide")
st.markdown("""
<style>
/* 柔和高级浅绿色背景 */
.stApp {
    background-color: #f4f9f6;
}
/* 隐藏侧边栏导航 */
[data-testid="stSidebarNav"] {
    display: none;
}
/* 卡片容器样式 */
div[data-testid="stVerticalBlock"] > div[style*="border"] {
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.03);
    border: 1px solid #e0f0e9;
}
/* 按钮排版 */
.stPageLink {
    font-size: 1rem !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ===================== 侧边栏 =====================
with st.sidebar:
    st.subheader("⚙️ 总操作仪表盘")
    st.caption("全局参数统一配置，全页面自动同步")
    st.markdown("---")

    herb_list = herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox("🌿 药材品种", ["请选择"] + herb_list)

    region_list = regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox("📍 产区", ["请选择"] + region_list)

    electricity_price = st.number_input("⚡ 电价（元/kWh）", value=0.6, step=0.01)
    annual_capacity = st.number_input("⚙️ 年处理量（吨/年）", value=400, step=50)

    # ===================== 权重折叠面板 =====================
    with st.expander("⚖️ 评价权重设置", expanded=False):
        st.caption("不调整则使用默认值")
        default_weights = [0.40, 0.20, 0.20, 0.05, 0.10, 0.05]
        if "weights" not in st.session_state:
            st.session_state.weights = default_weights

        w1 = st.slider("有效成分保留率", 0.0, 1.0, st.session_state.weights[0], 0.01)
        w2 = st.slider("干燥时间", 0.0, 1.0, st.session_state.weights[1], 0.01)
        w3 = st.slider("单位能耗", 0.0, 1.0, st.session_state.weights[2], 0.01)
        w4 = st.slider("碳排放", 0.0, 1.0, st.session_state.weights[3], 0.01)
        w5 = st.slider("单位总成本", 0.0, 1.0, st.session_state.weights[4], 0.01)
        w6 = st.slider("投资回收期", 0.0, 1.0, st.session_state.weights[5], 0.01)

        total = sum([w1, w2, w3, w4, w5, w6])
        w1n, w2n, w3n, w4n, w5n, w6n = [x / total for x in [w1, w2, w3, w4, w5, w6]]
        st.session_state.weights = [w1, w2, w3, w4, w5, w6]

        st.caption(f"保:{w1n:.2f} 时:{w2n:.2f} 能:{w3n:.2f}")
        st.caption(f"碳:{w4n:.2f} 本:{w5n:.2f} 收:{w6n:.2f}")

        if st.button("🔧 恢复默认权重"):
            st.session_state.weights = default_weights
            st.rerun()

    # 全局状态保存
    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("✅ 全局参数已自动生效")

# ===================== 主页 =====================
st.title("中药材低碳干燥工艺智能决策与优化系统")
st.caption("智能工艺推荐 · 能耗核算 · 低碳分析 · 药效保留综合决策")
st.divider()

# 系统简介
with st.container(border=True):
    st.markdown("### 📘 系统简介")
    st.write("""
    本系统面向中药材干燥加工环节，集成智能工艺推荐、能耗计算、碳排放分析、干燥动力学可视化等功能于一体。
    系统以生产成本、低碳环保、药效保留、干燥效率为核心指标，为中药材干燥提供科学、高效、可落地的优化决策方案。
    """)

st.divider()

# 核心功能模块
st.markdown("### 🚀 核心功能模块")

col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    with st.container(border=True):
        st.page_link("pages/1_数据浏览.py", label="📊 数据浏览\n基础信息管理", use_container_width=True)
with col2:
    with st.container(border=True):
        st.page_link("pages/2_工艺推荐.py", label="⚙️ 工艺推荐\n多目标优化决策", use_container_width=True)
with col3:
    with st.container(border=True):
        st.page_link("pages/3_能耗计算.py", label="🔋 能耗计算\n能耗与碳排放核算", use_container_width=True)

col4, col5, col6 = st.columns(3, gap="medium")
with col4:
    with st.container(border=True):
        st.page_link("pages/4_图表可视化.py", label="📈 图表可视化\n干燥动力学分析", use_container_width=True)
with col5:
    with st.container(border=True):
        st.page_link("pages/5_报告导出.py", label="📄 报告导出\n一键生成综合报告", use_container_width=True)
with col6:
    with st.container(border=True):
        st.page_link("pages/6_干燥实时仿真.py", label="📶 干燥实时仿真\n全过程动态监控", use_container_width=True)

st.divider()

# 项目价值
with st.container(border=True):
    st.markdown("### 📖 项目价值")
    st.write("""
    ✅ **降低干燥能耗**，优化热风循环与余热利用，显著提升能源利用率  
    ✅ **减少碳排放**，精准核算碳足迹，助力企业实现“双碳”目标与绿色生产  
    ✅ **最大化药效保留**，科学控温控湿，减少热敏性有效成分分解与流失  
    ✅ **提升生产效率**，缩短干燥周期，提高设备利用率与批次处理能力  
    ✅ **降低生产成本**，减少能耗支出与人工调试成本，提升企业经济效益  
    ✅ **保障品质均一稳定**，减少工艺波动带来的药材品质差异  
    ✅ **全流程数字化追溯**，实现干燥过程可视化、可模拟、可优化  
    ✅ **推动中药智能制造**，为传统工艺现代化、标准化提供数据支撑
    """)