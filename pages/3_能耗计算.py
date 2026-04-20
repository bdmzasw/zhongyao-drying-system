import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 读取数据 =====================
def read_csv_safe(path):
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        return pd.read_csv(path, encoding="gbk")

@st.cache_data
def load_all_data():
    return {
        "herbs": read_csv_safe("data/药材库.csv"),
        "regions": read_csv_safe("data/区域库.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
regions_df = data["regions"]

# ===================== 页面样式 =====================
st.set_page_config(page_title="能耗核算", page_icon="⚡", layout="wide")
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {display: none;}
    .stApp { background-color: #f5f9f5; }
</style>
""", unsafe_allow_html=True)

if st.button("🏠 返回主页"):
    st.switch_page("Home.py")

# ===================== 统一侧边栏：全局总控 =====================
with st.sidebar:
    st.subheader("⚙️ 总操作仪表盘")
    st.markdown("---")

    herb_list = ["请选择"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox(
        "🌿 药材品种", herb_list,
        index=herb_list.index(st.session_state.get("selected_herb", "请选择")) 
        if st.session_state.get("selected_herb") in herb_list else 0
    )

    region_list = ["请选择"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox(
        "📍 产区", region_list,
        index=region_list.index(st.session_state.get("selected_area", "请选择")) 
        if st.session_state.get("selected_area") in region_list else 0
    )

    electricity_price = st.number_input(
        "⚡ 电价（元/kWh）",
        value=st.session_state.get("electricity_price", 0.6), step=0.01
    )

    annual_capacity = st.number_input(
        "📦 年处理量（吨/年）",
        value=st.session_state.get("annual_capacity", 400), step=50
    )

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("✅ 全系统同步生效")

# ===================== 标题 =====================
st.markdown("## ⚡ 能耗核算与节能分析")
st.caption("基于中药材干燥工艺，开展能耗、成本、碳排放及余热回收效益量化计算")
st.divider()

# ===================== 能耗独有参数（放页面上） =====================
st.subheader("⚙️ 核算参数")
col1, col2, col3 = st.columns(3)
with col1:
    脱水量 = st.number_input("💧 脱水量（kg）", min_value=1, step=10, value=100)
with col2:
    工艺列表 = [
        "请选择",
        "热风干燥",
        "真空干燥",
        "热泵干燥",
        "微波干燥",
        "远红外干燥",
        "组合式低温干燥"
    ]
    工艺 = st.selectbox("🔥 干燥工艺", 工艺列表, index=0)
with col3:
    启用余热回收 = st.checkbox("♻️ 启用余热回收", value=True)

st.divider()

# ===================== 真实联动全局 =====================
电价 = st.session_state.get("electricity_price", 0.6)
年产量 = st.session_state.get("annual_capacity", 400)
年运行Days = 300
碳排放系数 = 0.58

单位能耗表 = {
    "热风干燥": 0.80,
    "真空干燥": 0.60,
    "热泵干燥": 0.45,
    "微波干燥": 0.30,
    "远红外干燥": 0.35,
    "组合式低温干燥": 0.28
}

节能率表 = {
    "热风干燥": 0.0,
    "真空干燥": 0.40,
    "热泵干燥": 0.835,
    "微波干燥": 0.20,
    "远红外干燥": 0.35,
    "组合式低温干燥": 0.75
}

# ===================== 你的原版计算（完全不动） =====================
if 工艺 != "请选择":
    单位能耗 = 单位能耗表.get(工艺, 0.5)
    节能率 = 节能率表.get(工艺, 0.0) if 启用余热回收 else 0.0
    有效单位能耗 = 单位能耗 * (1 - 节能率)

    总耗电量 = 有效单位能耗 * 脱水量
    总碳排放 = 总耗电量 * 碳排放系数
    总电费 = 总耗电量 * 电价

    节能电量 = (单位能耗 - 有效单位能耗) * 脱水量
    节能电费 = 节能电量 * 电价
    减少碳排放 = 节能电量 * 碳排放系数

    st.subheader("📊 核算结果")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总耗电量", f"{总耗电量:.2f} kWh")
    with col2:
        st.metric("总电费", f"{总电费:.2f} 元")
    with col3:
        st.metric("总碳排放", f"{总碳排放:.2f} kg CO₂")

    if 启用余热回收:
        st.divider()
        st.subheader("♻️ 余热回收节能效果")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("节能率", f"{节能率:.1%}")
        with col_b:
            st.metric("节能电量", f"{节能电量:.2f} kWh")
        with col_c:
            st.metric("减少碳排放", f"{减少碳排放:.2f} kg CO₂")

    if "热风" in 工艺:
        st.warning("📌 热风干燥为基准工艺，无余热回收节能，用于对比参考")

    st.divider()
    st.subheader("📅 年度能耗估算")

    吨脱水量 = 脱水量 / 1000
    年耗电量 = 有效单位能耗 * 1000 * 吨脱水量 * 年产量 * (年运行Days / 365)
    年电费 = 年耗电量 * 电价
    年碳排放总量 = 年耗电量 * 碳排放系数

    年节能电量 = (单位能耗 - 有效单位能耗) * 1000 * 吨脱水量 * 年产量 * (年运行Days / 365)
    年减少碳排放 = 年节能电量 * 碳排放系数

    cola, colb, colc = st.columns(3)
    with cola:
        st.metric("年耗电量（万kWh)", f"{年耗电量/10000:.2f}")
    with colb:
        st.metric("年电费（万元)", f"{年电费/10000:.2f}")
    with colc:
        st.metric("年碳排放（吨)", f"{年碳排放总量/1000:.2f}")

    if 启用余热回收 and "热风" not in 工艺:
        st.info(f"年度节约电量：{年节能电量/10000:.2f} 万kWh | 减碳：{年减少碳排放/1000:.2f} 吨")

    st.divider()
    st.subheader("📊 不同工艺年度能耗对比")
    年度数据 = []
    for 工艺术名, 单耗 in 单位能耗表.items():
        有效单耗 = 单耗 * (1 - (节能率表[工艺术名] if 启用余热回收 else 0))
        年耗 = 有效单耗 * 1000 * 吨脱水量 * 年产量 * (年运行Days / 365)
        年度数据.append({"工艺": 工艺术名, "年度耗电(kWh)": 年耗})
    st.line_chart(pd.DataFrame(年度数据), x="工艺", y="年度耗电(kWh)", height=350)

    st.divider()
    st.subheader("📋 核算明细")
    st.dataframe(pd.DataFrame({
        "项目": ["单位能耗", "有效单位能耗", "总耗电量", "总电费", "总碳排放"],
        "数值": [
            f"{单位能耗:.2f} kWh/kg",
            f"{有效单位能耗:.2f} kWh/kg",
            f"{总耗电量:.2f} kWh",
            f"{总电费:.2f} 元",
            f"{总碳排放:.2f} kg"
        ]
    }), use_container_width=True)

else:
    st.info("👈 请选择干燥工艺")

st.divider()
st.subheader("📈 各工艺单位能耗对比")
st.bar_chart(pd.DataFrame({
    "工艺": list(单位能耗表.keys()),
    "单位能耗(kWh/kg)": list(单位能耗表.values())
}), x="工艺", y="单位能耗(kWh/kg)", height=300)

st.divider()