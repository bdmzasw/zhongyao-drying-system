import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 安全数字转换 =====================
def safe_float(value, default=0.0):
    if pd.isna(value) or value == "-":
        return default
    s = str(value).strip()
    if "~" in s or "-" in s:
        try:
            sep = "~" if "~" in s else "-"
            a, b = s.split(sep)
            return (float(a.strip()) + float(b.strip())) / 2
        except:
            return default
    try:
        return float(s)
    except:
        return default

# ===================== 自动兼容编码读取 =====================
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
techs_df = data["techs"]
regions_df = data["regions"]
carbon_df = data["carbon"]
lcc_df = data["lcc"]

# ===================== 页面 =====================
st.set_page_config(page_title="工艺推荐", layout="wide")
st.markdown("""
<style>
.stApp { background-color: #f5f9f5; }
[data-testid="stSidebarNav"] { display: none; }
.stage-card {
    background: #ffffff;
    border-radius: 10px;
    padding: 16px;
    margin: 10px 0;
    border-left: 5px solid #1890ff;
}
.highlight {
    color: #fa8c16;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

if st.button("🏠 返回主页"):
    st.switch_page("Home.py")

# ===================== 侧边栏全局联动 =====================
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

    elec_price = st.number_input(
        "⚡ 电价（元/kWh）",
        value=st.session_state.get("electricity_price", 0.6), step=0.01
    )

    annual_output = st.number_input(
        "📦 年处理量（吨/年）",
        value=st.session_state.get("annual_capacity", 400), step=50
    )

    recovery_rate = st.slider("♻️ 余热回收效率 %", 0, 80, 30)

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = elec_price
    st.session_state["annual_capacity"] = annual_output

    st.markdown("---")
    st.caption("✅ 全系统同步生效")

# ===================== 主页面 =====================
st.title("工艺参数与方案推荐")
st.markdown("""
基于多目标决策模型，综合品质、效率、能耗、碳排放、成本与投资回报进行工艺优选。
""")
st.divider()

# ===================== 读取全局权重（来自主页）=====================
default_weights = [0.40, 0.20, 0.20, 0.05, 0.10, 0.05]
w1, w2, w3, w4, w5, w6 = st.session_state.get("weights", default_weights)
total = sum([w1, w2, w3, w4, w5, w6])
w1n, w2n, w3n, w4n, w5n, w6n = [x / total for x in [w1, w2, w3, w4, w5, w6]]

# ===================== 计算逻辑 =====================
if selected_herb == "请选择" or selected_area == "请选择":
    st.info("👈 请先选择药材与产区")
    st.stop()

st.subheader("📊 基础工艺参数计算")
herb_row = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
init_mc = safe_float(herb_row["鲜品初始含水率(%)"])
final_mc = safe_float(herb_row["药典规定成品含水率(%)"])
water_removed = 1000 * (init_mc - final_mc) / (100 - final_mc)
st.write(f"**{selected_herb} | {selected_area}**")
st.success(f"每吨脱水量：{water_removed:.1f} kg")

region_row = regions_df[regions_df["产区名称"] == selected_area].iloc[0]
province = region_row["所辖主要省市"].split("、")[0]
carbon_factor = 0.55
cf_match = carbon_df[carbon_df.iloc[:,0] == province]
if not cf_match.empty:
    carbon_factor = safe_float(cf_match.iloc[0,2])
st.write(f"📌 碳排放因子：{carbon_factor:.2f} kgCO₂/kWh")

st.divider()
st.subheader("🔎 各工艺综合评价结果")

# ===================== 工艺计算 =====================
result = []
for _, tech_row in techs_df.iterrows():
    tech_name = tech_row["干燥技术"]
    unit_energy = safe_float(tech_row["单位能耗(kWh/kg水)"])
    total_energy = water_removed * unit_energy
    electricity_cost = total_energy * elec_price
    carbon_emission = total_energy * carbon_factor
    retention = safe_float(tech_row["有效成分保留率(%)"])
    dry_time = safe_float(tech_row["干燥时间范围 (h)"])

    try:
        match = lcc_df[lcc_df["干燥模式"].str.contains(tech_name[:4], na=False)]
        if match.empty:
            match = lcc_df[lcc_df["干燥模式"].str.contains("组合", na=False)]
        lcc_row = match.iloc[0]
    except:
        lcc_row = lcc_df.iloc[0]

    invest = safe_float(lcc_row["设备初始投资(元/台套)"])
    years = safe_float(lcc_row["年折旧年限(年)"])
    labor_year = safe_float(lcc_row["年人工成本(元/年)"])
    om_year = safe_float(lcc_row["年运维耗材费(元/年)"])
    residue_rate = safe_float(lcc_row["残值率(%)"])
    payback = safe_float(lcc_row.get("投资回收期(年)", 5))

    deprec_cost = (invest * (1 - residue_rate/100) / years) / annual_output
    labor_cost = labor_year / annual_output
    om_cost = om_year / annual_output
    total_cost = deprec_cost + labor_cost + om_cost + electricity_cost

    result.append({
        "干燥技术": tech_name,
        "有效成分保留率(%)": round(retention,1),
        "干燥时间(h)": round(dry_time,1),
        "总能耗(kWh/吨)": round(total_energy,1),
        "碳排放(kg/吨)": round(carbon_emission,1),
        "单位总成本(元/吨)": round(total_cost,1),
        "投资回收期(年)": round(payback,1)
    })

df = pd.DataFrame(result)

# ===================== 归一化 =====================
def normalize(s, reverse):
    if s.max() == s.min():
        return pd.Series([0.5]*len(s))
    return (s.max() - s) / (s.max() - s.min()) if reverse else (s - s.min()) / (s.max() - s.min())

df["品质"] = normalize(df["有效成分保留率(%)"], False)
df["时间"] = normalize(df["干燥时间(h)"], True)
df["能耗"] = normalize(df["总能耗(kWh/吨)"], True)
df["碳排"] = normalize(df["碳排放(kg/吨)"], True)
df["成本"] = normalize(df["单位总成本(元/吨)"], True)
df["回收"] = normalize(df["投资回收期(年)"], True)

df["综合得分"] = (w1n * df["品质"] + w2n * df["时间"] + w3n * df["能耗"] +
                  w4n * df["碳排"] + w5n * df["成本"] + w6n * df["回收"]).round(2)

df = df.sort_values("综合得分", ascending=False)
st.dataframe(df[["干燥技术","有效成分保留率(%)","干燥时间(h)","总能耗(kWh/吨)",
                 "碳排放(kg/吨)","单位总成本(元/吨)","投资回收期(年)","综合得分"]], use_container_width=True)

best = df.iloc[0]
st.success(f"🏆 最优推荐：{best['干燥技术']}（得分：{best['综合得分']}）")

# ==========================================================================================
# 美观版分段干燥
# ==========================================================================================
st.divider()
st.subheader("📋 分段式干燥工艺推荐")

def get_stage_info(m):
    if m >= 60:
        return "第一阶段：强脱水段", "≥60%", "热风/热泵强通风", "35～45℃", "高速", "#f5222d"
    elif 30 <= m < 60:
        return "第二阶段：稳定干燥段", "30%~60%", "热泵干燥", "28～35℃", "中速", "#1890ff"
    else:
        return "第三阶段：缓苏定色段", "12%~30%", "低温/真空辅助", "20～28℃", "低速", "#52c41a"

for mc in [70, 45, 20]:
    stage, interval, tech, temp, wind, color = get_stage_info(mc)
    with st.container():
        st.markdown(f"""
<div class="stage-card" style="border-left-color:{color}">
<h4 style="margin:0;color:{color}">{stage}</h4>
<p>区间：{interval}</p>
<p>推荐工艺：<span class='highlight'>{tech}</span></p>
<p>温度：{temp} | 风速：{wind}</p>
</div>
""", unsafe_allow_html=True)

# 余热回收
best_eng = best["总能耗(kWh/吨)"]
recovered = best_eng * recovery_rate / 100
st.divider()
st.subheader("♻️ 余热回收与节能效益")
c1,c2,c3 = st.columns(3)
c1.metric("总能耗", f"{best_eng:.1f} kWh")
c2.metric("可回收余热", f"{recovered:.1f} kWh")
c3.metric("节能率", f"{recovered/best_eng*100:.1f}%")

# ==========================================================================================
# 最终工艺方案
# ==========================================================================================
st.divider()
st.subheader("📄 最终干燥工艺优化方案")

herb_data = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
stage1_switch = safe_float(herb_data.get("一段切换含水率(%)", 60))
stage2_switch = safe_float(herb_data.get("二段切换/终点含水率(%)", 30))

st.markdown(f"""
### 🌿 {selected_herb} 干燥工艺方案
**推荐最优工艺：{best['干燥技术']}**

### 三段式干燥路径
1. **强脱水段**
   区间：≥ {stage1_switch}%
   工艺：快速脱水，提高效率
2. **稳定干燥段**
   区间：{stage2_switch}% ~ {stage1_switch}%
   工艺：恒温干燥，保护成分
3. **缓苏定色段**
   区间：≤ {stage2_switch}%
   工艺：低温缓干，稳定品质

### 节能与环保效益
- 单位能耗：{best_eng:.1f} kWh/吨
- 碳排放量：{best['碳排放(kg/吨)']:.1f} kg/吨
- 节能率：{recovered/best_eng*100:.1f}%

本方案基于药典标准、文献参数与行业规范综合生成，适用于规模化生产与工艺优化。
""")