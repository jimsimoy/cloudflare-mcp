"""Minimal async client for the Cloudflare API v4 (zones and DNS records only)."""

from __future__ import annotations

from typing import Any

import httpx

from .config import CloudflareCredentials

_BASE_URL = "https://api.cloudflare.com/client/v4"


class CloudflareApiError(RuntimeError):
    def __init__(self, status_code: int, errors: Any) -> None:
        self.status_code = status_code
        self.errors = errors
        super().__init__(f"Cloudflare API error {status_code}: {errors}")


class CloudflareClient:
    def __init__(self, credentials: CloudflareCredentials) -> None:
        self._credentials = credentials
        self._http = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {credentials.api_token}",
                "Content-Type": "application/json",
            },
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._http.get(path, params=_clean(params))
        return self._unwrap(response)

    async def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 50,
        max_pages: int = 20,
    ) -> list[Any]:
        """Follow Cloudflare's page/result_info.total_pages pagination."""
        results: list[Any] = []
        page_params = dict(_clean(params) or {})
        page_params["per_page"] = per_page
        for page in range(1, max_pages + 1):
            page_params["page"] = page
            response = await self._http.get(path, params=page_params)
            body = self._raw_body(response)
            results.extend(body.get("result") or [])
            total_pages = (body.get("result_info") or {}).get("total_pages", page)
            if page >= total_pages:
                break
        return results

    async def post(self, path: str, json_body: dict[str, Any]) -> Any:
        response = await self._http.post(path, json=json_body)
        return self._unwrap(response)

    async def patch(self, path: str, json_body: dict[str, Any]) -> Any:
        response = await self._http.patch(path, json=json_body)
        return self._unwrap(response)

    async def delete(self, path: str) -> Any:
        response = await self._http.delete(path)
        return self._unwrap(response)

    def _unwrap(self, response: httpx.Response) -> Any:
        body = self._raw_body(response)
        if not body.get("success", False):
            raise CloudflareApiError(response.status_code, body.get("errors"))
        return body.get("result")

    @staticmethod
    def _raw_body(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if response.status_code >= 400 and not body:
            raise CloudflareApiError(response.status_code, response.text)
        return body


def _clean(params: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop None values so optional filters aren't sent as literal 'None'."""
    if params is None:
        return None
    return {k: v for k, v in params.items() if v is not None}
