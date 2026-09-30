"""Real Qt flow with isolated local task data; does not touch Anki cards."""
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).parent))
import verify_anki_backend
from aqt.qt import QApplication, QFont, QFontDatabase
from cet_core.daily_ui import DailyDialog
from cet_core.daily import load_days
from cet_core.recommendation import StudyPlan

app = QApplication.instance() or QApplication([])
font = QFontDatabase.addApplicationFont('C:/Windows/Fonts/msyh.ttc')
if font >= 0:
    app.setFont(QFont(QFontDatabase.applicationFontFamilies(font)[0], 10))
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / 'user_data.json'
    plan = StudyPlan(dict(vocabulary=5, listening=5, reading=5, writing=5), '', '')
    dialog = DailyDialog(None, path, plan)
    dialog.list.setCurrentRow(2)
    assert not any(button.isEnabled() for button in dialog.ratings)
    assert 'contributes to' not in dialog.prompt.toPlainText()
    dialog.response.setPlainText('促成')
    dialog.list.setCurrentRow(3)
    dialog.list.setCurrentRow(2)
    assert dialog.response.toPlainText() == '促成'
    dialog.reveal.click()
    assert all(button.isEnabled() for button in dialog.ratings)
    dialog.ratings[2].click()
    assert not any(button.isEnabled() for button in dialog.ratings)
    dialog.list.setCurrentRow(3)
    assert '参考：' not in dialog.prompt.toPlainText()
    dialog.reveal.click()
    dialog.ratings[0].click()
    tasks = load_days(path)[1][dialog.day]
    assert tasks['reading']['items'][0]['rating'] == 'good'
    assert tasks['writing']['items'][0]['rating'] == 'again'
    dialog.list.setCurrentRow(0)
    dialog.complete.click()
    assert not dialog.complete.isEnabled()
    dialog.reject()
    reopened = DailyDialog(None, path, plan)
    assert '已完成 3/4' in reopened.summary.text()
    assert reopened.list.currentRow() == 1
    reopened.list.setCurrentRow(2)
    assert reopened.response.toPlainText() == '促成'
    reopened.undo.click()
    assert reopened.response.isEnabled()
    assert not any(button.isEnabled() for button in reopened.ratings)
    reopened.reveal.click()
    reopened.ratings[2].click()
    reopened.list.setCurrentRow(3)
    reopened.reveal.click()
    reopened.show()
    app.processEvents()
    assert reopened.grab().save(str(Path(__file__).resolve().parents[1] / 'docs/evidence/daily-tasks-offscreen.png'))
    reopened.reject()
print('PASS: real Qt reveal-before-rating, independent tracks, completion, persistence and reopen')
