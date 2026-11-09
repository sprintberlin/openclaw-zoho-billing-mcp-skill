"""Regression tests for profile graph and CLI lookup validation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import lookup_actions


class LookupValidationTests(unittest.TestCase):
    def setUp(self):
        self.catalog = lookup_actions.load_catalog(ROOT / 'references' / 'actions.jsonl')
        self.profiles = lookup_actions.load_profiles_data(ROOT / 'references' / 'profiles.json')

    def test_missing_and_removed_profile_and_task_references_fail(self):
        data = copy.deepcopy(self.profiles)
        data['profiles']['billing-readonly']['actions'].append('Does_not_exist')
        data['tasks']['invoice-inspection']['actions'].append('Also_missing')
        errors = lookup_actions.validate_all(self.catalog, data)
        self.assertTrue(any('Does_not_exist' in error for error in errors))
        self.assertTrue(any('Also_missing' in error for error in errors))
        catalog = copy.deepcopy(self.catalog)
        catalog['List_all_Invoices']['removed'] = '2026-11-09'
        self.assertTrue(any('List_all_Invoices' in error for error in lookup_actions.validate_all(catalog, self.profiles)))

    def test_cycles_duplicates_denials_and_missing_parents_fail(self):
        data = copy.deepcopy(self.profiles)
        data['profiles']['billing-readonly']['extends'] = 'billing-operations'
        data['profiles']['billing-readonly']['actions'].append(data['profiles']['billing-readonly']['actions'][0])
        data['profiles']['billing-operations']['denied'] = ['Not_a_real_action']
        errors = lookup_actions.validate_all(self.catalog, data)
        self.assertTrue(any('circular' in error for error in errors))
        self.assertTrue(any('duplicate' in error for error in errors))
        self.assertTrue(any('Not_a_real_action' in error for error in errors))
        data['profiles']['billing-readonly']['extends'] = 'missing'
        self.assertTrue(any('non-existent' in error for error in lookup_actions.validate_all(self.catalog, data)))

    def test_malformed_profile_shapes_are_reported(self):
        for profile in (None, {'actions': None}, {'actions': [None]}, {'denied': 'not-a-list'}, {'extends': []}):
            data = copy.deepcopy(self.profiles)
            data['profiles']['billing-readonly'] = profile
            self.assertTrue(lookup_actions.validate_all(self.catalog, data), repr(profile))
        for tasks in (None, [], {'one': {'actions': ['valid', None]}}):
            data = copy.deepcopy(self.profiles)
            data['tasks'] = tasks
            self.assertTrue(lookup_actions.validate_all(self.catalog, data), repr(tasks))

    def test_lookup_by_label_and_key(self):
        cli = ROOT / 'scripts' / 'lookup_actions.py'
        for value in ('List_all_Invoices', 'List all Invoices', 'list all invoices'):
            result = subprocess.run([sys.executable, str(cli), '--action', value, '--json'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['key'], 'List_all_Invoices')
        result = subprocess.run([sys.executable, str(cli), '--action', 'Invented action'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_duplicate_catalog_keys_rejected(self):
        row = self.catalog['List_all_Invoices']
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'catalog.jsonl'
            p.write_text(json.dumps(row) + '\n' + json.dumps(row) + '\n')
            with self.assertRaises(lookup_actions.ActionLookupError):
                lookup_actions.load_catalog(p)


if __name__ == '__main__':
    unittest.main()
