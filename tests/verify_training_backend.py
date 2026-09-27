"""在具备 Anki Python 包的环境运行；仅使用临时集合。"""

import json
from pathlib import Path
import tempfile

from verify_anki_backend import Collection  # 同时初始化独立 cet_core 模块包
from cet_core.training import MODES, import_training


def verify():
    results = []
    with tempfile.TemporaryDirectory() as folder:
        col = Collection(str(Path(folder) / "collection.anki2"))
        try:
            for mode, label in MODES.items():
                query = f'deck:"CET 备考::专项训练::{label}"'
                assert import_training(col, mode).added
                assert not import_training(col, mode).added
                ids = col.find_cards(query)
                assert len(ids) == 12
                card = col.get_card(ids[0])
                assert card.queue == 0 and card.reps == 0
                assert "参考答案" not in card.question()
                assert "来源" in card.answer()
                col.undo()
                assert not col.find_cards(query)
                import_training(col, mode)
                results.append({"mode": mode, "count": 12, "repeat_skipped": True,
                                "single_undo": True, "rendered": True})
            assert col.card_count() == 24
        finally:
            col.close()
    return results


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
