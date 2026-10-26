"""Read new-card inventory and Anki's currently available daily counts."""


VOCABULARY_DECKS = (
    ("四级词汇", "CET 备考::四级词汇"),
    ("六级词汇", "CET 备考::六级词汇"),
    ("雅思词汇", "CET 备考::雅思词汇"),
    ("自定义词汇", "CET6 Personalized"),
)
PARENT_DECK = "CET 备考"


def _find_tree_node(node, deck_id):
    if node is None:
        return None
    if int(node.deck_id) == int(deck_id):
        return node
    for child in node.children:
        match = _find_tree_node(child, deck_id)
        if match is not None:
            return match
    return None


def _new_card_ids(col, deck_name):
    safe_name = deck_name.replace('"', '\\"')
    return col.find_cards(f'deck:"{safe_name}" is:new')


def read_vocabulary_stats(col):
    """Return all new vocabulary cards separately from today's Anki limits.

    Inventory counts are collected by card ID so nested decks cannot be counted
    twice. Daily counts come from Anki's scheduler tree, which applies the same
    limits shown in Anki's deck list.
    """
    tree = col.sched.deck_due_tree()
    all_new_ids = set()
    rows = []
    for label, deck_name in VOCABULARY_DECKS:
        deck = col.decks.by_name(deck_name)
        if deck is None:
            rows.append({"label": label, "deck_name": deck_name,
                         "total_new": 0, "today_new": 0})
            continue
        ids = set(_new_card_ids(col, deck_name))
        all_new_ids.update(ids)
        node = _find_tree_node(tree, deck["id"])
        rows.append({"label": label, "deck_name": deck_name,
                     "total_new": len(ids),
                     "today_new": int(node.new_count) if node is not None else 0})

    parent = col.decks.by_name(PARENT_DECK)
    parent_node = _find_tree_node(tree, parent["id"]) if parent else None
    return {
        "total_new": len(all_new_ids),
        "today_new": int(parent_node.new_count) if parent_node is not None else 0,
        "decks": rows,
    }
