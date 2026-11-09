"""Credential-free endpoint/helper checks."""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from mcp_endpoint import EndpointResolutionError, resolve_mcp_url


class EndpointSafetyTests(unittest.TestCase):
    def test_environment_resolution_and_safe_errors(self):
        resolved = resolve_mcp_url(type('A', (), {'mcp_url': None, 'profile': None, 'profiles_file': None})(), 'billing', ('ZOHO_BILLING_MCP_URL',), {'ZOHO_BILLING_MCP_URL': 'https://billing.example/mcp/one/message'})
        self.assertEqual(resolved, 'https://billing.example/mcp/one/message')
        with self.assertRaises(EndpointResolutionError):
            resolve_mcp_url(type('A', (), {'mcp_url': None, 'profile': None, 'profiles_file': None})(), 'billing', ('ZOHO_BILLING_MCP_URL',), {})
        for bad in ('http://billing.example/x', 'https://user@example/x', 'https://example/x#frag', ' https://billing.example/x y', 'https://billing.example/\x00x', 'https://billing.example:99999/x'):
            with self.assertRaises(EndpointResolutionError):
                resolve_mcp_url(type('A', (), {'mcp_url': bad, 'profile': None, 'profiles_file': None})(), 'billing', ('ZOHO_BILLING_MCP_URL',), {})

    def test_named_profile_from_env_and_help_is_credential_free(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profiles.json'
            path.write_text(json.dumps({'version': 1, 'profiles': {'sample': {'services': {'billing': {'env': 'SAMPLE_URL'}}}}}))
            args = type('A', (), {'mcp_url': None, 'profile': 'sample', 'profiles_file': str(path)})()
            resolved = resolve_mcp_url(args, 'billing', ('ZOHO_BILLING_MCP_URL',), {'SAMPLE_URL': 'https://billing.example/mcp/token/message'})
            self.assertEqual(resolved, 'https://billing.example/mcp/token/message')
            missing = type('A', (), {'mcp_url': None, 'profile': 'sample', 'profiles_file': str(path)})()
            with self.assertRaises(EndpointResolutionError):
                resolve_mcp_url(missing, 'billing', ('ZOHO_BILLING_MCP_URL',), {})

    def test_check_endpoint_reports_valid_config_with_redacted_credential(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith('ZOHO_')}
        env['ZOHO_BILLING_MCP_URL'] = 'https://billing.example/mcp/secret/message'
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'check_endpoint.py')], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn('valid locally', result.stdout)
        self.assertNotIn('secret', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
