"""Credential loading for the Cloudflare API.

Cloudflare API tokens are simple bearer credentials — unlike OAuth access
tokens they don't expire on a short cycle and don't need a refresh step, so
there's no token-provider/refresh machinery here, just a read from the
environment. See https://developers.cloudflare.com/fundamentals/api/get-started/create-token/
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CloudflareCredentials:
    api_token: str
    account_id: str | None

    @classmethod
    def from_env(cls) -> "CloudflareCredentials":
        return cls(
            api_token=_require_env("CLOUDFLARE_API_TOKEN"),
            account_id=os.environ.get("CLOUDFLARE_ACCOUNT_ID") or None,
        )


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable {name!r}. Set CLOUDFLARE_API_TOKEN "
            "before starting the server — create a scoped token at "
            "https://dash.cloudflare.com/profile/api-tokens."
        )
    return value
