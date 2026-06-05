# BuzzerBeater 数据查看器
# 使用 PyQt6 编写的桌面应用程序

import sys
import json
import os
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMenuBar, QMenu, QFileDialog, QLineEdit, QLabel, QDialog,
    QDialogButtonBox, QMessageBox, QStatusBar,
    QFrame, QSplitter, QComboBox, QSpinBox, QGroupBox,
    QGridLayout, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QPalette, QColor, QFont


def same_day(date_str1, date_str2):
    """判断两个ISO日期字符串是否是同一天"""
    if not date_str1 or not date_str2:
        return False
    return date_str1[:10] == date_str2[:10]


class PlayerDetailDialog(QDialog):
    """球员详细信息对话框"""
    def __init__(self, player_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"球员详情 - {player_data.get('name', 'Unknown')}")
        self.setMinimumSize(500, 600)
        self.setup_ui(player_data)
    
    def setup_ui(self, p):
        layout = QVBoxLayout()
        basic_group = QGroupBox("基本信息")
        basic_layout = QVBoxLayout()
        fields = [
            ("ID", "id"), ("姓名", "name"), ("国籍", "nationality"),
            ("位置", "position"), ("年龄", "age"), ("身高", "height"),
            ("薪金", "salary"), ("潜力", "potential"),
        ]
        for label, key in fields:
            value = p.get(key, "N/A")
            if key == "salary" and value:
                value = f"${value:,}"
            basic_layout.addWidget(QLabel(f"{label}: {value}"))
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        skill_group = QGroupBox("技能数据")
        skill_layout = QVBoxLayout()
        skills = [
            ("跳投能力", "jump_shot"), ("投篮范围", "jump_range"),
            ("外线防守", "perim_def"), ("控球能力", "handling"),
            ("运球能力", "driving"), ("传球能力", "passing"),
            ("内线投篮", "inside_shot"), ("内线防守", "inside_def"),
            ("篮板能力", "rebound"), ("盖帽能��", "shot_block"),
        ]
        for label, key in skills:
            value = p.get(key, 0)
            skill_layout.addWidget(QLabel(f"{label}: {value}"))
        skill_group.setLayout(skill_layout)
        layout.addWidget(skill_group)
        if p.get('scrapedAt'):
            layout.addWidget(QLabel(f"数据采集时间: {p['scrapedAt']}"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        self.setLayout(layout)


class PlayerHistoryDialog(QDialog):
    """同一球员所有历史记录对话框"""
    def __init__(self, player_id, records, parent=None):
        super().__init__(parent)
        self.player_id = player_id
        self.records = records  # 原始引用，修改会同步到 model
        self.parent_window = parent
        self.selected_rows = set()
        self.manage_mode = False
        self.setWindowTitle(f"球员历史记录 - ID: {player_id}")
        self.setMinimumSize(1000, 500)
        self.main_layout = QVBoxLayout()

        # 标题栏
        title_layout = QHBoxLayout()
        self.lbl_title = QLabel(f"球员 {player_id} 共有 {len(records)} 条记录（按采集时间排序）")
        title_layout.addWidget(self.lbl_title)
        title_layout.addStretch()
        self.btn_manage = QPushButton("管理")
        self.btn_manage.clicked.connect(self.toggle_manage_mode)
        title_layout.addWidget(self.btn_manage)
        self.main_layout.addLayout(title_layout)

        self.columns = [
            ("采集时间", "scrapedAt"), ("薪金", "salary"), ("年龄", "age"),
            ("跳投", "jump_shot"), ("范围", "jump_range"), ("外防", "perim_def"),
            ("控球", "handling"), ("运球", "driving"), ("传球", "passing"),
            ("内���", "inside_shot"), ("内防", "inside_def"), ("篮板", "rebound"),
            ("盖帽", "shot_block"),
        ]

        self.table = QTableWidget()
        self.build_table()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.main_layout.addWidget(self.table)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        self.main_layout.addWidget(buttons)
        self.setLayout(self.main_layout)

    def build_table(self):
        """构建/刷新表格"""
        sorted_records = sorted(self.records, key=lambda x: x.get('scrapedAt', ''), reverse=True)

        col_count = len(self.columns)
        if self.manage_mode:
            col_count += 1  # 多一个复选框列

        self.table.clear()
        self.table.setColumnCount(col_count)
        headers = []
        if self.manage_mode:
            headers.append("")
        headers.extend([c[0] for c in self.columns])
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(sorted_records))

        for row, rec in enumerate(sorted_records):
            if self.manage_mode:
                cb = QTableWidgetItem()
                cb.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                if row in self.selected_rows:
                    cb.setCheckState(Qt.CheckState.Checked)
                else:
                    cb.setCheckState(Qt.CheckState.Unchecked)
                cb.setData(Qt.ItemDataRole.UserRole, row)  # 存排序后的行索引
                self.table.setItem(row, 0, cb)

            col_offset = 1 if self.manage_mode else 0
            for col, (_, key) in enumerate(self.columns):
                val = rec.get(key, "")
                if key == "salary" and val:
                    val = f"${val:,}"
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, id(rec))  # 通过对象id定位记录
                self.table.setItem(row, col + col_offset, item)

        self.table.itemChanged.connect(self.on_item_changed)

    def on_item_changed(self, item):
        if self.manage_mode and item.column() == 0:
            row = item.data(Qt.ItemDataRole.UserRole)
            if item.checkState() == Qt.CheckState.Checked:
                self.selected_rows.add(row)
            else:
                self.selected_rows.discard(row)

    def toggle_manage_mode(self):
        self.manage_mode = not self.manage_mode
        if self.manage_mode:
            self.btn_manage.setText("删除选中")
            self.btn_manage.setStyleSheet("background-color: #c0392b; color: white;")
            self.selected_rows.clear()
            self.table.itemChanged.disconnect(self.on_item_changed)
        else:
            # 执行删除
            if self.selected_rows:
                sorted_records = sorted(self.records, key=lambda x: x.get('scrapedAt', ''), reverse=True)
                to_delete = set()
                for idx in self.selected_rows:
                    rec = sorted_records[idx]
                    # 通过 id() 定位原始列表中要删���的记录
                    for orig in list(self.records):
                        if id(orig) == id(rec):
                            to_delete.add(id(orig))
                            break

                before = len(self.records)
                self.records[:] = [r for r in self.records if id(r) not in to_delete]
                deleted = before - len(self.records)

                self.lbl_title.setText(f"球员 {self.player_id} 共有 {len(self.records)} 条记录（按采集时间排序）")

                # 通知主窗口刷新
                if self.parent_window and hasattr(self.parent_window, 'update_table'):
                    self.parent_window.update_table()

                QMessageBox.information(self, "删除完成", f"已删除 {deleted} 条记录")
            else:
                self.btn_manage.setText("管理")
                self.btn_manage.setStyleSheet("")
                self.manage_mode = False
                return

            self.btn_manage.setText("管理")
            self.btn_manage.setStyleSheet("")

        self.build_table()


class PlayerTableModel:
    """球员数据模型"""
    def __init__(self):
        self.players = []
        self.columns = [
            ("id", "ID"), ("name", "姓名"), ("position", "位置"),
            ("age", "年龄"), ("nationality", "国籍"), ("salary", "薪金"),
            ("potential", "潜力"),
            ("jump_shot", "跳投"), ("jump_range", "范围"),
            ("perim_def", "外防"), ("handling", "控球"),
            ("driving", "运球"), ("passing", "传球"),
            ("inside_shot", "内投"), ("inside_def", "内防"),
            ("rebound", "篮板"), ("shot_block", "盖帽"),
        ]
    
    def load_from_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.sqlite', '.sqlite3', '.db'):
            return self.load_from_sqlite(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'players' in data:
                self.players = data['players']
            elif isinstance(data, list):
                self.players = data
    
    def load_from_sqlite(self, filepath):
        """从 SQLite 文件加载球员数据"""
        conn = sqlite3.connect(filepath)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(players)")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.execute("SELECT * FROM players")
        rows = cursor.fetchall()
        self.players = []
        for row in rows:
            player = dict(zip(columns, row))
            self.players.append(player)
        conn.close()
    
    def read_file(self, filepath):
        """读取文件（JSON或SQLite）返回球员列表，不修改自身"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.sqlite', '.sqlite3', '.db'):
            conn = sqlite3.connect(filepath)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(players)")
            columns = [row[1] for row in cursor.fetchall()]
            cursor.execute("SELECT * FROM players")
            rows = cursor.fetchall()
            players = [dict(zip(columns, row)) for row in rows]
            conn.close()
            return players
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'players' in data:
                return data['players']
            elif isinstance(data, list):
                return data
        return []
    
    def merge_from_file(self, filepath):
        """合并另一个文件的数据（同ID同天去重）"""
        new_players = self.read_file(filepath)
        old_ids = {}  # key: (id, date) -> True
        for p in self.players:
            pid = p.get('id')
            pdate = (p.get('scrapedAt') or '')[:10]
            if pid is not None and pdate:
                old_ids[(pid, pdate)] = True
        
        imported = 0
        skipped = 0
        for p in new_players:
            pid = p.get('id')
            pdate = (p.get('scrapedAt') or '')[:10]
            if pid is not None and (pid, pdate) in old_ids:
                skipped += 1
            else:
                self.players.append(p)
                imported += 1
                if pid is not None and pdate:
                    old_ids[(pid, pdate)] = True
        
        return imported, skipped
    
    def save_to_file(self, filepath):
        """将当前数据保存到JSON或SQLite文件"""
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.sqlite', '.sqlite3', '.db'):
            self.save_to_sqlite(filepath)
        else:
            self.save_to_json(filepath)
    
    def save_to_json(self, filepath):
        """保存为JSON"""
        data = {
            'exportedAt': __import__('datetime').datetime.now().isoformat(),
            'count': len(self.players),
            'players': self.players
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_to_sqlite(self, filepath):
        """保存为SQLite"""
        if os.path.exists(filepath):
            os.remove(filepath)
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        # 建表（使用当前players中有的字段）
        all_keys = set()
        for p in self.players:
            all_keys.update(p.keys())
        columns = [
            ('id', 'INTEGER'), ('name', 'TEXT'), ('salary', 'INTEGER'),
            ('age', 'INTEGER'), ('height', 'TEXT'), ('nationality', 'TEXT'),
            ('potential', 'TEXT'), ('position', 'TEXT'),
            ('jump_shot', 'INTEGER'), ('jump_range', 'INTEGER'),
            ('perim_def', 'INTEGER'), ('handling', 'INTEGER'),
            ('driving', 'INTEGER'), ('passing', 'INTEGER'),
            ('inside_shot', 'INTEGER'), ('inside_def', 'INTEGER'),
            ('rebound', 'INTEGER'), ('shot_block', 'INTEGER'),
            ('scraped_at', 'TEXT'),
        ]
        col_names = [c[0] for c in columns]
        col_defs = ', '.join([f'{k} {t}' for k, t in columns])
        cursor.execute(f"CREATE TABLE players ({col_defs})")
        placeholders = ', '.join(['?' for _ in col_names])
        for p in self.players:
            values = [p.get(k, None) for k in col_names]
            cursor.execute(f"INSERT INTO players ({', '.join(col_names)}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
    
    @staticmethod
    def potential_to_number(pot):
        """将潜力文字转为数字等级"""
        if pot is None:
            return 0
        if isinstance(pot, (int, float)):
            return int(pot)
        text = str(pot).strip().lower()
        
        # 文字→数字映射
        mapping = [
            ('announcer', 0),
            ('bench warmer', 1), ('bench', 1),
            ('role player', 2), ('role', 2),
            ('6th man', 3), ('6th', 3),
            ('starter', 4),
            ('star', 5),
            ('allstar', 6), ('all star', 6),
            ('perennial allstar', 7), ('perennial', 7),
            ('superstar', 8),
            ('mvp', 9),
            ('hall of famer', 10), ('hall', 10),
            ('all-time great', 11), ('all time great', 11),
        ]
        for keyword, level in mapping:
            if keyword in text:
                return level
        return 0
    
    def get_latest_unique(self):
        """获取每个ID的最新一条记录"""
        seen = {}
        for p in self.players:
            pid = p.get('id')
            if pid is None:
                continue
            if pid not in seen:
                seen[pid] = p
            else:
                # ���较采集时间，保留最新的
                old_time = seen[pid].get('scrapedAt', '')
                new_time = p.get('scrapedAt', '')
                if new_time > old_time:
                    seen[pid] = p
        return list(seen.values())
    
    def get_history(self, player_id):
        """获取某个ID的所有历史记录（按采集时间排序）"""
        records = [p for p in self.players if str(p.get('id')) == str(player_id)]
        return sorted(records, key=lambda x: x.get('scrapedAt', ''), reverse=True)
    
    def row_count(self):
        return len(self.players)
    
    def column_count(self):
        return len(self.columns)
    
    def data(self, player, column):
        key, _ = self.columns[column]
        value = player.get(key)
        if value is None:
            return ""
        if key == "salary" and value:
            return f"${value:,}"
        if isinstance(value, (int, float)) and value == 0:
            return ""
        return str(value)


class FilterPanel(QWidget):
    """筛选面板"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.filters = {}
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 基本筛选
        basic_grid = QGridLayout()
        
        self.filters['age_min'] = QSpinBox()
        self.filters['age_min'].setRange(0, 99)
        self.filters['age_min'].setPrefix("≥ ")
        self.filters['age_min'].setFixedWidth(100)
        self.filters['age_max'] = QSpinBox()
        self.filters['age_max'].setRange(0, 99)
        self.filters['age_max'].setPrefix("≤ ")
        self.filters['age_max'].setFixedWidth(100)
        
        self.filters['salary_min'] = QSpinBox()
        self.filters['salary_min'].setRange(0, 9999999)
        self.filters['salary_min'].setPrefix("≥ $")
        self.filters['salary_min'].setSingleStep(1000)
        self.filters['salary_min'].setFixedWidth(130)
        self.filters['salary_max'] = QSpinBox()
        self.filters['salary_max'].setRange(0, 9999999)
        self.filters['salary_max'].setPrefix("≤ $")
        self.filters['salary_max'].setSingleStep(1000)
        self.filters['salary_max'].setFixedWidth(130)
        
        self.filters['potential_min'] = QSpinBox()
        self.filters['potential_min'].setRange(0, 11)
        self.filters['potential_min'].setPrefix("≥ ")
        self.filters['potential_min'].setFixedWidth(90)
        self.filters['potential_max'] = QSpinBox()
        self.filters['potential_max'].setRange(0, 11)
        self.filters['potential_max'].setPrefix("≤ ")
        self.filters['potential_max'].setFixedWidth(90)
        
        basic_grid.addWidget(QLabel("年龄:"), 0, 0)
        basic_grid.addWidget(self.filters['age_min'], 0, 1)
        basic_grid.addWidget(self.filters['age_max'], 0, 2)
        basic_grid.addWidget(QLabel("薪金:"), 1, 0)
        basic_grid.addWidget(self.filters['salary_min'], 1, 1)
        basic_grid.addWidget(self.filters['salary_max'], 1, 2)
        basic_grid.addWidget(QLabel("潜力:"), 2, 0)
        basic_grid.addWidget(self.filters['potential_min'], 2, 1)
        basic_grid.addWidget(self.filters['potential_max'], 2, 2)
        
        basic_group = QGroupBox("基本筛选")
        basic_group.setLayout(basic_grid)
        layout.addWidget(basic_group)
        
        # 技能筛选
        skill_grid = QGridLayout()
        skills = [
            ("跳投", "jump_shot"), ("范围", "jump_range"), ("外防", "perim_def"),
            ("控球", "handling"), ("运球", "driving"), ("传球", "passing"),
            ("内投", "inside_shot"), ("内防", "inside_def"),
            ("篮板", "rebound"), ("盖帽", "shot_block"),
        ]
        
        self.skill_filters = {}
        for i, (label, key) in enumerate(skills):
            col = i % 2
            row = i // 2 * 2
            skill_grid.addWidget(QLabel(f"{label}:"), row, col * 3)
            w_min = QSpinBox()
            w_min.setRange(0, 40)
            w_min.setPrefix("≥ ")
            w_min.setFixedWidth(70)
            w_max = QSpinBox()
            w_max.setRange(0, 40)
            w_max.setPrefix("≤ ")
            w_max.setFixedWidth(70)
            skill_grid.addWidget(w_min, row, col * 3 + 1)
            skill_grid.addWidget(w_max, row, col * 3 + 2)
            self.skill_filters[key] = {'min': w_min, 'max': w_max}
        
        skill_group = QGroupBox("技能筛选")
        skill_group.setLayout(skill_grid)
        layout.addWidget(skill_group)
        
        # 重置按钮
        reset_btn = QPushButton("重置筛选")
        reset_btn.clicked.connect(self.reset_all)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def reset_all(self):
        for key, w in self.filters.items():
            if isinstance(w, QSpinBox):
                w.setValue(0)
        for key, pair in self.skill_filters.items():
            pair['min'].setValue(0)
            pair['max'].setValue(0)
    
    def matches(self, player):
        """检查球员是否匹配所有筛选条件"""
        # 年龄
        age = player.get('age', 0) or 0
        if self.filters['age_min'].value() > 0 and age < self.filters['age_min'].value():
            return False
        if self.filters['age_max'].value() > 0 and age > self.filters['age_max'].value():
            return False
        
        # 薪金
        salary = player.get('salary', 0) or 0
        if self.filters['salary_min'].value() > 0 and salary < self.filters['salary_min'].value():
            return False
        if self.filters['salary_max'].value() > 0 and salary > self.filters['salary_max'].value():
            return False
        
        # 潜力 - 文字→数字转换
        pot_num = PlayerTableModel.potential_to_number(player.get('potential', ''))
        if self.filters['potential_min'].value() > 0 and pot_num < self.filters['potential_min'].value():
            return False
        if self.filters['potential_max'].value() > 0 and pot_num > self.filters['potential_max'].value():
            return False
        
        # 技能
        for key, pair in self.skill_filters.items():
            val = player.get(key, 0) or 0
            min_val = pair['min'].value()
            max_val = pair['max'].value()
            if min_val > 0 and val < min_val:
                return False
            if max_val > 0 and val > max_val:
                return False
        
        return True


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.model = PlayerTableModel()
        self.current_file = None
        self.show_latest_only = True  # 默认只显示最新记录
        self.sort_column = -1  # 当前排序列，-1表示未排序
        self.sort_order = Qt.SortOrder.AscendingOrder  # 当前排序方向
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("BuzzerBeater 数据查看器 Ver1.1")
        self.setGeometry(100, 100, 1600, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        # 左侧筛选面板
        self.filter_panel = FilterPanel()
        for w in self.filter_panel.findChildren(QSpinBox):
            w.valueChanged.connect(self.filter_table)
        self.filter_panel.findChild(QPushButton).clicked.connect(self.filter_table)
        
        scroll = QScrollArea()
        scroll.setWidget(self.filter_panel)
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(380)
        scroll.setMaximumWidth(400)
        main_layout.addWidget(scroll)
        
        # 右侧区域
        right = QWidget()
        right_layout = QVBoxLayout(right)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.btn_open = QPushButton("打开")
        self.btn_open.clicked.connect(self.open_file)
        toolbar.addWidget(self.btn_open)
        
        self.btn_merge = QPushButton("导入")
        self.btn_merge.clicked.connect(self.merge_file)
        toolbar.addWidget(self.btn_merge)
        
        self.btn_save = QPushButton("保存")
        self.btn_save.clicked.connect(self.save_file)
        toolbar.addWidget(self.btn_save)
        
        self.chk_latest = QCheckBox("仅最新")
        self.chk_latest.setChecked(True)
        self.chk_latest.toggled.connect(self.on_show_latest_toggled)
        toolbar.addWidget(self.chk_latest)
        
        toolbar.addWidget(QLabel("搜索:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("姓名/位置/国籍/ID...")
        self.search_box.textChanged.connect(self.filter_table)
        toolbar.addWidget(self.search_box)
        
        toolbar.addWidget(QLabel("位置:"))
        self.position_filter = QComboBox()
        self.position_filter.addItem("全部")
        self.position_filter.currentTextChanged.connect(self.filter_table)
        toolbar.addWidget(self.position_filter)
        
        toolbar.addStretch()
        self.lbl_count = QLabel("共 0 条")
        toolbar.addWidget(self.lbl_count)
        
        right_layout.addLayout(toolbar)
        
        # 表格
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.doubleClicked.connect(self.on_table_double_click)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        right_layout.addWidget(self.table)
        
        main_layout.addWidget(right)
        
        # 状态栏
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("就绪")
        
        # 菜单
        self.create_menu()
    
    def create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开文件...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        merge_action = QAction("导入数据（合并）...", self)
        merge_action.setShortcut("Ctrl+I")
        merge_action.triggered.connect(self.merge_file)
        file_menu.addAction(merge_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("保存", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("另存为...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self.save_as_file)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于", self)
        about_action.triggered.connect(lambda: QMessageBox.about(self, "关于",
            "BuzzerBeater 数据查看器\n\n"
            "查看BuzzerBeater导出的JSON/SQLite球员数据\n"
            "支持多条件筛选、数据合并、历史记录查看"))
        help_menu.addAction(about_action)
    
    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "",
            "支持的格式 (*.json *.sqlite *.sqlite3 *.db);;JSON 文件 (*.json);;SQLite 文件 (*.sqlite *.sqlite3 *.db)"
        )
        if filepath:
            try:
                self.model.load_from_file(filepath)
                self.current_file = filepath
                self.update_table()
                self.update_position_filter()
                self.statusBar().showMessage(f"已加载: {os.path.basename(filepath)} | 共 {len(self.model.players)} 条记录")
                self.setWindowTitle(f"BuzzerBeater 数据查看器 - {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败:\n{str(e)}")
    
    def merge_file(self):
        """导入另一个文件的数据，同ID同天去重"""
        if len(self.model.players) == 0:
            QMessageBox.information(self, "提示", "请先打开一个数据文件")
            return
        filepath, _ = QFileDialog.getOpenFileName(
            self, "导入数据（合并）", "",
            "支持的格式 (*.json *.sqlite *.sqlite3 *.db);;JSON 文件 (*.json);;SQLite 文件 (*.sqlite *.sqlite3 *.db)"
        )
        if filepath:
            try:
                imported, skipped = self.model.merge_from_file(filepath)
                self.update_table()
                self.update_position_filter()
                self.statusBar().showMessage(
                    f"导入完成: 新增 {imported} 条, 跳过 {skipped} 条(同ID同天已存在) | 共 {len(self.model.players)} 条记录"
                )
                QMessageBox.information(self, "导入完成",
                    f"导入文件: {os.path.basename(filepath)}\n"
                    f"新增: {imported} 条\n"
                    f"跳过（同ID同天）: {skipped} 条\n"
                    f"当前总计: {len(self.model.players)} 条"
                )
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败:\n{str(e)}")
    
    def save_file(self):
        """保存到当前文件，如果没有则另存为"""
        if self.current_file and os.path.exists(self.current_file):
            try:
                self.model.save_to_file(self.current_file)
                self.statusBar().showMessage(f"已保存: {os.path.basename(self.current_file)} | {len(self.model.players)} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
        else:
            self.save_as_file()
    
    def save_as_file(self):
        """另存为"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "另存为", "",
            "JSON 文件 (*.json);;SQLite 文件 (*.sqlite)"
        )
        if filepath:
            try:
                self.model.save_to_file(filepath)
                self.current_file = filepath
                self.statusBar().showMessage(f"已保存: {os.path.basename(filepath)} | {len(self.model.players)} 条记录")
                self.setWindowTitle(f"BuzzerBeater 数据查看器 - {os.path.basename(filepath)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
    
    def on_show_latest_toggled(self, checked):
        self.show_latest_only = checked
        self.filter_table()
    
    def update_position_filter(self):
        positions = set()
        src = self.model.get_latest_unique() if self.show_latest_only else self.model.players
        for p in src:
            if p.get('position'):
                positions.add(p['position'])
        self.position_filter.blockSignals(True)
        self.position_filter.clear()
        self.position_filter.addItem("全部")
        for pos in sorted(positions):
            self.position_filter.addItem(pos)
        self.position_filter.blockSignals(False)
    
    def filter_table(self):
        search_text = self.search_box.text().lower()
        position_filter = self.position_filter.currentText()
        
        # 决定数据源
        src = self.model.get_latest_unique() if self.show_latest_only else self.model.players
        
        self.table.setRowCount(0)
        row = 0
        
        # 先把所有匹配结果收集起来，再插入表格
        matches = []
        for i, player in enumerate(src):
            # 位置过滤
            if position_filter != "全部" and player.get('position') != position_filter:
                continue
            # 搜索过滤
            if search_text:
                searchable = ['name', 'position', 'nationality', 'potential', 'id']
                match_found = False
                for key in searchable:
                    if search_text in str(player.get(key, '')).lower():
                        match_found = True
                        break
                if not match_found:
                    continue
            # 多条件筛选
            if not self.filter_panel.matches(player):
                continue
            
            matches.append(player)
        
        # 插入表格
        columns = self.model.columns
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in columns])
        
        # 修复：设置列标题
        header = self.table.horizontalHeader()
        
        self.table.setRowCount(len(matches))
        for row_idx, player in enumerate(matches):
            for col in range(len(columns)):
                key, _ = columns[col]
                raw_value = player.get(key)
                item = QTableWidgetItem(self.model.data(player, col))
                # 为数值列设置排序用的数值
                if key in ('id', 'age', 'salary', 'potential',
                           'jump_shot', 'jump_range', 'perim_def',
                           'handling', 'driving', 'passing',
                           'inside_shot', 'inside_def', 'rebound', 'shot_block'):
                    num_val = raw_value
                    if key == 'potential':
                        num_val = PlayerTableModel.potential_to_number(raw_value)
                    if num_val is None:
                        num_val = 0
                    item.setData(Qt.ItemDataRole.UserRole, float(num_val))
                # 如果是ID列，特殊标记以便双击查看历史
                if key == 'id':
                    item.setData(Qt.ItemDataRole.UserRole + 1, player.get('id'))
                    item.setForeground(QColor(100, 180, 255))  # 蓝色显示，提示可点击
                self.table.setItem(row_idx, col, item)
        
        # 调整列宽
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # 应用排序
        if self.sort_column >= 0:
            self.table.sortItems(self.sort_column, self.sort_order)
        
        self.lbl_count.setText(f"共 {len(matches)} 条")
        self.statusBar().showMessage(f"显示 {len(matches)} / {len(src)} 条记录")
    
    def update_table(self):
        self.filter_table()
    
    def on_header_clicked(self, col):
        """点击列头排序"""
        if self.sort_column == col:
            # 同一列，切换排序方向
            self.sort_order = Qt.SortOrder.DescendingOrder if self.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder
        else:
            self.sort_column = col
            self.sort_order = Qt.SortOrder.AscendingOrder
        
        # 自定义排序：数值列按UserRole排序，文字列按文本排序
        key, _ = self.model.columns[col]
        numeric_keys = {'id', 'age', 'salary', 'potential',
                        'jump_shot', 'jump_range', 'perim_def',
                        'handling', 'driving', 'passing',
                        'inside_shot', 'inside_def', 'rebound', 'shot_block'}
        
        if key in numeric_keys:
            # 数值排序：使用UserRole中存储的数值
            self.table.sortItems(col, self.sort_order)
            # QTableWidget默认按文本排序，需要手动按数值重排
            rows_data = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, col)
                num_val = item.data(Qt.ItemDataRole.UserRole) if item and item.data(Qt.ItemDataRole.UserRole) is not None else 0
                row_items = []
                for c in range(self.table.columnCount()):
                    row_items.append(self.table.takeItem(row, c))
                rows_data.append((num_val, row_items))
            
            # 排序
            rows_data.sort(key=lambda x: x[0], reverse=(self.sort_order == Qt.SortOrder.DescendingOrder))
            
            # 重新填入
            for row_idx, (_, row_items) in enumerate(rows_data):
                for c, item in enumerate(row_items):
                    if item:
                        self.table.setItem(row_idx, c, item)
        else:
            self.table.sortItems(col, self.sort_order)
    
    def on_table_double_click(self, index):
        row = index.row()
        item = self.table.item(row, 0)  # ID列
        if item:
            player_id = item.data(Qt.ItemDataRole.UserRole + 1)
            if player_id:
                # 获取该ID的所有历史记录
                records = self.model.get_history(player_id)
                if len(records) > 1:
                    dialog = PlayerHistoryDialog(player_id, records, self)
                    dialog.exec()
                else:
                    # 只有一条记录，直接显示详情
                    player = records[0] if records else None
                    if player:
                        dialog = PlayerDetailDialog(player, self)
                        dialog.exec()
    
    def show_about(self):
        QMessageBox.about(self, "关于",
            "BuzzerBeater 数据查看器\n\n"
            "查看BuzzerBeater导出的JSON球员数据\n"
            "支持多条件筛选、历史记录查看")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
