import pandas as pd
import numpy as np
import re

# ---------- 辅助函数 ----------
def extract_number(s):
    if pd.isna(s):
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    s = str(s).strip()
    numbers = re.findall(r"-?\d+\.?\d*", s)
    if not numbers:
        return 0.0
    nums = [float(n) for n in numbers]
    if len(nums) >= 2:
        return (nums[0] + nums[1]) / 2
    return nums[0]

def calc_water_removed(initial, final):
    return (initial/100 - final/100) / (1 - final/100) * 1000

# ---------- 读取数据 ----------
herbs = pd.read_excel("数据参数表.xlsx", sheet_name="药材库")
techs = pd.read_excel("数据参数表.xlsx", sheet_name="技术库")
regions = pd.read_excel("数据参数表.xlsx", sheet_name="区域库")
carbon = pd.read_excel("数据参数表.xlsx", sheet_name="区域碳排因子")
lcc = pd.read_excel("数据参数表.xlsx", sheet_name="LCC经济成本库")

# ---------- 数据清洗 ----------
# 药材库：重命名关键列
herbs = herbs.rename(columns={
    "药材标准名称(药典名)": "药材名称",
    "鲜品初始含水率(%)": "初始含水率",
    "药典规定成品含水率(%)": "成品含水率",
    "药用部位": "药用部位",
    "热敏性等级(高/中/低)": "热敏性"
})

# 技术库：重命名关键列，并添加平均能耗
techs = techs.rename(columns={
    "干燥技术": "技术名称",
    "适用药用部位": "适用部位",
    "适用热敏等级": "适用热敏",
    "单位能耗(kWh/kg水)": "能耗范围",
    "有效成分保留率(%)": "保留率范围"
})
techs["平均能耗"] = techs["能耗范围"].apply(extract_number)
techs["平均保留率"] = techs["保留率范围"].apply(extract_number)

# 区域库：提取省份
regions["省份"] = regions["所辖主要省市"].str.split("、").str[0]

# LCC库：重命名
lcc = lcc.rename(columns={
    "干燥模式": "技术名称",
    "设备初始投资(元/台套)": "投资范围",
    "年折旧年限(年)": "折旧年限"
})
lcc["平均投资"] = lcc["投资范围"].apply(extract_number)
lcc["平均折旧"] = lcc["折旧年限"].apply(extract_number)

# 碳排放因子表
carbon = carbon.rename(columns={"碳排放因子(kgCO₂/kWh)": "碳排因子"})

# ---------- 生成所有组合 ----------
# 提取去重列表
herb_names = herbs["药材名称"].unique()
region_names = regions["产区名称"].unique()
tech_names = techs["技术名称"].unique()

# 笛卡尔积
combinations = []
for h in herb_names:
    for r in region_names:
        for t in tech_names:
            combinations.append((h, r, t))
df_all = pd.DataFrame(combinations, columns=["药材名称", "产区名称", "技术名称"])

# ---------- 匹配并计算 ----------
def get_herb_info(herb_name):
    return herbs[herbs["药材名称"] == herb_name].iloc[0]

def get_tech_info(tech_name):
    return techs[techs["技术名称"] == tech_name].iloc[0]

def get_region_info(region_name):
    return regions[regions["产区名称"] == region_name].iloc[0]

def get_carbon_factor(province):
    row = carbon[carbon["省份"] == province]
    if not row.empty:
        return row.iloc[0]["碳排因子"]
    return 0.5

def get_lcc(tech_name):
    row = lcc[lcc["技术名称"].str.contains(tech_name, na=False)]
    if not row.empty:
        return row.iloc[0]
    return pd.Series({"平均投资": 100000, "平均折旧": 10})

# 存储结果
results = []
for idx, row in df_all.iterrows():
    herb = get_herb_info(row["药材名称"])
    tech = get_tech_info(row["技术名称"])
    region = get_region_info(row["产区名称"])

    # 筛选有效组合（药用部位匹配 + 热敏匹配）
    # 药用部位匹配：药材部位包含在技术适用部位中（模糊匹配）
    herb_part = herb["药用部位"]
    tech_parts = tech["适用部位"]
    if not (isinstance(tech_parts, str) and (herb_part in tech_parts or ("根茎" in tech_parts and ("根及根茎" in herb_part or "块根" in herb_part)))):
        continue
    # 热敏匹配：药材热敏等级在技术适用等级中
    herb_sens = herb["热敏性"]
    tech_sens = tech["适用热敏"]
    if not (isinstance(tech_sens, str) and herb_sens in tech_sens):
        continue

    # 计算脱水量
    water_removed = calc_water_removed(herb["初始含水率"], herb["成品含水率"])
    # 能耗
    unit_energy = tech["平均能耗"]
    total_energy = water_removed * unit_energy
    # 碳排放因子
    province = region["省份"]
    carbon_factor = get_carbon_factor(province)
    carbon_emission = total_energy * carbon_factor
    # 电价（固定0.6）
    electricity_price = 0.6
    energy_cost = total_energy * electricity_price
    # 设备折旧
    lcc_info = get_lcc(row["技术名称"])
    investment = lcc_info["平均投资"] / 10000 # 万元
    dep_years = lcc_info["平均折旧"]
    annual_throughput = 800
    depreciation = (investment * 10000 / dep_years) / annual_throughput
    # 碳交易成本
    carbon_price = 60
    carbon_cost = carbon_emission * carbon_price / 1000
    total_cost = energy_cost + depreciation + carbon_cost
    # 药效保留率
    retention = tech["平均保留率"] / 100
    # 归一化需要的组内极值（稍后统一计算）
    results.append({
        "药材名称": row["药材名称"],
        "区域": row["产区名称"],
        "技术名称": row["技术名称"],
        "脱水量(kg/吨)": water_removed,
        "总能耗(kWh/吨)": total_energy,
        "碳排放(kgCO₂/吨)": carbon_emission,
        "总成本(元/吨)": total_cost,
        "药效保留率": retention,
        "综合得分": None
    })

# 转换为DataFrame
df_results = pd.DataFrame(results)

# 归一化并计算综合得分（分组）
def group_normalize(group):
    min_cost = group["总成本(元/吨)"].min()
    max_cost = group["总成本(元/吨)"].max()
    min_carbon = group["碳排放(kgCO₂/吨)"].min()
    max_carbon = group["碳排放(kgCO₂/吨)"].max()
    # 避免除零
    norm_cost = (group["总成本(元/吨)"] - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
    norm_carbon = (group["碳排放(kgCO₂/吨)"] - min_carbon) / (max_carbon - min_carbon) if max_carbon > min_carbon else 0
    # 权重
    w_cost, w_carbon, w_quality = 0.4, 0.3, 0.3
    score = w_cost * norm_cost + w_carbon * norm_carbon + w_quality * (1 - group["药效保留率"])
    group["综合得分"] = score
    return group

df_results = df_results.groupby(["药材名称", "区域"]).apply(group_normalize).reset_index(drop=True)

# 选取每组综合得分最小的技术
idx_min = df_results.groupby(["药材名称", "区域"])["综合得分"].idxmin()
df_recommend = df_results.loc[idx_min].copy()

# 整理最终列
df_recommend = df_recommend[["药材名称", "区域", "技术名称", "综合得分", "总成本(元/吨)", "碳排放(kgCO₂/吨)", "药效保留率"]]
df_recommend["药效保留率"] = df_recommend["药效保留率"].apply(lambda x: f"{x*100:.1f}%")

# 保存为CSV
df_recommend.to_csv("data/推荐结果.csv", index=False, encoding='utf-8-sig')
print("✅ 推荐结果已生成: data/推荐结果.csv")