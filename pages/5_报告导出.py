import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import re
from datetime import datetime
import base64
from io import BytesIO
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

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
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    except:
        df = pd.read_csv(path, encoding="gbk", dtype=str)
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

def find_kinetics(herb_name, tech_name):
    herb_core = re.sub(r'[（(].*[）)]', '', herb_name).strip()
    tech_core = re.sub(r'[（(].*[）)]', '', tech_name).strip()
    mask_herb = kinetics_df["药材名称"].str.contains(herb_core[:4], na=False)
    candidates = kinetics_df[mask_herb]
    if candidates.empty:
        return None
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
            return matched.iloc[0]
    return candidates.iloc[0]

# ===================== 页面配置（统一风格） =====================
st.set_page_config(page_title="报告导出", layout="wide")
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
        border-radius: 12px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(80,120,80,0.08);
        border-left: 5px solid;
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
    annual_output = st.number_input("年处理量（吨/年）", value=st.session_state.get("annual_output", 400), step=50)

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
    st.session_state["annual_output"] = annual_output

st.title("中药材干燥工艺决策报告")
st.caption("基于最优推荐结果，一键生成专业 Word 报告")

if selected_herb == "请选择" or selected_area == "请选择":
    st.info("请选择药材与产区")
    st.stop()

# ===================== 数据计算 =====================
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = extract_number(herb_row["鲜品初始含水率(%)"])
final_mc = extract_number(herb_row["药典规定成品含水率(%)"])
water_removed_per_ton = calc_water_removed(init_mc, final_mc)

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

results = []
for _, tech in techs_df.iterrows():
    tech_name = tech["干燥技术"]
    unit_energy = extract_number(tech["单位能耗(kWh/kg水)"])
    total_energy = water_removed_per_ton * unit_energy
    recovery = RECOVERY_RATES.get(tech_name, 0.0)
    net_energy = total_energy * (1 - recovery)
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
        "折旧": deprec,
        "人工": labor_c,
        "运维": om_c,
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

best = df.iloc[0]
second_best = df.iloc[1] if len(df) > 1 else best

herb_taboo = herb_row.get("干燥禁忌提示", "无")
herb_comp = herb_row.get("主要有效成分类型", "无")
herb_stability = herb_row.get("有效成分热稳定性(高/中/低)", "未知")

# 分段参数
best_tech_row = techs_df[techs_df["干燥技术"] == best["干燥技术"]].iloc[0]
stage1_switch = extract_number(herb_row.get("一段切换含水率(%)", 60))
stage2_switch = extract_number(herb_row.get("二段切换/终点含水率(%)", 30))

def clean_str(val):
    s = str(val).strip()
    return s if s and s != 'nan' else '—'

t1_range = clean_str(best_tech_row.get("一段干燥温度(℃)", "—"))
v1_range = clean_str(best_tech_row.get("一段干燥风速(m/s)", "—"))
t2_range = clean_str(best_tech_row.get("二段干燥温度(℃)", "—"))
v2_range = clean_str(best_tech_row.get("二段干燥风速(m/s)", "—"))

t3_raw = best_tech_row.get("三段干燥温度(℃)")
has_third = pd.notna(t3_raw) and str(t3_raw).strip() not in ["", "—", "-", "nan"]
if has_third:
    t3_range = clean_str(t3_raw)
    v3_range = clean_str(best_tech_row.get("三段干燥风速(m/s)", "—"))
else:
    t3_range = "—"
    v3_range = "—"

best_recovery_rate = RECOVERY_RATES.get(best["干燥技术"], 0.0) * 100
kinetics_row = find_kinetics(selected_herb, best["干燥技术"])

# ===================== 预览 =====================
with st.expander("报告实时预览", expanded=True):
    st.markdown(f"## 中药材低碳干燥工艺决策报告")
    st.markdown(f"**药材**：{selected_herb}　|　**产地**：{selected_area}　|　**年处理量**：{annual_output} 吨")
    st.divider()
    st.markdown("### 一、药材基础信息")
    st.markdown(f"""
    - 初始含水率：**{init_mc:.1f}%** → 目标含水率：**{final_mc:.1f}%**
    - 吨脱水量：**{water_removed_per_ton:.1f} kg**
    - 有效成分：**{herb_comp}**（热稳定性：**{herb_stability}**）
    - 禁忌：**{herb_taboo}**
    """)

    st.divider()
    st.markdown("### 二、推荐方案")
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"**主方案：{best['干燥技术']}**")
        st.markdown(f"""
        - 保留率：**{best['保留率']*100:.1f}%**
        - 净能耗：**{best['净能耗']:.1f}** kWh/吨
        - 综合得分：**{best['综合得分']}**
        """)
    with c2:
        st.info(f"**备选方案：{second_best['干燥技术']}**")
        st.markdown(f"""
        - 保留率：**{second_best['保留率']*100:.1f}%**
        - 净能耗：**{second_best['净能耗']:.1f}** kWh/吨
        - 综合得分：**{second_best['综合得分']}**
        """)

    st.divider()
    st.markdown("### 三、最优技术分段干燥参数")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stage-card" style="border-left-color:#e67e22">
            <h4>1. 强脱水段</h4>
            <p>含水率 ≥ {stage1_switch}%</p>
            <p>温度：{t1_range} ℃</p>
            <p>风速：{v1_range} m/s</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stage-card" style="border-left-color:#3498db">
            <h4>2. 稳定干燥段</h4>
            <p>含水率 {stage2_switch}%~{stage1_switch}%</p>
            <p>温度：{t2_range} ℃</p>
            <p>风速：{v2_range} m/s</p>
        </div>
        """, unsafe_allow_html=True)
    if has_third:
        st.markdown(f"""
        <div class="stage-card" style="border-left-color:#2ecc71">
            <h4>3. 缓苏定色段</h4>
            <p>含水率 ≤ {stage2_switch}%</p>
            <p>温度：{t3_range} ℃</p>
            <p>风速：{v3_range} m/s</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 四、余热回收")
    st.write(f"系统节能率：**{best_recovery_rate:.1f}%**")

    st.divider()
    st.markdown("### 五、全技术对比")
    display_df = df[["干燥技术","保留率","时间","净能耗","碳排放","总成本","综合得分"]]
    num_cols = display_df.select_dtypes(include='number').columns.tolist()
    st.dataframe(display_df.style.format({col: "{:.3f}" for col in num_cols}), use_container_width=True)

    st.divider()
    st.markdown("### 六、年度成本构成")
    annual_factors = {
        "设备折旧": best["折旧"] * annual_output,
        "人工": best["人工"] * annual_output,
        "运维耗材": best["运维"] * annual_output,
        "电费": best["电费"] * annual_output,
        "碳交易成本": best["碳成本"] * annual_output
    }
    total_annual = sum(annual_factors.values())
    for item, val in annual_factors.items():
        st.write(f"- {item}：{val:.2f} 元 ({val/total_annual*100:.1f}%)")
    st.markdown(f"**年度总成本：{total_annual:.2f} 元**")

    st.divider()
    st.markdown("### 七、评价权重")
    st.write(f"品质 {w1n:.2f}　时间 {w2n:.2f}　能耗 {w3n:.2f}　碳排放 {w4n:.2f}　成本 {w5n:.2f}　回收期 {w6n:.2f}")

    if kinetics_row is not None:
        st.divider()
        st.markdown("### 八、干燥动力学")
        st.write(f"模型：{kinetics_row.get('最适动力学模型', '-')}")
        st.write(f"扩散系数：{kinetics_row.get('有效水分扩散系数(m2/s)', '-')}")
        st.write(f"活化能：{kinetics_row.get('干燥活化能(kJ/mol)', '-')} kJ/mol")
        st.write(f"R²：{kinetics_row.get('拟合R2', '-')}")

# ===================== Word 导出 =====================
def create_word_report():
    doc = Document()

    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    style = doc.styles['Normal']
    style.font.name = 'SimSun'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), 'SimSun')
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.15

    header = section.header
    header.paragraphs[0].text = "中药材低碳干燥工艺决策报告"
    header.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer = section.footer
    footer.paragraphs[0].text = "中药干燥智能决策系统"
    footer.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER

    title = doc.add_heading("中药材低碳干燥工艺决策报告", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"生成日期：{datetime.now().strftime('%Y-%m-%d')}")
    doc.add_paragraph(f"药材：{selected_herb}    产地：{selected_area}    年处理量：{annual_output} 吨")

    doc.add_heading("一、药材基础信息", level=1)
    doc.add_paragraph(f"初始含水率：{init_mc:.1f}% → 目标含水率：{final_mc:.1f}%")
    doc.add_paragraph(f"吨脱水量：{water_removed_per_ton:.1f} kg")
    doc.add_paragraph(f"有效成分：{herb_comp}，热稳定性：{herb_stability}")
    doc.add_paragraph(f"禁忌：{herb_taboo}")

    doc.add_heading("二、推荐方案", level=1)
    doc.add_heading("1. 主方案（综合最优）", level=2)
    doc.add_paragraph(f"工艺：{best['干燥技术']}")
    doc.add_paragraph(f"保留率：{best['保留率']*100:.1f}%")
    doc.add_paragraph(f"净能耗：{best['净能耗']:.1f} kWh/吨")
    doc.add_paragraph(f"综合得分：{best['综合得分']}")

    doc.add_heading("2. 备选方案", level=2)
    doc.add_paragraph(f"工艺：{second_best['干燥技术']}")
    doc.add_paragraph(f"保留率：{second_best['保留率']*100:.1f}%")
    doc.add_paragraph(f"净能耗：{second_best['净能耗']:.1f} kWh/吨")
    doc.add_paragraph(f"综合得分：{second_best['综合得分']}")

    # 三、分段干燥参数
    doc.add_heading("三、最优技术分段干燥参数", level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Light Grid Accent 1'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_cells = table.rows[0].cells
    headers = ["干燥阶段", "含水率范围", "温度 (℃)", "风速 (m/s)"]
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        hdr_cells[i].paragraphs[0].runs[0].font.bold = True

    data_rows = [
        ["强脱水段", f"≥{stage1_switch}%", t1_range, v1_range],
        ["稳定干燥段", f"{stage2_switch}%~{stage1_switch}%", t2_range, v2_range]
    ]
    if has_third:
        data_rows.append(["缓苏定色段", f"≤{stage2_switch}%", t3_range, v3_range])

    for row_data in data_rows:
        row_cells = table.add_row().cells
        for j, val in enumerate(row_data):
            row_cells[j].text = val

    doc.add_heading("四、余热回收", level=1)
    doc.add_paragraph(f"系统节能率：{best_recovery_rate:.1f}%")

    doc.add_heading("五、全技术对比表", level=1)
    table2 = doc.add_table(rows=1, cols=6)
    table2.style = 'Light Grid Accent 1'
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr2 = table2.rows[0].cells
    headers2 = ["干燥技术", "保留率", "净能耗(kWh/吨)", "碳排放(kg/吨)", "总成本(元/吨)", "综合得分"]
    for i, h in enumerate(headers2):
        hdr2[i].text = h
        hdr2[i].paragraphs[0].runs[0].font.bold = True
    for _, row in df.iterrows():
        row_cells = table2.add_row().cells
        row_cells[0].text = str(row["干燥技术"])
        row_cells[1].text = f"{row['保留率']*100:.1f}%"
        row_cells[2].text = f"{row['净能耗']:.1f}"
        row_cells[3].text = f"{row['碳排放']:.1f}"
        row_cells[4].text = f"{row['总成本']:.1f}"
        row_cells[5].text = f"{row['综合得分']:.4f}"

    doc.add_heading("六、年度成本构成", level=1)
    doc.add_paragraph(f"基于年处理量 {annual_output} 吨估算：")
    annual_factors = {
        "折旧": best["折旧"] * annual_output,
        "人工": best["人工"] * annual_output,
        "运维": best["运维"] * annual_output,
        "电费": best["电费"] * annual_output,
        "碳成本": best["碳成本"] * annual_output
    }
    total_annual = sum(annual_factors.values())
    for k, v in annual_factors.items():
        doc.add_paragraph(f"• {k}：{v:.2f} 元 ({v/total_annual*100:.1f}%)")
    doc.add_paragraph(f"年度总成本：{total_annual:.2f} 元")

    doc.add_heading("七、评价权重", level=1)
    doc.add_paragraph(f"品质 {w1n:.2f}，时间 {w2n:.2f}，能耗 {w3n:.2f}，碳排放 {w4n:.2f}，成本 {w5n:.2f}，回收期 {w6n:.2f}")

    if kinetics_row is not None:
        doc.add_heading("八、干燥动力学参考", level=1)
        doc.add_paragraph(f"模型：{kinetics_row.get('最适动力学模型', '-')}")
        doc.add_paragraph(f"扩散系数：{kinetics_row.get('有效水分扩散系数(m2/s)', '-')}")
        doc.add_paragraph(f"活化能：{kinetics_row.get('干燥活化能(kJ/mol)', '-')} kJ/mol")
        doc.add_paragraph(f"R²：{kinetics_row.get('拟合R2', '-')}")

    doc.add_heading("九、结论与建议", level=1)
    doc.add_paragraph(f"1. 优先推荐采用“{best['干燥技术']}”工艺，综合评分最高。")
    doc.add_paragraph(f"2. 若设备受限或生产任务紧急，可暂用“{second_best['干燥技术']}”作为替代。")
    doc.add_paragraph("3. 建议在实际生产中根据季节、原料批次微调干燥参数，以达到最佳品质与能耗平衡。")

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

word_file = create_word_report()
b64 = base64.b64encode(word_file.getvalue()).decode()
href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="中药材干燥报告_{selected_herb}.docx">下载完整 Word 报告</a>'
st.markdown(href, unsafe_allow_html=True)