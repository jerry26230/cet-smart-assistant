"""Build a deterministic .ankiaddon from an explicit distribution allowlist."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "cet_smart_assistant"
MODULES = """__init__ ai_service anki_service builtin_vocab card_design card_ui daily
daily_ui data_service exam_calendar feedback models practice practice_ui practice_variants
recommendation training training_ui ui word_guidance word_hooks word_import word_ui""".split()
FILES = [*(name + ".py" for name in MODULES), "manifest.json", *(
    "vocabularies/" + name for name in
    ("cet4.json", "cet6.json", "ielts_core.json", "LICENSE", "NOTICE.md", "provenance.json"))]


def build(output_dir=None):
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    output_dir = Path(output_dir) if output_dir else ROOT / "downloads"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"cet-smart-assistant-{manifest['human_version']}.ankiaddon"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(FILES):
            data = (SOURCE / name).read_bytes()
            if name.endswith(".py"):
                compile(data, name, "exec")
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(".ankiaddon.sha256").write_text(f"{digest}  {target.name}\n", encoding="ascii")
    return target


if __name__ == "__main__":
    print(build())
