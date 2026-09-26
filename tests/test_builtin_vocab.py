import unittest
import test_anki_service  # 初始化独立模块包
from cet_core.builtin_vocab import BOOKS, load_book, import_book


class BuiltinDataTests(unittest.TestCase):
    def test_all_shipped_books_valid_and_complete(self):
        for key, count in (("cet4", 3815), ("cet6", 5371), ("ielts_core", 4974)):
            with self.subTest(key=key):
                self.assertEqual(len(load_book(key)), count)

    def test_unknown_book(self):
        with self.assertRaises(ValueError):
            load_book("../../outside")

