"""Offline importer tests: validation, snapshot fidelity and merge semantics."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import import_actions as importer


class ImportTests(unittest.TestCase):
    def row(self, v='List_all_Invoices', n='List all Invoices', d='List invoices.'):
        return {'v': v, 'n': n, 'd': d}

    def test_exact_conversion_and_no_invented_schema(self):
        row = self.row(d=' First  line.\nSecond line. ')
        actual = importer.parse_dump(json.dumps([row]), 1)
        self.assertEqual(actual, [{'key': row['v'], 'name': row['n'], 'summary': 'First line. Second line.', 'description': row['d']}])

    def test_rejects_incomplete_duplicate_and_malformed_exports(self):
        invalid = [([], None), ([self.row()], 2), ([self.row(), self.row()], 2),
                   ([{'v':'v', 'n':'n'}], 1), ([self.row(d='')], 1),
                   ([self.row(), self.row(v='different')], 2), ([{'v':'v', 'n':'n', 'd':'d', 'extra': 'x'}], 1)]
        for rows, count in invalid:
            with self.subTest(rows=rows, count=count):
                with self.assertRaises(importer.ImportError_):
                    importer.parse_dump(json.dumps(rows), count)
        with self.assertRaises(importer.ImportError_):
            importer.parse_dump('{bad')

    def test_merge_preserves_add_date_marks_removed_and_revives(self):
        old = {'key': 'one', 'name': 'One', 'summary': 's', 'description': 'd', 'added': '2026-01-01', 'removed': '2026-02-01'}
        lost = {'key': 'two', 'name': 'Two', 'summary': 's', 'description': 'd', 'added': '2026-01-01'}
        entries = [{'key':'one', 'name':'One', 'summary':'s2', 'description':'d2'}, {'key':'new', 'name':'New', 'summary':'n', 'description':'n'}]
        merged = {r['key']: r for r in importer.merge(entries, {'one':old, 'two':lost}, '2026-11-09')}
        self.assertEqual(merged['one']['added'], '2026-01-01')
        self.assertNotIn('removed', merged['one'])
        self.assertEqual(merged['two']['removed'], '2026-11-09')
        self.assertEqual(merged['new']['added'], '2026-11-09')
        self.assertNotIn('removed', lost)

    def test_dry_run_and_expected_count_prevent_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dump = root / 'dump.json'
            catalog = root / 'actions.jsonl'
            dump.write_text(json.dumps([self.row()]))
            command = [sys.executable, str(ROOT / 'scripts' / 'import_actions.py'), str(dump), '--catalog', str(catalog)]
            result = subprocess.run(command + ['--expected-count', '2'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(catalog.exists())
            result = subprocess.run(command + ['--expected-count', '1', '--dry-run'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertFalse(catalog.exists())
            result = subprocess.run(command + ['--expected-count', '1', '--today', '2026-11-09'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(catalog.read_text())['key'], 'List_all_Invoices')


if __name__ == '__main__':
    unittest.main()
