#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import random
import datetime

# 设置输出编码
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

random.seed(42)

# 名字生成素材
first_names_cn = ["Wang", "Li", "Zhang", "Liu", "Chen", "Yang", "Huang", "Zhao", "Zhou", "Wu",
                   "Xu", "Sun", "Hu", "Zhu", "Gao", "Lin", "He", "Guo", "Ma", "Luo"]
first_names_en = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
                   "Thomas", "Charles", "Chris", "Kobe", "LeBron", "Stephen", "Kevin", "Anthony",
                   "Paul", "Derrick", "Russell", "Blake"]
last_names_en = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Jackson", "White",
                  "Harris", "Martin", "Thompson", "Robinson", "Clark"]
genders = ["M", "F"]

positions = ["PG", "SG", "SF", "PF", "C"]
potential_texts = [
    ("announcer", 0), ("bench warmer", 1), ("role player", 2), ("6th man", 3),
    ("starter", 4), ("star", 5), ("allstar", 6), ("perennial allstar", 7),
    ("superstar", 8), ("MVP", 9), ("hall of famer", 10), ("all-time great", 11)
]
nationalities = ["USA", "China", "France", "Spain", "Germany", "Italy", "Australia",
                  "Argentina", "Brazil", "Canada", "Greece", "Hrvatska", "Serbia",
                  "Russia", "Turkey", "Lithuania", "Nigeria", "Angola", "Japan", "Korea"]

def generate_name(idx):
    if idx % 3 == 0:
        return f"{random.choice(first_names_cn)} {random.choice(last_names_en)}"
    return f"{random.choice(first_names_en)} {random.choice(last_names_en)}"

def generate_player(id_base, age_shift=0):
    pot_text, pot_num = random.choice(potential_texts)
    age = random.randint(17, 38) + age_shift
    height_cm = random.randint(175, 220)
    feet = int((height_cm - 5) / 30.48)
    inches = int(((height_cm - 5) / 2.54) % 12)
    height = f"{feet}'{inches}\" / {height_cm} cm"
    
    base_skills = [random.randint(1, 10) for _ in range(10)]
    # 根据潜力调整技能水平
    boost = pot_num * 8
    skills = [min(40, s + max(0, boost - random.randint(0, 20))) for s in base_skills]
    
    salary = int(random.randint(1000, 50000) * (1 + pot_num * 0.15))
    
    return {
        "name": generate_name(id_base),
        "id": 50000000 + id_base,
        "position": random.choice(positions),
        "salary": salary,
        "age": age,
        "height": height,
        "potential": pot_text,
        "jump_shot": skills[0], "jump_range": skills[1], "perim_def": skills[2],
        "handling": skills[3], "driving": skills[4], "passing": skills[5],
        "inside_shot": skills[6], "inside_def": skills[7], "rebound": skills[8],
        "shot_block": skills[9],
        "stamina": random.randint(1, 20),
        "free_throw": random.randint(1, 20),
        "nationality": random.choice(nationalities),
    }

def make_date(base_date, days_ago):
    d = base_date - datetime.timedelta(days=days_ago)
    return d.isoformat() + "Z"

players = []
base_date = datetime.datetime(2026, 5, 16, 9, 17, 23)
current_id = 0

# 2个ID 各有50条不同时间数据 = 100条
print("生成 2个ID × 50条...")
for _ in range(2):
    pid = current_id
    current_id += 1
    base_player = generate_player(pid)
    for i in range(50):
        p = base_player.copy()
        p["scrapedAt"] = make_date(base_date, i * 7)  # 每7天采集一次
        players.append(p)

# 10个ID 各有10条不同时间数据 = 100条
print("生成 10个ID × 10条...")
for _ in range(10):
    pid = current_id
    current_id += 1
    base_player = generate_player(pid)
    for i in range(10):
        p = base_player.copy()
        p["scrapedAt"] = make_date(base_date, i * 14)
        players.append(p)

# 50个ID 各有3条不同时间数据 = 150条
print("生成 50个ID × 3条...")
for _ in range(50):
    pid = current_id
    current_id += 1
    base_player = generate_player(pid)
    for i in range(3):
        p = base_player.copy()
        p["scrapedAt"] = make_date(base_date, i * 30)
        players.append(p)

# 剩余单条数据 = 650条
print(f"生成 {650} 个单��ID...")
for _ in range(650):
    pid = current_id
    current_id += 1
    p = generate_player(pid)
    p["scrapedAt"] = make_date(base_date, random.randint(0, 365))
    players.append(p)

print(f"总计: {len(players)} 条记录")
print(f"不同ID数: {current_id}")

# 验证数据分布
from collections import Counter
id_counts = Counter(p["id"] for p in players)
print(f"不同ID数: {len(id_counts)}")
multi = {k: v for k, v in id_counts.items() if v > 1}
print(f"多记录ID数: {len(multi)}")
for cnt, num in Counter(multi.values()).items():
    print(f"  {num} 个ID有 {cnt} 条记录")

# 保存
output = {
    "exportedAt": base_date.isoformat() + "Z",
    "count": len(players),
    "players": players
}

filepath = "D:\\WWW\\buzzerbeater-scraper-extension\\test_data_1000.json"
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"已保存到: {filepath}")
print(f"文件大小: {len(json.dumps(output, ensure_ascii=False)) // 1024} KB")
