"""在带 aqt/PyQt 的 Anki Python 环境执行；只操作临时资料。"""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from datetime import date
from unittest.mock import patch

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_loader("cet_calendar_ui", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(root / "cet_smart_assistant")]
sys.modules["cet_calendar_ui"] = package
from aqt.qt import QApplication, QWidget, QDate
from cet_calendar_ui.models import StudentProfile
from cet_calendar_ui.data_service import save_profile, load_profile
import cet_calendar_ui.ui as ui
import cet_calendar_ui.models as models


class Clock(date):
    current = date(2026, 9, 27)

    @classmethod
    def today(cls):
        return cls.current


app = QApplication.instance() or QApplication([])
parent = QWidget()
with tempfile.TemporaryDirectory() as folder, patch.object(ui, "date", Clock), patch.object(models, "date", Clock), patch.object(ui, "showInfo"), patch.object(ui, "showWarning") as warning:
    path = Path(folder) / "user_data.json"
    profile = StudentProfile(470, 115, 190, 165, 500, 90, 120)
    save_profile(path, profile)
    before = path.read_bytes()
    dialog = ui.ProfileDialog(parent, path)
    assert "旧资料" in dialog.status.text()
    assert path.read_bytes() == before
    dialog.exam_selector.setCurrentIndex(dialog.exam_selector.count() - 1)
    dialog.exam_date.setDate(QDate(2026, 12, 12))
    dialog.save()
    assert not warning.called
    assert load_profile(path).exam_date == "2026-12-12"
    reopened = ui.ProfileDialog(parent, path)
    assert "剩余 76 天" in reopened.plan_label.text()
    Clock.current = date(2026, 9, 28)
    reopened.refresh_day()
    assert "75 天" in reopened.countdown_label.text()
    assert "剩余 75 天" in reopened.plan_label.text()
    # 跨日不覆盖未保存的输入，也不恢复已失效的计划。
    reopened.fields["daily_minutes"].setText("121")
    Clock.current = date(2026, 9, 29)
    reopened.refresh_day()
    assert reopened.fields["daily_minutes"].text() == "121"
    assert "重新生成" in reopened.plan_label.text()
    # 过期日期仍能读取旧资料，不阻止练习历史读写。
    Clock.current = date(2026, 12, 13)
    expired = ui.ProfileDialog(parent, path)
    assert "已过 1 天" in expired.plan_label.text()
    assert load_profile(path).exam_date == "2026-12-12"
    print("Qt calendar passed: legacy confirmation, save/reopen, midnight refresh, unsaved input preservation, expired target.")
