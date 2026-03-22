import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import platform
import os

# ========== 页面配置 ==========
st.set_page_config(
    page_title="中药材低碳干燥智能选型系统",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 中文字体设置（强化版） ==========
def setup_chinese_font():
    """设置中文字体，确保图表中文正常显示"""
    system = platform.system()
    
    # 更全面的中文字体列表
    chinese_fonts = [
        'SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'KaiTi',
        'PingFang SC', 'Heiti SC', 'STHeiti', 'Songti SC',
        'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback'
    ]
    
    # 尝试加载系统字体文件
    font_dirs = []
    if system == 'Windows':
        font_dirs = ['C:/Windows/Fonts']
    elif system == 'Darwin':
        font_dirs = ['/System/Library/Fonts', '/Library/Fonts']
    else:
        font_dirs = ['/usr/share/fonts/truetype', '/usr/share/fonts/opentype']
    
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for root, dirs, files in os.walk(font_dir):
                for file in files:
                    if file.endswith(('.ttf', '.ttc', '.otf')) and ('hei' in file.lower() or 'song' in file.lower() or 'yahei' in file.lower()):
                        try:
                            font_path = os.path.join(root, file)
                            fm.fontManager.addfont(font_path)
                        except:
                            pass
    
    matplotlib.rcParams['font.sans-serif'] = chinese_fonts + ['DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus'] = False
    matplotlib.rcParams['font.size'] = 10

setup_chinese_font()

# ========== 自定义CSS样式（侧边栏加深） ==========
st.markdown("""
<style>
    /* 全局背景 */
    .stApp {
        background: #f5f2ed;
    }
    
    /* 侧边栏 - 加深背景色，与主区域明显区分 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c4a2e 0%, #1f3a21 100%);
        border-right: 2px solid #e8dcc8;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #f0f0e8;
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stNumberInput label {
        color: #e8e0c8;
        font-weight: 500;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #f5e6b0;
        font-weight: 600;
    }
    
    /* 侧边栏选择框 */
    [data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #faf7f0;
        border: 1px solid #6b8c6b;
        border-radius: 10px;
    }
    
    [data-testid="stSidebar"] .stNumberInput > div > div > input {
        background-color: #faf7f0;
        border: 1px solid #6b8c6b;
        border-radius: 10px;
    }
    
    /* 侧边栏卡片 */
    .sidebar-card {
        background: rgba(255, 255, 245, 0.12);
        border-radius: 12px;
        padding: 0.8rem;
        margin: 0.8rem 0;
        border-left: 3px solid #e8c87c;
    }
    
    /* 主区域标题 */
    .hero-section {
        background: linear-gradient(135deg, #e8e0d0 0%, #ddd0bc 100%);
        padding: 1.5rem 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        border: 1px solid #c8bc9c;
    }
    
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        color: #2c4a2e;
        margin-bottom: 0.5rem;
    }
    
    .hero-subtitle {
        font-size: 0.9rem;
        color: #5a5a4a;
    }
    
    .hero-badge {
        background: #2c4a2e;
        border-radius: 20px;
        padding: 0.25rem 1rem;
        display: inline-block;
        margin-top: 0.8rem;
        color: #f5e6b0;
        font-size: 0.8rem;
    }
    
    /* 卡片样式 */
    .soft-card {
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0d4c0;
    }
    
    /* 按钮 */
    .stButton > button {
        background: linear-gradient(135deg, #5a8c5a 0%, #3a6b3a 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6b9c6b 0%, #4a7a4a 100%);
        box-shadow: 0 4px 12px rgba(60, 100, 60, 0.3);
    }
    
    /* 标签页 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        background: #e8e0d0;
        padding: 0.4rem;
        border-radius: 40px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 30px;
        padding: 0.4rem 1.2rem;
        color: #5a5a4a;
    }
    
    .stTabs [aria-selected="true"] {
        background: #5a8c5a;
        color: white;
    }
    
    /* 表格 */
    .stDataFrame {
        border-radius: 12px;
    }
    
    /* 脚注 */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #8a8a7a;
        font-size: 0.75rem;
        border-top: 1px solid #e0d4c0;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== 表格格式化函数 ==========
def centered_table(df):
    df_display = df.copy()
    for col in df_display.columns:
        if df_display[col].dtype in ['float64', 'float32']:
            max_val = df_display[col].max()
            if pd.isna(max_val):
                continue
            if max_val < 1:
                df_display[col] = df_display[col].map(lambda x: f"{x:.4f}" if pd.notna(x) else "")
            elif max_val < 10:
                df_display[col] = df_display[col].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
            elif max_val < 1000:
                df_display[col] = df_display[col].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
            else:
                df_display[col] = df_display[col].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
    
    return df_display.style.set_properties(**{
        'text-align': 'center',
        'vertical-align': 'middle',
        'padding': '8px 6px',
        'font-size': '12px'
    }).set_table_styles([
        {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', '600'), 
                                     ('background-color', '#e8e0d0'), ('color', '#2c4a2e')]},
        {'selector': 'td', 'props': [('text-align', 'center'), ('padding', '6px')]},
        {'selector': 'tr:hover', 'props': [('background-color', '#faf5e8')]}
    ])


# ========== 基础数据 ==========
herb_data = {
    "药材ID": ["H001", "H002", "H003", "H004", "H005"],
    "药材名称": ["黄芪", "金银花", "党参", "当归", "菊花"],
    "药用部位": ["根", "花", "根", "根", "花"],
    "建议干燥温度": ["≤60", "40-45", "50-60", "≤50", "≤45"],
    "温度类型": ["单上限", "双区间", "双区间", "单上限", "单上限"],
    "敏感成分": ["黄芪甲苷", "挥发油", "党参多糖", "挥发油", "挥发油+黄酮"],
    "药效敏感等级": ["中敏", "高敏", "中敏", "高敏", "高敏"],
    "初始含水率%": [60, 75, 65, 70, 80],
    "目标含水率%": [10, 12, 10, 10, 12],
    "每吨除水量kg": [556, 716, 611, 667, 773],
    "碳足迹系数": [2.6, 3.2, 2.6, 2.9, 3.4]
}
df_herb = pd.DataFrame(herb_data)


tech_data = {
    "技术ID": ["T001", "T002", "T003", "T004", "T005"],
    "技术名称": ["热泵干燥", "红外干燥", "传统热风", "微波干燥", "真空干燥"],
    "适用最低温(℃)": [30, 35, 60, 30, 30],
    "适用最高温(℃)": [65, 120, 120, 80, 60],
    "控温精度": ["±1", "±3", "±5", "±2", "±1"],
    "最小能耗": [1.0, 1.6, 2.2, 1.3, 1.2],
    "最大能耗": [1.3, 2.0, 2.8, 1.6, 1.5],
    "药效保留率": [0.93, 0.90, 0.82, 0.88, 0.95],
    "平均能耗系数": [1.15, 1.8, 2.5, 1.45, 1.35],
    "设备投资(万元)": [12, 8, 3.5, 10, 18],
    "适用药材部位": ["根茎果实", "花叶", "通用", "根茎果实", "根/贵重"],
    "寿命(年)": [15, 10, 10, 12, 15]
}
df_tech = pd.DataFrame(tech_data)


area_data = {
    "区域ID": ["R001", "R002", "R003", "R004", "R005", "R006", "R007", "R008"],
    "区域名称": ["甘肃定西", "安徽亳州", "河北安国", "宁夏中卫", "浙江杭州", "四川成都", "广东广州", "云南昆明"],
    "年均温度": [8, 15, 12, 9, 17, 16, 22, 15],
    "年均湿度(%)": [63, 78, 70, 58, 76, 82, 79, 73],
    "年均风速": [2.5, 2.0, 2.2, 2.8, 2.1, 1.5, 2.3, 2.4],
    "年降水量": [400, 800, 500, 200, 1400, 900, 1700, 1000],
    "工业电价": [0.51, 0.64, 0.65, 0.51, 0.63, 0.54, 0.64, 0.41],
    "设备补贴(%)": [20, 0, 10, 15, 0, 0, 0, 10],
    "主要药材": ["党参/黄芪", "白芍/丹皮", "白芷/山药", "枸杞/黄芪", "杭白菊", "川穹/川贝", "广藿香", "三七"],
    "综合修正因子": [0.77, 1.40, 1.18, 0.78, 1.35, 1.22, 1.40, 0.77],
    "碳交易价格": [81.58, 81.58, 81.58, 81.58, 81.58, 81.58, 38.84, 81.58]
}
df_area = pd.DataFrame(area_data)


# ========== 常量与函数 ==========
DEFAULT_WEIGHTS = {"成本": 0.260, "碳排放": 0.106, "药效保留": 0.633}
BASE_PARAMS = {"电价": 0.57, "年产量": 800.0, "设备投资": 10.3, "能耗系数": 1.65, "碳交易价格": 76.24}


def parse_herb_temp(temp_str):
    if "≤" in temp_str:
        return 0, int(temp_str.replace("≤", ""))
    elif "-" in temp_str:
        parts = temp_str.split("-")
        return int(parts[0].strip()), int(parts[1].strip())
    else:
        val = int(temp_str)
        return val, val


def check_temp_match(herb_temp_str, tech_min, tech_max):
    herb_min, herb_max = parse_herb_temp(herb_temp_str)
    return herb_max <= tech_max


def calc_total_cost(tech_row, area_row, herb_tons_water, annual_output=800):
    life = tech_row["寿命(年)"]
    invest = tech_row["设备投资(万元)"] * (1 - area_row["设备补贴(%)"]/100)
    depre_cost = round(invest / life, 3) if life != 0 else 0
    energy_coeff = tech_row["平均能耗系数"]
    elec_price = area_row["工业电价"]
    energy_cost = round((annual_output * herb_tons_water * energy_coeff * elec_price) / 10000, 3)
    carbon_price = area_row["碳交易价格"]
    carbon_cost = round((tech_row["平均能耗系数"] * 300 * area_row["综合修正因子"] * carbon_price) / 10000, 3)
    total_cost = round(depre_cost + energy_cost + carbon_cost, 3)
    return total_cost, depre_cost, energy_cost, carbon_cost


def normalize_series(s):
    if s.max() == s.min() or s.max() - s.min() < 1e-6:
        return pd.Series([0.0]*len(s), index=s.index)
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
        df_tech_filter["综合成本(万元)"] = [x[0] for x in cost_cols]
        df_tech_filter["设备折旧(万元)"] = [x[1] for x in cost_cols]
        df_tech_filter["能耗成本(万元)"] = [x[2] for x in cost_cols]
        df_tech_filter["碳交易成本(万元)"] = [x[3] for x in cost_cols]
        df_tech_filter["综合碳排(吨)"] = round(df_tech_filter["平均能耗系数"] * 300 * area_row["综合修正因子"], 3)
        df_tech_filter["药效得分"] = df_tech_filter["药效保留率"]
        df_tech_filter["成本归一化"] = normalize_series(df_tech_filter["综合成本(万元)"])
        df_tech_filter["碳排归一化"] = normalize_series(df_tech_filter["综合碳排(吨)"])
        df_tech_filter["药效归一化"] = normalize_series(df_tech_filter["药效得分"])
        df_tech_filter["综合得分"] = (weights["成本"] * df_tech_filter["成本归一化"] + 
                                      weights["碳排放"] * df_tech_filter["碳排归一化"] + 
                                      weights["药效保留"] * (1 - df_tech_filter["药效归一化"])).round(6)
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
                ar["工业电价"] = val
                cost,_,_,_ = calc_total_cost(tech_row, ar, herb_tons_water)
            elif base_param == "年产量":
                cost,_,_,_ = calc_total_cost(tech_row, area_row, herb_tons_water, val)
            elif base_param == "设备投资":
                tr = tech_row.copy()
                tr["设备投资(万元)"] = val
                cost,_,_,_ = calc_total_cost(tr, area_row, herb_tons_water)
            elif base_param == "能耗系数":
                tr = tech_row.copy()
                tr["平均能耗系数"] = val
                cost,_,_,_ = calc_total_cost(tr, area_row, herb_tons_water)
            elif base_param == "碳交易价格":
                ar = area_row.copy()
                ar["碳交易价格"] = val
                cost,_,_,_ = calc_total_cost(tech_row, ar, herb_tons_water)
            chg = round((cost-base_cost)/base_cost*100,2) if base_cost !=0 else 0
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
        res.append({"参数":p,"基准值":round(BASE_PARAMS[p],2),"敏感度系数":coe,"敏感程度":lv})
    return pd.DataFrame(res)


# ========== 饼图绘制函数 ==========
def draw_pie_chart(labels, values, title="", colors=None):
    label_map = {
        "成本": "成本",
        "碳排放": "碳排放", 
        "药效保留": "药效保留",
        "设备折旧": "设备折旧",
        "能耗成本": "能耗成本",
        "碳交易成本": "碳交易成本"
    }
    
    chn_labels = [label_map.get(label, label) for label in labels]
    
    fig, ax = plt.subplots(figsize=(5.5, 4))
    
    if colors is None:
        colors = ["#6b8c6b", "#d9a56c", "#c97e5a"]
    
    wedges, texts, autotexts = ax.pie(
        values,
        labels=chn_labels,
        autopct='%1.2f%%',
        startangle=90,
        colors=colors,
        wedgeprops=dict(edgecolor="white", linewidth=1.5),
        pctdistance=1.2,
        labeldistance=1.4,
        textprops={'fontsize': 10, 'fontfamily': 'sans-serif'}
    )
    
    for t in texts:
        t.set_fontsize(10)
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("black")
        at.set_fontweight("bold")
    
    ax.axis("equal")
    if title:
        ax.set_title(title, fontsize=11, pad=10)
    
    plt.tight_layout()
    return fig


# ========== 绘制敏感度分析图 ==========
def draw_sensitivity_chart(df_full):
    """绘制敏感度分析水平条形图"""
    fig, ax = plt.subplots(figsize=(8, 4))
    
    df_plot = df_full.sort_values(by="敏感度系数", key=abs)
    
    colors = ['#c97e5a' if x < 0 else '#6b8c6b' for x in df_plot["敏感度系数"]]
    bars = ax.barh(df_plot["参数"], df_plot["敏感度系数"], color=colors, edgecolor='white', linewidth=1)
    
    ax.axvline(x=0, color='#888888', linestyle='--', alpha=0.7, linewidth=1)
    ax.set_xlabel('敏感度系数', fontsize=11, fontweight='500')
    ax.set_title('参数敏感度分析', fontsize=12, fontweight='600', pad=12)
    
    for bar in bars:
        width = bar.get_width()
        offset = 0.03 if width > 0 else -0.03
        ha = 'left' if width > 0 else 'right'
        ax.text(width + offset, bar.get_y() + bar.get_height()/2, 
                f'{width:.3f}', ha=ha, va='center', fontsize=9)
    
    ax.set_xlim(min(df_plot["敏感度系数"].min() - 0.1, -0.1), 
                max(df_plot["敏感度系数"].max() + 0.1, 0.3))
    ax.grid(axis='x', alpha=0.3, linestyle=':')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    return fig


# ========== 界面 ==========
# 主标题区域
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🌿 中药材低碳干燥智能选型系统</div>
    <div class="hero-subtitle">基于能源经济视角的多目标决策模型</div>
    <div class="hero-badge">⚡ 低碳 · 🎯 智能 · 💰 经济</div>
</div>
""", unsafe_allow_html=True)

# 侧边栏（加深背景色）
with st.sidebar:
    st.markdown("""
    <div style="background: rgba(255,255,240,0.15); border-radius: 15px; padding: 1rem; text-align: center; margin-bottom: 1.5rem;">
        <span style="font-size: 1.3rem; font-weight: 600; color: #f5e6b0;">⚙️ 参数设置</span>
    </div>
    """, unsafe_allow_html=True)
    
    herb_name = st.selectbox("🌱 选择药材", df_herb["药材名称"].tolist(), index=3)
    area_name = st.selectbox("📍 选择区域", df_area["区域名称"].tolist(), index=5)
    annual_output = st.number_input("📦 年产量(吨)", min_value=100, max_value=2000, value=800, step=100)
    
    st.markdown("---")
    
    st.markdown('<div class="sidebar-card">📚 <strong>数据来源</strong></div>', unsafe_allow_html=True)
    st.caption("《中国药典2025版》")
    st.caption("各省气象/发改委数据")
    st.caption("CNKI核心期刊")
    st.caption("全国碳排放权交易市场")
    
    st.markdown('<div class="sidebar-card">🎯 <strong>系统特点</strong></div>', unsafe_allow_html=True)
    st.caption("✅ 多目标优化决策")
    st.caption("✅ 生命周期碳排放评估")
    st.caption("✅ 区域动态适配因子")
    st.caption("✅ 敏感性分析")
    
    st.markdown('<div class="sidebar-card">💡 <strong>使用提示</strong></div>', unsafe_allow_html=True)
    st.caption("1️⃣ 选择药材和区域")
    st.caption("2️⃣ 调整权重偏好")
    st.caption("3️⃣ 点击开始选型")
    st.caption("4️⃣ 查看推荐结果")

# 标签页
tab1, tab2, tab3, tab4 = st.tabs(["📊 数据库查看", "🎯 智能选型", "📈 敏感性分析", "🖥️ 决策仪表盘"])

# ========== 标签1：数据库 ==========
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.subheader("📖 药材库")
        st.dataframe(centered_table(df_herb), hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.subheader("⚙️ 默认决策权重")
        df_weights = pd.DataFrame(DEFAULT_WEIGHTS.items(), columns=["指标", "权重"])
        df_weights["占比(%)"] = round(df_weights["权重"] * 100, 1)
        st.dataframe(centered_table(df_weights), hide_index=True, use_container_width=True)
        st.success("✅ 一致性检验 CR=0.033 < 0.1")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.subheader("🔧 技术库")
        st.dataframe(centered_table(df_tech), hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="soft-card">', unsafe_allow_html=True)
        st.subheader("🗺️ 区域库")
        st.dataframe(centered_table(df_area), hide_index=True, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ========== 标签2：智能选型 ==========
with tab2:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("🎯 智能选型结果")
    st.markdown(f"**当前参数**：🌱 {herb_name} | 📍 {area_name} | 📦 {annual_output} 吨")
    
    st.markdown("### ⚖️ 权重自定义调整")
    col1, col2, col3 = st.columns(3)
    with col1:
        cost_weight = st.slider("💰 成本权重", 0, 100, int(DEFAULT_WEIGHTS["成本"]*100), step=1)
    with col2:
        carbon_weight = st.slider("🌍 碳排放权重", 0, 100, int(DEFAULT_WEIGHTS["碳排放"]*100), step=1)
    with col3:
        efficacy_weight = st.slider("💊 药效权重", 0, 100, int(DEFAULT_WEIGHTS["药效保留"]*100), step=1)
    
    total_weight = cost_weight + carbon_weight + efficacy_weight
    if total_weight == 0:
        custom_weights = DEFAULT_WEIGHTS
        st.warning("⚠️ 权重总和不能为0，使用默认权重")
    else:
        custom_weights = {"成本": round(cost_weight/total_weight,3), 
                         "碳排放": round(carbon_weight/total_weight,3), 
                         "药效保留": round(efficacy_weight/total_weight,3)}
    
    if st.button("🚀 开始选型", type="primary", use_container_width=True):
        with st.spinner("计算中..."):
            df_result, best_tech, best_costs, msg = herb_dry_selection(herb_name, area_name, annual_output, custom_weights)
        
        if not best_tech:
            st.error(f"❌ {msg}")
        else:
            st.success(f"✅ 推荐技术：**{best_tech}**")
            
            herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
            best_tech_row = df_tech[df_tech["技术名称"] == best_tech].iloc[0]
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"🌡️ **温度匹配**\n- 药材要求：{herb_row['建议干燥温度']}℃\n- 技术适用：{best_tech_row['适用最低温(℃)']}-{best_tech_row['适用最高温(℃)']}℃\n- 控温精度：{best_tech_row['控温精度']}℃")
            with col2:
                st.success(f"🎯 **选型结果**\n- 推荐技术：{best_tech}\n- 综合得分：{df_result[df_result['技术名称'] == best_tech]['综合得分'].iloc[0]:.4f}\n- 综合成本：{best_costs['综合成本(万元)']} 万元/年")
            
            st.subheader("📋 候选技术排序")
            show_cols = ["技术名称", "综合成本(万元)", "综合碳排(吨)", "药效保留率", "综合得分"]
            st.dataframe(centered_table(df_result[show_cols]), hide_index=True, use_container_width=True)
            
            if best_costs is not None:
                st.subheader(f"💰 {best_tech} 年度成本构成")
                cost_labels = ["设备折旧", "能耗成本", "碳交易成本"]
                cost_values = [best_costs["设备折旧(万元)"], best_costs["能耗成本(万元)"], best_costs["碳交易成本(万元)"]]
                fig = draw_pie_chart(cost_labels, cost_values, "")
                st.pyplot(fig)
                st.success(f"✅ 综合总成本：{round(best_costs['综合成本(万元)'],3)} 万元/年")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 标签3：敏感性分析 ==========
with tab3:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("📈 敏感性分析")
    df_result, best_tech, _, _ = herb_dry_selection(herb_name, area_name, annual_output)
    
    if not best_tech:
        st.warning("⚠️ 请先在「智能选型」完成选型")
    else:
        st.markdown(f"**分析对象**：{herb_name} | {area_name} | 最优技术：{best_tech}")
        sensi_param = st.selectbox("选择分析参数", ["电价","年产量","设备投资","能耗系数","碳交易价格","全参数汇总"])
        
        if st.button("🔍 开始分析", type="primary", use_container_width=True):
            with st.spinner("计算中..."):
                if sensi_param == "全参数汇总":
                    df_full = full_sensitivity_analysis(herb_name, area_name)
                    st.subheader("全参数敏感度系数汇总")
                    st.dataframe(centered_table(df_full), hide_index=True, use_container_width=True)
                    
                    if not df_full.empty:
                        st.subheader("📊 参数敏感度分析图")
                        fig = draw_sensitivity_chart(df_full)
                        st.pyplot(fig)
                else:
                    df_sensi = sensitivity_analysis(herb_name, area_name, sensi_param)
                    st.subheader(f"{sensi_param} 波动影响")
                    st.dataframe(centered_table(df_sensi), hide_index=True, use_container_width=True)
                    st.line_chart(df_sensi, x="波动比例(%)", y="综合成本(万元)", color="#6b8c6b")
                    
                    df_calc = df_sensi[pd.to_numeric(df_sensi["波动比例(%)"])!=0]
                    if not df_calc.empty:
                        avg_coeff = round((pd.to_numeric(df_calc["成本变化率(%)"])/pd.to_numeric(df_calc["波动比例(%)"])).mean(),3)
                        if abs(avg_coeff)>=0.9: lv="🔴 最敏感"
                        elif abs(avg_coeff)>=0.5: lv="🟡 高敏感"
                        elif abs(avg_coeff)>=0.1: lv="⚪ 一般"
                        else: lv="🟢 最不敏感"
                        st.success(f"平均敏感度系数：{avg_coeff} | {lv}")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== 标签4：决策仪表盘 ==========
with tab4:
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.subheader("📊 决策仪表盘")
    df_result, best_tech, best_costs, msg = herb_dry_selection(herb_name, area_name, annual_output)
    
    if not best_tech:
        st.warning("⚠️ 请先在「智能选型」完成选型")
    else:
        herb_row = df_herb[df_herb["药材名称"] == herb_name].iloc[0]
        area_row = df_area[df_area["区域名称"] == area_name].iloc[0]
        best_tech_row = df_tech[df_tech["技术名称"] == best_tech].iloc[0]
        best_score = df_result[df_result["技术名称"] == best_tech]["综合得分"].iloc[0] if not df_result.empty else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎯 当前选型")
            st.info(f"- 药材：{herb_name}\n- 区域：{area_name}\n- 推荐技术：**{best_tech}**\n- 综合得分：{round(best_score,4)}")
            
            st.markdown("### 🌡️ 温度匹配")
            st.success(f"✅ 药材要求：{herb_row['建议干燥温度']}℃\n✅ 技术适用：{best_tech_row['适用最低温(℃)']}-{best_tech_row['适用最高温(℃)']}℃\n✅ 控温精度：{best_tech_row['控温精度']}℃")
            
            st.markdown("### ⚖️ 权重分布")
            fig1 = draw_pie_chart(list(DEFAULT_WEIGHTS.keys()), list(DEFAULT_WEIGHTS.values()), "", colors=["#6b8c6b", "#d9a56c", "#c97e5a"])
            st.pyplot(fig1)
        
        with col2:
            st.markdown("### 📍 区域适配")
            adapt_cols = ["综合修正因子", "工业电价", "碳交易价格"]
            df_adapt_show = pd.DataFrame({col: [area_row[col]] for col in adapt_cols})
            st.dataframe(centered_table(df_adapt_show), hide_index=True, use_container_width=True)
            
            if best_costs is not None:
                st.markdown("### 💰 成本构成")
                cost_labels = ["设备折旧", "能耗成本", "碳交易成本"]
                cost_values = [best_costs["设备折旧(万元)"], best_costs["能耗成本(万元)"], best_costs["碳交易成本(万元)"]]
                fig2 = draw_pie_chart(cost_labels, cost_values, "")
                st.pyplot(fig2)
                st.success(f"总成本：{round(best_costs['综合成本(万元)'],3)} 万元/年")
        
        st.markdown("### 📈 敏感度分析汇总")
        df_sensi_dash = full_sensitivity_analysis(herb_name, area_name)
        if not df_sensi_dash.empty:
            st.dataframe(centered_table(df_sensi_dash), hide_index=True, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# 脚注
st.markdown("""
<div class="footer">
    📚 基于《中药材低碳干燥智能选型研究》开发 | 一致性检验 CR=0.033 | © 2025
</div>
""", unsafe_allow_html=True)
