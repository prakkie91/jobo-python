"""Exception types for the Jobo Enterprise client."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class JoboError(Exception):
    """Base exception for all Jobo client errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        detail: Optional[str] = None,
        response_body: Optional[Any] = None,
        code: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail
        self.response_body = response_body
        self.code = code
        """Stable machine-readable problem code, when the API supplies one."""
        self.api_version = api_version


class JoboAuthenticationError(JoboError):
    """Raised when the API key is missing or invalid (401)."""


class JoboPermissionError(JoboError):
    """Raised when the key is valid but not entitled to the resource (403).

    The managed feed raises this for sandbox and marketplace keys, which carry
    no customer account and therefore no managed job sources.
    """


class JoboNotFoundError(JoboError):
    """Raised when the requested resource does not exist (404)."""


class JoboRateLimitError(JoboError):
    """Raised when the rate limit is exceeded (429) and retries are exhausted."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class JoboValidationError(JoboError):
    """Raised when the request is invalid (400)."""


class JoboCursorRestartRequiredError(JoboError):
    """Raised when a feed cursor can no longer be continued (409).

    A legacy non-stable scan reached the deep-pagination boundary. The cursor
    cannot be retried — discard it and start a new scan, leaving ``stable_scan``
    at its default.
    """


class JoboServerError(JoboError):
    """Raised when the server returns a 5xx error."""


def _problem_fields(body: Any) -> Tuple[str, Optional[str], Optional[str]]:
    """Pull ``detail``, ``code`` and ``api_version`` out of a problem body."""
    if not isinstance(body, dict):
        return str(body), None, None
    detail = body.get("detail") or body.get("error") or ""
    code = body.get("code")
    api_version = body.get("api_version")
    return str(detail), code, api_version


def _handle_error(response: "httpx.Response") -> None:
    """Raise a typed exception based on the HTTP status code."""
    status = response.status_code
    try:
        body = response.json()
    except Exception:
        body = response.text

    detail, code, api_version = _problem_fields(body)
    message = f"HTTP {status}: {detail}" if detail else f"HTTP {status}"
    kwargs: Dict[str, Any] = {
        "status_code": status,
        "detail": detail,
        "response_body": body,
        "code": code,
        "api_version": api_version,
    }

    if status == 401:
        raise JoboAuthenticationError(message, **kwargs)
    if status == 403:
        raise JoboPermissionError(message, **kwargs)
    if status == 404:
        raise JoboNotFoundError(message, **kwargs)
    if status == 409:
        raise JoboCursorRestartRequiredError(message, **kwargs)
    if status == 429:
        retry_after = response.headers.get("Retry-After")
        raise JoboRateLimitError(
            message,
            retry_after=int(retry_after) if retry_after and retry_after.isdigit() else None,
            **kwargs,
        )
    if status == 400:
        raise JoboValidationError(message, **kwargs)
    if status >= 500:
        raise JoboServerError(message, **kwargs)

    raise JoboError(message, **kwargs)
