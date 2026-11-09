"""Local credential-free snapshot tests: catalog count/uniqueness and profile consistency."""
from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'references' / 'actions.jsonl'
PROFILES = ROOT / 'references' / 'profiles.json'
REPO_COMMIT_NEVER = ('mcp.zoho.eu/', 'http://', 'ya29.', 'ghp_', 'gho_', '@zoho', '@gmail', '@gmx', 'BEGIN PRIVATE')

sys.path.insert(0, str(ROOT / 'scripts'))
import lookup_actions


def read_catalog():
    lines = [line for line in CATALOG.read_text(encoding='utf-8').splitlines() if line.strip()]
    records = [json.loads(line) for line in lines]
    active = [r for r in records if not r.get('removed')]
    return lines, records, active


class CatalogSnapshotTests(unittest.TestCase):
    def test_snapshot_count_uniqueness_and_source_shape(self):
        lines, records, active = read_catalog()
        self.assertEqual(len(lines), 518, 'snapshot catalog count changed')
        self.assertEqual(len(active), 518, 'removed records present in fresh snapshot')
        keys = [record['key'] for record in active]
        names = [record['name'] for record in active]
        self.assertEqual(len(set(keys)), len(keys), 'duplicate setup value')
        self.assertEqual(len(set(names)), len(names), 'duplicate display name')
        for record in active:
            self.assertEqual(set(record), {'key', 'name', 'summary', 'description', 'added'}, f'unexpected fields in {record["key"]}')
            for field in ('key', 'name', 'summary', 'description'):
                self.assertTrue(record[field].strip(), f'empty {field} in {record["key"]}')
            self.assertRegex(record['added'], r'^\d{4}-\d{2}-\d{2}$', f'invalid added date in {record["key"]}')
            self.assertNotIn('\n', record['summary'], f'multiline summary in {record["key"]}')

    def test_no_live_runtime_or_auth_claims(self):
        lines, _, active = read_catalog()
        profiles = json.loads(PROFILES.read_text(encoding='utf-8'))
        text = '\n'.join(lines + [PROFILES.read_text(encoding='utf-8')])
        self.assertNotIn('ZohoBilling_', text)
        for marker in ('mcp_url', 'MCP_URL', 'query_params', 'tool name', 'Authorization'):
            self.assertNotIn(marker, text)
        self.assertEqual(profiles.get('service'), 'billing')

    def test_profiles_reference_exact_safe_catalog_keys(self):
        _, _, active = read_catalog()
        keys = {record['key'] for record in active}
        profiles = json.loads(PROFILES.read_text(encoding='utf-8'))['profiles']
        readonly = set(lookup_actions.resolve_profile_actions('billing-readonly', profiles))
        self.assertEqual(len(readonly), 31)
        operations = set(lookup_actions.resolve_profile_actions('billing-operations', profiles))
        self.assertEqual(len(operations), 52)
        self.assertTrue(readonly.issubset(operations))
        self.assertEqual({r for r in operations - readonly}, set(profiles['billing-operations']['actions']))
        self.assertEqual(sorted(readonly | (operations - readonly)), sorted(set(readonly) | set(profiles['billing-operations']['actions'])))
        self.assertTrue(readonly | (operations - readonly) <= keys)
        self.assertEqual(len(operations), len(set(profiles['billing-operations']['actions'])) + len(readonly) - len(set(profiles['billing-operations']['actions']) & readonly))
        forbidden = re.compile(r'^(Delete|Bulk|Void|Cancel|Refund|Email|Invite|Mark an Invoice as Void|Write Off|Create|Update)', re.IGNORECASE)
        self.assertEqual([action for action in readonly if forbidden.match(action.replace('_', ' '))], [])
        for action in operations - readonly:
            self.assertTrue(action.startswith(('Create_', 'Update_', 'Add_')), action)
        self.assertEqual(lookup_actions.validate_all({r['key']: r for r in active}, json.loads(PROFILES.read_text(encoding='utf-8'))), [])

    def test_cli_and_no_secrets(self):
        for arguments in (['--validate'], ['--profiles'], ['--profile', 'billing-readonly', '--names-only'], ['--task', 'invoice-inspection', '--names-only'], ['--search', 'subscription', '--names-only']):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'lookup_actions.py'), *arguments], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, arguments)
        self.assertIn('billing-readonly', subprocess.run([sys.executable, str(ROOT / 'scripts' / 'lookup_actions.py'), '--profiles'], capture_output=True, text=True).stdout)
        payload = CATALOG.read_bytes() + PROFILES.read_bytes() + (ROOT / 'scripts' / 'lookup_actions.py').read_bytes()
        lowered = payload.decode('utf-8', 'replace').lower()
        for marker in REPO_COMMIT_NEVER:
            self.assertNotIn(marker.lower(), lowered)


if __name__ == '__main__':
    unittest.main()
