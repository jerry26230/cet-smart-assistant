"""真实 Anki 集合及 Qt 集成；临时数据，AI 使用替身，不产生 API 费用。"""
from dataclasses import replace
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
from verify_anki_backend import Collection
from cet_core.anki_service import import_vocabulary, MODEL_NAME
from cet_core.word_guidance import BUILTIN_GUIDES, lookup_guide
from cet_core.word_hooks import append_word_guide, handle_word_message
from cet_core.ai_service import AIError
import cet_core.word_ui as ui
from aqt.qt import QApplication, QWidget, QFontDatabase, QFont
from aqt.taskman import TaskManager

app = QApplication.instance() or QApplication([])
font_id = QFontDatabase.addApplicationFont("C:/Windows/Fonts/msyh.ttc")
if font_id >= 0:
    app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 10))
parent = QWidget()
manager = TaskManager(SimpleNamespace(weakref=lambda: parent))
main_thread = threading.get_ident()
worker_threads = []


def fake_generate(word, settings):
    worker_threads.append(threading.get_ident())
    return replace(BUILTIN_GUIDES["good"], reason="隔离测试的模拟 AI 内容")


def wait_idle(dialog):
    deadline = time.monotonic() + 10
    while dialog.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert not dialog.busy


with tempfile.TemporaryDirectory() as folder:
    path = Path(folder) / "word_guides.json"
    col = Collection(str(Path(folder) / "collection.anki2"))
    try:
        import_vocabulary(col, [("abandon", "放弃"), ("good", "好"), ("unlistedword", "测试")],
                          model_name=MODEL_NAME + " cet6")
        ids = col.find_cards("")
        snapshots = [(col.get_card(i).due, col.get_card(i).reps, col.get_card(i).queue, col.get_card(i).ivl) for i in ids]
        with patch("cet_core.word_hooks.guides_path", return_value=path):
            for card_id in ids:
                card = col.get_card(card_id)
                original = card.answer()
                enhanced = append_word_guide(original, card, "reviewAnswer")
                assert "cet-word-guide" in enhanced
                question = append_word_guide("question", card, "reviewQuestion")
                assert "cet-card" in question and "先回想" in question
                assert "cet-word-guide" not in question and "beneficial" not in question
                assert card.answer() == original
                if card.note()["Front"] == "abandon":
                    assert "先练阅读识别" in enhanced and "forget" in enhanced
                if card.note()["Front"] == "good":
                    assert "beneficial" in enhanced
                if card.note()["Front"] == "unlistedword":
                    assert "暂无专项" in enhanced
            with patch.object(ui, "mw", SimpleNamespace(taskman=manager)), patch.object(ui, "generate_guide", side_effect=fake_generate):
                dialog = ui.WordGuideDialog(parent, path, "good")
                assert "beneficial" in dialog.preview.toPlainText()
                dialog.model.setText("test-model")
                dialog.key.setText("test-key")
                dialog.generate()
                wait_idle(dialog)
                assert dialog.pending and dialog.save_button.isEnabled()
                assert not path.exists()  # 生成完成也不自动保存。
                dialog.save()
                assert "模拟" in lookup_guide("good", path)[0].reason
                assert "test-key" not in path.read_text(encoding="utf-8")
                before = path.read_bytes()
                dialog.word.setCurrentText("abandon")
                assert not dialog.save_button.isEnabled() and dialog.pending is None
                with patch.object(ui, "generate_guide", side_effect=AIError("模拟连接失败")):
                    dialog.generate()
                    wait_idle(dialog)
                    assert "失败" in dialog.status.text()
                    assert dialog.pending is None and path.read_bytes() == before
                dialog.show_local()
                dialog.key.clear()
                dialog.model.clear()
                dialog.show()
                app.processEvents()
                assert dialog.grab().save(str(Path(__file__).resolve().parents[1] / "docs/evidence/word-usage-ai-offscreen.png"))
                dialog.key.setText("test-key")
                dialog.reject()
                assert not dialog.key.text()
            for card_id in ids:
                card = col.get_card(card_id)
                if card.note()["Front"] == "good":
                    assert "隔离测试的模拟 AI 内容" in append_word_guide(card.answer(), card, "reviewAnswer")
            assert snapshots == [(col.get_card(i).due, col.get_card(i).reps, col.get_card(i).queue, col.get_card(i).ivl) for i in ids]
            assert col.card_count() == 3
            assert all(worker != main_thread for worker in worker_threads)
        print("PASS: real Anki answer enrichment, unchanged cards/scheduling, real Qt background generation, explicit save, failure preserves data, no stored key.")
    finally:
        col.close()
