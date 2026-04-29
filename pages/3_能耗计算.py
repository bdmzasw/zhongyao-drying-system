import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import re
import plotly.express as px

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
        "heat_recovery": read_csv_safe("data/余热回收技术对比表.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]
heat_recovery_df = data["heat_recovery"]

# 构建余热回收字典（系统节能率）
def get_recovery_rates():
    rates = {}
    for _, row in heat_recovery_df.iterrows():
        tech = str(row["干燥技术名称"]).split("-")[0].strip()
        val = row["系统节能率(%)"]
        if pd.notna(val) and str(val) != "—":
            rates[tech] = extract_number(val) / 100.0
    defaults = {
        "热泵干燥（HPD）": 0.835,
        "热风干燥（HAD）": 0.0,
        "微波干燥（MD）": 0.20,
        "冷冻干燥（FD）": -2.75,
        "真空干燥（VD）": 0.40,
        "远红外干燥（FIR）": 0.35,
        "热泵-微波联合干燥": 0.79,
        "热泵-远红外联合干燥": 0.925,
        "热风-热泵联合干燥": 0.745
    }
    for k, v in defaults.items():
        if k not in rates:
            rates[k] = v
    return rates

RECOVERY_RATES = get_recovery_rates()

# ===================== 页面配置（统一风格） =====================
st.set_page_config(page_title="能耗核算", layout="wide")
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
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(80,120,80,0.08);
        border: 1px solid #cde0cf;
    }
    .metric-card .label { color: #555; font-size: 0.85rem; }
    .metric-card .value { font-size: 1.8rem; font-weight: 700; color: #2d4a32; }
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #81a884, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 侧边栏（全局仪表盘） =====================
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

st.title("能耗核算与节能分析")

if selected_herb == "请选择" or selected_area == "请选择":
    st.info("请在侧边栏选择药材与产区")
    st.stop()

# 药材数据与脱水量
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = extract_number(herb_row["鲜品初始含水率(%)"])
final_mc = extract_number(herb_row["药典规定成品含水率(%)"])
water_removed_per_ton = calc_water_removed(init_mc, final_mc)

# 省份及碳排放因子
region_row = regions_df[regions_df["产区名称"] == selected_area].iloc[0]
province = region_row["所辖主要省市"].split("、")[0]
province = re.sub(r'(东部|西部|南部|北部)', '', province)
carbon_factor = 0.55
cf_match = carbon_df[carbon_df.iloc[:, 0] == province]
if not cf_match.empty:
    carbon_factor = extract_number(cf_match.iloc[0, 2])

st.markdown(f"### {selected_herb} · {selected_area}")
st.markdown(f"吨脱水量：**{water_removed_per_ton:.1f} kg** | 碳排因子：**{carbon_factor:.4f} kgCO₂/kWh**")

# ================== 遍历技术计算能耗 ==================
tech_list = []
for _, tech in techs_df.iterrows():
    tech_name = tech["干燥技术"]
    unit_energy = extract_number(tech["单位能耗(kWh/kg水)"])
    total_energy = water_removed_per_ton * unit_energy
    recovery = RECOVERY_RATES.get(tech_name, 0.0)
    net_energy = total_energy * (1 - recovery)
    emission = net_energy * carbon_factor
    cost_elec = net_energy * elec_price
    annual_energy = net_energy * annual_output
    annual_cost = annual_energy * elec_price
    annual_emission = annual_energy * carbon_factor
    tech_list.append({
        "干燥技术": tech_name,
        "单位能耗(kWh/kg水)": unit_energy,
        "总能耗(kWh/吨)": total_energy,
        "系统节能率": recovery * 100,
        "净能耗(kWh/吨)": net_energy,
        "碳排放(kg/吨)": emission,
        "电费(元/吨)": cost_elec,
        "年净能耗(万kWh)": annual_energy / 10000,
        "年碳排放(吨)": annual_emission / 1000,
        "年电费(万元)": annual_cost / 10000
    })

df_energy = pd.DataFrame(tech_list)

tech_names = df_energy["干燥技术"].tolist()
selected_tech = st.selectbox("选择要查看明细的干燥技术", tech_names)
tech_row = df_energy[df_energy["干燥技术"] == selected_tech].iloc[0]

st.subheader(f"{selected_tech} 能耗明细")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-card'><div class='label'>单位能耗</div><div class='value'>{tech_row['单位能耗(kWh/kg水)']:.3f}</div><div class='label'>kWh/kg水</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='metric-card'><div class='label'>净能耗/吨</div><div class='value'>{tech_row['净能耗(kWh/吨)']:.1f}</div><div class='label'>kWh</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='metric-card'><div class='label'>碳排放/吨</div><div class='value'>{tech_row['碳排放(kg/吨)']:.1f}</div><div class='label'>kg CO₂</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='metric-card'><div class='label'>电费/吨</div><div class='value'>{tech_row['电费(元/吨)']:.1f}</div><div class='label'>元</div></div>", unsafe_allow_html=True)

st.subheader("年度能耗估算（基于年处理量）")
c1, c2, c3 = st.columns(3)
c1.metric("年净能耗", f"{tech_row['年净能耗(万kWh)']:.2f} 万kWh")
c2.metric("年电费", f"{tech_row['年电费(万元)']:.2f} 万元")
c3.metric("年碳排放", f"{tech_row['年碳排放(吨)']:.1f} 吨")

recovery_rate = tech_row["系统节能率"]
if recovery_rate != 0:
    st.info(f"该系统节能率：{recovery_rate:.1f}%，净能耗已考虑回收效益。")

st.subheader("各技术能耗与碳排放对比")
fig1 = px.bar(df_energy, x="干燥技术", y="净能耗(kWh/吨)", 
              text=df_energy["净能耗(kWh/吨)"].apply(lambda x: f"{x:.1f}"),
              title="净能耗对比 (kWh/吨)", color_discrete_sequence=["#4CAF50"])
fig1.update_traces(textposition="outside", textfont_size=12)
fig1.update_layout(yaxis_title="净能耗 (kWh/吨)", xaxis_title="")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(df_energy, x="干燥技术", y="碳排放(kg/吨)", 
              text=df_energy["碳排放(kg/吨)"].apply(lambda x: f"{x:.1f}"),
              title="碳排放对比 (kg/吨)", color_discrete_sequence=["#FF9800"])
fig2.update_traces(textposition="outside", textfont_size=12)
fig2.update_layout(yaxis_title="碳排放 (kg/吨)", xaxis_title="")
st.plotly_chart(fig2, use_container_width=True)

with st.expander("全部技术能耗数据表"):
    st.dataframe(df_energy[["干燥技术","单位能耗(kWh/kg水)","净能耗(kWh/吨)","系统节能率","碳排放(kg/吨)","年净能耗(万kWh)","年碳排放(吨)"]].style.format({
        "单位能耗(kWh/kg水)": "{:.3f}",
        "净能耗(kWh/吨)": "{:.1f}",
        "系统节能率": "{:.1f}%",
        "碳排放(kg/吨)": "{:.1f}",
        "年净能耗(万kWh)": "{:.2f}",
        "年碳排放(吨)": "{:.1f}"
    }), use_container_width=True)

st.caption("能耗计算基于药材含水率、区域碳排因子、设备节能率及电价，年度估算采用年处理量。")