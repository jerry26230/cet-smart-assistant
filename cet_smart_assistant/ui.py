"""Task 002：原生 Qt 资料输入窗口。"""

from aqt.qt import QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout
from aqt.utils import showInfo, showWarning

from .data_service import DataError, load_profile, save_profile
from .models import StudentProfile


class ProfileDialog(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.path = path
        self.setWindowTitle("CET 智能备考助手 · 基本信息")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        intro = QLabel("填写四级成绩及六级备考目标。资料仅保存在当前 Anki 账户的本机目录。")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QFormLayout()
        self.fields = {}
        definitions = [
            ("cet4_total", "四级总分", "0～710"),
            ("listening", "听力成绩", "0～248.5"),
            ("reading", "阅读成绩", "0～248.5"),
            ("writing", "写作与翻译", "0～213"),
            ("cet6_target", "六级目标分数", "1～710，例如 500"),
            ("days_remaining", "距离考试（天）", "1～3650，整数"),
            ("daily_minutes", "每日学习（分钟）", "1～1440，整数"),
        ]
        for name, label, hint in definitions:
            field = QLineEdit()
            field.setObjectName(name)
            field.setPlaceholderText(hint)
            field.setAccessibleName(label)
            self.fields[name] = field
            form.addRow(label + "：", field)
        layout.addLayout(form)
        note = QLabel("四级成绩用于建立初始能力画像，不能准确预测六级成绩。\n本阶段提供资料输入与保存，能力分析将在后续阶段加入。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.status = QLabel("尚未保存资料。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("保存资料")
        self.save_button.clicked.connect(self.save)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.reject)
        buttons.addWidget(self.save_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        try:
            profile = load_profile(path)
            if profile:
                for name, field in self.fields.items():
                    field.setText(str(getattr(profile, name)))
                self.status.setText("已读取上次保存的资料。")
        except DataError as error:
            self.status.setText(str(error) + "\n请先备份并修复资料文件后重新打开窗口。\n" + str(path))
            self.save_button.setEnabled(False)

    def save(self):
        values = {}
        for name, field in self.fields.items():
            try:
                value = float(field.text().strip())
                if name in ("days_remaining", "daily_minutes") and value.is_integer():
                    value = int(value)
                values[name] = value
            except ValueError:
                field.setFocus()
                showWarning(f"请填写有效的{field.accessibleName()}。", parent=self)
                return
        try:
            profile = StudentProfile(**values)
            profile.validate()
            save_profile(self.path, profile)
        except (ValueError, DataError) as error:
            showWarning(str(error), parent=self)
            return
        warning = profile.score_warning()
        self.status.setText("资料已保存。" + ("\n" + warning if warning else ""))
        showInfo("资料已保存。" + ("\n" + warning if warning else ""), parent=self)
