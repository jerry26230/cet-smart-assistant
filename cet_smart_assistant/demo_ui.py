"""固定答辩场景，只在内存中调用正式推荐逻辑。"""

from datetime import date

from aqt.qt import QAbstractItemView, QComboBox, QDialog, QHeaderView, QLabel, QPlainTextEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from .demo_data import documents
from .models import StudentProfile
from .practice import PracticeRecord
from .recommendation import generate_study_plan
from .feedback import update_plan_from_practice


CASES = (
    ("student-a.json", "学生 A：确认听力重点"),
    ("student-b.json", "学生 B：确认阅读重点"),
    ("feedback-before.json", "动态调整前：听力下降"),
    ("feedback-after.json", "动态调整后：阅读下降"),
)


class DemoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CET 智能备考助手 · 答辩演示（模拟数据）")
        self.resize(780, 620)
        self.today = date.today()
        self.documents = documents(self.today)
        layout = QVBoxLayout(self)
        notice = QLabel("以下全部为模拟数据，仅演示规则如何工作，不代表真实提分效果。\n演示在独立内存中运行，不读写你的成绩、练习历史或 Anki 卡片。")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.selector = QComboBox()
        self.selector.setAccessibleName("答辩演示场景")
        for key, title in CASES:
            self.selector.addItem(title, key)
        layout.addWidget(self.selector)
        self.table = QTableWidget(4, 5)
        self.table.setAccessibleName("四种方案的分钟对比")
        self.table.setHorizontalHeaderLabels(["演示场景", "词汇", "听力", "阅读", "写作翻译"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, 5):
            self.table.setColumnWidth(column, 70)
        self.table.setMaximumHeight(165)
        layout.addWidget(self.table)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setAccessibleName("模拟资料、推荐依据与练习明细")
        layout.addWidget(self.details)
        self.reports = {}
        for row, (key, title) in enumerate(CASES):
            document = self.documents[key]
            profile = StudentProfile(**document["profile"])
            records = [PracticeRecord(**{k: v for k, v in record.items() if k not in ("id", "record_version")})
                       for record in document["practice_history"]]
            trends = ()
            if profile.study_focus == "feedback":
                result = update_plan_from_practice(profile, records, self.today)
                plan, trends = result.plan, result.trends
            else:
                plan = generate_study_plan(profile, self.today)
            cells = [title] + [str(plan.minutes[s]) for s in ("vocabulary", "listening", "reading", "writing")]
            for column, value in enumerate(cells):
                self.table.setItem(row, column, QTableWidgetItem(value))
            lines = [title, "", f"模拟四级总分 {profile.cet4_total:g}；听力 {profile.listening:g}；阅读 {profile.reading:g}；写作翻译 {profile.writing:g}。",
                     f"每日 {profile.daily_minutes} 分钟；模拟目标日期 {profile.exam_date}（非官方考试安排）。",
                     "", "分配依据", plan.explanation, plan.guidance]
            if trends:
                lines += ["", "同组趋势依据", *trends, "", "模拟练习明细（日期 / 专项 / 得分与满分）"]
                for record in sorted(records, key=lambda r: (r.day, r.skill)):
                    label = "听力" if record.skill == "listening" else "阅读"
                    lines.append(f"{record.day} / {label} / {record.score:g} / {record.maximum:g}")
                lines += ["同一专项组内均确认可比，满分 100、题量 20。", "前后场景使用同一演示基准日，后者增加后续模拟记录。"]
            else:
                lines += ["", "说明：两人的计划差异来自各自确认的学习重点；分项得分率不能直接当作可比能力。"]
            self.reports[key] = "\n".join(lines)
        close = QPushButton("关闭演示")
        close.clicked.connect(self.reject)
        layout.addWidget(close)
        self.selector.currentIndexChanged.connect(self.show_case)
        self.show_case()

    def show_case(self):
        self.details.setPlainText(self.reports[self.selector.currentData()])
