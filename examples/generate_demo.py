"""生成独立答辩资料，不访问个人账户。python examples/generate_demo.py --output 路径"""

import argparse
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_loader("cet_demo", loader=None, is_package=True)
package = importlib.util.module_from_spec(spec)
package.__path__ = [str(Path(__file__).resolve().parents[1] / "cet_smart_assistant")]
sys.modules["cet_demo"] = package
from cet_demo.demo_data import documents


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    target = parser.parse_args().output
    target.mkdir(parents=True, exist_ok=True)
    docs = documents()
    if any((target/name).exists() for name in docs):
        raise SystemExit("输出目录中已有同名文件，请选择新目录。")
    for name, data in docs.items():
        with (target/name).open("x", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
    print(f"已生成 {len(docs)} 份模拟资料：{target.resolve()}")
