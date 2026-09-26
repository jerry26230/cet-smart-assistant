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


def _check_deck(col, deck_name=DECK_NAME):
    deck = col.decks.by_name(deck_name)
    if deck and deck.get("dyn"):
        raise ValueError(f"{deck_name} 已被筛选牌组使用，请先在 Anki 中处理同名冲突。")
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
    return import_vocabulary(col, [(word, meaning)])


def import_vocabulary(col, entries, deck_name=DECK_NAME, model_name=MODEL_NAME) -> CardResult:
    from anki.collection import AddNoteRequest, OpChanges

    entries = [validate_card(*entry) for entry in entries]
    if not entries or len(entries) > 10000:
        raise ValueError("每批请输入 1～10000 条词汇。")
    _check_deck(col, deck_name)
    model = col.models.by_name(model_name)
    known = {}
    if model:
        _check_model(model)
        for note_id in col.models.nids(model["id"]):
            known[normalize_word(unescape(col.get_note(note_id)["Front"]))] = int(note_id)
    pending = []
    seen = set(known)
    for word, meaning in entries:
        key = normalize_word(word)
        if key not in seen:
            pending.append((word, meaning))
            seen.add(key)
    skipped = len(entries) - len(pending)
    if not pending:
        return CardResult(OpChanges(), f"该词汇已存在，跳过 {skipped} 条，未重复添加，也未覆盖原释义。",
                          known.get(normalize_word(entries[0][0])))
    undo_id = col.add_custom_undo_entry("CET：导入词汇卡片")
    count = 0
    try:
        if model is None:
            model = col.models.new(model_name)
            for field_name in ("Front", "Back"):
                col.models.add_field(model, col.models.new_field(field_name))
            template = col.models.new_template("词汇卡")
            template["qfmt"], template["afmt"] = QUESTION, ANSWER
            col.models.add_template(model, template)
            model = col.models.get(col.models.add_dict(model).id)
        deck_id = col.decks.add_normal_deck_with_name(deck_name).id
        requests = []
        for word, meaning in pending:
            note = col.new_note(model)
            note["Front"] = escape(word)
            note["Back"] = escape(meaning).replace("\n", "<br>")
            note.tags = ["cet_smart_assistant", "cet6_vocabulary"]
            requests.append(AddNoteRequest(note=note, deck_id=deck_id))
        col.add_notes(requests)
        count = len(requests)
    except Exception as error:
        col.merge_undo_entries(undo_id)
        raise RuntimeError(f"导入中断，可能已有部分内容写入。可在 Anki 中撤销本批操作，或重试并跳过已有词。原因：{error}") from error
    changes = col.merge_undo_entries(undo_id)
    return CardResult(changes, f"已添加 {count} 条到 {deck_name}，跳过重复 {skipped} 条。", int(note.id), True)
