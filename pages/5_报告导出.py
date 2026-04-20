from docx import Document
from docx.shared import Pt, Inches
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import base64
from io import BytesIO
import matplotlib.pyplot as plt

# ===================== FONT FIX (NO CHINESE) =====================
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'DejaVu Sans'

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===================== SAFE FLOAT =====================
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

# ===================== READ CSV =====================
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
        "kinetics": read_csv_safe("data/干燥动力学.csv")
    }

data = load_all_data()
herbs_df = data["herbs"]
regions_df = data["regions"]
techs_df = data["techs"]

# ===================== PAGE SETUP =====================
st.set_page_config(page_title="Report", page_icon="📄", layout="wide")
st.markdown("""
<style>
[data-testid="stSidebarNav"] {display: none;}
.stApp { background-color: #f5f9f5; }
</style>
""", unsafe_allow_html=True)

if st.button("🏠 Back to Home"):
    st.switch_page("Home.py")

# ===================== SIDEBAR ======================
with st.sidebar:
    st.subheader("⚙️ Control Panel")
    herb_list = ["Please Select"] + herbs_df["药材标准名称(药典名)"].dropna().unique().tolist()
    selected_herb = st.selectbox("🌿 Herb", herb_list, index=herb_list.index(st.session_state.get("selected_herb", "Please Select")) if st.session_state.get("selected_herb") in herb_list else 0)
    region_list = ["Please Select"] + regions_df["产区名称"].dropna().unique().tolist()
    selected_area = st.selectbox("📍 Production Area", region_list, index=region_list.index(st.session_state.get("selected_area", "Please Select")) if st.session_state.get("selected_area") in region_list else 0)
    electricity_price = st.number_input("⚡ Electricity Price (CNY/kWh)", value=st.session_state.get("electricity_price", 0.6), step=0.01)
    annual_capacity = st.number_input("📦 Annual Capacity (tons)", value=st.session_state.get("annual_capacity", 400), step=50)

    st.session_state["selected_herb"] = selected_herb
    st.session_state["selected_area"] = selected_area
    st.session_state["electricity_price"] = electricity_price
    st.session_state["annual_capacity"] = annual_capacity
    st.markdown("---")
    st.caption("✅ System Ready")

# ===================== MAIN UI =====================
st.markdown("## 📄 Herbal Drying Process Decision Report")
st.caption("Preview & Word Export are fully consistent")
st.divider()

if selected_herb == "Please Select" or selected_area == "Please Select":
    st.warning("⚠️ Please select herb and production area first")
else:
    herb_info = herbs_df[herbs_df["药材标准名称(药典名)"] == selected_herb].iloc[0]
    region_info = regions_df[regions_df["产区名称"] == selected_area].iloc[0]
    init_mc = safe_float(herb_info["鲜品初始含水率(%)"])
    final_mc = safe_float(herb_info["药典规定成品含水率(%)"])
    water_removed = 1000 * (init_mc - final_mc) / (100 - final_mc)

    # Calculate all processes
    result = []
    for _, t in techs_df.iterrows():
        en = safe_float(t["单位能耗(kWh/kg水)"]) * water_removed
        cost = en * electricity_price
        carbon = en * 0.55
        result.append({
            "Process": t["干燥技术"],
            "Retention": round(safe_float(t["有效成分保留率(%)"]),1),
            "Time": round(safe_float(t["干燥时间范围 (h)"]),1),
            "Energy": round(en,1),
            "Carbon": round(carbon,1),
            "Cost": round(cost,1),
        })

    df = pd.DataFrame(result)
    df["Score"] = (df["Retention"]*0.4 - df["Energy"]*0.2 - df["Time"]*0.15 - df["Carbon"]*0.15 - df["Cost"]*0.1).round(2)
    df = df.sort_values("Score", ascending=False)
    best1 = df.iloc[0]
    best2 = df.iloc[1]

    # Process name mapping (ENGLISH ONLY)
    tech_mapping = {
        "热风干燥": "Hot Air Drying",
        "真空干燥": "Vacuum Drying",
        "热泵干燥": "Heat Pump Drying",
        "微波干燥": "Microwave Drying",
        "远红外干燥": "Far Infrared Drying",
        "热风-远红外联合干燥": "Hybrid Drying",
        "组合式低温干燥": "Low-temp Drying"
    }
    df["Label"] = df["Process"].map(tech_mapping)

    # ------------------- CHART 1 -------------------
    fig1, ax1 = plt.subplots(figsize=(6, 3.5))
    ax1.barh(df["Label"], df["Retention"], color="#4a9f75")
    ax1.set_xlabel("Retention Rate (%)")
    ax1.set_title("Active Ingredient Retention Rate")
    plt.tight_layout()
    buf1 = BytesIO()
    fig1.savefig(buf1, dpi=150, format="png")
    buf1.seek(0)

    # ------------------- CHART 2 -------------------
    fig2, ax2 = plt.subplots(figsize=(6, 3.5))
    ax2.bar(df["Label"], df["Score"], color="#3b82f6")
    ax2.set_ylabel("Comprehensive Score")
    ax2.set_title("Process Comprehensive Score")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    buf2 = BytesIO()
    fig2.savefig(buf2, dpi=150, format="png")
    buf2.seek(0)

    # ===================== PREVIEW =====================
    with st.expander("📄 Report Preview", expanded=True):
        st.markdown("# Herbal Drying Process Decision Report")
        st.markdown(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**Herb**: {selected_herb}　|　**Area**: {selected_area}　|　**Capacity**: {annual_capacity} tons")
        st.divider()

        st.markdown("## 1. Basic Herb Information")
        st.write(f"- Initial Moisture: {init_mc:.1f} %")
        st.write(f"- Target Moisture: {final_mc:.1f} %")
        st.write(f"- Water Removed: {water_removed:.1f} kg/ton")

        st.divider()
        st.markdown("## 2. Recommended Plans")
        c1, c2 = st.columns(2)
        with c1:
            st.success("🏆 TOP 1 RECOMMENDED")
            st.write(f"Process: {best1['Label']}")
            st.write(f"Score: {best1['Score']}")
            st.write(f"Retention: {best1['Retention']}%")
        with c2:
            st.info("📌 ALTERNATIVE PLAN")
            st.write(f"Process: {best2['Label']}")
            st.write(f"Score: {best2['Score']}")
            st.write(f"Retention: {best2['Retention']}%")

        st.divider()
        st.markdown("## 3. Comparison Charts")
        col1, col2 = st.columns(2)
        with col1:
            st.pyplot(fig1)
        with col2:
            st.pyplot(fig2)

        st.divider()
        st.markdown("## 4. Annual Energy & Carbon Emission")
        st.write(f"- Annual Electricity: {best1['Energy'] * annual_capacity:.0f} kWh")
        st.write(f"- Annual Carbon: {best1['Carbon'] * annual_capacity / 1000:.2f} tCO₂")
        st.write(f"- Annual Cost: {best1['Cost'] * annual_capacity:.0f} CNY")

        st.divider()
        st.markdown("## 5. Conclusion")
        st.write(f"1. Recommended: {best1['Label']}")
        st.write(f"2. Alternative: {best2['Label']}")
        st.write("3. Balances quality, efficiency, energy and low carbon.")

    # ===================== WORD EXPORT =====================
    def generate_full_docx():
        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Arial'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), 'Arial')
        style.font.size = Pt(12)

        doc.add_heading("Herbal Drying Process Decision Report", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc.add_paragraph(f"Herb: {selected_herb} | Area: {selected_area} | Capacity: {annual_capacity} tons")

        doc.add_heading("1. Basic Herb Information", level=1)
        doc.add_paragraph(f"Initial Moisture: {init_mc:.1f}%")
        doc.add_paragraph(f"Target Moisture: {final_mc:.1f}%")
        doc.add_paragraph(f"Water Removed: {water_removed:.1f} kg/ton")

        doc.add_heading("2. Recommended Plans", level=1)
        doc.add_heading("Top Recommended", level=2)
        doc.add_paragraph(f"Process: {best1['Label']} | Score: {best1['Score']}")
        doc.add_paragraph(f"Retention: {best1['Retention']}% | Energy: {best1['Energy']} kWh/ton")

        doc.add_heading("Alternative Plan", level=2)
        doc.add_paragraph(f"Process: {best2['Label']} | Score: {best2['Score']}")
        doc.add_paragraph(f"Retention: {best2['Retention']}% | Energy: {best2['Energy']} kWh/ton")

        doc.add_heading("3. Comparison Charts", level=1)
        doc.add_picture(buf1, width=Inches(5.0))
        doc.add_paragraph("Figure 1: Active Ingredient Retention Rate").alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_picture(buf2, width=Inches(5.0))
        doc.add_paragraph("Figure 2: Process Comprehensive Score").alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_heading("4. Annual Performance", level=1)
        doc.add_paragraph(f"Annual Electricity: {best1['Energy'] * annual_capacity:.0f} kWh")
        doc.add_paragraph(f"Annual Carbon Emission: {best1['Carbon'] * annual_capacity / 1000:.2f} tCO₂")
        doc.add_paragraph(f"Annual Cost: {best1['Cost'] * annual_capacity:.0f} CNY")

        doc.add_heading("5. Conclusion", level=1)
        doc.add_paragraph(f"Recommended Process: {best1['Label']}")
        doc.add_paragraph(f"Alternative Process: {best2['Label']}")
        doc.add_paragraph("This solution optimizes quality, energy, efficiency and low-carbon performance.")

        final_buf = BytesIO()
        doc.save(final_buf)
        final_buf.seek(0)
        return final_buf

    # Download
    docx_file = generate_full_docx()
    b64 = base64.b64encode(docx_file.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64,{b64}" download="Drying_Report_{selected_herb}.docx">📥 Download Full English Report</a>'
    st.markdown(href, unsafe_allow_html=True)
    st.success("✅ Report generated: Preview = Export (NO CHINESE, NO GARBAGE CODE)")

st.divider()
