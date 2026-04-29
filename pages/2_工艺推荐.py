import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import re

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
        "lcc": read_csv_safe("data/LCC经济成本库-干燥设备对比.csv"),
        "heat_recovery": read_csv_safe("data/余热回收技术对比表.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]
lcc_df = data["lcc"]
heat_recovery_df = data["heat_recovery"]

LCC_MAP = {
    "热泵干燥（HPD）": "热泵干燥（HPD）",
    "热风干燥（HAD）": "热风干燥（HAD）",
    "微波干燥（MD）": "微波干燥（MD）",
    "冷冻干燥（FD）": "冷冻干燥（FD）",
    "真空干燥（VD）": "真空干燥（VD）",
    "远红外干燥（FIR）": "远红外干燥（FIR）",
    "热泵-微波联合干燥": "组合干燥（热泵+微波/远红外等）",
    "热泵-远红外联合干燥": "组合干燥（热泵+微波/远红外等）",
    "热风-热泵联合干燥": "组合干燥（热泵+微波/远红外等）",
}

def get_heat_recovery_rates():
    rates = {}
    for _, row in heat_recovery_df.iterrows():
        tech_name = str(row["干燥技术名称"]).strip()
        tech_name_clean = tech_name.split("-")[0].strip()
        if tech_name_clean in LCC_MAP or tech_name_clean in techs_df["干燥技术"].values:
            val = row["系统节能率(%)"]
            if pd.notna(val) and str(val) != "—":
                rate = extract_number(val)
                rates[tech_name_clean] = rate
    defaults = {
        "热泵干燥（HPD）": 83.5,
        "热风干燥（HAD）": 0.0,
        "微波干燥（MD）": 20.0,
        "冷冻干燥（FD）": -275.0,
        "真空干燥（VD）": 40.0,
        "远红外干燥（FIR）": 35.0,
        "热泵-微波联合干燥": 79.0,
        "热泵-远红外联合干燥": 92.5,
        "热风-热泵联合干燥": 74.5
    }
    for k, v in defaults.items():
        if k not in rates:
            rates[k] = v
    return rates

RECOVERY_RATES = get_heat_recovery_rates()

# ===================== 页面配置（统一风格） =====================
st.set_page_config(page_title="工艺推荐", layout="wide")
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
    .stage-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 12px rgba(80,120,80,0.08);
        border-left: 5px solid;
    }
    .metric-item {
        background: #ffffff;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .metric-item .label { font-size: 0.85rem; color: #555; }
    .metric-item .value { font-size: 1.6rem; font-weight: 700; color: #2e4a35; }
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(to right, transparent, #81a884, transparent);
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 移除返回主页按钮
# if st.button("🏠 返回主页"):
#     st.switch_page("Home.py")

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

    with st.expander("评价权重设置", expanded=False):
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

        total = w1 + w2 + w3 + w4 + w5 + w6
        if total > 0:
            w1n, w2n, w3n, w4n, w5n, w6n = [x / total for x in [w1, w2, w3, w4, w5, w6]]
        else:
            w1n = w2n = w3n = w4n = w5n = w6n = 0.0

        st.caption(f"归一化：保 {w1n:.2f}　时 {w2n:.2f}　能 {w3n:.2f}")
        st.caption(f"碳 {w4n:.2f}　本 {w5n:.2f}　收 {w6n:.2f}")

        if st.button("恢复默认权重"):
            st.session_state.weights = default_weights
            st.rerun()

        st.session_state.weights = [w1, w2, w3, w4, w5, w6]

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = elec_price
    st.session_state["annual_capacity"] = annual_output

st.title("工艺参数与方案推荐")
st.caption("智能匹配干燥工艺，兼顾品质、效率、低碳与经济性")

if selected_herb == "请选择" or selected_area == "请选择":
    st.info("请在左侧选择药材与产区")
    st.stop()

# 药材数据
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = extract_number(herb_row["鲜品初始含水率(%)"])
final_mc = extract_number(herb_row["药典规定成品含水率(%)"])
water_removed = calc_water_removed(init_mc, final_mc)

# 省份及碳排放因子
region_row = regions_df[regions_df["产区名称"] == selected_area].iloc[0]
province = region_row["所辖主要省市"].split("、")[0]
province = re.sub(r'(东部|西部|南部|北部)', '', province)
carbon_factor = 0.55
cf_match = carbon_df[carbon_df.iloc[:, 0] == province]
if not cf_match.empty:
    carbon_factor = extract_number(cf_match.iloc[0, 2])

weights = st.session_state.get("weights", default_weights)
total_w = sum(weights)
w1n, w2n, w3n, w4n, w5n, w6n = [x/total_w for x in weights] if total_w > 0 else [0]*6

# ================== 遍历全部技术 ==================
results = []
for _, tech in techs_df.iterrows():
    tech_name = tech["干燥技术"]
    unit_energy = extract_number(tech["单位能耗(kWh/kg水)"])
    total_energy = water_removed * unit_energy
    recovery_rate = RECOVERY_RATES.get(tech_name, 0.0) / 100.0
    net_energy = total_energy * (1 - recovery_rate)
    electricity_cost = net_energy * elec_price
    carbon_emission = net_energy * carbon_factor
    carbon_cost = carbon_emission * 60 / 1000
    retention = extract_number(tech["有效成分保留率(%)"]) / 100
    dry_time = extract_number(tech["干燥时间范围 (h)"])

    matched_lcc = LCC_MAP.get(tech_name, tech_name)
    lcc_match = lcc_df[lcc_df["干燥模式"] == matched_lcc]
    if lcc_match.empty:
        lcc_match = lcc_df.iloc[[0]]
    lcc_r = lcc_match.iloc[0]
    invest = extract_number(lcc_r["设备初始投资(元/台套)"])
    years = extract_number(lcc_r["年折旧年限(年)"])
    labor = extract_number(lcc_r["年人工成本(元/年)"])
    om = extract_number(lcc_r["年运维耗材费(元/年)"])
    residue = extract_number(lcc_r["残值率(%)"])
    deprec = (invest * (1 - residue/100) / years) / annual_output
    labor_c = labor / annual_output
    om_c = om / annual_output
    total_cost = deprec + labor_c + om_c + electricity_cost + carbon_cost

    results.append({
        "干燥技术": tech_name,
        "保留率": retention,
        "时间": dry_time,
        "能耗": total_energy,
        "净能耗": net_energy,
        "碳排放": carbon_emission,
        "总成本": total_cost,
        "回收期": years,
        "系统节能率": recovery_rate * 100
    })

df = pd.DataFrame(results)

def minmax_norm(s, reverse):
    if s.max() == s.min():
        return pd.Series([0.5]*len(s))
    if reverse:
        return (s.max() - s) / (s.max() - s.min())
    return (s - s.min()) / (s.max() - s.min())

df["品质分"] = minmax_norm(df["保留率"], False)
df["时间分"] = minmax_norm(df["时间"], True)
df["能耗分"] = minmax_norm(df["能耗"], True)
df["碳排分"] = minmax_norm(df["碳排放"], True)
df["成本分"] = minmax_norm(df["总成本"], True)
df["回收分"] = minmax_norm(df["回收期"], True)

df["综合得分"] = (w1n*df["品质分"] + w2n*df["时间分"] + w3n*df["能耗分"] +
                  w4n*df["碳排分"] + w5n*df["成本分"] + w6n*df["回收分"]).round(4)

df = df.sort_values("综合得分", ascending=False).reset_index(drop=True)

col1, col2, col3 = st.columns(3)
col1.metric("药材", selected_herb)
col2.metric("产区", selected_area)
col3.metric("吨脱水量", f"{water_removed:.1f} kg")

st.markdown("---")

st.subheader("工艺综合评价结果")
display_df = df[["干燥技术","保留率","时间","净能耗","系统节能率","碳排放","总成本","回收期","综合得分"]]
num_cols = display_df.select_dtypes(include='number').columns.tolist()
st.dataframe(display_df.style.format({col: "{:.3f}" for col in num_cols}), use_container_width=True)

best = df.iloc[0]
st.success(f"最优推荐：{best['干燥技术']}（综合得分 {best['综合得分']:.4f}）")

# ================== 分段干燥卡片（保留） ==================
best_tech_name = best["干燥技术"]
best_tech_row = techs_df[techs_df["干燥技术"] == best_tech_name].iloc[0]

st.markdown("---")
st.subheader("分段式干燥工艺推荐")

third_temp_raw = best_tech_row.get("三段干燥温度(℃)", "")
has_third = pd.notna(third_temp_raw) and str(third_temp_raw).strip() not in ["", "—", "-"]
stage_count = 3 if has_third else 2
st.markdown(f"{best_tech_name} 采用 {stage_count} 段干燥")

stage1_switch = extract_number(herb_row.get("一段切换含水率(%)", 60))
stage2_switch = extract_number(herb_row.get("二段切换/终点含水率(%)", 30))

def get_range_str(cell):
    if pd.isna(cell):
        return ""
    return str(cell).strip()

t1_range = get_range_str(best_tech_row.get("一段干燥温度(℃)", ""))
v1_range = get_range_str(best_tech_row.get("一段干燥风速(m/s)", ""))
t2_range = get_range_str(best_tech_row.get("二段干燥温度(℃)", ""))
v2_range = get_range_str(best_tech_row.get("二段干燥风速(m/s)", ""))

def build_stage_card(title, moisture_text, temp_range, wind_range, color):
    temp_line = f"<p>最适温度区间：<b>{temp_range} ℃</b></p>" if temp_range else ""
    wind_line = f"<p>推荐风速：<b>{wind_range} m/s</b></p>" if wind_range and wind_range != "—" else ""
    return f"""
    <div class="stage-card" style="border-left-color:{color}">
        <h4>{title}</h4>
        <p>{moisture_text}</p>
        {temp_line}
        {wind_line}
    </div>
    """

c1, c2 = st.columns(2)
with c1:
    st.markdown(build_stage_card("1. 强脱水段",
        f"含水率 ≥ {stage1_switch:.0f}%",
        t1_range, v1_range, "#e67e22"), unsafe_allow_html=True)
with c2:
    st.markdown(build_stage_card("2. 稳定干燥段",
        f"含水率 {stage2_switch:.0f}% ~ {stage1_switch:.0f}%",
        t2_range, v2_range, "#3498db"), unsafe_allow_html=True)

if has_third:
    t3_range = get_range_str(best_tech_row.get("三段干燥温度(℃)", ""))
    v3_range = get_range_str(best_tech_row.get("三段干燥风速(m/s)", ""))
    st.markdown(build_stage_card("3. 缓苏定色段",
        f"含水率 ≤ {stage2_switch:.0f}%",
        t3_range, v3_range, "#2ecc71"), unsafe_allow_html=True)

st.caption("实际干燥温度可根据药材特性在设备允许范围内灵活调整。")

# ================== 节能效益卡片（保留） ==================
st.markdown("---")
st.subheader("余热回收与节能效益")

m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(f"""
    <div class="metric-item">
        <div class="label">总能耗</div>
        <div class="value">{best['能耗']:.1f}</div>
        <div class="label">kWh/吨</div>
    </div>
    """, unsafe_allow_html=True)
with m_col2:
    st.markdown(f"""
    <div class="metric-item">
        <div class="label">系统节能率</div>
        <div class="value">{best['系统节能率']:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)
with m_col3:
    st.markdown(f"""
    <div class="metric-item">
        <div class="label">净能耗（回收后）</div>
        <div class="value">{best['净能耗']:.1f}</div>
        <div class="label">kWh/吨</div>
    </div>
    """, unsafe_allow_html=True)
with m_col4:
    st.markdown(f"""
    <div class="metric-item">
        <div class="label">碳排放</div>
        <div class="value">{best['碳排放']:.1f}</div>
        <div class="label">kg/吨</div>
    </div>
    """, unsafe_allow_html=True)