#!/usr/bin/env python3
"""Import the Zoho Billing setup UI JSON export into the JSONL catalog.

The input is an array of objects with exactly v (setup value), n (display
name), d (description). This catalog describes setup Actions, not runtime
MCP tool names or schemas. Use --expected-count to reject incomplete exports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / 'references' / 'actions.jsonl'


class ImportError_(ValueError):
    pass


def summarize(description: str) -> str:
    text = ' '.join(description.split())
    if len(text) <= 220:
        return text
    boundary = text.find('. ', 40)
    if 0 < boundary <= 220:
        return text[:boundary + 1]
    cut = text.rfind(' ', 0, 220)
    return text[:cut if cut >= 40 else 220].rstrip(',;:') + '...'


def parse_dump(text: str, expected_count: int | None = None) -> list[dict]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ImportError_(f'invalid JSON: {exc}') from exc
    if not isinstance(payload, list) or not payload:
        raise ImportError_('expected a non-empty JSON array')
    if expected_count is not None and len(payload) != expected_count:
        raise ImportError_(f'expected {expected_count} Actions, found {len(payload)}')
    entries = []
    for i, row in enumerate(payload, 1):
        if not isinstance(row, dict) or set(row) != {'v', 'n', 'd'}:
            raise ImportError_(f'entry {i}: expected exactly v, n, d')
        if any(not isinstance(row[field], str) or not row[field].strip() for field in ('v', 'n', 'd')):
            raise ImportError_(f'entry {i}: v, n, d must be non-empty strings')
        # Preserve source values exactly; never guess runtime names or normalize descriptions.
        entries.append({'key': row['v'], 'name': row['n'],
                        'summary': summarize(row['d']), 'description': row['d']})
    for field in ('key', 'name'):
        duplicates = [value for value, count in Counter(x[field] for x in entries).items() if count > 1]
        if duplicates:
            raise ImportError_(f'duplicate {field}: {duplicates[0]!r}')
    return entries


def load_catalog(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    entries = {}
    try:
        for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not isinstance(row.get('key'), str) or not row['key']:
                raise ImportError_(f'catalog line {i}: missing key')
            if row['key'] in entries:
                raise ImportError_(f'catalog line {i}: duplicate key')
            entries[row['key']] = row
    except (json.JSONDecodeError, OSError) as exc:
        raise ImportError_(f'cannot read catalog: {exc}') from exc
    return entries


def merge(entries: list[dict], known: dict[str, dict], today: str) -> list[dict]:
    merged = []
    seen = set()
    for entry in entries:
        record = dict(entry)
        record['added'] = known.get(record['key'], {}).get('added', today)
        merged.append(record)  # reappearing entries lose their removed marker
        seen.add(record['key'])
    for key, previous in known.items():
        if key not in seen:
            record = dict(previous)
            record['removed'] = record.get('removed', today)
            merged.append(record)
    return sorted(merged, key=lambda x: x['key'].lower())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dump', help='setup UI export JSON (array of v/n/d objects)')
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--today', default=date.today().isoformat())
    parser.add_argument('--expected-count', type=int, help='abort if export count differs')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        date.fromisoformat(args.today)
        if args.expected_count is not None and args.expected_count < 1:
            raise ImportError_('expected-count must be positive')
        known = load_catalog(args.catalog)
        entries = parse_dump(Path(args.dump).read_text(encoding='utf-8'), args.expected_count)
        current = {e['key'] for e in entries}
        added = sum(e['key'] not in known for e in entries)
        removed = sum(k not in current and not v.get('removed') for k, v in known.items())
        changed = sum(e['key'] in known and any(e[f] != known[e['key']].get(f) for f in ('name', 'description')) for e in entries)
        records = merge(entries, known, args.today)
        if not args.dry_run:
            args.catalog.parent.mkdir(parents=True, exist_ok=True)
            args.catalog.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
        print(f'parsed: {len(entries)}; added: {added}; removed: {removed}; changed: {changed}')
        if args.dry_run:
            print('dry run: catalog not written')
        return 0
    except (ImportError_, OSError, ValueError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
