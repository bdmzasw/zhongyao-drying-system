import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
import re
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 辅助函数 =====================
def extract_number(s):
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    sup_map = {'⁻': '-', '⁺': '+', '⁰': '0', '¹': '1', '²': '2', '³': '3',
               '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'}
    for k, v in sup_map.items():
        s = s.replace(k, v)
    s = s.replace('×10', 'e')
    parts = re.split(r'\s*[~～]\s*', s)
    nums = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            nums.append(float(part))
        except ValueError:
            fallback = re.findall(r"-?\d+\.?\d*", part)
            for fb in fallback:
                nums.append(float(fb))
    if not nums:
        return 0.0
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2.0
    return nums[0]

def calc_water_removed(initial, final):
    return (initial/100 - final/100) / (1 - final/100) * 1000

def read_csv_safe(path):
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except:
        df = pd.read_csv(path, encoding="gbk")
    sup_map = {'₀':'0','₁':'1','₂':'2','₃':'3','₄':'4','₅':'5','₆':'6','₇':'7','₈':'8','₉':'9',
               '⁰':'0','¹':'1','²':'2','³':'3','⁴':'4','⁵':'5','⁶':'6','⁷':'7','⁸':'8','⁹':'9'}
    new_columns = []
    for col in df.columns:
        clean_col = col
        for k, v in sup_map.items():
            clean_col = clean_col.replace(k, v)
        new_columns.append(clean_col)
    df.columns = new_columns
    return df

@st.cache_data
def load_all_data():
    return {
        "herbs": read_csv_safe("data/药材库.csv"),
        "techs": read_csv_safe("data/技术库.csv"),
        "regions": read_csv_safe("data/区域库.csv"),
        "carbon": read_csv_safe("data/区域碳排放因子.csv"),
        "kinetics": read_csv_safe("data/干燥动力学.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]
kinetics_df = data["kinetics"]

# ===================== 页面配置（统一风格） =====================
st.set_page_config(page_title="干燥仿真", layout="wide")
st.markdown("""
<style>
    .stApp {
        background-color: #f4f9f2;
    }
    [data-testid="stSidebar"] {
        background-color: #f5ede0;
        border-right: 1px solid #d8c8b2;
    }
    div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
    div[data-testid="stSidebar"] .stNumberInput input {
        border: 1px solid #d8c8b2 !important;
        border-radius: 8px !important;
        background-color: #ffffff;
    }
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
    h1 {
        color: #2e4a35;
        font-weight: 700;
        font-size: 2.2rem;
        border-bottom: 2px solid #81a884;
        padding-bottom: 0.4rem;
        margin-bottom: 0.8rem;
    }
    h2, h3 {
        color: #3a5a42;
        font-weight: 600;
    }
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #81a884, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 侧边栏 =====================
with st.sidebar:
    st.subheader("总操作仪表盘")
    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox(
        "药材品种", herb_list,
        index=herb_list.index(st.session_state.get("selected_herb", "请选择"))
        if st.session_state.get("selected_herb", "请选择") in herb_list else 0
    )
    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox(
        "产区", region_list,
        index=region_list.index(st.session_state.get("selected_area", "请选择"))
        if st.session_state.get("selected_area", "请选择") in region_list else 0
    )
    elec_price = st.number_input("电价（元/kWh）", value=st.session_state.get("electricity_price", 0.6), step=0.01)
    annual_output = st.number_input("年处理量（吨/年）", value=st.session_state.get("annual_capacity", 400), step=50)
    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = elec_price
    st.session_state["annual_capacity"] = annual_output

st.title("中药材干燥实时仿真")
st.caption("基于干燥动力学参数动态模拟含水率变化、能耗及碳排放")

if selected_herb == "请选择" or selected_area == "请选择":
    st.info("请选择药材与产区")
    st.stop()

# 药材数据
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = extract_number(herb_row["鲜品初始含水率(%)"])
final_mc = extract_number(herb_row["药典规定成品含水率(%)"])
water_removed_per_ton = calc_water_removed(init_mc, final_mc)

# 省份碳排放因子
region_row = regions_df[regions_df["产区名称"] == selected_area].iloc[0]
province = region_row["所辖主要省市"].split("、")[0]
province = re.sub(r'(东部|西部|南部|北部)', '', province)
carbon_factor = 0.55
cf_match = carbon_df[carbon_df.iloc[:, 0] == province]
if not cf_match.empty:
    carbon_factor = extract_number(cf_match.iloc[0, 2])

# ===================== 选择干燥技术 =====================
tech_list = techs_df["干燥技术"].tolist()
selected_tech = st.selectbox("选择干燥工艺", tech_list)
tech_row = techs_df[techs_df["干燥技术"] == selected_tech].iloc[0]
unit_energy = extract_number(tech_row["单位能耗(kWh/kg水)"])
total_hours = extract_number(tech_row["干燥时间范围 (h)"])

# ===================== 动力学参数 =====================
def get_core_name(name):
    return re.sub(r'[（(].*[）)]', '', name).strip()

def find_kinetics(herb_name, tech_name):
    herb_core = get_core_name(herb_name)
    kinetics_core_herbs = kinetics_df["药材名称"].apply(get_core_name)
    mask_herb = (kinetics_core_herbs == herb_core) | kinetics_core_herbs.str.contains(herb_core, na=False)
    candidates = kinetics_df[mask_herb]
    if candidates.empty:
        return None, None, None

    tech_core = get_core_name(tech_name)
    keywords = []
    for tw in ["热泵干燥", "热风干燥", "微波干燥", "冷冻干燥", "真空干燥", "远红外干燥", "红外干燥"]:
        if tw in tech_core:
            keywords.append(tw)
    if not keywords:
        keywords.append(tech_core)

    for kw in keywords:
        mask_tech = candidates["干燥技术"].str.contains(kw, na=False)
        matched = candidates[mask_tech]
        if not matched.empty:
            row = matched.iloc[0]
            return row, row["干燥活化能(kJ/mol)"], row["有效水分扩散系数(m2/s)"]

    ref_row = candidates.iloc[0]
    return ref_row, ref_row["干燥活化能(kJ/mol)"], ref_row["有效水分扩散系数(m2/s)"]

ref_row, ea_raw, diff_raw = find_kinetics(selected_herb, selected_tech)

if ref_row is not None:
    Ea = extract_number(ea_raw)
    D_ref = extract_number(diff_raw)
    model_name = str(ref_row.get("最适动力学模型", "Page"))
    r2_str = str(ref_row.get("拟合R2", "-"))
    param_desc = f"**{model_name}** 模型 (拟合度 {r2_str})"
    param_desc += f"  \n- 水分扩散系数: {D_ref:.2e} m²/s (越大水分跑得越快)"
    param_desc += f"  \n- 干燥活化能: {Ea:.2f} kJ/mol (代表干燥难易程度，越低越容易干燥)"
else:
    D_ref = 1e-10
    Ea = 45.0
    param_desc = "暂无文献数据，采用通用模型参数"

st.info(param_desc)

# ===================== Page 模型参数 =====================
if total_hours <= 0:
    total_hours = 5
n = 1.2
MR_target = 0.001
k = -np.log(MR_target) / (total_hours ** n)

# ===================== 仿真控制 =====================
col1, col2 = st.columns(2)
with col1:
    sim_speed = st.slider("仿真速度", 0.5, 2.0, 1.0)
with col2:
    sim_steps = st.slider("仿真步数", 20, 80, 40)

if st.button("开始仿真", type="primary"):
    steps = sim_steps
    history = []
    chart_placeholder = st.empty()
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(steps + 1):
        t = (i / steps) * total_hours
        mr = np.exp(-k * (t ** n))
        mr = max(0.0, min(1.0, mr))
        current_mc = final_mc + (init_mc - final_mc) * mr
        water_removed = 1000 * (init_mc - current_mc) / (100 - final_mc)
        total_energy = water_removed * unit_energy
        total_emission = total_energy * carbon_factor
        total_cost = total_energy * elec_price

        if i > 0:
            prev_mc = history[-1]["含水率(%)"]
            rate = abs(current_mc - prev_mc) / (total_hours / steps)
        else:
            rate = 0.0

        history.append({
            "时间(h)": round(t, 2),
            "含水率(%)": round(current_mc, 2),
            "干燥速率(%/h)": round(rate, 2),
            "累计能耗(kWh)": round(total_energy, 2),
            "累计碳排放(kg)": round(total_emission, 2),
            "累计成本(元)": round(total_cost, 2)
        })

        df_sim = pd.DataFrame(history)

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("含水率变化", "干燥速率与能耗"),
            specs=[[{"secondary_y": False}, {"secondary_y": True}]]
        )

        fig.add_trace(go.Scatter(
            x=df_sim["时间(h)"], y=df_sim["含水率(%)"],
            mode='lines+markers', name='含水率',
            line=dict(color='#e74c3c', width=2),
            marker=dict(size=4)
        ), row=1, col=1)
        fig.add_hline(y=final_mc, line_dash="dash", line_color="green",
                      annotation_text=f"目标 {final_mc:.1f}%", row=1, col=1)
        fig.update_yaxes(title_text="含水率 (%)", row=1, col=1)
        fig.update_xaxes(title_text="时间 (h)", row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df_sim["时间(h)"], y=df_sim["干燥速率(%/h)"],
            mode='lines+markers', name='干燥速率',
            line=dict(color='#3498db', width=2),
            marker=dict(size=4)
        ), row=1, col=2, secondary_y=False)
        fig.update_yaxes(title_text="干燥速率 (%/h)", row=1, col=2, secondary_y=False)

        fig.add_trace(go.Scatter(
            x=df_sim["时间(h)"], y=df_sim["累计能耗(kWh)"],
            mode='lines', name='累计能耗',
            line=dict(color='#f39c12', width=2, dash='dot')
        ), row=1, col=2, secondary_y=True)
        fig.update_yaxes(title_text="累计能耗 (kWh)", row=1, col=2, secondary_y=True)
        fig.update_xaxes(title_text="时间 (h)", row=1, col=2)

        fig.update_layout(
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        chart_placeholder.plotly_chart(fig, use_container_width=True)
        progress_bar.progress(i / steps)
        status_text.info(f"⏳ {t:.1f}h | 含水率: {current_mc:.1f}% | 累计能耗: {total_energy:.1f} kWh | 累计成本: {total_cost:.1f} 元")
        time.sleep(0.3 / sim_speed)

    progress_bar.progress(1.0)
    st.success(f"✅ 仿真完成！最终含水率：{history[-1]['含水率(%)']:.2f}%")

    st.divider()
    st.subheader("仿真结果汇总")
    final_data = history[-1]
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("每吨脱水量", f"{water_removed_per_ton:.1f} kg")
    col_b.metric("每吨能耗", f"{water_removed_per_ton * unit_energy:.1f} kWh")
    col_c.metric("每吨碳排放", f"{water_removed_per_ton * unit_energy * carbon_factor:.1f} kg")
    col_d.metric("每吨电费", f"{water_removed_per_ton * unit_energy * elec_price:.1f} 元")

    with st.expander("全过程仿真数据"):
        st.dataframe(pd.DataFrame(history), use_container_width=True)