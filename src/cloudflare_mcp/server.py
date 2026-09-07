"""MCP server exposing the Cloudflare API v4: zones and DNS record management.

Scope is deliberately limited to zones and DNS records — Cloudflare's REST API
also covers Workers, KV/R2/D1, cache purging, zone settings, Analytics, and
Radar, none of which are exposed here. See
https://developers.cloudflare.com/api/ for the full surface this
intentionally doesn't wrap.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from .client import CloudflareClient
from .config import CloudflareCredentials

mcp = MCPServer(
    name="cloudflare",
    version="0.1.0",
    instructions=(
        "Manage Cloudflare zones and DNS records. Requires CLOUDFLARE_API_TOKEN "
        "to be set in the environment (a scoped token from "
        "https://dash.cloudflare.com/profile/api-tokens with Zone:Read and "
        "DNS:Edit permissions). CLOUDFLARE_ACCOUNT_ID is optional, used only to "
        "filter list_zones when the token has access to more than one account."
    ),
)

_client: CloudflareClient | None = None

_DNS_RECORD_TYPES = {
    "A", "AAAA", "CNAME", "MX", "TXT", "SRV", "NS", "CAA", "CERT", "DNSKEY",
    "DS", "LOC", "NAPTR", "PTR", "SMIMEA", "SSHFP", "SVCB", "TLSA", "URI",
}


def _get_client() -> CloudflareClient:
    global _client
    if _client is None:
        credentials = CloudflareCredentials.from_env()
        _client = CloudflareClient(credentials)
    return _client


def _validate_record_type(record_type: str) -> None:
    if record_type not in _DNS_RECORD_TYPES:
        raise ValueError(
            f"Invalid DNS record type: {record_type!r}. Valid values are: "
            f"{sorted(_DNS_RECORD_TYPES)}"
        )


# --- Zones ---------------------------------------------------------------------


@mcp.tool()
async def list_zones(
    name: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    """List zones (domains) visible to this API token.

    name filters to an exact zone name (e.g. 'example.com'). status filters
    by zone status (e.g. 'active', 'pending'). Automatically scoped to
    CLOUDFLARE_ACCOUNT_ID if that's set in the environment.
    """
    client = _get_client()
    credentials = CloudflareCredentials.from_env()
    params = {
        "name": name,
        "status": status,
        "account.id": credentials.account_id,
    }
    return await client.get_all_pages("/zones", params=params)


@mcp.tool()
async def get_zone(zone_id: str) -> dict[str, Any]:
    """Fetch one zone's details by its Cloudflare zone ID."""
    client = _get_client()
    return await client.get(f"/zones/{zone_id}")


# --- DNS records -----------------------------------------------------------------


@mcp.tool()
async def list_dns_records(
    zone_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
) -> list[dict[str, Any]]:
    """List DNS records in a zone, optionally filtered by type, name, or content.

    type is a record type such as A, AAAA, CNAME, MX, TXT, NS, CAA, SRV, etc.
    name is an exact record name (e.g. 'www.example.com'). content filters by
    the record's value (e.g. an IP address).
    """
    if type is not None:
        _validate_record_type(type)
    client = _get_client()
    params = {"type": type, "name": name, "content": content}
    return await client.get_all_pages(f"/zones/{zone_id}/dns_records", params=params)


@mcp.tool()
async def get_dns_record(zone_id: str, dns_record_id: str) -> dict[str, Any]:
    """Fetch one DNS record's details by its ID within a zone."""
    client = _get_client()
    return await client.get(f"/zones/{zone_id}/dns_records/{dns_record_id}")


@mcp.tool()
async def create_dns_record(
    zone_id: str,
    type: str,
    name: str,
    content: str,
    ttl: int = 1,
    proxied: bool = False,
    priority: int | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Create a DNS record in a zone.

    type is one of A, AAAA, CNAME, MX, TXT, NS, CAA, SRV, etc. name is the
    record name (e.g. 'www.example.com' or '@' for the zone apex). content
    is the record's value (an IP for A/AAAA, a hostname for CNAME/MX, etc.).
    ttl is in seconds; 1 means "automatic". proxied routes traffic through
    Cloudflare's proxy (orange cloud) — only valid for A/AAAA/CNAME records.
    priority is required for MX and some SRV/URI records.
    """
    _validate_record_type(type)
    body: dict[str, Any] = {
        "type": type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "proxied": proxied,
    }
    if priority is not None:
        body["priority"] = priority
    if comment is not None:
        body["comment"] = comment

    client = _get_client()
    return await client.post(f"/zones/{zone_id}/dns_records", body)


@mcp.tool()
async def update_dns_record(
    zone_id: str,
    dns_record_id: str,
    type: str | None = None,
    name: str | None = None,
    content: str | None = None,
    ttl: int | None = None,
    proxied: bool | None = None,
    priority: int | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Partially update an existing DNS record. Only the fields you pass are changed."""
    if type is not None:
        _validate_record_type(type)
    body: dict[str, Any] = {
        "type": type,
        "name": name,
        "content": content,
        "ttl": ttl,
        "proxied": proxied,
        "priority": priority,
        "comment": comment,
    }
    body = {k: v for k, v in body.items() if v is not None}
    if not body:
        raise ValueError("Provide at least one field to update.")

    client = _get_client()
    return await client.patch(f"/zones/{zone_id}/dns_records/{dns_record_id}", body)


@mcp.tool()
async def delete_dns_record(zone_id: str, dns_record_id: str) -> dict[str, Any]:
    """Delete a DNS record from a zone. This is irreversible."""
    client = _get_client()
    return await client.delete(f"/zones/{zone_id}/dns_records/{dns_record_id}")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
