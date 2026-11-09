# Billing Action catalog format

`actions.jsonl` is the setup Action source of truth: one object per line. The source was an existing Zoho Billing setup UI export array with 518 objects, each containing `v`, `n`, `d`. No runtime tool metadata or schemas were supplied.

```json
{"key":"List_all_Invoices","name":"List all Invoices","summary":"List all invoices.","description":"List all invoices.","added":"2026-11-09"}
```

The example description above is illustrative; consult the actual catalog for exact source text. `key` preserves the UI value `v` verbatim; `name` preserves its label `n`; `description` preserves `d`; `summary` is a short derived preview; `added` is the date of import. Profiles and tasks reference **keys**, while `--names-only` prints labels. `removed` marks entries absent from a later complete export. Reappearing entries lose this marker. This setup value is not asserted to be the runtime MCP tool name.

## Import a new complete export

1. Obtain an authorized sanitized Billing setup UI JSON array of `{ "v": "...", "n": "...", "d": "..." }` objects. Verify completeness against the UI count and inspect for credentials and customer data before saving or committing. Do not use a partial/filtered list to mark removals.
2. Run a dry run with the independently observed count, inspect changes, then import:

```bash
python3 scripts/import_actions.py /path/to/sanitized-export.json --expected-count 518 --dry-run
python3 scripts/import_actions.py /path/to/sanitized-export.json --expected-count 518
python3 scripts/lookup_actions.py --validate
python3 -m unittest discover -s tests -v
```

Change `--expected-count` to the independently observed new UI count if Zoho changes it; also update the snapshot-count test and documented count. The importer rejects missing, empty, duplicate or malformed fields, preserves `added`, marks missing entries `removed`, and reports changes. It cannot itself prove the export is complete or sanitized. Review the diff and profile references before commit. Catalog descriptions are hints only; the live server is authoritative for actual tools and schemas.
