"""Validate distribution with the installed Anki manifest parser and Python runtime."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import zipfile
from aqt.addons import AddonManager

root = Path(__file__).resolve().parents[1]
version = json.loads((root / 'cet_smart_assistant/manifest.json').read_text(encoding='utf-8'))['human_version']
archive_path = root / f'downloads/cet-smart-assistant-{version}.ankiaddon'
with zipfile.ZipFile(archive_path) as archive, tempfile.TemporaryDirectory() as folder:
    manager = object.__new__(AddonManager)
    manifest = manager.readManifestFile(archive)
    assert manifest['package'] == 'cet_smart_assistant'
    assert manifest['human_version'] == version
    archive.extractall(folder)
    for source in Path(folder).glob('*.py'):
        compile(source.read_bytes(), str(source), 'exec')
    spec = importlib.util.spec_from_loader('packaged_cet', loader=None, is_package=True)
    package = importlib.util.module_from_spec(spec)
    package.__path__ = [folder]
    sys.modules['packaged_cet'] = package
    from packaged_cet.builtin_vocab import load_book
    assert [len(load_book(key)) for key in ('cet4', 'cet6', 'ielts_core')] == [3815, 5371, 4974]
print('PASS: actual Anki manifest parser, runtime syntax and extracted vocabulary integrity')
