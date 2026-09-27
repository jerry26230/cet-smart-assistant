"""专项练习输入、历史及按专项汇总。"""

from uuid import uuid4

from aqt.qt import (QCheckBox, QComboBox, QDate, QDateEdit, QDialog, QFormLayout, QHBoxLayout,
                    QLabel, QLineEdit, QPlainTextEdit, QPushButton, QSpinBox,
                    QTableWidget, QTableWidgetItem, QVBoxLayout, QAbstractItemView, QScrollArea, QWidget)
from aqt.utils import showWarning

from .data_service import DataError
from .practice import PracticeRecord, SKILLS, append_record, read_records, summarize


class PracticeDialog(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.path = path
        self.record_id = str(uuid4())
        self.blocked = False
        self.setWindowTitle("CET 智能备考助手 · 专项练习记录")
        self.resize(820, 680)
        layout = QVBoxLayout(self)
        hint = QLabel("记录实际完成的练习。得分可留空；只有你确认同题型、相近难度、同评分方式的记录才用于趋势。")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        form = QFormLayout()
        self.day = QDateEdit(QDate.currentDate())
        self.day.setCalendarPopup(True)
        self.day.setDisplayFormat("yyyy-MM-dd")
        self.day.setMaximumDate(QDate.currentDate())
        self.skill = QComboBox()
        for key, label in SKILLS.items():
            self.skill.addItem(label, key)
        self.minutes = QSpinBox()
        self.minutes.setRange(1, 1440)
        self.minutes.setValue(20)
        self.title = QLineEdit()
        self.title.setMaxLength(200)
        self.title.setPlaceholderText("例如：2025 年 6 月六级阅读第一套")
        self.score = QLineEdit()
        self.score.setPlaceholderText("可留空，例如 8")
        self.maximum = QLineEdit()
        self.maximum.setPlaceholderText("与得分同时填写，例如 10")
        self.comparison_group = QLineEdit()
        self.comparison_group.setMaxLength(100)
        self.comparison_group.setPlaceholderText("例如：六级仔细阅读·同教材同难度；不同组不能混填")
        self.questions = QLineEdit()
        self.questions.setPlaceholderText("题量，可留空，例如 10")
        self.comparable = QCheckBox("确认本组题型、难度和评分方式可比，纳入趋势")
        self.note = QPlainTextEdit()
        self.note.setMaximumHeight(65)
        for label, widget in (("日期", self.day), ("专项", self.skill), ("实际用时（分钟）", self.minutes),
                              ("练习名称", self.title), ("得分（可选）", self.score),
                              ("满分（可选）", self.maximum), ("题量（可选）", self.questions),
                              ("可比组（可选）", self.comparison_group), ("可比确认", self.comparable), ("复盘备注", self.note)):
            widget.setAccessibleName(label)
            form.addRow(label, widget)
        form_content = QWidget()
        form_content.setLayout(form)
        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setWidget(form_content)
        form_scroll.setMinimumHeight(200)
        form_scroll.setMaximumHeight(370)
        layout.addWidget(form_scroll)
        self.save_button = QPushButton("保存练习记录")
        self.save_button.clicked.connect(self.save)
        close = QPushButton("关闭")
        close.clicked.connect(self.reject)
        buttons = QHBoxLayout()
        buttons.addWidget(self.save_button)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.status = QLabel("尚未提交。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.history = QTableWidget(0, 9)
        self.history.setHorizontalHeaderLabels(["日期", "专项", "分钟", "练习名称", "原始得分 / 满分", "复盘备注", "可比组", "纳入趋势", "题量"])
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.history)
        for widget in (self.title, self.score, self.maximum, self.note, self.comparison_group, self.questions):
            widget.textChanged.connect(self.changed)
        self.comparable.toggled.connect(self.changed)
        self.day.dateChanged.connect(self.changed)
        self.skill.currentIndexChanged.connect(self.changed)
        self.minutes.valueChanged.connect(self.changed)
        self.refresh()

    def changed(self, *args):
        self.record_id = str(uuid4())
        if not self.blocked:
            self.save_button.setEnabled(True)
            self.status.setText("当前练习尚未保存。")

    def refresh(self):
        try:
            records, skipped = read_records(self.path)
        except DataError as error:
            self.blocked = True
            self.save_button.setEnabled(False)
            self.status.setText(str(error))
            return
        totals = summarize(records)
        text = "全部已识别记录：" + "；".join(
            f"{SKILLS[key]} {value['count']} 次 / {value['minutes']} 分钟" for key, value in totals.items())
        text += "\n列表显示最近 500 条，汇总包含全部已识别记录。"
        if skipped:
            text += f" {skipped} 条旧格式或无效记录已保留，未纳入汇总。"
        self.summary.setText(text)
        visible = records[:500]
        self.history.setRowCount(len(visible))
        for row, record in enumerate(visible):
            score = "未记录" if record.score is None else f"{record.score:g} / {record.maximum:g}"
            for column, value in enumerate((record.day, SKILLS[record.skill], str(record.minutes), record.title, score, record.note, record.comparison_group, "是" if record.comparable else "否", str(record.questions or "未填"))):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.history.setItem(row, column, item)
        self.history.resizeColumnsToContents()
        self.history.setColumnWidth(3, 190)
        self.history.setColumnWidth(5, 180)

    def save(self):
        if self.blocked or not self.save_button.isEnabled():
            return
        try:
            score = float(self.score.text()) if self.score.text().strip() else None
            maximum = float(self.maximum.text()) if self.maximum.text().strip() else None
            record = PracticeRecord(self.day.date().toString("yyyy-MM-dd"), self.skill.currentData(),
                                    self.minutes.value(), self.title.text().strip(), score, maximum,
                                    self.note.toPlainText().strip(), self.comparison_group.text().strip(),
                                    self.comparable.isChecked(), int(self.questions.text()) if self.questions.text().strip() else None)
            append_record(self.path, record, self.record_id)
        except (ValueError, DataError) as error:
            showWarning(str(error), parent=self)
            return
        self.refresh()
        self.save_button.setEnabled(False)
        self.status.setText("练习已保存。修改表单后可记录下一次练习；重复点击不会再次保存。")
