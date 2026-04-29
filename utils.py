import pandas as pd
import re

def extract_number(s):
    """
    从字符串中提取单一数值：区间取平均，正确处理科学计数法（含上标）
    如 '0.25~0.30' → 0.275, '1.155×10⁻¹⁰' → 1.155e-10
    """
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()

    # 1. 替换科学计数法上标
    superscript_map = {
        '⁻': '-', '⁺': '+', '⁰': '0', '¹': '1', '²': '2',
        '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7',
        '⁸': '8', '⁹': '9'
    }
    for k, v in superscript_map.items():
        s = s.replace(k, v)
    s = s.replace('×10', 'e')   # 现在 '1.155e-10' 可以直接 float

    # 2. 按区间符号分割
    parts = re.split(r'\s*[~～]\s*', s)
    nums = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        try:
            nums.append(float(part))
        except ValueError:
            # 如果转换失败，回退用正则提取数字（处理残留的非指数写法）
            fallback = re.findall(r"-?\d+\.?\d*", part)
            for fb in fallback:
                nums.append(float(fb))

    if not nums:
        return 0.0
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2.0
    return nums[0]


def find_column(df, candidates):
    """在DataFrame列名中查找包含任一候选词的列，返回第一个匹配的列名"""
    for col in df.columns:
        for cand in candidates:
            if cand in col or col in cand:
                return col
    return None


def calc_water_removed_per_ton(initial_mc, final_mc):
    initial = initial_mc / 100.0
    final = final_mc / 100.0
    water_per_kg = (initial - final) / (1 - final)
    return water_per_kg * 1000.0


def get_tech_energy(tech_row, tech_df):
    col = find_column(tech_df, ["单位能耗", "能耗(kWh/kg水)"])
    if col:
        val = tech_row[col]
        return extract_number(val)
    return 0.0


def get_tech_retention(tech_row, tech_df):
    col = find_column(tech_df, ["有效成分保留率", "保留率(%)"])
    if col:
        val = tech_row[col]
        return extract_number(val) / 100.0
    return 0.8


# ---------- LCC 精确匹配映射表 ----------
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


def get_tech_investment(tech_name, lcc_df):
    mode_col = find_column(lcc_df, ["干燥模式", "技术名称"])
    if not mode_col:
        return 10.0  # 默认投资 10 万元

    # 用精确映射查找
    matched_name = LCC_MAP.get(tech_name, tech_name)
    match = lcc_df[lcc_df[mode_col] == matched_name]
    if match.empty:
        return 10.0

    invest_col = find_column(lcc_df, ["设备初始投资", "投资(元)"])
    if invest_col:
        invest_str = match.iloc[0][invest_col]
        return extract_number(invest_str) / 10000.0
    return 10.0


def get_depreciation_years(tech_name, lcc_df):
    mode_col = find_column(lcc_df, ["干燥模式", "技术名称"])
    if not mode_col:
        return 10

    matched_name = LCC_MAP.get(tech_name, tech_name)
    match = lcc_df[lcc_df[mode_col] == matched_name]
    if match.empty:
        return 10

    years_col = find_column(lcc_df, ["年折旧年限", "折旧年限"])
    if years_col:
        years_str = match.iloc[0][years_col]
        return extract_number(years_str)
    return 10