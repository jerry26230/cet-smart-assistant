"""词汇卡片对话框；所有 Collection 写入交由 CollectionOp 串行执行。"""

from aqt.operations import CollectionOp
from aqt.qt import QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout
from aqt.utils import showWarning

from .anki_service import DECK_NAME, add_vocabulary, create_deck, import_vocabulary, validate_card
from .word_import import parse_words, read_word_file
from .builtin_vocab import BOOKS, import_book


class VocabularyDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.busy = False
        self.setWindowTitle("CET 智能备考助手 · 词汇卡片")
        self.resize(580, 510)
        layout = QVBoxLayout(self)
        builtin_hint = QLabel("内置词库：选择后即可建立学习牌组，无需下载或自行准备文件。\n四级 3815 词 · 六级 5371 词 · 雅思 4974 词\n开源备考参考词表，非官方完整词表；首次建卡可能需要一些时间。")
        builtin_hint.setWordWrap(True)
        layout.addWidget(builtin_hint)
        self.book_choice = QComboBox()
        for key, (label, _) in BOOKS.items():
            self.book_choice.addItem(label, key)
        self.book_choice.setCurrentIndex(1)
        layout.addWidget(self.book_choice)
        self.book_button = QPushButton("使用所选词库（自动建卡）")
        self.book_button.clicked.connect(self.use_book)
        layout.addWidget(self.book_button)
        introduction = QLabel(f"也可补充自己的词汇，保存到：{DECK_NAME}。复习间隔由 Anki 安排。")
        introduction.setWordWrap(True)
        layout.addWidget(introduction)
        self.bulk_button = QPushButton("批量导入词库（文件 / 粘贴）")
        self.bulk_button.clicked.connect(self.open_bulk)
        layout.addWidget(self.bulk_button)
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
        for widget in (self.book_choice, self.book_button, self.bulk_button, self.create_button, self.add_button, self.close_button, self.word, self.meaning):
            widget.setEnabled(not busy)

    def use_book(self):
        key = self.book_choice.currentData()
        self.run_operation(lambda col: import_book(col, key))

    def open_bulk(self):
        dialog = BulkImportDialog(self)
        dialog.exec()
        dialog.deleteLater()

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


class BulkImportDialog(VocabularyDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.busy = False
        self.preview = None
        self.setWindowTitle("CET 智能备考助手 · 批量导入")
        self.resize(660, 600)
        layout = QVBoxLayout(self)
        hint = QLabel("从 Excel 复制两列即可粘贴，或选择 CSV / TSV / TXT 文件。\n每行：单词 + 制表符 + 释义，或 CSV 两列；支持 UTF-8、GB18030。\n最多 10000 条 / 5 MB。重复词保留首次释义，不覆盖已有卡片。")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.file_button = QPushButton("选择词库文件…")
        self.file_button.clicked.connect(self.choose_file)
        layout.addWidget(self.file_button)
        self.source = QPlainTextEdit()
        self.source.setPlaceholderText("word\tmeaning\nabandon\tv. 放弃；抛弃\nabstract\ta. 抽象的")
        self.source.textChanged.connect(self.invalidate_preview)
        layout.addWidget(self.source)
        self.preview_button = QPushButton("预览并检查格式")
        self.preview_button.clicked.connect(self.preview_words)
        layout.addWidget(self.preview_button)
        self.report = QPlainTextEdit()
        self.report.setReadOnly(True)
        layout.addWidget(self.report)
        self.status = QLabel("先预览再导入。已有卡片将在导入时检查并跳过。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.import_button = QPushButton("导入预览中的词汇")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.import_words)
        layout.addWidget(self.import_button)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.close_button)

    def invalidate_preview(self):
        self.preview = None
        self.import_button.setEnabled(False)
        self.report.clear()
        self.status.setText("内容已更新，请重新预览。")

    def choose_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择词库", "", "词库文本 (*.csv *.tsv *.txt)")
        if not path:
            return
        try:
            self.source.setPlainText(read_word_file(path))
            self.preview_words()
        except (OSError, ValueError) as error:
            showWarning(str(error), parent=self)

    def preview_words(self):
        self.invalidate_preview()
        try:
            self.preview = parse_words(self.source.toPlainText())
        except ValueError as error:
            showWarning(str(error), parent=self)
            return
        result = self.preview
        summary = f"有效词汇 {len(result.entries)} 条；文件内重复 {result.duplicates} 条；错误 {len(result.errors)} 处。"
        lines = [summary, "预览前 100 条："]
        lines.extend(f"{word} — {meaning}" for word, meaning in result.entries[:100])
        lines.extend(result.errors[:100])
        self.report.setPlainText("\n".join(lines))
        self.status.setText("请修正错误后重新预览，尚未写入卡片。" if result.errors else summary)
        self.import_button.setEnabled(bool(result.entries) and not result.errors)

    def import_words(self):
        if self.preview and self.preview.entries and not self.preview.errors:
            entries = tuple(self.preview.entries)
            self.run_operation(lambda col: import_vocabulary(col, entries))

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.source, self.file_button, self.preview_button, self.close_button):
            widget.setEnabled(not busy)
        self.import_button.setEnabled(not busy and bool(self.preview and self.preview.entries and not self.preview.errors))
