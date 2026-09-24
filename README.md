# Cloudflare MCP — Zones & DNS Management

<div align="center">

<img src="https://img.shields.io/badge/python-3.12%2B-blue.svg?style=flat-square" alt="Python 3.12+">
<a href="https://github.com/jimsimoy/cloudflare-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
<a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-green.svg?style=flat-square" alt="MCP Compatible"></a>
<img src="https://img.shields.io/badge/tools-13-brightgreen.svg?style=flat-square" alt="13 Tools">
<img src="https://img.shields.io/badge/package%20manager-uv-orange.svg?style=flat-square" alt="Managed with uv">

**13 tools for Cloudflare zone/DNS management and Email Routing — for Claude Desktop, Claude Code, and any MCP client.**

by [Jan Ivan Simoy](https://github.com/jimsimoy)

</div>

---

> **Unofficial.** This is an independent, community-built project — not affiliated with, endorsed by, or sponsored by Cloudflare.

## What is this?

Cloudflare MCP is a [Model Context Protocol](https://modelcontextprotocol.io) server that gives AI assistants structured access to the [Cloudflare API v4](https://developers.cloudflare.com/api/) — zones (domains), their DNS records, and Email Routing (destination addresses + forwarding rules).

It deliberately covers only this slice. Cloudflare's REST API is enormous — Workers, KV/R2/D1, cache purging, general zone settings, Analytics, Radar, and more — and Cloudflare already ships more than a dozen product-specific MCP servers of its own for that surface. This one stays narrow: zones, DNS records, and the Email Routing feature (which itself just manages a specific set of DNS records plus destination-address verification and rule matching). Cache purging and other zone-settings edits are explicitly out of scope for v1 — they change how traffic is served for an entire domain and deserve their own deliberate tool design later, not a bolt-on here.

**Supported platform:** any MCP client on macOS, Linux, or Windows with Python 3.12+.

---

## Tools

| Category | Tools | What you can do |
|---|---|---|
| **Zones** | 2 | List zones (domains) visible to the token, fetch one by ID |
| **DNS Records** | 5 | List/filter, fetch, create, update, and delete DNS records within a zone |
| **Email Routing** | 6 | Enable routing on a zone, manage destination addresses, manage forwarding rules |

<details>
<summary>Full tool reference</summary>

| Tool | Description |
|---|---|
| `list_zones` | List zones visible to this API token, optionally filtered by name/status |
| `get_zone` | Fetch one zone's details by zone ID |
| `list_dns_records` | List DNS records in a zone, optionally filtered by type/name/content |
| `get_dns_record` | Fetch one DNS record's details by record ID |
| `create_dns_record` | Create a DNS record (A, AAAA, CNAME, MX, TXT, NS, CAA, SRV, etc.) |
| `update_dns_record` | Partially update an existing DNS record — only the fields you pass change |
| `delete_dns_record` | Delete a DNS record (irreversible) |
| `enable_email_routing` | Enable Email Routing on a zone (auto-adds/locks the required MX + SPF-include records) |
| `list_email_routing_addresses` | List destination addresses on the account (shared across all zones), with verification status |
| `create_email_routing_address` | Add a destination address (triggers a verification email, unless it's the account's own login email) |
| `list_email_routing_rules` | List forwarding rules for a zone |
| `create_email_routing_rule` | Create a rule forwarding one exact address to a verified destination |

</details>

### A note on Email Routing permissions

Beyond the base `Zone:DNS:Edit`/`Zone:Zone:Read` above, Email Routing needs three more token permissions: **Account → Email Routing Addresses → Edit**, **Zone → Email Routing Rules → Edit**, and **Zone → Zone Settings → Edit** (the last one specifically gates the enable/disable toggle — easy to miss since it's not obviously "email" named). `CLOUDFLARE_ACCOUNT_ID` is **required**, not optional, for the two account-scoped address tools.

If a zone already has MX/SPF records from another provider (e.g. registrar-based forwarding), remove those first with `delete_dns_record` — Cloudflare Email Routing's own MX records will conflict with them otherwise, and SPF only allows one TXT record.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.12 or later |
| [uv](https://docs.astral.sh/uv/) | any recent version |
| Cloudflare account | with at least one zone (domain) added |
| Cloudflare API token | scoped, created via the dashboard (see below) |

---

## Authentication

Cloudflare API tokens are simple bearer credentials — no OAuth flow, no refresh step. Setup:

1. Go to [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) and click **Create Token**.
2. Choose **Create Custom Token**.
3. Under **Permissions**, add:
   - `Zone` → `Zone` → `Read`
   - `Zone` → `DNS` → `Edit`
4. Under **Zone Resources**, scope it to **Specific zone** and pick the domain(s) this server should be able to touch — avoid "All zones" unless you actually need it. This is the principle of least privilege: a leaked token scoped to one zone can't touch the rest of the account.
5. Click **Continue to summary**, then **Create Token**. Copy it immediately — Cloudflare shows it once.
6. Put it in `.env` (see [Installation](#installation)).

`CLOUDFLARE_ACCOUNT_ID` is optional — only needed if the token has access to more than one Cloudflare account and you want `list_zones` scoped to a specific one. Find it on the right sidebar of any domain's Overview page in the dashboard.

If the token is ever exposed, revoke it from the same API Tokens page — this immediately invalidates it account-wide.

---

## Installation

```bash
git clone https://github.com/jimsimoy/cloudflare-mcp.git
cd cloudflare-mcp
uv sync
cp .env.example .env   # fill in CLOUDFLARE_API_TOKEN (and CLOUDFLARE_ACCOUNT_ID if needed)
```

Run directly:

```bash
uv run cloudflare-mcp
```

---

## Client Setup

```json
{
  "mcpServers": {
    "cloudflare": {
      "command": "uv",
      "args": ["--directory", "/path/to/cloudflare-mcp", "run", "cloudflare-mcp"],
      "env": {
        "CLOUDFLARE_API_TOKEN": "...",
        "CLOUDFLARE_ACCOUNT_ID": "..."
      }
    }
  }
}
```

Restart your MCP client after saving. The 7 Cloudflare tools will appear automatically.

---

## Usage Examples

### See what's in the account

```
List my Cloudflare zones, then list the DNS records for the first one
```

### Point a subdomain at a new IP

```
Create an A record for api.example.com pointing to 203.0.113.10 in zone
<zone_id>, not proxied, TTL automatic
```

### Update an existing record

```
Update DNS record <record_id> in zone <zone_id> to change its content to
203.0.113.20
```

### Clean up a stale record

```
Delete DNS record <record_id> from zone <zone_id>
```

---

## Security

- The credential (`CLOUDFLARE_API_TOKEN`) is read from the environment only — `.env` and `.env.*` (except `.env.example`) are gitignored.
- A Cloudflare API token is a long-lived credential. Scope it to specific zones and only the permissions listed above; treat it like a password and revoke it at [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) if it's ever exposed.
- `create_dns_record`, `update_dns_record`, and `delete_dns_record` make real changes to live DNS — a wrong `delete_dns_record` call can take a subdomain offline. There's no confirmation step in the server itself; that judgment call belongs to whatever is driving the MCP client.
- Cache purging, zone settings (SSL mode, security level, page rules, etc.), and anything outside zones/DNS are out of scope for this server by design — see [What is this?](#what-is-this).

---

## Project Structure

```
src/cloudflare_mcp/
  server.py  # MCP server entry point and tool definitions
  client.py  # Cloudflare API client (bearer auth, pagination, error unwrapping)
  config.py  # Credential loading from the environment
```

The server communicates over stdio using JSON-RPC 2.0, the standard MCP transport.

---

## A note on testing

This was built directly from Cloudflare's official REST API v4 reference (zone and DNS record endpoints, request/response shapes, and the `success`/`errors`/`result`/`result_info` envelope), with pagination and error handling covered by manual verification of the client against that reference. It has **not** been exercised against a live Cloudflare account — no API token was available in this environment at build time. Before relying on it, run it against a real account starting with the read-only tools (`list_zones`, `list_dns_records`) and confirm the shapes match what you expect before trying `create_dns_record` / `update_dns_record` / `delete_dns_record`.

---

## License

[MIT](./LICENSE) — free to use, modify, and distribute.

---

<div align="center">

[Report a Bug](https://github.com/jimsimoy/cloudflare-mcp/issues) · [Request a Feature](https://github.com/jimsimoy/cloudflare-mcp/issues)

</div>
