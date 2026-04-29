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

def normalize_part(part_str):
    """将药材部位和技术适用部位统一映射到标准类别"""
    if not isinstance(part_str, str):
        return set()
    
    mapping = {
        '根及根茎': '根茎类',
        '根茎及块茎': '根茎类',
        '块根': '根茎类',
        '根茎': '根茎类',
        '根': '根茎类',
        '块茎': '根茎类',
        '根茎类': '根茎类',
        
        '花': '花叶类',
        '花类': '花叶类',
        '叶': '花叶类',
        '叶类': '花叶类',
        '全草': '花叶类',
        
        '果实': '果实类',
        '果皮': '果实类',
        '果实类': '果实类',
        '果皮类': '果实类',
        
        '菌核': '特殊类',
        '提取物': '特殊类',
        '高价值药材': '特殊类',
    }
    
    # 处理技术库的逗号、顿号分隔
    parts = re.split(r'[、，,]', part_str)
    result = set()
    for p in parts:
        p = p.strip()
        if p in mapping:
            result.add(mapping[p])
    return result

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

# 区域库：提取省份，并去掉方位后缀（如“内蒙古东部”->“内蒙古”）
regions["省份"] = regions["所辖主要省市"].str.split("、").str[0].str.replace("东部|西部|南部|北部", "", regex=True)

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
herb_names = herbs["药材名称"].unique()
region_names = regions["产区名称"].unique()
tech_names = techs["技术名称"].unique()

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
    # 技术名称 → LCC干燥模式 精确映射
    lcc_map = {
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
    matched_name = lcc_map.get(tech_name, tech_name)
    row = lcc[lcc["技术名称"] == matched_name]
    if not row.empty:
        return row.iloc[0]
    return pd.Series({"平均投资": 100000, "平均折旧": 10})

results = []
for idx, row in df_all.iterrows():
    herb = get_herb_info(row["药材名称"])
    tech = get_tech_info(row["技术名称"])
    region = get_region_info(row["产区名称"])

    # ===== 部位匹配（标准化后集合取交集）=====
    herb_parts = normalize_part(herb["药用部位"])
    tech_parts = normalize_part(tech["适用部位"])
    if not herb_parts.intersection(tech_parts):
        continue

    # ===== 热敏匹配（数值化比较）=====
    sens_map = {"高": 3, "中": 2, "低": 1}
    herb_sens = sens_map.get(str(herb["热敏性"]).strip(), 2)
    tech_sens_str = tech["适用热敏"]
    if isinstance(tech_sens_str, str):
        tech_sens_values = [sens_map.get(s.strip(), 0) for s in re.split(r'[、，,]', tech_sens_str)]
        tech_sens_max = max(tech_sens_values) if tech_sens_values else 3
    else:
        tech_sens_max = 3
    # 药材不能比技术能处理的最高热敏等级更敏感
    if herb_sens > tech_sens_max:
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
    investment = lcc_info["平均投资"] / 10000  # 万元
    dep_years = lcc_info["平均折旧"]
    annual_throughput = 800
    depreciation = (investment * 10000 / dep_years) / annual_throughput
    # 碳交易成本
    carbon_price = 60
    carbon_cost = carbon_emission * carbon_price / 1000
    total_cost = energy_cost + depreciation + carbon_cost
    # 药效保留率
    retention = tech["平均保留率"] / 100

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

# 如果没有结果，避免后续报错
if df_results.empty:
    print("❌ 没有任何有效组合，请检查匹配规则！")
    exit()

# 归一化并计算综合得分（分组）
def group_normalize(group):
    min_cost = group["总成本(元/吨)"].min()
    max_cost = group["总成本(元/吨)"].max()
    min_carbon = group["碳排放(kgCO₂/吨)"].min()
    max_carbon = group["碳排放(kgCO₂/吨)"].max()
    # 避免除零
    norm_cost = (group["总成本(元/吨)"] - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
    norm_carbon = (group["碳排放(kgCO₂/吨)"] - min_carbon) / (max_carbon - min_carbon) if max_carbon > min_carbon else 0
    # 权重：越小越好，质量转化为惩罚项
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

# 调试输出
print(f"📊 有效组合总数: {len(df_results)}")
print(f"📊 推荐结果数: {len(df_recommend)}")
print(f"📊 药材覆盖: {df_recommend['药材名称'].nunique()}/{herbs['药材名称'].nunique()}")
print("\n推荐结果预览：")
print(df_recommend.head(10).to_string())