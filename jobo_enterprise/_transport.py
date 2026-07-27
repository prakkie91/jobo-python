"""Shared request helpers: bounded retries and typed error raising.

Every sub-client goes through :func:`request` / :func:`arequest` rather than
touching ``httpx`` directly, so retry behaviour and error mapping stay in one
place.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import httpx

from jobo_enterprise.exceptions import _handle_error

#: Statuses the API documents as transient. Everything else fails immediately.
RETRY_STATUSES = frozenset({429, 503})

#: Retries *after* the initial attempt, so 3 means at most 4 requests.
DEFAULT_MAX_RETRIES = 3

#: Upper bound on a single backoff sleep, including a server ``Retry-After``.
MAX_BACKOFF_SECONDS = 30.0

#: The feed endpoints stream up to 1,000 full job records per call. The API
#: docs ask for a response timeout of at least 120 seconds on those routes.
DEFAULT_FEED_TIMEOUT = 120.0


def _backoff_seconds(response: httpx.Response, attempt: int) -> float:
    """Honour ``Retry-After`` when present, else exponential backoff."""
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return min(float(retry_after), MAX_BACKOFF_SECONDS)
        except ValueError:
            pass
    return min(0.5 * float(2**attempt), MAX_BACKOFF_SECONDS)


def _build(
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Any] = None,
    timeout: Optional[float] = None,
) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {"method": method, "url": url}
    if params is not None:
        kwargs["params"] = params
    if json is not None:
        kwargs["json"] = json
    if timeout is not None:
        kwargs["timeout"] = timeout
    return kwargs


def request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Any] = None,
    timeout: Optional[float] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Any:
    """Send a request, retrying transient statuses, and return the parsed body."""
    kwargs = _build(method, url, params=params, json=json, timeout=timeout)
    for attempt in range(max_retries + 1):
        response = client.request(**kwargs)
        if response.status_code == 200:
            return response.json()
        if response.status_code in RETRY_STATUSES and attempt < max_retries:
            time.sleep(_backoff_seconds(response, attempt))
            continue
        _handle_error(response)
    raise AssertionError("unreachable")  # pragma: no cover


async def arequest(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Any] = None,
    timeout: Optional[float] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> Any:
    """Async twin of :func:`request`."""
    kwargs = _build(method, url, params=params, json=json, timeout=timeout)
    for attempt in range(max_retries + 1):
        response = await client.request(**kwargs)
        if response.status_code == 200:
            return response.json()
        if response.status_code in RETRY_STATUSES and attempt < max_retries:
            await asyncio.sleep(_backoff_seconds(response, attempt))
            continue
        _handle_error(response)
    raise AssertionError("unreachable")  # pragma: no cover
