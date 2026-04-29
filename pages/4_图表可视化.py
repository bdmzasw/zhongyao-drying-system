import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
        "lcc": read_csv_safe("data/LCC经济成本库-干燥设备对比.csv"),
        "heat_recovery": read_csv_safe("data/余热回收技术对比表.csv"),
        "kinetics": read_csv_safe("data/干燥动力学.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]
lcc_df = data["lcc"]
heat_recovery_df = data["heat_recovery"]
kinetics_df = data["kinetics"]

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
st.set_page_config(page_title="图表可视化", layout="wide")
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
    .kinetics-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border-left: 4px solid #4CAF50;
    }
    .kinetics-card h4 { margin: 0 0 0.6rem 0; color: #2d4a32; font-weight: 600; }
    .kinetics-card .param { display: flex; justify-content: space-between; margin: 0.3rem 0; }
    .kinetics-card .param .label { color: #555; }
    .kinetics-card .param .value { font-weight: 600; color: #1e3b2a; }
    .kinetics-card .sub { font-size: 0.85rem; color: #777; margin-top: 0.5rem; }
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

    # 折叠权重
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

st.title("图表可视化分析")
if selected_herb == "请选择" or selected_area == "请选择":
    st.info("请选择药材与产区")
    st.stop()

# 药材与产区数据
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = extract_number(herb_row["鲜品初始含水率(%)"])
final_mc = extract_number(herb_row["药典规定成品含水率(%)"])
water_removed = calc_water_removed(init_mc, final_mc)

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

# 计算所有技术指标
results = []
for _, tech in techs_df.iterrows():
    tech_name = tech["干燥技术"]
    unit_energy = extract_number(tech["单位能耗(kWh/kg水)"])
    total_energy = water_removed * unit_energy
    recovery = RECOVERY_RATES.get(tech_name, 0.0)
    net_energy = total_energy * (1 - recovery)
    electricity_cost = net_energy * elec_price
    carbon_emission_ton = net_energy * carbon_factor
    carbon_cost = carbon_emission_ton * 60 / 1000
    retention = extract_number(tech["有效成分保留率(%)"]) / 100
    dry_time = extract_number(tech["干燥时间范围 (h)"])

    matched_lcc = LCC_MAP.get(tech_name, tech_name)
    lcc_match = lcc_df[lcc_df["干燥模式"] == matched_lcc]
    if lcc_match.empty:
        lcc_match = lcc_df.iloc[[0]]
    lcc_r = lcc_match.iloc[0]
    invest = extract_number(lcc_r["设备初始投资(元/台套)"])
    years = extract_number(lcc_r["年折旧年限(年)"])
    labor_year = extract_number(lcc_r["年人工成本(元/年)"])
    om_year = extract_number(lcc_r["年运维耗材费(元/年)"])
    residue = extract_number(lcc_r["残值率(%)"])
    deprec_ton = (invest * (1 - residue/100) / years) / annual_output
    labor_ton = labor_year / annual_output
    om_ton = om_year / annual_output
    total_cost = deprec_ton + labor_ton + om_ton + electricity_cost + carbon_cost

    results.append({
        "干燥技术": tech_name,
        "保留率": retention,
        "时间": dry_time,
        "能耗": total_energy,
        "净能耗": net_energy,
        "碳排放": carbon_emission_ton,
        "总成本": total_cost,
        "回收期": years,
        "折旧": deprec_ton,
        "人工": labor_ton,
        "运维": om_ton,
        "电费": electricity_cost,
        "碳成本": carbon_cost
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

# ===================== 综合得分排名 =====================
st.subheader("综合得分排名")
fig_bar = px.bar(df, x="干燥技术", y="综合得分", text="综合得分",
                 color="综合得分", color_continuous_scale="RdYlGn")
fig_bar.update_traces(texttemplate='%{text:.3f}', textposition='outside')
fig_bar.update_layout(yaxis_title="综合得分", xaxis_title="")
st.plotly_chart(fig_bar, use_container_width=True)

# ===================== 雷达图（可选择技术）=====================
st.subheader("技术六维指标对比")
st.caption("选择要查看的技术，雷达图随侧边栏权重实时更新")
tech_options = df["干燥技术"].tolist()
default_tech = tech_options[0] if tech_options else None
selected_tech_radar = st.selectbox("选择技术", tech_options, index=0)
tech_radar = df[df["干燥技术"] == selected_tech_radar].iloc[0]
categories = ['品质', '时间', '能耗', '碳排', '成本', '回收']
values = [tech_radar['品质分'], tech_radar['时间分'], tech_radar['能耗分'],
          tech_radar['碳排分'], tech_radar['成本分'], tech_radar['回收分']]
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(
    r=values, theta=categories, fill='toself',
    name=selected_tech_radar, line_color='#2d4a32'
))
fig_radar.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    showlegend=True
)
st.plotly_chart(fig_radar, use_container_width=True)

# ===================== 热力图 =====================
st.subheader("技术×指标热力图（归一化得分）")
heatmap_df = df[["干燥技术", "品质分", "时间分", "能耗分", "碳排分", "成本分", "回收分"]].set_index("干燥技术")
fig_heat = px.imshow(heatmap_df, text_auto=True, aspect="auto", color_continuous_scale="RdYlGn",
                     labels=dict(x="指标", y="技术", color="得分"))
fig_heat.update_layout(margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_heat, use_container_width=True)

# ===================== 气泡图（品质-碳排放-成本）=====================
st.subheader("品质-碳排放-成本 气泡图")
st.caption("X轴碳排放、Y轴保留率、气泡大小=总成本、颜色=综合得分")
fig_bubble = px.scatter(df, x="碳排放", y="保留率", size="总成本", color="综合得分",
                        hover_name="干燥技术", size_max=45,
                        color_continuous_scale="RdYlGn")
fig_bubble.update_layout(xaxis_title="碳排放 (kg/吨)", yaxis_title="有效成分保留率")
st.plotly_chart(fig_bubble, use_container_width=True)

# ===================== 成本构成堆叠柱状图 =====================
st.subheader("各技术成本构成（元/吨）")
cost_df = df[["干燥技术", "折旧", "人工", "运维", "电费", "碳成本"]].set_index("干燥技术")
fig_cost = px.bar(cost_df, x=cost_df.index, y=cost_df.columns,
                  title="成本构成（元/吨）", labels={"value": "元/吨", "variable": "成本项"})
fig_cost.update_layout(barmode='stack', xaxis_title="", yaxis_title="元/吨")
st.plotly_chart(fig_cost, use_container_width=True)

# ===================== 干燥动力学卡片 =====================
st.subheader("干燥动力学参数")
st.caption("活化能越低表示干燥越容易进行，扩散系数越高表示水分迁移越快")
if not kinetics_df.empty:
    kinetics_df["活化能_数值"] = kinetics_df["干燥活化能(kJ/mol)"].apply(extract_number)
    kinetics_df["扩散系数_数值"] = kinetics_df["有效水分扩散系数(m2/s)"].apply(extract_number)
    herb_name_short = selected_herb.replace("（", "(").replace("）", ")")
    kdf_filter = kinetics_df[kinetics_df["药材名称"].str.contains(herb_name_short[:2])]
    if not kdf_filter.empty:
        cols = st.columns(min(len(kdf_filter), 3))
        for i, (_, row) in enumerate(kdf_filter.iterrows()):
            with cols[i % 3]:
                r2_value = row.get("拟合R2", row.get("拟合R²", "-"))
                st.markdown(f"""
                <div class="kinetics-card">
                    <h4>{row['干燥技术']}</h4>
                    <div class="param"><span class="label">活化能</span><span class="value">{row['活化能_数值']:.2f} kJ/mol</span></div>
                    <div class="param"><span class="label">扩散系数</span><span class="value">{row['扩散系数_数值']:.2e} m²/s</span></div>
                    <div class="sub">模型：{row.get('最适动力学模型', '-')} R²：{r2_value}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("暂无该药材的干燥动力学数据")
else:
    st.warning("干燥动力学数据未加载")

st.caption("数据基于药典、技术库与文献动力学参数")