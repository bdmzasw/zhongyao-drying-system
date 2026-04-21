import streamlit as st
import pandas as pd
import time
import plotly.express as px
import numpy as np

# ===================== 安全浮点转换 =====================
def safe_float(value, default=0.0):
    if pd.isna(value):
        return default
    s = str(value).strip()
    if "~" in s or "-" in s:
        sep = "~" if "~" in s else "-"
        try:
            a, b = s.split(sep)
            return (float(a.strip()) + float(b.strip())) / 2
        except:
            return default
    try:
        return float(s)
    except:
        return default

# ===================== 读取CSV =====================
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
        "carbon": read_csv_safe("data/区域碳排放因子.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]

# ===================== 页面设置 =====================
st.set_page_config(page_title="实时干燥仿真", page_icon="♨️", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
.stApp {background-color: #f5f9f5;}
.block-container {padding-top: 3rem; padding-bottom:1rem;}
div[data-testid="stVerticalBlock"] {gap:0.5rem;}
/* 把按钮固定在页面最顶部，不会被挡住 */
div.stButton > button:first-child {
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 9999;
}
</style>
""", unsafe_allow_html=True)

# 固定在左上角的返回主页按钮
if st.button("🏠 返回主页"):
    st.switch_page("Home.py")

# ===================== 全局侧边栏 =====================
with st.sidebar:
    st.subheader("⚙️ 总操作仪表盘")
    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox("🌿 药材品种", herb_list, index=herb_list.index(st.session_state.get("selected_herb", "请选择")) if st.session_state.get("selected_herb") in herb_list else 0)
    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox("📍 产区", region_list, index=region_list.index(st.session_state.get("selected_area", "请选择")) if st.session_state.get("selected_area") in region_list else 0)
    electricity_price = st.number_input("⚡ 电价", value=st.session_state.get("electricity_price", 0.6), step=0.01)
    annual_capacity = st.number_input("📦 年处理量", value=st.session_state.get("annual_capacity", 400), step=50)
    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity
    st.caption("全系统参数同步")

# ===================== 页面标题 =====================
st.title("♨️ 中药材实时干燥仿真")
st.caption("基于真实药材特性与工艺参数，动态模拟干燥全过程")
st.divider()

# ===================== 仿真控制面板 =====================
col1, col2, col3 = st.columns(3)
with col1:
    tech_list = ["请选择"] + techs_df["干燥技术"].unique().tolist()
    selected_tech = st.selectbox("🔥 干燥工艺", tech_list)
with col2:
    sim_speed = st.slider("⏩ 仿真速度", 0.4, 1.6, 0.7)
with col3:
    sim_steps = st.slider("📌 仿真精度（步数）", 30, 100, 50, help="控制曲线平滑度与仿真细腻程度。数值越大，含水率变化越平滑，最终越接近目标值。")

mode = st.radio("仿真模式", ["标准模式", "快速模式", "对比模式(热风基准)"], horizontal=True)
st.divider()

# ===================== 开始仿真 =====================
if selected_herb == "请选择" or selected_tech == "请选择" or selected_area == "请选择":
    st.info("👈 请先选择药材、产区、工艺")
else:
    herb = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
    tech = techs_df[techs_df["干燥技术"] == selected_tech].iloc[0]
    region = regions_df[regions_df["产区名称"] == selected_area].iloc[0]

    M0 = safe_float(herb["鲜品初始含水率(%)"], 80.0)
    Mt = safe_float(herb["药典规定成品含水率(%)"], 12.0)
    unit_eng = safe_float(tech["单位能耗(kWh/kg水)"], 0.4)
    total_h = safe_float(tech["干燥时间范围 (h)"], 8.0)

    province = region["所辖主要省市"].split("、")[0]
    carbon_k = 0.55
    cf_match = carbon_df[carbon_df.iloc[:,0] == province]
    if not cf_match.empty:
        carbon_k = safe_float(cf_match.iloc[0,2])

    # 基础计算
    remove_per_ton = 1000 * (M0 - Mt) / (100 - Mt)
    eng_per_ton = remove_per_ton * unit_eng
    cost_per_ton = eng_per_ton * electricity_price
    carbon_per_ton = eng_per_ton * carbon_k

    # 模式适配
    total_steps = sim_steps
    if mode == "快速模式":
        total_steps = int(sim_steps * 0.6)
        total_h = total_h * 0.6

    # 热风对比
    hot_unit = 0.8
    if mode == "对比模式(热风基准)":
        hot_mask = techs_df["干燥技术"].str.contains("热风", na=False)
        if not techs_df[hot_mask].empty:
            hot_tech_row = techs_df[hot_mask].iloc[0]
            hot_unit = safe_float(hot_tech_row["单位能耗(kWh/kg水)"], 0.8)

    # 显示核心参数
    st.subheader("📊 核心参数")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("初始含水率", f"{M0:.1f}%")
    with c2: st.metric("目标含水率", f"{Mt:.1f}%")
    with c3: st.metric("干燥时间", f"{total_h:.1f}h")
    with c4: st.metric("单位能耗", f"{unit_eng:.2f}")

    st.divider()
    st.subheader("📉 实时仿真过程")

    # 图表占位
    chart_L = st.empty()
    chart_R = st.empty()
    meter_L = st.empty()
    meter_R = st.empty()
    status = st.empty()
    bar = st.progress(0)

    history = []
    current_M = M0

    # 关键修复：使用对数衰减模型模拟真实干燥，末端逼近目标值
    for i in range(total_steps + 1):
        ratio = i / total_steps
        # 对数衰减模型：前期快、后期慢，最终无限逼近Mt
        current_M = Mt + (M0 - Mt) * np.exp(-3 * ratio)

        # 计算累计能耗与成本
        removed = M0 - current_M
        total_eng = removed * unit_eng
        total_carbon = total_eng * carbon_k
        total_cost = total_eng * electricity_price

        history.append({
            "time": round(i * total_h / total_steps, 1),
            "mois": round(current_M, 1),
            "eng": round(total_eng, 1),
            "carbon": round(total_carbon, 1),
            "cost": round(total_cost, 1)
        })

        # 实时更新
        df = pd.DataFrame(history)
        fig1 = px.line(df, x="time", y="mois", title="含水率变化", color_discrete_sequence=["#e74c3c"])
        fig1.add_hline(y=Mt, line_dash="dash", line_color="green", annotation_text="目标含水率")
        fig1.add_hline(y=current_M, line_dash="dot", line_color="blue", annotation_text="当前含水率")
        chart_L.plotly_chart(fig1, use_container_width=True)
        meter_L.metric("当前含水率", f"{current_M:.1f}%", f"目标：{Mt:.1f}%")

        fig2 = px.line(df, x="time", y=["eng","carbon"], title="能耗 & 碳排放")
        chart_R.plotly_chart(fig2, use_container_width=True)
        meter_R.metric("累计能耗", f"{total_eng:.1f} kWh")

        bar.progress(ratio)
        status.info(f"时间：{history[-1]['time']}h | 累计脱水：{removed:.1f}kg | 累计成本：{total_cost:.1f}元")
        time.sleep(0.22 / sim_speed)

    bar.progress(1.0)
    st.success("✅ 干燥仿真完成！含水率已逼近药典标准")

    st.divider()
    st.subheader("📋 全过程数据")
    st.dataframe(pd.DataFrame(history), use_container_width=True)

    st.divider()
    st.subheader("📊 结果分析")
    a1,a2,a3 = st.columns(3)
    with a1: st.metric("每吨脱水量", f"{remove_per_ton:.1f} kg")
    with a2: st.metric("每吨能耗", f"{eng_per_ton:.1f} kWh")
    with a3: st.metric("每吨成本", f"{cost_per_ton:.1f} 元")

    if mode == "对比模式(热风基准)":
        st.divider()
        final_energy = history[-1]['eng']
        save_rate = (hot_unit - unit_eng) / hot_unit * 100
        st.info(f"相比热风干燥（基准）能耗降低：{save_rate:.1f}%")
