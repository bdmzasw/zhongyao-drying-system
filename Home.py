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

# ===================== 页面配置 =====================
st.set_page_config(page_title="中药材低碳干燥智能决策系统", layout="wide")
st.markdown("""
<style>
    /* 主内容区背景 */
    .stApp {
        background-color: #f4f9f2;
    }

    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background-color: #f5ede0;
        border-right: 1px solid #d8c8b2;
    }

    /* 侧边栏控件 */
    div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
    div[data-testid="stSidebar"] .stNumberInput input {
        border: 1px solid #d8c8b2 !important;
        border-radius: 8px !important;
        background-color: #ffffff;
    }

    /* 原生导航 */
    [data-testid="stSidebarNav"] {
        background: #ffffff !important;
        border: 1px solid #b7d0b4;
        border-radius: 10px;
        padding: 0.3rem 0;
        margin: 1rem 0.5rem;
        box-shadow: 0 2px 6px rgba(80,120,80,0.08);
    }
    [data-testid="stSidebarNav"] li a {
        display: block;
        padding: 0.4rem 1rem;
        font-size: 0.9rem;
        color: #3a5a42 !important;
        font-weight: 500;
        border-radius: 6px;
        margin: 2px 6px;
        text-decoration: none;
    }
    [data-testid="stSidebarNav"] li a:hover {
        background-color: #e6f2e1;
    }

    /* 通用卡片 */
    .info-card {
        background: #f0f7f0;
        border: 1px solid #b7d0b4;
        border-radius: 14px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 14px rgba(80,120,80,0.08);
    }

    /* 特色亮点三列卡片 */
    .highlight-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 1.8rem 1.5rem;
        margin: 0;
        box-shadow: 0 6px 16px rgba(0,0,0,0.05);
        border: 1px solid #cde0cf;
        text-align: center;
    }
    .highlight-card h4 {
        color: #2e4a35;
        font-weight: 700;
        font-size: 1.25rem;
        margin-bottom: 0.8rem;
    }
    .highlight-card p {
        color: #4a5e4a;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* 主标题 */
    h1 {
        color: #1e3824;
        font-weight: 700;
        font-size: 3rem;
        font-family: "Segoe UI", "Noto Serif SC", "SimSun", serif;
        text-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border-bottom: 2px solid #a0c0a0;
        padding-bottom: 0.6rem;
        margin-bottom: 0.8rem;
        letter-spacing: 1px;
        line-height: 1.3;
    }

    h2 {
        color: #2e4a35;
        font-weight: 600;
        font-size: 1.7rem;
        font-family: "Segoe UI", "Noto Serif SC", "SimSun", serif;
        border-left: 5px solid #81a884;
        padding-left: 0.8rem;
        margin-top: 1.5rem;
    }

    h3 {
        color: #3a5a42;
        font-weight: 600;
        font-size: 1.3rem;
        font-family: "Segoe UI", "Noto Serif SC", "SimSun", serif;
        margin-top: 1.5rem;
    }

    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #81a884, transparent);
        margin: 2rem 0;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 会话初始化 =====================
if "selected_herb" not in st.session_state:
    st.session_state.selected_herb = "请选择"
if "selected_area" not in st.session_state:
    st.session_state.selected_area = "请选择"
if "electricity_price" not in st.session_state:
    st.session_state.electricity_price = 0.6
if "annual_capacity" not in st.session_state:
    st.session_state.annual_capacity = 400
if "weights" not in st.session_state:
    st.session_state.weights = [0.40, 0.20, 0.20, 0.05, 0.10, 0.05]

# ===================== 侧边栏 =====================
with st.sidebar:
    st.subheader("总操作仪表盘")
    st.caption("全局参数统一配置，全页面自动同步")
    st.markdown("---")

    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    if st.session_state.selected_herb not in herb_list:
        st.session_state.selected_herb = "请选择"
    selected_herb = st.selectbox(
        "药材品种",
        herb_list,
        index=herb_list.index(st.session_state.selected_herb)
    )

    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    if st.session_state.selected_area not in region_list:
        st.session_state.selected_area = "请选择"
    selected_area = st.selectbox(
        "产区",
        region_list,
        index=region_list.index(st.session_state.selected_area)
    )

    electricity_price = st.number_input(
        "电价（元/kWh）",
        value=st.session_state.electricity_price,
        step=0.01
    )
    annual_capacity = st.number_input(
        "年处理量（吨/年）",
        value=st.session_state.annual_capacity,
        step=50
    )

    with st.expander("评价权重设置", expanded=False):
        st.caption("不调整则使用默认值，调整后自动归一化")
        w1 = st.slider("有效成分保留率", 0.0, 1.0, st.session_state.weights[0], 0.01)
        w2 = st.slider("干燥时间", 0.0, 1.0, st.session_state.weights[1], 0.01)
        w3 = st.slider("单位能耗", 0.0, 1.0, st.session_state.weights[2], 0.01)
        w4 = st.slider("碳排放", 0.0, 1.0, st.session_state.weights[3], 0.01)
        w5 = st.slider("单位总成本", 0.0, 1.0, st.session_state.weights[4], 0.01)
        w6 = st.slider("投资回收期", 0.0, 1.0, st.session_state.weights[5], 0.01)

        total = sum([w1, w2, w3, w4, w5, w6])
        if total > 0:
            w1n, w2n, w3n, w4n, w5n, w6n = [x / total for x in [w1, w2, w3, w4, w5, w6]]
        else:
            w1n = w2n = w3n = w4n = w5n = w6n = 0.0

        st.caption(f"归一化：保 {w1n:.2f}　时 {w2n:.2f}　能 {w3n:.2f}")
        st.caption(f"碳 {w4n:.2f}　本 {w5n:.2f}　收 {w6n:.2f}")

        if st.button("恢复默认权重"):
            st.session_state.weights = [0.40, 0.20, 0.20, 0.05, 0.10, 0.05]
            st.rerun()

        st.session_state.weights = [w1, w2, w3, w4, w5, w6]

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("全局参数已自动生效")

# ===================== 主页内容 =====================
st.title("中药材低碳干燥工艺智能决策与优化系统")
st.caption("智能工艺推荐 · 能耗核算 · 低碳分析 · 药效保留综合决策")
st.divider()

# ---------- 特色亮点 ----------
st.markdown("### 系统特色与优势")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("""
    <div class="highlight-card">
        <h4>⚡ 智能工艺推荐</h4>
        <p>基于多目标优化算法，综合考虑品质、能耗、排放与成本，自动推荐最优干燥技术方案。</p>
    </div>
    """, unsafe_allow_html=True)
with col_b:
    st.markdown("""
    <div class="highlight-card">
        <h4>🌱 节能降碳分析</h4>
        <p>精准核算每种工艺的能耗与碳足迹，结合区域碳排放因子，助力企业达成“双碳”目标。</p>
    </div>
    """, unsafe_allow_html=True)
with col_c:
    st.markdown("""
    <div class="highlight-card">
        <h4>📊 全流程可视化</h4>
        <p>提供干燥动力学仿真、多维指标对比等可视化工具，让数据洞察一目了然。</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ---------- 系统简介 ----------
with st.container():
    st.markdown("""
    <div class="info-card">
        <h3>系统简介</h3>
        <p style="font-size:1.05rem; line-height:1.8; color:#2e3b2c;">
        本系统面向中药材干燥加工环节，集成智能工艺推荐、能耗计算、碳排放分析、干燥动力学可视化等功能于一体。
        系统以生产成本、低碳环保、药效保留、干燥效率为核心指标，为中药材干燥提供科学、高效、可落地的优化决策方案。
        </p>
        <p style="font-size:0.95rem; color:#5a7a5a;">
        通过左侧全局仪表盘选择药材、产区等参数，点击侧边栏下方导航进入各功能模块。
        </p>
    </div>
    """, unsafe_allow_html=True)

# ---------- 项目价值 ----------
with st.container():
    st.markdown("""
    <div class="info-card">
        <h3>项目价值</h3>
        <ul style="font-size:1.05rem; line-height:2; color:#2e3b2c; padding-left:1.2rem;">
            <li><strong>降低干燥能耗</strong> — 优化热风循环与余热利用，显著提升能源利用率</li>
            <li><strong>减少碳排放</strong> — 精准核算碳足迹，助力企业实现“双碳”目标与绿色生产</li>
            <li><strong>最大化药效保留</strong> — 科学控温控湿，减少热敏性有效成分分解与流失</li>
            <li><strong>提升生产效率</strong> — 缩短干燥周期，提高设备利用率与批次处理能力</li>
            <li><strong>降低生产成本</strong> — 减少能耗支出与人工调试成本，提升企业经济效益</li>
            <li><strong>保障品质均一稳定</strong> — 减少工艺波动带来的药材品质差异</li>
            <li><strong>全流程数字化追溯</strong> — 实现干燥过程可视化、可模拟、可优化</li>
            <li><strong>推动中药智能制造</strong> — 为传统工艺现代化、标准化提供数据支撑</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)