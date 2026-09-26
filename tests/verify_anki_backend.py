"""在安装了 Anki Python 包的环境运行；只操作临时集合，不访问个人账户。"""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile

from anki.collection import Collection

spec = importlib.util.spec_from_loader("cet_core", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "cet_smart_assistant")]
sys.modules["cet_core"] = package
from cet_core.builtin_vocab import BOOKS, import_book, load_book


def verify():
    results = []
    with tempfile.TemporaryDirectory() as folder:
        col = Collection(str(Path(folder) / "collection.anki2"))
        try:
            for key, (_, deck) in BOOKS.items():
                first = import_book(col, key)
                count = len(col.find_cards(f'deck:"{deck}"'))
                assert count == len(load_book(key))
                assert first.added
                second = import_book(col, key)
                assert not second.added
                assert len(col.find_cards(f'deck:"{deck}"')) == count
                # 整套词库必须只需一次撤销；再导入恢复。
                col.undo()
                assert len(col.find_cards(f'deck:"{deck}"')) == 0
                import_book(col, key)
                card = col.get_card(col.find_cards(f'deck:"{deck}"')[0])
                assert card.reps == 0 and card.queue == 0
                assert card.question() and card.answer()
                results.append({"book": key, "cards": count, "repeat_skipped": True,
                                "single_undo": True, "rendered": True})
            assert col.card_count() == 14160
        finally:
            col.close()
    return results


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
