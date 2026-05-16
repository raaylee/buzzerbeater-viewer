# 🖥️ BuzzerBeater 数据查看器

[BuzzerBeater](https://www.buzzerbeater.com/) 篮球经理游戏的球员数据桌面查看器，配合 [buzzerbeater-scraper-extension](https://github.com/raaylee/buzzerbeater-scraper-extension) 浏览器插件使用。

基于 PyQt6 构建，跨平台（Windows / macOS / Linux）。

---

## 功能

- **多格式支持** — 直接打开 JSON 和 SQLite 文件（`.json` / `.sqlite` / `.sqlite3` / `.db`）
- **数据合并** — 导入多个文件自动合并，同 ID 同天去重
- **多维筛选** — 年龄、薪金、潜力、10 项技能的范围筛选 + 位置过滤 + 关键词搜索
- **最新记录模式** — 一键切换，只显示每个球员的最新记录
- **历史追溯** — 双击球员查看全部历史数据变化
- **批量管理** — 在历史记录窗口可批量删除冗余数据
- **数据持久化** — 保存 / 另存为 JSON 或 SQLite
- **暗色主题** — 舒适暗色界面，长时间使用不疲劳

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 打开文件 |
| `Ctrl+S` | 保存 |
| `Ctrl+Shift+S` | 另存为 |
| `Ctrl+I` | 导入合并 |
| `Ctrl+Q` | 退出 |

---

## 安装与运行

### 前置要求

- Python 3.8+

### 安装

```bash
pip install PyQt6>=6.5.0
```

### 运行

```bash
cd buzzerbeater-viewer
python viewer.py
```

---

## 数据字段

| 类别 | 字段 | 说明 |
|------|------|------|
| **基本信息** | id, name, position, age, height, nationality, salary, potential | 球员基本资料 |
| **技能** | jump_shot, jump_range, perim_def, handling, driving, passing, inside_shot, inside_def, rebound, shot_block | 10 项篮球技能 |
| **元数据** | stamina, free_throw, scrapedAt | 体能、罚球、采集时间 |

### 潜力等级映射

| 文字（英文 / 中文） | 数值 |
|---|---|
| announcer / 播音员 | 0 |
| bench warmer / 板凳球员 | 1 |
| role player / 角色球员 | 2 |
| 6th man / 第六人 | 3 |
| starter / 主力 | 4 |
| star / 明星球员 | 5 |
| allstar / 全明星 | 6 |
| perennial allstar / 常驻全明星 | 7 |
| superstar / 超级巨星 | 8 |
| MVP / MVP | 9 |
| hall of famer / 名人堂 | 10 |
| all-time great / 历史级巨星 | 11 |

---

## 相关项目

- [buzzerbeater-scraper-extension](https://github.com/raaylee/buzzerbeater-scraper-extension) — BuzzerBeater 数据采集浏览器插件
