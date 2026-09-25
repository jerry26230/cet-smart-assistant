"""通过 Anki Collection API 创建卡组和词汇笔记，不改调度参数。"""

from dataclasses import dataclass
from html import escape, unescape
from typing import Any
import unicodedata


DECK_NAME = "CET6 Personalized"
MODEL_NAME = "CET Smart Assistant Vocabulary"
QUESTION = "{{Front}}"
ANSWER = '{{FrontSide}}<hr id="answer">{{Back}}'


@dataclass
class CardResult:
    changes: Any  # CollectionOp 使用此属性刷新 Anki 界面及撤销状态。
    message: str
    note_id: int | None = None
    added: bool = False


def normalize_word(word: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", word).split()).casefold()


def validate_card(word: str, meaning: str) -> tuple[str, str]:
    if not isinstance(word, str) or not isinstance(meaning, str):
        raise ValueError("词汇与释义必须是文字。")
    word, meaning = " ".join(word.split()), meaning.strip()
    if not normalize_word(word) or not meaning:
        raise ValueError("请填写词汇和释义，不能只输入空格。")
    if len(word) > 200 or len(meaning) > 5000:
        raise ValueError("词汇限 200 字符，释义限 5000 字符。")
    if any(unicodedata.category(char).startswith("C") and char not in "\n\r\t" for char in word + meaning):
        raise ValueError("内容包含不可见控制字符，请清理后重试。")
    return word, meaning


def _check_deck(col):
    deck = col.decks.by_name(DECK_NAME)
    if deck and deck.get("dyn"):
        raise ValueError(f"{DECK_NAME} 已被筛选牌组使用，请先在 Anki 中处理同名冲突。")
    return deck


def create_deck(col) -> CardResult:
    existing = _check_deck(col)
    result = col.decks.add_normal_deck_with_name(DECK_NAME)
    message = "卡组已存在，可直接添加词汇。" if existing else f"已创建卡组：{DECK_NAME}。"
    return CardResult(result.changes, message)


def _check_model(model):
    # 不覆盖用户更改过的同名模板，避免意外生成额外卡片或改变目的卡组。
    templates = model.get("tmpls", [])
    if (model.get("type") != 0 or [field["name"] for field in model["flds"]] != ["Front", "Back"]
            or len(templates) != 1 or templates[0].get("qfmt") != QUESTION
            or templates[0].get("afmt") != ANSWER or templates[0].get("did")):
        raise ValueError("同名词汇模板已被修改或不兼容。请在 Anki 中检查模板；插件不会覆盖它。")


def add_vocabulary(col, word: str, meaning: str) -> CardResult:
    from anki.collection import OpChanges

    word, meaning = validate_card(word, meaning)
    _check_deck(col)
    model = col.models.by_name(MODEL_NAME)
    if model:
        _check_model(model)
        # 在整个账户的专用笔记类型内查重，移到其他卡组后仍可识别。
        # MVP 逐项比较；将来大词库导入可改成索引查询。
        for note_id in col.models.nids(model["id"]):
            existing = col.get_note(note_id)
            if normalize_word(unescape(existing["Front"])) == normalize_word(word):
                return CardResult(OpChanges(), "该词汇已存在，未重复添加，也未覆盖原释义。", int(note_id))

    undo_id = col.add_custom_undo_entry("CET：添加词汇卡片")
    try:
        if model is None:
            model = col.models.new(MODEL_NAME)
            for field_name in ("Front", "Back"):
                col.models.add_field(model, col.models.new_field(field_name))
            template = col.models.new_template("词汇卡")
            template["qfmt"], template["afmt"] = QUESTION, ANSWER
            col.models.add_template(model, template)
            model_id = col.models.add_dict(model).id
            model = col.models.get(model_id)
        deck_id = col.decks.add_normal_deck_with_name(DECK_NAME).id
        note = col.new_note(model)
        # 输入按纯文本显示，不允许输入内容作为 HTML 或脚本执行。
        note["Front"] = escape(word).replace("\n", "<br>")
        note["Back"] = escape(meaning).replace("\n", "<br>")
        note.tags = ["cet_smart_assistant", "cet6_vocabulary"]
        col.add_note(note, deck_id)
    except Exception:
        # 已完成的步骤保留为一个可撤销操作，错误仍交由界面明确报告。
        col.merge_undo_entries(undo_id)
        raise
    changes = col.merge_undo_entries(undo_id)
    return CardResult(changes, f"已添加到 {DECK_NAME}。可关闭助手，在 Anki 牌组中学习。", int(note.id), True)
