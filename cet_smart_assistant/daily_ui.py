"""Actionable daily tasks without taking over Anki scheduling."""
from datetime import date
from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QPlainTextEdit
from aqt.utils import showWarning
from .daily import LABELS, RATINGS, MODES, ensure_day, load_days, record_result, exercise
from .data_service import DataError


class DailyDialog(QDialog):
    def __init__(self, parent, path, plan):
        super().__init__(parent)
        self.path, self.day = path, date.today().isoformat()
        self.setWindowTitle("今日任务 · 认识与会用")
        self.resize(760, 800)
        self.setStyleSheet("""
            QDialog { font-size: 14px; }
            QListWidget, QPlainTextEdit { border: 1px solid palette(mid); border-radius: 10px; padding: 12px; }
            QListWidget::item { padding: 8px; }
            QPushButton { padding: 9px 14px; border: 1px solid palette(mid); border-radius: 8px; }
            QPushButton:hover { background: palette(alternate-base); }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        note = QLabel("任务在首次打开时固定，计划修改次日生效。分钟数是预算，并非已学习时长。\n阅读与写作分别自评，不代表考试能力；例句为原创示例，非真题。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.list = QListWidget()
        self.list.setMaximumHeight(160)
        layout.addWidget(self.list)
        self.prompt = QPlainTextEdit()
        self.prompt.setMinimumHeight(180)
        self.prompt.setReadOnly(True)
        layout.addWidget(self.prompt)
        self.response = QPlainTextEdit()
        self.response.setPlaceholderText("先尝试作答（草稿仅留在本窗口，不保存），再核对参考答案。")
        self.response.setMaximumHeight(100)
        layout.addWidget(self.response)
        self.reveal = QPushButton("显示参考答案")
        self.reveal.clicked.connect(self.show_answer)
        layout.addWidget(self.reveal)
        row = QHBoxLayout()
        self.ratings = []
        for value, label in RATINGS.items():
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, value=value: self.save_result(value))
            self.ratings.append(button)
            row.addWidget(button)
        layout.addLayout(row)
        self.complete = QPushButton("我已完成这项任务")
        self.complete.clicked.connect(lambda: self.save_result())
        layout.addWidget(self.complete)
        close = QPushButton("关闭")
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        self.list.currentRowChanged.connect(self.select)
        ensure_day(path, plan)
        self.refresh()

    def refresh(self):
        selected = max(0, self.list.currentRow())
        _, days = load_days(self.path)
        tasks = days.get(self.day, {})
        self.rows = []
        self.list.blockSignals(True)
        self.list.clear()
        for skill, task in tasks.items():
            for item in task["items"] or [None]:
                done = item["rating"] is not None if item else task["done"]
                title = f"{LABELS[skill]}" + (f" · {item['word']}" if item else f" · {task['minutes']} 分钟")
                self.rows.append((skill, item, task))
                self.list.addItem(("已完成 · " if done else "待完成 · ") + title)
        self.list.blockSignals(False)
        total = len(self.rows)
        finished = sum((item["rating"] is not None if item else task["done"]) for _, item, task in self.rows)
        allocation = " / ".join(f"{LABELS[s]} {t['minutes']} 分钟" for s, t in tasks.items())
        self.summary.setText(f"{self.day} · 已完成 {finished}/{total}\n{allocation}\n专项先做列出的短练习，剩余预算用于同方向练习与复盘。")
        if total:
            self.list.setCurrentRow(min(selected, total - 1))
            self.select(self.list.currentRow())
        else:
            self.prompt.setPlainText("当前没有任务：请检查考试日期与每日预算。")
            self.select(-1)

    def select(self, index):
        self.response.clear()
        self.reveal.setEnabled(False)
        self.complete.setEnabled(False)
        for button in self.ratings:
            button.setEnabled(False)
        if index < 0:
            return
        skill, item, task = self.rows[index]
        self.response.setEnabled(item is not None and item["rating"] is None)
        if item:
            question, self.answer = exercise(item["word"], skill)
            result = f"\n已记录：{RATINGS[item['rating']]}" if item["rating"] else ""
            self.question = f"推荐依据：{item['reason']}\n\n{question}{result}"
            self.prompt.setPlainText(self.question)
            self.reveal.setEnabled(True)
        else:
            text = ("返回 Anki 对应词汇牌组，按原生复习顺序学习。若有到期卡先复习，预算内再学新词；不要为完成任务强行清空全部卡片。"
                    if skill == "vocabulary" else "选择自己的听力材料：先听并作答，再核对答案，重听错题片段并复盘。此处不自带音频。")
            self.prompt.setPlainText(text + f"\n\n预算：{task['minutes']} 分钟。完成后手动确认。")
            self.complete.setEnabled(not task["done"])

    def show_answer(self):
        skill, item, task = self.rows[self.list.currentRow()]
        self.prompt.setPlainText(self.question + "\n\n—— 参考与说明 ——\n" + self.answer)
        for button in self.ratings:
            button.setEnabled(item["rating"] is None)

    def save_result(self, rating=None):
        skill, item, task = self.rows[self.list.currentRow()]
        try:
            record_result(self.path, self.day, skill, item["word"] if item else None, rating)
            self.refresh()
        except DataError as error:
            showWarning(str(error), parent=self)
