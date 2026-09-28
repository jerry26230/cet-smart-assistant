"""用法查询与按需 AI；密钥仅保留当前对话框，不写入配置文件。"""

from aqt import mw
from aqt.qt import QComboBox, QDialog, QFormLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QVBoxLayout

from .ai_service import AISettings, AIError, generate_guide
from .data_service import DataError
from .word_guidance import BUILTIN_GUIDES, guide_text, lookup_guide, save_guide, validate_word


class WordGuideDialog(QDialog):
    def __init__(self, parent, path, word="abandon"):
        super().__init__(parent)
        self.path = path
        self.busy = False
        self.pending = None
        self.setWindowTitle("CET · 单词用途与 AI 用法助手")
        self.resize(720, 720)
        layout = QVBoxLayout(self)
        intro = QLabel(f"阅读识别与写作表达分开练；精确用词优先于堆砌难词。\n内置 {len(BUILTIN_GUIDES)} 个词的用法。其他词可选用 AI，结果经你保存后显示在词卡背面。")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.word = QComboBox()
        self.word.setEditable(True)
        self.word.setAccessibleName("查询单词")
        self.word.addItems(sorted(BUILTIN_GUIDES))
        self.word.setCurrentText(word)
        layout.addWidget(self.word)
        self.local_button = QPushButton("查看本机用法（不联网）")
        self.local_button.clicked.connect(self.show_local)
        layout.addWidget(self.local_button)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAccessibleName("单词用法预览")
        layout.addWidget(self.preview, 1)
        form = QFormLayout()
        self.endpoint = QLineEdit("https://api.openai.com/v1/chat/completions")
        self.model = QLineEdit()
        self.model.setPlaceholderText("填写服务商支持的模型名")
        self.key = QLineEdit()
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.key.setPlaceholderText("仅保留到关闭此窗口，不写入磁盘")
        self.token_parameter = QComboBox()
        self.token_parameter.addItem("标准：max_completion_tokens", "max_completion_tokens")
        self.token_parameter.addItem("兼容旧接口：max_tokens", "max_tokens")
        for label, widget in (("完整 API 地址", self.endpoint), ("模型名", self.model), ("API Key", self.key), ("输出参数", self.token_parameter)):
            widget.setAccessibleName(label)
            form.addRow(label, widget)
        layout.addLayout(form)
        note = QLabel("点击生成将向上方地址发送所选词及固定教学要求，可能产生 API 费用。\n不发送成绩或练习历史；每次最多生成 1800 token，失败不自动重试。AI 例句与替换建议请先核对。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.generate_button = QPushButton("发送此词到上述 API，生成用法")
        self.generate_button.clicked.connect(self.generate)
        layout.addWidget(self.generate_button)
        self.save_button = QPushButton("确认保存这份用法到本机词卡提示")
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save)
        layout.addWidget(self.save_button)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.reject)
        layout.addWidget(self.close_button)
        self.word.currentTextChanged.connect(self.invalidate)
        self.show_local()

    def invalidate(self, *args):
        self.pending = None
        self.save_button.setEnabled(False)
        self.preview.clear()
        self.status.setText("单词已变化，请查看本机用法或重新生成。")

    def show_local(self):
        self.invalidate()
        try:
            word = validate_word(self.word.currentText())
            guide, source = lookup_guide(word, self.path)
            self.preview.setPlainText(guide_text(guide, source) if guide else "此词尚无专项用法标注；不据此判断它只适合阅读或不适合写作。可以按需使用 AI 生成并核对。")
            self.status.setText("本机查询完成，未联网。")
        except (ValueError, OSError) as error:
            self.status.setText(str(error))

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.word, self.local_button, self.endpoint, self.model, self.key, self.token_parameter, self.generate_button, self.close_button):
            widget.setEnabled(not busy)
        self.save_button.setEnabled(not busy and self.pending is not None)

    def generate(self):
        if self.busy:
            return
        self.pending = None
        self.save_button.setEnabled(False)
        try:
            word = validate_word(self.word.currentText())
            settings = AISettings(self.endpoint.text().strip(), self.model.text().strip(), self.key.text().strip(), self.token_parameter.currentData())
            settings.validate()
        except ValueError as error:
            self.status.setText(str(error))
            return
        self.preview.clear()
        self.set_busy(True)
        self.status.setText("正在生成，仅发送此词；请稍候…")

        def finished(future):
            try:
                guide = future.result()
                self.pending = (word, guide)
                self.preview.setPlainText(guide_text(guide, "AI 生成，尚未保存，请核对。"))
                self.status.setText("生成完成。确认保存后，在下次显示该词答案时生效。")
            except (AIError, ValueError) as error:
                self.status.setText(str(error))
            except Exception:
                self.status.setText("生成失败，未保存。请检查服务设置后重试。")
            finally:
                self.set_busy(False)

        mw.taskman.run_in_background(lambda: generate_guide(word, settings), finished, uses_collection=False)

    def save(self):
        if self.pending is None or self.busy:
            return
        try:
            word, guide = self.pending
            save_guide(self.path, word, guide)
            self.pending = None
            self.save_button.setEnabled(False)
            self.status.setText("已保存。下次显示该词答案会附上用法；原释义与复习安排保持不变。")
        except (ValueError, OSError, DataError) as error:
            self.status.setText(str(error))

    def reject(self):
        if not self.busy:
            self.key.clear()
            super().reject()

    def closeEvent(self, event):
        if self.busy:
            event.ignore()
        else:
            self.key.clear()
            super().closeEvent(event)
