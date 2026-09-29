import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import hashlib

spec = importlib.util.spec_from_file_location("build_addon", Path(__file__).resolve().parents[1] / "scripts/build_addon.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PackageTests(unittest.TestCase):
    def test_structure_resources_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as folder:
            path = builder.build(folder)
            original = path.read_bytes()
            self.assertEqual(builder.build(folder).read_bytes(), original)
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertEqual(names, set(builder.FILES))
                self.assertIn('__init__.py', names)
                manifest = json.loads(archive.read('manifest.json'))
                self.assertEqual(manifest['package'], 'cet_smart_assistant')
                self.assertFalse(any('demo' in n or '__pycache__' in n or n.endswith('user_data.json') for n in names))
                provenance = json.loads(archive.read('vocabularies/provenance.json'))
                for key, entry in provenance['files'].items():
                    raw = archive.read('vocabularies/' + key + '.json')
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
                    self.assertEqual(len(json.loads(raw)['words']), entry['count'])
                for name in names:
                    if name.endswith('.py'):
                        self.assertEqual(archive.read(name), (builder.SOURCE / name).read_bytes())
