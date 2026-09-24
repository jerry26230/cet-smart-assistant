"""CET 智能备考助手：最小 Anki 插件入口。"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect, showInfo


def show_startup_message() -> None:
    """通过 Anki 自带的对话框验证插件已加载。"""
    showInfo("CET Smart Assistant is running successfully.")


# 使用 Anki 提供的 Qt 兼容层，让菜单项由主窗口管理。
action = QAction("CET 智能备考助手", mw)
qconnect(action.triggered, show_startup_message)
mw.form.menuTools.addAction(action)
