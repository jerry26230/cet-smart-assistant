"""在 Anki Python/Qt 环境执行，仅使用临时资料。"""
import importlib.util
from pathlib import Path
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_loader("cet_demo_ui", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(root / "cet_smart_assistant")]
sys.modules["cet_demo_ui"] = package
from aqt.qt import QApplication, QWidget, QFontDatabase, QFont
from cet_demo_ui.demo_data import documents
from cet_demo_ui.models import StudentProfile
from cet_demo_ui.data_service import save_profile
from cet_demo_ui.ui import ProfileDialog
from cet_demo_ui.demo_ui import DemoDialog

app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont("C:/Windows/Fonts/msyh.ttc")
if font_id >= 0:
    app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 10))
parent = QWidget()
with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "user_data.json"
    save_profile(path, StudentProfile(**documents()["student-a.json"]["profile"]))
    before = path.read_bytes()
    main = ProfileDialog(parent, path)
    main.fields["daily_minutes"].setText("133")
    dialog = DemoDialog(main)
    for index, expected in enumerate(([24, 48, 24, 24], [24, 24, 48, 24], [24, 48, 24, 24], [24, 24, 48, 24])):
        dialog.selector.setCurrentIndex(index)
        assert [int(dialog.table.item(index, column).text()) for column in range(1, 5)] == expected
        assert dialog.selector.currentText() in dialog.details.toPlainText()
    assert "改善" in dialog.details.toPlainText() and "下降" in dialog.details.toPlainText()
    assert dialog.details.isReadOnly()
    dialog.show()
    app.processEvents()
    assert dialog.grab().save(str(root / "docs/evidence/task010-demo-offscreen.png"))
    dialog.reject()
    assert path.read_bytes() == before
    assert main.fields["daily_minutes"].text() == "133"
    assert list(Path(folder).iterdir()) == [path]
    print("Demo Qt passed: four scenarios, real rule outputs, read-only details, unchanged stored profile and unsaved form.")
