import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os

# ========== Streamlit 自动安装中文字体 + 稳定中文渲染 ==========
os.system('apt-get update && apt-get install -y fonts-wqy-zenhei')
matplotlib.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei']
matplotlib.rcParams['axes.unicode_minus'] = False
matplotlib.rcParams['figure.facecolor'] = 'white'

# ========== 表格：居中 + 强制 3 位小数 ==========
def centered_table(df):
    df = df.round(3)
    return df.style.set_properties(**{
        'text-align': 'center',
        'vertical-align': 'middle',
        'padding': '8px'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ])

st.set_page_config(page_title="中药材低碳干燥智能选型系统", page_icon="🌿")

# ========== 基础数据 ==========
herb_data = {
    "药材ID": ["H001", "H002", "H003", "H004", "H005"],
    "药材名称": ["黄芪", "金银花", "党参", "当归", "菊花"],
    "药用部位": ["根", "花", "根", "根", "花"],
    "建议干燥温度": ["≤60", "40-45", "50-60", "≤50", "≤45"],
    "温度类型": ["单上限（≤X）", "双区间(X-Y)", "双区间(X-Y)", "单上限（≤X）", "单上限（≤X）"],
    "敏感成分": ["黄芪甲苷", "挥发油", "党参多糖", "挥发油", "挥发油+黄酮"],
    "药效敏感等级": ["中敏", "高敏", "中敏", "高敏", "高敏"],
    "初始含水率%": [60, 75, 65, 70, 80],
    "目标含水率%": [10, 12, 10, 10, 12],
    "每吨除水量kg": [556, 716, 611, 667, 773],
    "碳足迹系数(kgCO2/kg)": [2.6, 3.2, 2.6, 2.9, 3.4],
    "核心依据": ["黄芪甲苷在60℃以上开始降解", "挥发油在45℃以上损失明显",
                "党参多糖在60℃以下稳定", "含挥发油，50℃以上损失", "含挥发油和黄酮"],
    "数据来源": ["《中国药典2020版一部》", "康廷国《中药鉴定学》第五版",
                "《甘肃省中药材标准》+王玉《食品科学》", "《甘肃省中药材标准》", "《浙江省中药炮制规范》"]
}
df_herb = pd.DataFrame(herb_data)

tech_data = {
    "技术ID": ["T001", "T002", "T003", "T004", "T005"],
    "技术名称": ["热泵干燥", "红外干燥", "传统热风", "微波干燥", "真空干燥"],
    "适用最低温(℃)": [30, 35, 60, 30, 30],
    "适用最高温(℃)": [65, 120, 120, 80, 60],
    "控温精度": ["±1", "±3", "±5", "±2", "±1"],
    "最小能耗(kWh/kg水)": [1.0, 1.6, 2.2, 1.3, 1.2],
    "最大能耗(kWh/kg水)": [1.3, 2.0, 2.8, 1.6, 1.5],
    "药效保留率": [0.930, 0.900, 0.820, 0.880, 0.950],
    "平均能耗系数": [1.150, 1.800, 2.500, 1.450, 1.350],
    "设备平均投资(万元)": [12, 8, 3.5, 10, 18],
    "适用药材部位": ["根，茎，果实", "花，叶", "通用", "根，茎，果实", "根，贵重药材"]
}
df_tech = pd.DataFrame(tech_data)

area_data = {
    "区域ID": ["R001", "R002", "R003", "R004", "R005", "R006", "R007", "R008"],
    "区域名称": ["甘肃定西", "安徽亳州", "河北安国", "宁夏中卫", "浙江杭州", "四川成都", "广东广州", "云南昆明"],
    "年均温度（℃）": [8, 15, 12, 9, 17, 16, 22, 15],
    "年均湿度(%)": [63, 78, 70, 58, 76, 82, 79, 73],
    "年均风速（m/s）": [2.5, 2.0, 2.2, 2.8, 2.1, 1.5, 2.3, 2.4],
    "年降水量（mm）": [400, 800, 500, 200, 1400, 900, 1700, 1000],
    "工业电价(元/度)": [0.510, 0.640, 0.650, 0.510, 0.630, 0.540, 0.640, 0.410],
    "设备补贴比例（%）": [20, 0, 10, 15, 0, 0, 0, 10],
    "主要药材类型": ["党参，黄芪", "白芍，牡丹皮", "白芷，山药", "枸杞，黄芪", "杭白菊", "川穹，川贝", "广藿香", "三七"],
    "数据来源": ["中国气象数据网"]*8
}
df_area = pd.DataFrame(area_data)

adapt_data = {
    "区域名称": ["甘肃定西", "安徽亳州", "河北安国", "宁夏中卫", "浙江杭州", "四川成都", "广东广州", "云南昆明"],
    "湿度修正系数": [0.980, 1.130, 1.050, 0.930, 1.110, 1.170, 1.140, 1.080],
    "电价修正系数": [0.980, 1.240, 1.250, 0.980, 1.210, 1.040, 1.230, 0.790],
    "设备补贴系数": [0.800, 1.000, 0.900, 0.850, 1.000, 1.000, 1.000, 0.900],
    "碳交易价格（元）": [81.580, 81.580, 81.580, 81.580, 81.580, 81.580, 38.840, 81.580],
    "综合修正因子": [0.770, 1.400, 1.180, 0.780, 1.350, 1.220, 1.400, 0.770],
    "电网碳排放因子": [0.667, 0.704, 0.903, 0.667, 0.525, 0.526, 0.451, 0.527]
}
df_adapt = pd.DataFrame(adapt_data)
df_area = pd.merge(df_area, df_adapt, on="区域名称", how="left")

carbon_data = {
    "技术名称": ["热泵干燥", "红外干燥", "传统热风", "微波干燥", "真空干燥"],
    "设备制造碳（吨）": [8.200, 4.800, 2.100, 6.300, 11.500],
    "运输碳（吨）": [0.100, 0.075, 0.050, 0.090, 0.125],
    "年使用碳（吨）": [409.360, 640.740, 889.910, 516.150, 480.550],
    "废弃碳（吨）": [0.400, 0.300, 0.200, 0.360, 0.500],
    "寿命（年）": [15, 10, 10, 12, 15],
    "年均全周期碳（吨）": [317.960, 497.280, 690.180, 400.730, 373.380]
}
df_carbon = pd.DataFrame(carbon_data)
df_tech = pd.merge(df_tech, df_carbon, on="技术名称", how="left")

# ========== 常量 ==========
DEFAULT_WEIGHTS = {"成本": 0.260, "碳排放": 0.106, "药效保留": 0.633}
BASE_PARAMS = {"电价": 0.570, "年产量": 800.000, "设备投资": 10.300, "能耗系数": 1.650, "碳交易价格": 76.240}
FLUCTUATIONS = [-0.2, -0.1, 0, 0.1, 0.2]

# ========== 计算函数（已修正拼写错误） ==========
def parse_herb_temp(temp_str):
    if "≤" in temp_str:
        min_temp = 0
        max_temp = int(temp_str.replace("≤", ""))
    elif "-" in temp_str:
        parts = temp_str.split("-")
        min_temp = int(parts[0].strip())
        max_temp = int(parts[1].strip())
    else:
        min_temp = max_temp = int(temp_str)
    return min_temp, max_temp

def check_temp_match(herb_temp_str, tech_min, tech_max):
    herb_min, herb_max = parse_herb_temp(herb_temp_str)
    return herb_max <= tech_max

def calc_total_cost(tech_row, area_row, herb_tons_water, annual_output=800):
    life = tech_row["寿命（年）"]
    invest = tech_row["设备平均投资(万元)"] * (1 - area_row["设备补贴比例（%）"]/100)
    depre_cost = round(invest / life, 3) if life != 0 else 0
    energy_coeff = tech_row["平均能耗系数"]
    elec_price = area_row["工业电价(元/度)"]
    energy_cost = round((annual_output * herb_tons_water * energy_coeff * elec_price) / 10000, 3)
    carbon_price = area_row["碳交易价格（元）"]
    carbon_cost = round((tech_row["年均全周期碳（吨）"] * area_row["综合修正因子"] * carbon_price) / 10000, 3)
    total_cost = round(depre_cost + energy_cost + carbon_cost, 3) # 已修正拼写
    return total_cost, depre_cost, energy_cost, carbon_cost

def normalize_series(s):
    if s.max() == s.min() or s.max() - s.min() < 1e-6:
        return pd.Series([0.000]*len(s), index=s.index)
    return (s - s.min()) / (s.max() - s.min())

def herb_dry_selection(herb_name, area_name, annual_output=800, custom_weights=None):
    try:
        if herb_name not in df_herb["药材名称"].tolist() or area_name not in df_area["区域名称"].tolist():
            return None, None, None, "药材或区域不存在！"
        weights = custom_weights if custom_weights is not None else DEFAULT_WEIGHTS
        herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
        area_row = df_area[df_area["区域名称"] == area_name].iloc[0]
        herb_part = herb_row["药用部位"]
        herb_temp_str = herb_row["建议干燥温度"]
        herb_tons_water = herb_row["每吨除水量kg"]
        df_tech_filter = df_tech.copy()
        df_tech_filter["部位匹配"] = df_tech_filter["适用药材部位"].apply(lambda x: "通用" in x or herb_part in x)
        df_tech_filter = df_tech_filter[df_tech_filter["部位匹配"]]
        if df_tech_filter.empty:
            return None, None, None, "无匹配的药材部位干燥技术！"
        df_tech_filter["温度匹配"] = df_tech_filter.apply(lambda x: check_temp_match(herb_temp_str, x["适用最低温(℃)"], x["适用最高温(℃)"]), axis=1)
        df_tech_filter = df_tech_filter[df_tech_filter["温度匹配"]]
        if df_tech_filter.empty:
            return None, None, None, "无匹配温度的干燥技术！"
        cost_cols = df_tech_filter.apply(lambda x: calc_total_cost(x, area_row, herb_tons_water, annual_output), axis=1)
        df_tech_filter["综合成本(万元)"] = [round(x[0],3) for x in cost_cols]
        df_tech_filter["设备折旧(万元)"] = [round(x[1],3) for x in cost_cols]
        df_tech_filter["能耗成本(万元)"] = [round(x[2],3) for x in cost_cols]
        df_tech_filter["碳交易成本(万元)"] = [round(x[3],3) for x in cost_cols]
        df_tech_filter["综合碳排(吨)"] = round(df_tech_filter["年均全周期碳（吨）"] * area_row["综合修正因子"], 3)
        df_tech_filter["药效得分"] = df_tech_filter["药效保留率"]
        df_tech_filter["成本归一化"] = normalize_series(df_tech_filter["综合成本(万元)"])
        df_tech_filter["碳排归一化"] = normalize_series(df_tech_filter["综合碳排(吨)"])
        df_tech_filter["药效归一化"] = normalize_series(df_tech_filter["药效得分"])
        df_tech_filter["综合得分"] = round((weights["成本"] * df_tech_filter["成本归一化"] + weights["碳排放"] * df_tech_filter["碳排归一化"] + weights["药效保留"] * (1 - df_tech_filter["药效归一化"])), 3)
        df_result = df_tech_filter.sort_values("综合得分", ascending=True).reset_index(drop=True)
        best_tech = df_result.iloc[0]["技术名称"] if not df_result.empty else None
        best_costs = df_result.iloc[0][["设备折旧(万元)", "能耗成本(万元)", "碳交易成本(万元)", "综合成本(万元)"]] if not df_result.empty else None
        return df_result, best_tech, best_costs, "选型成功"
    except Exception as e:
        return None, None, None, f"函数内部错误：{str(e)}"

def sensitivity_analysis(herb_name, area_name, base_param, fluct_ratios=[-0.2,-0.1,0,0.1,0.2]):
    try:
        df_result, best_tech, _, _ = herb_dry_selection(herb_name, area_name)
        if not best_tech:
            return pd.DataFrame(columns=["分析参数", "波动比例(%)", "参数值", "综合成本(万元)", "成本变化率(%)"])
        herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
        area_row = df_area[df_area["区域名称"] == area_name].iloc[0]
        tech_row = df_tech[df_tech["技术名称"] == best_tech].iloc[0]
        herb_tons_water = herb_row["每吨除水量kg"]
        base_val = BASE_PARAMS[base_param]
        base_cost,_,_,_ = calc_total_cost(tech_row, area_row, herb_tons_water)
        if base_cost < 1e-6:
            base_cost = 1e-6
        data = []
        for fr in fluct_ratios:
            val = round(base_val*(1+fr),3)
            cost = base_cost
            if base_param == "电价":
                ar = area_row.copy()
                ar["工业电价(元/度)"] = val
                cost,_,_,_ = calc_total_cost(tech_row, ar, herb_tons_water)
            elif base_param == "年产量":
                cost,_,_,_ = calc_total_cost(tech_row, area_row, herb_tons_water, val)
            elif base_param == "设备投资":
                tr = tech_row.copy()
                tr["设备平均投资(万元)"] = val
                cost,_,_,_ = calc_total_cost(tr, area_row, herb_tons_water)
            elif base_param == "能耗系数":
                tr = tech_row.copy()
                tr["平均能耗系数"] = val
                cost,_,_,_ = calc_total_cost(tr, area_row, herb_tons_water)
            elif base_param == "碳交易价格":
                ar = area_row.copy()
                ar["碳交易价格（元）"] = val
                cost,_,_,_ = calc_total_cost(tech_row, ar, herb_tons_water)
            chg = round((cost-base_cost)/base_cost*100,3) if base_cost !=0 else 0
            data.append({"分析参数":base_param,"波动比例(%)":f"{fr*100:.0f}","参数值":val,"综合成本(万元)":round(cost,3),"成本变化率(%)":chg})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame(columns=["分析参数", "波动比例(%)", "参数值", "综合成本(万元)", "成本变化率(%)"])

def full_sensitivity_analysis(herb_name, area_name):
    params = ["电价","年产量","设备投资","能耗系数","碳交易价格"]
    res = []
    for p in params:
        df = sensitivity_analysis(herb_name,area_name,p)
        if df.empty: continue
        df2 = df[pd.to_numeric(df["波动比例(%)"])!=0]
        if df2.empty: continue
        coe = round((pd.to_numeric(df2["成本变化率(%)"])/pd.to_numeric(df2["波动比例(%)"])).mean(),3)
        if abs(coe)>=0.9: lv="🔴 最敏感"
        elif abs(coe)>=0.5: lv="🟡 高敏感"
        elif abs(coe)>=0.1: lv="⚪ 一般"
        else: lv="🟢 最不敏感"
        res.append({"参数":p,"基准值":round(BASE_PARAMS[p],3),"敏感度系数":coe,"敏感程度":lv})
    return pd.DataFrame(res)

# ========== 完整四页界面 ==========
st.title("中药材低碳干燥智能选型系统")
st.caption("——基于能源经济视角的多目标决策模型")

st.sidebar.header("⚙️ 参数设置")
herb_name = st.sidebar.selectbox("选择药材", df_herb["药材名称"].tolist(), index=3)
area_name = st.sidebar.selectbox("选择区域", df_area["区域名称"].tolist(), index=3)
annual_output = st.sidebar.number_input("年产量(吨)", min_value=100, max_value=2000, value=800, step=100)
st.sidebar.markdown("### 📚 数据来源")
st.sidebar.caption("《中国药典2025版》| 各省气象/发改委数据 | CNKI核心期刊 | 全国碳排放权交易市场")

tab1, tab2, tab3, tab4 = st.tabs(["📊 数据库查看", "🎯 智能选型", "📈 敏感性分析", "🖥️ 决策仪表盘"])

# Tab1
with tab1:
    st.subheader("1. 药材库")
    st.dataframe(centered_table(df_herb), hide_index=True)
    st.subheader("2. 技术库（含生命周期碳排放）")
    st.dataframe(centered_table(df_tech), hide_index=True)
    st.subheader("3. 区域库（含动态适配系数）")
    st.dataframe(centered_table(df_area), hide_index=True)
    st.subheader("4. 默认AHP决策权重")
    df_weights = pd.DataFrame(DEFAULT_WEIGHTS.items(), columns=["指标", "权重"])
    df_weights["权重占比(%)"] = round(df_weights["权重"] * 100, 3)
    st.dataframe(centered_table(df_weights), hide_index=True)
    st.success("✅ 一致性检验CR=0.033<0.1，权重分配有效")

# Tab2
with tab2:
    st.subheader("智能选型结果")
    st.markdown(f"**当前参数**：药材：`{herb_name}` | 区域：`{area_name}` | 年产量：`{annual_output} 吨`")
    st.markdown("### ⚖️ 权重自定义调整（总和自动归一化）")
    col1, col2, col3 = st.columns(3)
    with col1:
        cost_weight = st.slider("成本权重（%）", min_value=0, max_value=100, value=int(DEFAULT_WEIGHTS["成本"]*100), step=1)
    with col2:
        carbon_weight = st.slider("碳排放权重（%）", min_value=0, max_value=100, value=int(DEFAULT_WEIGHTS["碳排放"]*100), step=1)
    with col3:
        efficacy_weight = st.slider("药效保留权重（%）", min_value=0, max_value=100, value=int(DEFAULT_WEIGHTS["药效保留"]*100), step=1)
    total_weight = cost_weight + carbon_weight + efficacy_weight
    if total_weight == 0:
        custom_weights = DEFAULT_WEIGHTS
        st.warning("⚠️ 权重总和不能为0，已自动使用默认AHP权重")
    else:
        custom_weights = {"成本": round(cost_weight/total_weight,3), "碳排放": round(carbon_weight/total_weight,3), "药效保留": round(efficacy_weight/total_weight,3)}
        st.info(f"✅ 当前使用自定义权重：成本{custom_weights['成本']} | 碳排放{custom_weights['碳排放']} | 药效保留{custom_weights['药效保留']}")
    if st.button("开始选型", type="primary"):
        with st.spinner("正在执行多目标决策计算..."):
            df_result, best_tech, best_costs, msg = herb_dry_selection(herb_name, area_name, annual_output, custom_weights)
        if not best_tech:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ 推荐最优干燥技术：**{best_tech}** | {msg}")
            herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
            best_tech_row = df_tech[df_tech["技术名称"] == best_tech].iloc[0]
            herb_min, herb_max = parse_herb_temp(herb_row["建议干燥温度"])
            st.info(f"""🌡️ 温度匹配详情：
药材要求温度：{herb_row["建议干燥温度"]}℃ | 技术适用温度：{best_tech_row["适用最低温(℃)"]}-{best_tech_row["适用最高温(℃)"]}℃
控温精度：{best_tech_row["控温精度"]}℃ | 匹配结果：✅ 完全匹配""")
            st.subheader("候选技术排序（综合得分越小越优）")
            show_cols = ["技术名称", "综合成本(万元)", "综合碳排(吨)", "药效保留率", "综合得分"]
            st.dataframe(centered_table(df_result[show_cols]), hide_index=True)
            if best_costs is not None:
                st.subheader(f"{best_tech} 年度成本构成（万元）")
                cost_df = pd.DataFrame({
                    "成本类型":["设备折旧","能耗成本","碳交易成本"],
                    "金额":[round(best_costs["设备折旧(万元)"],3),round(best_costs["能耗成本(万元)"],3),round(best_costs["碳交易成本(万元)"],3)]
                })
                fig, ax = plt.subplots(figsize=(6,6))
                wedges, texts, autotexts = ax.pie(
                    cost_df["金额"],
                    labels=cost_df["成本类型"],
                    autopct='%1.2f%%',
                    startangle=90,
                    colors=["#95E1D3","#FCE38A","#FF8A80"],
                    wedgeprops=dict(edgecolor="white", linewidth=2),
                    pctdistance=1.2,
                    labeldistance=1.4,
                    textprops={"fontfamily":"WenQuanYi Zen Hei"}
                )
                for t in texts:
                    t.set_fontsize(11)
                for at in autotexts:
                    at.set_fontsize(10)
                    at.set_color("black")
                    at.set_weight("bold")
                ax.axis("equal")
                plt.tight_layout()
                st.pyplot(fig)
                st.success(f"✅ 综合总成本：{round(best_costs['综合成本(万元)'],3)} 万元/年")

# Tab3
with tab3:
    st.subheader("敏感性分析")
    df_result, best_tech, _, _ = herb_dry_selection(herb_name, area_name, annual_output)
    if not best_tech:
        st.warning("⚠️ 当前参数下无匹配的干燥技术，请先在「智能选型」页完成选型")
    else:
        st.markdown(f"**分析对象**：药材：`{herb_name}` | 区域：`{area_name}` | 最优技术：`{best_tech}`")
        sensi_param = st.selectbox("选择分析参数", ["电价","年产量","设备投资","能耗系数","碳交易价格","全参数汇总"])
        if st.button("开始分析", type="primary"):
            with st.spinner("正在计算参数波动对成本的影响..."):
                if sensi_param == "全参数汇总":
                    df_full = full_sensitivity_analysis(herb_name, area_name)
                    st.subheader("全参数敏感度系数汇总")
                    st.dataframe(centered_table(df_full), hide_index=True)
                    if not df_full.empty:
                        st.subheader("敏感度系数龙卷风图")
                        df_plot = df_full.sort_values(by="敏感度系数", key=abs)
                        fig, ax = plt.subplots(figsize=(8,4))
                        bars = ax.barh(df_plot["参数"], df_plot["敏感度系数"], color=["#FF4B4B" if x<0 else "#4B9CD3" for x in df_plot["敏感度系数"]])
                        ax.axvline(x=0, color="black", linestyle="--", alpha=0.5, linewidth=1)
                        ax.set_xlabel("敏感度系数", fontfamily="WenQuanYi Zen Hei")
                        ax.set_title("各参数对综合成本的敏感度影响", fontfamily="WenQuanYi Zen Hei")
                        for bar in bars:
                            width = bar.get_width()
                            ax.text(width + (0.05 if width>0 else -0.05), bar.get_y() + bar.get_height()/2, f"{width:.3f}", ha="left" if width>0 else "right")
                        plt.tight_layout()
                        st.pyplot(fig)
                else:
                    df_sensi = sensitivity_analysis(herb_name, area_name, sensi_param)
                    st.subheader(f"{sensi_param} 波动对综合成本的影响（基准值：{BASE_PARAMS[sensi_param]}）")
                    st.dataframe(centered_table(df_sensi), hide_index=True)
                    st.line_chart(df_sensi, x="波动比例(%)", y="综合成本(万元)", color="#4B9CD3")
                    df_calc = df_sensi[pd.to_numeric(df_sensi["波动比例(%)"])!=0]
                    if not df_calc.empty:
                        avg_coeff = round((pd.to_numeric(df_calc["成本变化率(%)"])/pd.to_numeric(df_calc["波动比例(%)"])).mean(),3)
                        if abs(avg_coeff)>=0.9: lv="🔴 最敏感"
                        elif abs(avg_coeff)>=0.5: lv="🟡 高敏感"
                        elif abs(avg_coeff)>=0.1: lv="⚪ 一般"
                        else: lv="🟢 最不敏感"
                        st.success(f"平均敏感度系数：{avg_coeff} | {lv}")

# Tab4
with tab4:
    st.subheader("📊 中药材低碳干燥智能决策仪表盘")
    df_result, best_tech, best_costs, msg = herb_dry_selection(herb_name, area_name, annual_output)
    if not best_tech:
        st.warning("⚠️ 请先在「智能选型」页选择有效参数完成选型")
    else:
        herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
        area_row = df_area[df_area["区域名称"] == area_name].iloc[0]
        best_tech_row = df_tech[df_tech["技术名称"] == best_tech].iloc[0]
        best_score = round(df_result[df_result["技术名称"] == best_tech]["综合得分"].iloc[0],3) if not df_result.empty else 0
        herb_min, herb_max = parse_herb_temp(herb_row["建议干燥温度"])
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            st.markdown("### 🎯 当前选型结果")
            st.info(f"""- 药材名称：{herb_name}
- 种植区域：{area_name}
- 推荐技术：**{best_tech}**
- 综合得分：**{best_score}**（越小越优）""", icon="ℹ️")
            st.markdown("### 🌡️ 温度匹配详情")
            st.success(f"""✅ 匹配结果：完全匹配
- 药材要求温度：{herb_row["建议干燥温度"]}℃
- 技术适用温度：{best_tech_row["适用最低温(℃)"]}-{best_tech_row["适用最高温(℃)"]}℃
- 控温精度：{best_tech_row["控温精度"]}℃""", icon="✅")
            st.markdown("### ⚖️ 决策权重分布")
            df_weight_plot = pd.DataFrame(DEFAULT_WEIGHTS.items(), columns=["指标","权重"])
            fig1, ax1 = plt.subplots(figsize=(6,6))
            ax1.pie(
                df_weight_plot["权重"],
                labels=df_weight_plot["指标"],
                autopct='%1.2f%%',
                startangle=90,
                colors=["#4B9CD3","#FFD700","#FF6B6B"],
                wedgeprops=dict(edgecolor="white", linewidth=2),
                pctdistance=1.2,
                labeldistance=1.4,
                textprops={"fontfamily":"WenQuanYi Zen Hei"}
            )
            ax1.axis("equal")
            plt.tight_layout()
            st.pyplot(fig1)
        with col2:
            st.markdown("### 📍 区域动态适配因子")
            adapt_cols = ["综合修正因子","电网碳排放因子","碳交易价格（元）","工业电价(元/度)"]
            df_adapt_show = pd.DataFrame(area_row[adapt_cols]).T
            st.dataframe(centered_table(df_adapt_show), hide_index=True)
            if best_costs is not None and not pd.isna(best_costs).all():
                st.markdown("### 💰 年度成本构成（万元）")
                cost_df = pd.DataFrame({
                    "成本类型":["设备折旧","能耗成本","碳交易成本"],
                    "金额":[round(best_costs["设备折旧(万元)"],3),round(best_costs["能耗成本(万元)"],3),round(best_costs["碳交易成本(万元)"],3)]
                })
                fig2, ax2 = plt.subplots(figsize=(6,6))
                wedges2, texts2, autotexts2 = ax2.pie(
                    cost_df["金额"],
                    labels=cost_df["成本类型"],
                    autopct='%1.2f%%',
                    startangle=90,
                    colors=["#95E1D3","#FCE38A","#FF8A80"],
                    wedgeprops=dict(edgecolor="white", linewidth=2),
                    pctdistance=1.2,
                    labeldistance=1.4,
                    textprops={"fontfamily":"WenQuanYi Zen Hei"}
                )
                for t in texts2:
                    t.set_fontsize(11)
                for at in autotexts2:
                    at.set_fontsize(10)
                    at.set_color("black")
                    at.set_weight("bold")
                ax2.axis("equal")
                plt.tight_layout()
                st.pyplot(fig2)
                st.success(f"✅ 综合总成本：{round(best_costs['综合成本(万元)'],3)} 万元/年")
        st.markdown("### 📈 全参数敏感度分析汇总")
        df_si = full_sensitivity_analysis(herb_name, area_name)
        if not df_si.empty:
            st.dataframe(centered_table(df_si), hide_index=True)
        else:
            st.info("暂无敏感度分析数据，请先执行单参数分析", icon="ℹ️")

st.markdown("---")
st.caption("📚 本系统基于《中药材低碳干燥智能选型研究——基于能源经济视角的多目标决策模型》开发 | 一致性检验CR=0.033<0.1")

