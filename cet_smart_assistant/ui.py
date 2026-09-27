"""资料输入与四级初始能力诊断窗口。"""

from datetime import date

from aqt.qt import QComboBox, QDate, QDateEdit, QTimer, QDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget
from aqt.utils import showInfo, showWarning

from .data_service import DataError, load_profile, save_profile
from .models import StudentProfile
from .exam_calendar import upcoming_exams, countdown_text
from .recommendation import SKILL_LABELS, diagnose_profile, generate_study_plan


class ProfileDialog(QDialog):
    def __init__(self, parent, path):
        super().__init__(parent)
        self.path = path
        self.rendered_profile = None
        self.current_day = date.today()
        self.setWindowTitle("CET 智能备考助手 · 学习计划")
        self.setMinimumWidth(560)
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.resize(640, 650)
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
        self.exam_selector = QComboBox()
        self.exam_selector.setAccessibleName("目标考试场次")
        for label, day, source in upcoming_exams(date.today()):
            self.exam_selector.addItem(f"{label} · {day}（已公布）", day)
        self.exam_selector.addItem("自定日期（请按学校通知或准考证确认）", None)
        self.exam_date = QDateEdit()
        self.exam_date.setAccessibleName("目标考试日期")
        self.exam_date.setCalendarPopup(True)
        self.exam_date.setDisplayFormat("yyyy-MM-dd")
        self.exam_date.setDate(QDate.currentDate())
        self.countdown_label = QLabel()
        self.countdown_label.setWordWrap(True)
        form.addRow("目标考试场次：", self.exam_selector)
        form.addRow("目标考试日期：", self.exam_date)
        form.addRow("自动倒计时：", self.countdown_label)
        self.calendar_note = QLabel("已公布日期离线内置；未来安排更新前请选择自定日期，以学校通知和准考证为准。")
        self.calendar_note.setWordWrap(True)
        form.addRow(self.calendar_note)
        self.focus_selector = QComboBox()
        self.focus_selector.setAccessibleName("学习重点")
        for label, value in [("均衡覆盖（默认）", "balanced"), ("参考初始关注项（小幅倾斜）", "initial"),
                             ("我确认：重点听力", "listening"), ("我确认：重点阅读", "reading"),
                             ("我确认：重点写作翻译", "writing"), ("根据近期同类练习动态调整", "feedback")]:
            self.focus_selector.addItem(label, value)
        form.addRow("学习重点：", self.focus_selector)
        note = QLabel("四级成绩仅用于建立初始能力画像，不能准确预测六级成绩。\n后续学习计划还需结合六级练习表现调整。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.status = QLabel("尚未保存资料。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        diagnosis_box = QGroupBox("初始画像（得分率仅作描述）")
        diagnosis_layout = QVBoxLayout(diagnosis_box)
        self.rates_label = QLabel("听力：—　阅读：—　写作翻译：—")
        self.rates_label.setWordWrap(True)
        self.summary_label = QLabel("保存资料后显示诊断。")
        self.summary_label.setWordWrap(True)
        self.explanation_label = QLabel("分项得分率不直接代表可比能力，请结合实际练习确认重点。")
        self.explanation_label.setWordWrap(True)
        for label in (self.rates_label, self.summary_label, self.explanation_label):
            diagnosis_layout.addWidget(label)
        layout.addWidget(diagnosis_box)
        self.plan_label = QLabel("保存后生成学习时间分配。")
        self.plan_label.setWordWrap(True)
        layout.addWidget(self.plan_label)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("保存并生成计划")
        self.save_button.clicked.connect(self.save)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.reject)
        buttons.addWidget(self.save_button)
        vocabulary_button = QPushButton("词汇卡片")
        vocabulary_button.clicked.connect(self.open_vocabulary)
        buttons.addWidget(vocabulary_button)
        practice_button = QPushButton("练习记录")
        practice_button.clicked.connect(self.open_practice)
        buttons.addWidget(practice_button)
        buttons.addWidget(close_button)
        outer.addLayout(buttons)
        training_button = QPushButton("阅读语境 / 写作表达训练")
        training_button.clicked.connect(self.open_training)
        outer.addWidget(training_button)
        for field in self.fields.values():
            field.textChanged.connect(self.invalidate_diagnosis)
        self.focus_selector.currentIndexChanged.connect(self.invalidate_diagnosis)
        self.exam_selector.currentIndexChanged.connect(self.select_exam)
        self.exam_date.dateChanged.connect(self.date_changed)
        self.select_exam()
        try:
            profile = load_profile(path)
            if profile:
                for name, field in self.fields.items():
                    field.setText(str(getattr(profile, name)))
                self.focus_selector.setCurrentIndex(self.focus_selector.findData(profile.study_focus))
                if profile.exam_date:
                    index = self.exam_selector.findData(profile.exam_date)
                    self.exam_selector.setCurrentIndex(index if index >= 0 else self.exam_selector.count() - 1)
                    self.exam_date.setDate(QDate.fromString(profile.exam_date, "yyyy-MM-dd"))
                    self.status.setText("已读取上次保存的资料，剩余天数按今天自动计算。")
                    self.show_diagnosis(profile)
                else:
                    self.status.setText("旧资料只有手填天数，无法推断当时的考试日期。请确认上方推荐场次或自定日期，保存后启用自动倒计时。")
        except DataError as error:
            self.status.setText(str(error) + "\n请先备份并修复资料文件后重新打开窗口。\n" + str(path))
            self.save_button.setEnabled(False)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_day)
        self.timer.start(30_000)

    def selected_date(self):
        return self.exam_date.date().toString("yyyy-MM-dd")

    def select_exam(self):
        day = self.exam_selector.currentData()
        self.exam_date.setEnabled(day is None)
        if day:
            self.exam_date.setDate(QDate.fromString(day, "yyyy-MM-dd"))
        self.date_changed()

    def date_changed(self):
        self.countdown_label.setText(countdown_text(self.selected_date(), date.today()))
        self.invalidate_diagnosis()

    def refresh_day(self):
        today = date.today()
        self.countdown_label.setText(countdown_text(self.selected_date(), today))
        if today != self.current_day:
            self.current_day = today
            if self.rendered_profile is not None:
                self.show_diagnosis(self.rendered_profile)

    def open_training(self):
        from .training_ui import TrainingDialog

        dialog = TrainingDialog(self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def open_practice(self):
        from .practice_ui import PracticeDialog

        dialog = PracticeDialog(self, self.path)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()
        # 不覆盖主窗口未保存的输入，提醒用户重新生成。
        self.invalidate_diagnosis()
        if self.save_button.isEnabled():
            self.status.setText("练习窗口已关闭，请保存并生成计划以刷新最新趋势。")

    def open_vocabulary(self):
        from .card_ui import VocabularyDialog

        dialog = VocabularyDialog(self)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def invalidate_diagnosis(self):
        self.rendered_profile = None
        self.rates_label.setText("听力：—　阅读：—　写作翻译：—")
        self.summary_label.setText("输入已修改，请保存并重新分析。")
        self.explanation_label.setText("分项得分率不直接代表可比能力，请结合实际练习确认重点。")
        self.plan_label.setText("资料或重点已修改，请保存并重新生成计划。")
        # 读取失败时保留错误提示与禁用状态。
        if self.save_button.isEnabled():
            self.status.setText("当前修改尚未保存。")

    def show_diagnosis(self, profile):
        self.rendered_profile = profile
        diagnosis = diagnose_profile(profile)
        self.rates_label.setText("　".join(
            f"{SKILL_LABELS[skill]}：{rate:.1%}" for skill, rate in diagnosis.rates.items()
        ))
        self.summary_label.setText(diagnosis.summary)
        self.explanation_label.setText(diagnosis.explanation)
        if profile.remaining_days() <= 0:
            self.plan_label.setText(countdown_text(profile.exam_date, date.today()) + "\n本场备考计划已结束；请确认新场次后保存。")
            return
        plan = generate_study_plan(profile)
        trend_text = ""
        if profile.study_focus == "feedback":
            from .feedback import update_plan_from_practice
            from .practice import read_records

            records, skipped = read_records(self.path)
            feedback = update_plan_from_practice(profile, records)
            plan = feedback.plan
            trend_text = "\n\n近期练习趋势（仅比较同组）：\n" + "\n".join(feedback.trends)
            if skipped:
                trend_text += f"\n{skipped} 条旧格式或无效记录保留但未参与。"

        labels = {"vocabulary": "词汇", **SKILL_LABELS}
        allocation = "　".join(f"{labels[skill]} {minutes} 分钟" for skill, minutes in plan.minutes.items())
        self.plan_label.setText(f"今日学习时间（合计 {sum(plan.minutes.values())} 分钟）\n{allocation}\n\n{plan.explanation}\n\n{plan.guidance}{trend_text}")

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
            values["study_focus"] = self.focus_selector.currentData()
            values["exam_date"] = self.selected_date()
            # 兼容旧 JSON 结构，实际计划只使用日期推算天数。
            values["days_remaining"] = max(1, min(3650, (date.fromisoformat(values["exam_date"]) - date.today()).days))
            profile = StudentProfile(**values)
            profile.validate()
            save_profile(self.path, profile)
        except (ValueError, DataError) as error:
            showWarning(str(error), parent=self)
            return
        warning = profile.score_warning()
        self.status.setText("资料已保存。" + ("\n" + warning if warning else ""))
        self.show_diagnosis(profile)
        showInfo("资料已保存。" + ("\n" + warning if warning else ""), parent=self)
