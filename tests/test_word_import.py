import unittest
from unittest.mock import patch, mock_open

from test_anki_service import MemoryCollection  # 初始化独立模块包，避免加载 Qt
from cet_core.word_import import parse_words, read_word_file


class WordImportTests(unittest.TestCase):
    def test_excel_tsv_header_and_duplicate(self):
        result = parse_words("\ufeff单词\t释义\nabandon\t放弃\nＡＢＡＮＤＯＮ\t重复\ntake off\t起飞\n")
        self.assertEqual(result.entries, [("abandon", "放弃"), ("take off", "起飞")])
        self.assertEqual(result.duplicates, 1)
        self.assertEqual(result.errors, [])

    def test_csv_quotes_and_multiline(self):
        result = parse_words('word,meaning\nabstract,"抽象的,摘要"\nadapt,"适应\n改编"')
        self.assertEqual(result.entries, [("abstract", "抽象的,摘要"), ("adapt", "适应\n改编")])
        self.assertFalse(result.errors)

    def test_errors_reported_not_silently_skipped(self):
        result = parse_words('good,好的\nbad\nempty,\nextra,多,列')
        self.assertEqual(len(result.errors), 3)
        self.assertIn("第 2 行", result.errors[0])
        self.assertEqual(len(result.entries), 1)
        self.assertTrue(parse_words('word,"未结束').errors)

    def test_empty_and_limits(self):
        self.assertEqual(parse_words("\n  \n").entries, [])
        with self.assertRaises(ValueError):
            parse_words("a,b\n" * 10002)
        with self.assertRaises(ValueError):
            parse_words("x" * (5 * 1024 * 1024 + 1))

    def test_file_encodings_and_size(self):
        for encoding in ("utf-8-sig", "gb18030"):
            with patch("pathlib.Path.open", mock_open(read_data="单词\t释义".encode(encoding))):
                self.assertEqual(read_word_file("test.tsv"), "单词\t释义")
        with patch("pathlib.Path.open", mock_open(read_data=b"x" * (5 * 1024 * 1024 + 1))):
            with self.assertRaises(ValueError):
                read_word_file("huge.csv")
