"""Actionable daily tasks without taking over Anki scheduling."""
from datetime import date
from aqt.qt import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QPlainTextEdit, QTimer, QProgressBar
from aqt.utils import showWarning
from .daily import LABELS, RATINGS, MODES, ensure_day, load_days, record_result, exercise, save_draft, undo_result
from .data_service import DataError


class DailyDialog(QDialog):
    def __init__(self, parent, path, plan):
        super().__init__(parent)
        self.path, self.day = path, date.today().isoformat()
        self.active = None
        self.dirty = False
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
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
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
        self.response.setPlaceholderText("先尝试作答，再核对参考。草稿自动保存在本机（最多 5000 字）。")
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
        navigation = QHBoxLayout()
        self.undo = QPushButton("撤销本项评价 / 完成")
        self.undo.clicked.connect(self.undo_current)
        navigation.addWidget(self.undo)
        self.next_button = QPushButton("下一项未完成 →")
        self.next_button.clicked.connect(self.next_pending)
        navigation.addWidget(self.next_button)
        layout.addLayout(navigation)
        self.draft_status = QLabel("草稿仅保存在当前账户，不发送到 AI。")
        layout.addWidget(self.draft_status)
        close = QPushButton("关闭")
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        self.list.currentRowChanged.connect(self.select)
        self.draft_timer = QTimer(self)
        self.draft_timer.setSingleShot(True)
        self.draft_timer.setInterval(700)
        self.draft_timer.timeout.connect(self.flush_draft)
        self.response.textChanged.connect(self.draft_changed)
        ensure_day(path, plan)
        self.refresh()
        self.next_pending(start=-1)

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
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(finished)
        self.progress.setFormat(f"完成 {finished} / {total} 项")
        self.next_button.setEnabled(finished < total)
        allocation = " / ".join(f"{LABELS[s]} {t['minutes']} 分钟" for s, t in tasks.items())
        self.summary.setText(f"{self.day} · 已完成 {finished}/{total}\n{allocation}\n专项先做列出的短练习，剩余预算用于同方向练习与复盘。")
        if total:
            self.list.setCurrentRow(min(selected, total - 1))
            self.select(self.list.currentRow())
        else:
            self.prompt.setPlainText("当前没有任务：请检查考试日期与每日预算。")
            self.select(-1)

    def select(self, index):
        if not self.flush_draft():
            self.list.blockSignals(True)
            self.list.setCurrentRow(self.active_index)
            self.list.blockSignals(False)
            return
        self.active = None
        self.response.blockSignals(True)
        self.response.clear()
        self.response.blockSignals(False)
        self.undo.setEnabled(False)
        self.reveal.setEnabled(False)
        self.complete.setEnabled(False)
        for button in self.ratings:
            button.setEnabled(False)
        if index < 0:
            return
        skill, item, task = self.rows[index]
        self.active_index = index
        self.active = (skill, item["word"]) if item else None
        self.response.blockSignals(True)
        self.response.setPlainText(item.get("draft", "") if item else "")
        self.response.blockSignals(False)
        self.undo.setEnabled(item["rating"] is not None if item else task["done"])
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
        if not self.flush_draft():
            return
        skill, item, task = self.rows[self.list.currentRow()]
        try:
            record_result(self.path, self.day, skill, item["word"] if item else None, rating)
            self.refresh()
        except DataError as error:
            showWarning(str(error), parent=self)

    def draft_changed(self):
        if self.active:
            self.dirty = True
            self.draft_status.setText("草稿待保存…")
            self.draft_timer.start()

    def flush_draft(self):
        if not self.dirty or not self.active:
            return True
        self.draft_timer.stop()
        try:
            save_draft(self.path, self.day, *self.active, self.response.toPlainText())
        except DataError as error:
            self.draft_status.setText(str(error) + " 草稿仍在输入框中。")
            return False
        self.dirty = False
        for skill, item, task in self.rows:
            if item and (skill, item["word"]) == self.active:
                item["draft"] = self.response.toPlainText()
        self.draft_status.setText("草稿已保存到本机。")
        return True

    def next_pending(self, checked=False, start=None):
        start = self.list.currentRow() if start is None else start
        for offset in range(1, len(self.rows) + 1):
            index = (start + offset) % len(self.rows)
            _, item, task = self.rows[index]
            if not (item["rating"] is not None if item else task["done"]):
                self.list.setCurrentRow(index)
                return

    def undo_current(self):
        if not self.flush_draft():
            return
        skill, item, task = self.rows[self.list.currentRow()]
        try:
            undo_result(self.path, self.day, skill, item["word"] if item else None)
            self.refresh()
        except DataError as error:
            showWarning(str(error), parent=self)

    def reject(self):
        if self.flush_draft():
            self.draft_timer.stop()
            super().reject()
