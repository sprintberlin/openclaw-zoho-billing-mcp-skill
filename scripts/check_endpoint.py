#!/usr/bin/env python3
"""Validate endpoint selection locally without printing credentials or connecting."""
import argparse
import sys

from mcp_endpoint import EndpointResolutionError, resolve_mcp_url, add_endpoint_arguments


def main(argv=None):
    parser = add_endpoint_arguments(argparse.ArgumentParser(description=__doc__))
    args = parser.parse_args(argv)
    try:
        resolve_mcp_url(args, 'billing', ('ZOHO_BILLING_MCP_URL',))
    except EndpointResolutionError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1
    print('Endpoint configuration is valid locally; no connection attempted.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
