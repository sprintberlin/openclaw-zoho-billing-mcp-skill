# Billing endpoint profiles

The included resolver validates configuration locally; it does **not** connect, query organizations, add authorization headers, or make MCP calls. For a single account, inject `ZOHO_BILLING_MCP_URL` securely and run `python3 scripts/check_endpoint.py`.

Endpoint selection order: explicit `--mcp-url`, then `--profile`, `ZOHO_BILLING_MCP_PROFILE`, `ZOHO_MCP_PROFILE`, then `ZOHO_BILLING_MCP_URL`. Profile file selection: `--profiles-file`, `ZOHO_MCP_PROFILES_FILE`, then `~/.config/zoho-mcp/profiles.json`.

Example with a non-secret environment variable name:

```json
{
  "version": 1,
  "profiles": {
    "sample": {"services": {"billing": {"env": "SAMPLE_BILLING_MCP_URL"}}}
  }
}
```

A Billing service may specify exactly one of `env`, `url_file`, or `url`. Relative `url_file` paths resolve from the profile file directory. Direct `url` makes the profile file a secret. Keep configuration and URL files outside repositories, restrict them to the account owner (e.g. `chmod 600`), and never print them. Only HTTPS endpoints without URL userinfo or fragments are accepted. `--mcp-url` is supported for one-off use but may leak via process arguments and shell history; avoid on shared systems. A profile selects an endpoint, not an organization: determine organization parameters from the live tool schema and explicitly verify the target. No client-to-server connection or runtime schema has been tested by this repository.
