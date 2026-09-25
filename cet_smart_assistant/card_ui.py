"""词汇卡片对话框；所有 Collection 写入交由 CollectionOp 串行执行。"""

from aqt.operations import CollectionOp
from aqt.qt import QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout
from aqt.utils import showWarning

from .anki_service import DECK_NAME, add_vocabulary, create_deck, validate_card


class VocabularyDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.busy = False
        self.setWindowTitle("CET 智能备考助手 · 词汇卡片")
        self.resize(540, 390)
        layout = QVBoxLayout(self)
        introduction = QLabel(f"目标卡组：{DECK_NAME}\n填写词汇和释义，创建一张正反面卡片。复习间隔由 Anki 安排。")
        introduction.setWordWrap(True)
        layout.addWidget(introduction)
        self.create_button = QPushButton("创建 CET6 卡组")
        self.create_button.clicked.connect(lambda: self.run_operation(create_deck))
        layout.addWidget(self.create_button)
        form = QFormLayout()
        self.word = QLineEdit()
        self.word.setAccessibleName("词汇")
        self.word.setPlaceholderText("例如 abandon")
        self.meaning = QPlainTextEdit()
        self.meaning.setAccessibleName("释义")
        self.meaning.setPlaceholderText("例如 v. 放弃；抛弃")
        form.addRow("正面词汇：", self.word)
        form.addRow("背面释义：", self.meaning)
        layout.addLayout(form)
        self.status = QLabel("添加时会自动创建卡组；同词不覆盖原释义。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.add_button = QPushButton("添加词汇卡片")
        self.add_button.clicked.connect(self.add_card)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def add_card(self):
        try:
            word, meaning = validate_card(self.word.text(), self.meaning.toPlainText())
        except ValueError as error:
            showWarning(str(error), parent=self)
            return
        # 在主线程取表单快照，后台线程不访问 Qt 控件。
        self.run_operation(lambda col: add_vocabulary(col, word, meaning))

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.create_button, self.add_button, self.close_button, self.word, self.meaning):
            widget.setEnabled(not busy)

    def run_operation(self, operation):
        if self.busy:
            return
        self.set_busy(True)
        self.status.setText("正在处理…")
        CollectionOp(parent=self, op=operation).success(self.succeeded).failure(self.failed).run_in_background()

    def succeeded(self, result):
        self.set_busy(False)
        self.status.setText(result.message)

    def failed(self, error):
        self.set_busy(False)
        self.status.setText("操作失败，请检查卡组或模板后重试。若已创建空卡组或模板，可在 Anki 中撤销。")
        showWarning(str(error), parent=self)

    def reject(self):
        if not self.busy:
            super().reject()

    def closeEvent(self, event):
        if self.busy:
            event.ignore()
        else:
            super().closeEvent(event)
