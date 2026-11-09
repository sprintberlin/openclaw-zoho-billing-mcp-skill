# Contributing

Issues and pull requests are welcome. Use the GitHub issue tracker and describe expected and actual behavior with a minimal, sanitized reproduction. Never include endpoints, tokens, Zoho Connection credentials, customer data or financial records. Do not assert live compatibility unless actually tested and clearly identify scope.

For catalog changes, use a complete, sanitized setup UI JSON export, follow `references/CATALOG_FORMAT.md`, review the diff and run:

```bash
python3 scripts/lookup_actions.py --validate
python3 -m unittest discover -s tests -v
```

Run a local secret scan before pushing. Update snapshot count tests and documentation when the upstream catalog changes. Profiles must reference exact active catalog keys; use minimal privilege. Keep runtime tool names and schemas out of the catalog unless supported by direct evidence.
