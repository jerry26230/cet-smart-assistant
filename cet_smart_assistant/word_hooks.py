"""仅增强本插件词卡的答案显示，不更新集合字段或调度状态。"""

from html import unescape
from pathlib import Path

from .anki_service import MODEL_NAME, QUESTION, ANSWER, normalize_word
from .card_design import STYLE, render_card
from .builtin_vocab import BOOKS
from .word_guidance import lookup_guide, render_guide, validate_word


def card_word(card):
    note = card.note()
    names = {MODEL_NAME, *(f"{MODEL_NAME} {key}" for key in BOOKS)}
    if note.note_type()["name"] not in names:
        return None
    try:
        return validate_word(normalize_word(unescape(note["Front"])))
    except ValueError:
        return None


def guides_path():
    from aqt import mw
    return Path(mw.pm.profileFolder()) / "cet_smart_assistant" / "word_guides.json"


def append_word_guide(text, card, kind):
    if kind not in ("reviewAnswer", "previewAnswer", "reviewQuestion", "previewQuestion"):
        return text
    word = card_word(card)
    if not word:
        return text
    templates = card.note().note_type().get("tmpls", [])
    standard = (len(templates) == 1 and templates[0].get("qfmt") == QUESTION
                and templates[0].get("afmt") == ANSWER)
    if kind.endswith("Question"):
        return render_card(text) if standard else text
    try:
        guide, source = lookup_guide(word, guides_path())
        addition = render_guide(guide, source) if guide else '<p>此词暂无专项用法标注；不代表不适合写作。</p>'
    except (OSError, ValueError):
        addition = '<p>本机用法文件读取失败，请在用法助手中检查；原卡片仍可复习。</p>'
    # 预览窗口只展示提示；在复习答案中提供一键打开当前词的入口。
    if kind == "reviewAnswer":
        addition += '<div class="cet-footer"><button onclick="pycmd(\'cet-word-guide\')">查看用法 / AI 补充 ↗</button></div>'
    marker = '<hr id="answer">'
    if standard and marker in text:
        front, back = text.split(marker, 1)
        return render_card(front, back, addition)
    return text + STYLE + '<div class="cet-card">' + addition + '</div>'


def handle_word_message(handled, message, context):
    if handled[0] or message != "cet-word-guide":
        return handled
    from aqt import mw
    if context is not mw.reviewer or mw.col is None or mw.reviewer.state != "answer":
        return (True, None)
    word = card_word(mw.reviewer.card)
    if word:
        from .word_ui import WordGuideDialog
        dialog = WordGuideDialog(mw, guides_path(), word)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()
    return (True, None)
