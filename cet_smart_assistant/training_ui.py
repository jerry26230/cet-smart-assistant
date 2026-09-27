"""用户确认困难 → 推荐方向 → 预览 → Anki 专项卡片。"""

from aqt.qt import QComboBox, QDialog, QLabel, QPlainTextEdit, QPushButton, QVBoxLayout

from .card_ui import VocabularyDialog
from .training import DIFFICULTIES, MODES, build_cards, import_training, recommend


class TrainingDialog(VocabularyDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.busy = False
        self.setWindowTitle("CET 智能备考助手 · 阅读与写作训练")
        self.resize(720, 650)
        layout = QVBoxLayout(self)
        intro = QLabel("同一个词，阅读练理解，写作练表达。\n当前提供 12 个词汇的原创示例，每个方向 12 张卡。不是完整专项课程，也不标注真题高频。")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addWidget(QLabel("你最近主要卡在哪里？"))
        self.difficulty = QComboBox()
        for key, (label, _, _) in DIFFICULTIES.items():
            self.difficulty.addItem(label, key)
        layout.addWidget(self.difficulty)
        self.advice = QLabel()
        self.advice.setWordWrap(True)
        layout.addWidget(self.advice)
        layout.addWidget(QLabel("训练方向（可自行修改）："))
        self.mode = QComboBox()
        for key, label in MODES.items():
            self.mode.addItem(label, key)
        layout.addWidget(self.mode)
        self.example = QComboBox()
        layout.addWidget(self.example)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview)
        self.status = QLabel("先预览，再添加所选方向的 12 张卡片；重复添加会跳过已有卡。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.import_button = QPushButton()
        self.import_button.clicked.connect(self.import_cards)
        layout.addWidget(self.import_button)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.close_button)
        self.difficulty.currentIndexChanged.connect(self.update_advice)
        self.mode.currentIndexChanged.connect(self.update_examples)
        self.example.currentIndexChanged.connect(self.show_example)
        self.update_advice()
        self.update_examples()

    def update_advice(self, *args):
        mode, explanation = recommend(self.difficulty.currentData())
        self.advice.setText(explanation)
        if mode is not None:
            self.mode.setCurrentIndex(self.mode.findData(mode))

    def update_examples(self, *args):
        from .training import EXAMPLES

        self.example.blockSignals(True)
        self.example.clear()
        for index, example in enumerate(EXAMPLES):
            self.example.addItem(f"示例 {index + 1}：{example[0]}", index)
        self.example.blockSignals(False)
        self.import_button.setText(f"添加 {MODES[self.mode.currentData()]} 训练卡（12 张）")
        self.status.setText("只添加所选方向；不会改变原有词库卡片或学习时间分配。")
        self.show_example()

    def show_example(self, *args):
        index = self.example.currentData()
        if index is None:
            return
        front, back = build_cards(self.mode.currentData())[index]
        self.preview.setPlainText(f"【卡片正面 · 先作答】\n{front}\n\n【卡片背面 · 核对与复盘】\n{back}")

    def import_cards(self):
        mode = self.mode.currentData()
        self.run_operation(lambda col: import_training(col, mode))

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.difficulty, self.mode, self.example, self.import_button, self.close_button):
            widget.setEnabled(not busy)
