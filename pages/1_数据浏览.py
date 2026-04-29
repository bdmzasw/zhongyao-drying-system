import streamlit as st
import pandas as pd
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== 工具函数 =====================
def read_csv_safe(path):
    """安全读取CSV，支持文件缺失、编码容错，并自动去除全空行、清洗列名中特殊字符"""
    if not os.path.exists(path):
        st.error(f"❌ 文件不存在：{path}")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="gbk")
    except Exception as e:
        st.error(f"❌ 读取文件失败：{path}，错误：{e}")
        return pd.DataFrame()

    # 去除全空行
    df = df.dropna(how='all')

    # 清洗列名中的 Unicode 上下标
    superscript_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
    }
    new_columns = []
    for col in df.columns:
        clean_col = col
        for k, v in superscript_map.items():
            clean_col = clean_col.replace(k, v)
        new_columns.append(clean_col)
    df.columns = new_columns

    return df

@st.cache_data
def load_all_data():
    """加载全部数据并缓存"""
    data = {
        "herbs": read_csv_safe("data/药材库.csv"),
        "techs": read_csv_safe("data/技术库.csv"),
        "regions": read_csv_safe("data/区域库.csv"),
        "carbon": read_csv_safe("data/区域碳排放因子.csv"),
        "lcc": read_csv_safe("data/LCC经济成本库-干燥设备对比.csv"),
    }
    for name, df in data.items():
        if df.empty:
            st.warning(f"⚠️ 数据表 `{name}` 为空或加载失败")
    return data

data = load_all_data()

# ===================== 页面配置（同主页风格） =====================
st.set_page_config(page_title="数据浏览", layout="wide")
st.markdown("""
<style>
    /* 主内容区背景：浅绿色 */
    .stApp {
        background-color: #f4f9f2;
    }

    /* 侧边栏：浅米色 */
    [data-testid="stSidebar"] {
        background-color: #f5ede0;
        border-right: 1px solid #d8c8b2;
    }

    /* 侧边栏内的选择框、数字框 */
    div[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
    div[data-testid="stSidebar"] .stNumberInput input {
        border: 1px solid #d8c8b2 !important;
        border-radius: 8px !important;
        background-color: #ffffff;
    }

    /* 原生导航容器：白底绿框 */
    [data-testid="stSidebarNav"] {
        background: #ffffff !important;
        border: 1px solid #b7d0b4;
        border-radius: 10px;
        padding: 0.3rem 0;
        margin: 1rem 0.5rem;
        box-shadow: 0 2px 6px rgba(80,120,80,0.08);
    }
    /* 导航链接 */
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

    /* 标题 */
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

    /* 表格容器微调 */
    div[data-testid="stDataFrame"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #cde0cf;
    }
</style>
""", unsafe_allow_html=True)

# ===================== 侧边栏：全局仪表盘 =====================
with st.sidebar:
    st.subheader("总操作仪表盘")
    st.caption("全局参数统一配置，全页面自动同步")
    st.markdown("---")

    herbs_df = data["herbs"]
    regions_df = data["regions"]

    herb_col = "药材标准名称(药典名)" if "药材标准名称(药典名)" in herbs_df.columns else herbs_df.columns[0]
    region_col = "产区名称" if "产区名称" in regions_df.columns else regions_df.columns[0]

    herb_list = ["请选择"] + herbs_df[herb_col].dropna().unique().tolist()
    selected_herb = st.selectbox(
        "药材品种",
        herb_list,
        index=herb_list.index(st.session_state.get("selected_herb", "请选择"))
        if st.session_state.get("selected_herb", "请选择") in herb_list else 0
    )

    region_list = ["请选择"] + regions_df[region_col].dropna().unique().tolist()
    selected_area = st.selectbox(
        "产区",
        region_list,
        index=region_list.index(st.session_state.get("selected_area", "请选择"))
        if st.session_state.get("selected_area", "请选择") in region_list else 0
    )

    electricity_price = st.number_input(
        "电价（元/kWh）",
        value=st.session_state.get("electricity_price", 0.6), step=0.01
    )
    annual_capacity = st.number_input(
        "年处理量（吨/年）",
        value=st.session_state.get("annual_capacity", 400), step=50
    )

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity

    st.markdown("---")
    st.caption("数据浏览联动")
    st.session_state["highlight_only"] = st.checkbox(
        "仅显示与选中药材/产区相关的行",
        value=st.session_state.get("highlight_only", False)
    )

# ===================== 主内容区 =====================
st.title("基础数据库浏览")
st.caption("系统内置权威数据库，所有工艺、能耗、碳排放计算均基于标准数据源。")

def apply_highlight(df, selected_herb, selected_area, highlight_only):
    if df.empty:
        return df
    df = df.copy()
    df["_highlight"] = False

    herb_col = next((c for c in df.columns if c in ["药材标准名称(药典名)", "药材名称", "药材"]), None)
    region_col = next((c for c in df.columns if c in ["产区名称", "产区", "区域"]), None)

    if selected_herb != "请选择" and herb_col:
        df["_highlight"] = df[herb_col].astype(str) == selected_herb
    if selected_area != "请选择" and region_col:
        df["_highlight"] |= df[region_col].astype(str) == selected_area

    if highlight_only:
        return df[df["_highlight"]].drop(columns=["_highlight"])
    return df

def render_dataframe_with_search(df, key_prefix):
    if df.empty:
        st.info("暂无数据")
        return

    search_term = st.text_input("搜索表格内容", key=f"search_{key_prefix}")
    filtered_df = df.copy()
    if search_term:
        mask = filtered_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
        filtered_df = filtered_df[mask]

    highlight_col = "_highlight" in filtered_df.columns

    num_cols = filtered_df.select_dtypes(include='number').columns.tolist()
    format_dict = {col: "{:.2f}" for col in num_cols if col != "_highlight"}

    if highlight_col:
        def highlight_rows(row):
            if row.get("_highlight"):
                return ['background-color: #e6f3e6'] * len(row)
            return [''] * len(row)
        styled = (filtered_df.drop(columns=["_highlight"])
                  .style.apply(highlight_rows, axis=1)
                  .format(format_dict))
        st.dataframe(styled, use_container_width=True, height=400)
    else:
        styled = filtered_df.style.format(format_dict)
        st.dataframe(styled, use_container_width=True, height=400)

    export_df = filtered_df.drop(columns=["_highlight"] if highlight_col else [])
    export_df[num_cols] = export_df[num_cols].round(2)
    csv = export_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="下载当前表格为 CSV",
        data=csv,
        file_name=f"{key_prefix}_filtered.csv",
        mime="text/csv",
        key=f"dl_{key_prefix}"
    )

    with st.expander("数据质量报告"):
        df_clean = export_df.copy()
        st.write(f"**行数：** {df_clean.shape[0]}，**列数：** {df_clean.shape[1]}")
        missing = df_clean.isnull().sum()
        missing = missing[missing > 0]
        if not missing.empty:
            st.warning("存在缺失值：")
            st.write(missing)
        else:
            st.success("无缺失值")

        if "鲜品初始含水率(%)" in df_clean.columns and "药典规定成品含水率(%)" in df_clean.columns:
            invalid = df_clean[df_clean["鲜品初始含水率(%)"] < df_clean["药典规定成品含水率(%)"]]
            if not invalid.empty:
                st.warning(f"⚠️ 发现 {len(invalid)} 条初始含水率低于成品含水率的异常记录！")

        num_cols_clean = df_clean.select_dtypes(include='number').columns.tolist()
        if num_cols_clean:
            st.write("数值列统计：")
            st.dataframe(df_clean[num_cols_clean].describe().round(4))

# ===================== 标签页 =====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "药材库",
    "干燥技术库",
    "产区库",
    "碳排放因子",
    "经济成本库"
])

with tab1:
    st.subheader("药材基础信息")
    df = apply_highlight(data["herbs"], selected_herb, selected_area, st.session_state.get("highlight_only", False))
    render_dataframe_with_search(df, "herbs")

with tab2:
    st.subheader("干燥技术参数库")
    df = apply_highlight(data["techs"], selected_herb, selected_area, st.session_state.get("highlight_only", False))
    render_dataframe_with_search(df, "techs")

with tab3:
    st.subheader("产区信息库")
    df = apply_highlight(data["regions"], selected_herb, selected_area, st.session_state.get("highlight_only", False))
    render_dataframe_with_search(df, "regions")

with tab4:
    st.subheader("区域碳排放因子")
    df = apply_highlight(data["carbon"], selected_herb, selected_area, st.session_state.get("highlight_only", False))
    render_dataframe_with_search(df, "carbon")

with tab5:
    st.subheader("设备经济成本库 (LCC)")
    df = apply_highlight(data["lcc"], selected_herb, selected_area, st.session_state.get("highlight_only", False))
    render_dataframe_with_search(df, "lcc")

st.divider()
st.caption("数据来源：药典、国标、公开发表文献、行业标准")