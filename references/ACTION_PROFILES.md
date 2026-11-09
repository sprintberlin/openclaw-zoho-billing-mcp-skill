# Billing Action profiles

`profiles.json` uses exact catalog setup values. To inspect or copy labels:

```bash
python3 scripts/lookup_actions.py --profiles
python3 scripts/lookup_actions.py --profile billing-readonly --names-only
python3 scripts/lookup_actions.py --profile billing-operations --names-only
python3 scripts/lookup_actions.py --tasks
python3 scripts/lookup_actions.py --validate
```

| Profile | Actions | Intent |
| --- | ---: | --- |
| `billing-readonly` | 31 | Suggested read-only discovery of organizations, customers, subscriptions, invoices, payments and product catalog. Minimize further. |
| `billing-operations` | 52 including inherited reads | Opt-in: selected create/update Actions for customers, contacts, subscriptions, quotes, invoices, products, plans, addons, coupons and items. |

The second profile excludes payment mutation/collection, refunds, deletion, cancellation, void/write-off, bulk, administrative automation and outgoing communications. Inclusion is not authorization; create/update can affect billing and should be selected individually for explicitly authorized work. Read Actions also expose sensitive data. These lists are recommendations, not guarantees that Actions are available, safe in every installation, or enabled on a server. Inspect the actual live tool schema and scope of a Connection. Task recipes are small optional selections, not verified live workflows.
