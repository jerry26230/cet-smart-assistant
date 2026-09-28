"""CET 智能备考助手：菜单入口。"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect, showInfo


def open_assistant() -> None:
    """在已打开的 Anki 账户中编辑个人资料。"""
    if mw.col is None:
        showInfo("请先打开一个 Anki 账户。")
        return
    from pathlib import Path
    from .ui import ProfileDialog

    # 按 Anki 账户隔离资料，插件代码升级不会覆盖用户数据。
    path = Path(mw.pm.profileFolder()) / "cet_smart_assistant" / "user_data.json"
    dialog = ProfileDialog(mw, path)
    try:
        dialog.exec()
    finally:
        dialog.deleteLater()


# 使用 Anki 提供的 Qt 兼容层，让菜单项由主窗口管理。
action = QAction("CET 智能备考助手", mw)
qconnect(action.triggered, open_assistant)
mw.form.menuTools.addAction(action)

# 对已有的插件词库卡片也即时生效，无需重新导入或更改笔记。
from aqt import gui_hooks
from .word_hooks import append_word_guide, handle_word_message

gui_hooks.card_will_show.append(append_word_guide)
gui_hooks.webview_did_receive_js_message.append(handle_word_message)
