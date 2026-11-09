---
name: "zoho-billing-mcp"
description: "Find Zoho Billing MCP setup Actions, select endpoints, and perform safe least-privilege Billing workflows."
---

# Zoho Billing MCP

Use the [public skill source](https://github.com/sprintberlin/openclaw-zoho-billing-mcp-skill) to find Billing Actions, not to infer live MCP schemas. The catalog is a 518-Action setup UI snapshot. It does **not** establish which Actions a specific MCP server enables, their runtime names, schemas, region support, or authentication settings; this release has not been live-server-tested.

## Setup

1. In your region's Zoho MCP portal, select the Zoho Billing Actions required for the task. Use a server-side Zoho **Connection** for authorization and scopes. Do not invent a Zoho `Authorization` action argument or manually substitute OAuth tokens; MCP endpoint authentication is separate and server-specific.
2. Start with `python3 scripts/lookup_actions.py --profile billing-readonly --names-only`, and select only the necessary subset. `billing-operations` contains write Actions and is opt-in.
3. Configure `ZOHO_BILLING_MCP_URL` or a named account profile; see [MULTI_ACCOUNT.md](references/MULTI_ACCOUNT.md). The endpoint may contain a credential: do not print, commit, or paste it into chat.
4. `python3 scripts/check_endpoint.py` validates configuration locally without connecting or printing the endpoint.
5. Inspect the actual MCP server tool list and the exact tool schema before a call. Use the names, arguments, and organization selection advertised by that server. The catalog is not a runtime schema.

## Look up Actions offline

```bash
python3 scripts/lookup_actions.py --profiles
python3 scripts/lookup_actions.py --profile billing-readonly --names-only
python3 scripts/lookup_actions.py --task invoice-inspection
python3 scripts/lookup_actions.py --search 'subscription'
python3 scripts/lookup_actions.py --action 'List all Invoices'
python3 scripts/lookup_actions.py --validate
```

`key` is the setup UI's `v` and `name` its display label; `--names-only` outputs display labels. See [catalog format](references/CATALOG_FORMAT.md) and [profiles](references/ACTION_PROFILES.md).

## Safety

- Resolve and verify the intended endpoint, account and organization; never substitute another account when authorization or lookup fails.
- Minimize sensitive reads. Inspect live schemas; never invent IDs, parameters or returned values.
- Create/update Actions can affect financial state. Require an explicit task, check amounts, currency, tax, duplicates and recipients, and verify results after a write.
- Keep deletion, cancellation, void, write-off, refund, payment collection, bulk operations, administration, and email/SMS/reminders disabled unless specifically required and approved.
- Avoid endpoint command-line arguments on shared hosts; even commands using an environment variable can expose the expanded value in process listings. Do not include endpoints, tokens, customer information or financial records in logs or issues.
