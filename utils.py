import pandas as pd
import re

def extract_number(s):
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    if '×10' in s:
        s = s.replace('×10', 'e')
        s = s.replace('⁻', '-').replace('⁺', '+')
        s = s.replace('⁰', '0').replace('¹', '1').replace('²', '2').replace('³', '3')
        s = s.replace('⁴', '4').replace('⁵', '5').replace('⁶', '6')
        s = s.replace('⁷', '7').replace('⁸', '8').replace('⁹', '9')
    numbers = re.findall(r"-?\d+\.?\d*", s)
    if not numbers:
        return 0.0
    nums = [float(n) for n in numbers]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
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

def get_tech_investment(tech_name, lcc_df):
    mode_col = find_column(lcc_df, ["干燥模式", "技术名称"])
    if mode_col:
        match = lcc_df[lcc_df[mode_col].str.contains(tech_name, na=False)]
        if not match.empty:
            invest_col = find_column(lcc_df, ["设备初始投资", "投资(元)"])
            if invest_col:
                invest_str = match.iloc[0][invest_col]
                return extract_number(invest_str) / 10000.0
    return 10.0

def get_depreciation_years(tech_name, lcc_df):
    mode_col = find_column(lcc_df, ["干燥模式", "技术名称"])
    if mode_col:
        match = lcc_df[lcc_df[mode_col].str.contains(tech_name, na=False)]
        if not match.empty:
            years_col = find_column(lcc_df, ["年折旧年限", "折旧年限"])
            if years_col:
                years_str = match.iloc[0][years_col]
                return extract_number(years_str)
    return 10