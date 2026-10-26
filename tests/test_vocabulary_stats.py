import unittest

import test_anki_service  # 初始化不依赖 Anki 的独立模块包

from cet_core.vocabulary_stats import (
    PARENT_DECK,
    VOCABULARY_DECKS,
    read_vocabulary_stats,
)


class Node:
    def __init__(self, deck_id, name, new_count, children=()):
        self.deck_id = deck_id
        self.name = name
        self.new_count = new_count
        self.children = list(children)


class FakeDecks:
    def __init__(self, entries):
        self.entries = entries

    def by_name(self, name):
        return self.entries.get(name)


class FakeScheduler:
    def __init__(self, tree):
        self.tree = tree

    def deck_due_tree(self):
        return self.tree


class FakeCollection:
    def __init__(self, decks, ids_by_name, tree):
        self.decks = FakeDecks(decks)
        self.sched = FakeScheduler(tree)
        self.ids_by_name = ids_by_name
        self.queries = []

    def find_cards(self, query):
        self.queries.append(query)
        for name in self.ids_by_name:
            if query == f'deck:"{name}" is:new':
                return self.ids_by_name[name]
        raise AssertionError(f"Unexpected search query: {query}")


class VocabularyStatsTests(unittest.TestCase):
    def test_separates_full_new_inventory_from_limited_daily_counts(self):
        deck_ids = {name: index for index, (_, name) in enumerate(VOCABULARY_DECKS, 1)}
        parent_id = 99
        children = [
            Node(deck_ids[name], name, 20)
            for _, name in VOCABULARY_DECKS[:3]
        ]
        tree = Node(0, "", 0, [Node(parent_id, PARENT_DECK, 20, children)])
        all_decks = {PARENT_DECK: {"id": parent_id}}
        all_decks.update({name: {"id": deck_ids[name]} for _, name in VOCABULARY_DECKS})
        ids_by_name = {
            VOCABULARY_DECKS[0][1]: [1, 2, 3],
            VOCABULARY_DECKS[1][1]: [4, 5, 6, 7],
            VOCABULARY_DECKS[2][1]: [8, 9],
            VOCABULARY_DECKS[3][1]: [10],
        }
        col = FakeCollection(all_decks, ids_by_name, tree)

        result = read_vocabulary_stats(col)

        self.assertEqual(result["total_new"], 10)
        self.assertEqual(result["today_new"], 20)
        self.assertEqual([row["total_new"] for row in result["decks"]], [3, 4, 2, 1])
        self.assertEqual([row["today_new"] for row in result["decks"]], [20, 20, 20, 0])
        self.assertTrue(all(query.endswith("is:new") for query in col.queries))

    def test_missing_vocabulary_decks_are_reported_as_empty(self):
        col = FakeCollection({}, {}, Node(0, "", 0))

        result = read_vocabulary_stats(col)

        self.assertEqual(result["total_new"], 0)
        self.assertEqual(result["today_new"], 0)
        self.assertEqual([row["total_new"] for row in result["decks"]], [0, 0, 0, 0])
        self.assertEqual(col.queries, [])


if __name__ == "__main__":
    unittest.main()
