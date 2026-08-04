"""
Shared HTTP client for the fastCRW API.

Transport rules that exist for a reason, do not relax them casually:

* POSTs are NEVER retried. Every POST here starts billable work, and the API has
  no idempotency key. The managed backend deliberately answers uncertain
  post-charge failures with a non-retryable 500 to stop double billing; a blind
  client retry would defeat that.
* Polling uses a monotonic absolute deadline, and caps every HTTP attempt and
  every sleep to what is left of it. Counting only sleeps lets one slow status
  read overrun the budget by minutes, and Dify kills the invocation at 300s.
"""

import json
import time
from collections.abc import Mapping
from typing import Any

import requests

DEFAULT_BASE_URL = "https://fastcrw.com/api"

# Dify's own MAX_REQUEST_TIMEOUT defaults to 300s. Stay clear of it so the tool
# can always return the job id instead of being killed mid-poll.
DEFAULT_POLL_BUDGET = 240.0
DEFAULT_HTTP_TIMEOUT = 120.0
# For endpoints the managed API completes synchronously and that can genuinely
# run for minutes (extract over a long URL list). Still under Dify's 300s.
SYNC_JOB_TIMEOUT = 270.0


class CrwError(Exception):
    """A fastCRW API error. Deliberately NOT a RequestException, so the retry
    loop cannot mistake it for a transient transport failure.

    `status_code` is the HTTP status when the server answered, and None when we
    never got a reply. The difference decides whether a failing poll is fatal.
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _api_error(resp: requests.Response) -> str:
    try:
        return str(resp.json().get("error", resp.text[:200]))
    except ValueError:
        return resp.text[:200] or resp.reason


class CrwClient:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _request(
        self,
        method: str,
        path: str,
        data: Mapping[str, Any] | None = None,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """`deadline` is an absolute `time.monotonic()` value bounding ALL
        attempts together. Without it, three retries at `timeout` each can take
        three times as long as the caller budgeted."""
        url = f"{self.base_url}{path}"
        # Only idempotent verbs may be retried. See the module docstring.
        attempts = 3 if method.upper() in ("GET", "HEAD") else 1
        if deadline is None and attempts > 1:
            # Retries must never multiply the caller's wait. Without this, a
            # stalled server turns one 120s GET into 360s and Dify kills the
            # invocation at 300s.
            deadline = time.monotonic() + timeout
        for i in range(attempts):
            attempt_timeout = timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CrwError(f"Ran out of time waiting for {url}")
                attempt_timeout = min(timeout, remaining)
            try:
                resp = requests.request(
                    method,
                    url,
                    json=data,
                    headers=self._headers(),
                    timeout=attempt_timeout,
                )
            except requests.exceptions.RequestException as exc:
                if i < attempts - 1 and _sleep_within(0.3 * (2**i), deadline):
                    continue
                # Every other failure path in this module speaks CrwError; a
                # connection failure should not be the one that leaks a
                # requests internal at the user.
                raise CrwError(f"Could not reach {url}: {exc}") from exc
            if 400 <= resp.status_code < 500:
                raise CrwError(
                    f"CRW API error ({resp.status_code}): {_api_error(resp)}",
                    resp.status_code,
                )
            if resp.status_code >= 500:
                if i < attempts - 1 and _sleep_within(0.3 * (2**i), deadline):
                    continue
                raise CrwError(
                    f"CRW API error ({resp.status_code}): {_api_error(resp)}",
                    resp.status_code,
                )
            try:
                result = resp.json()
            except ValueError:
                # A 2xx that is not JSON means we are not talking to a CRW
                # server. Retrying cannot fix a wrong Base URL.
                raise CrwError(
                    f"{url} returned {resp.status_code} but not JSON. "
                    "Check the CRW Server Base URL; it does not look like a CRW server.",
                    resp.status_code,
                ) from None
            if not result.get("success", True):
                raise CrwError(
                    f"CRW API error: {result.get('error', 'Unknown error')}",
                    resp.status_code,
                )
            return result
        # Unreachable: every iteration returns, raises, or continues, and the
        # last iteration cannot continue. Kept out of the code entirely rather
        # than left as a misleading "after retries" message.
        raise AssertionError("unreachable")

    def capabilities(self) -> dict[str, Any]:
        """Server info. Validates the API key without spending a credit."""
        return self._request("GET", "/v1/capabilities")

    def scrape(self, url: str, **kwargs: Any) -> dict[str, Any]:
        body = {"url": url, **kwargs}
        # `deadlineMs` is what the caller asked the SERVER for; the transport
        # deadline is derived from it so a hard-coded socket timeout can never
        # cut a request short before the server's own budget expires. Derived,
        # never a separate argument, so it cannot collide with a body field.
        deadline_ms = body.get("deadlineMs")
        return self._request(
            "POST",
            "/v1/scrape",
            body,
            timeout=_transport(deadline_ms / 1000 if deadline_ms else None),
        )

    def crawl(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/v1/crawl", {"url": url, **kwargs})

    def crawl_status(
        self,
        job_id: str,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "GET", f"/v1/crawl/{job_id}", timeout=timeout, deadline=deadline
        )

    def cancel_crawl(self, job_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/crawl/{job_id}")

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/v1/search", {"query": query, **kwargs})

    def map(self, url: str, **kwargs: Any) -> dict[str, Any]:
        body = {"url": url, **kwargs}
        # Map's own `timeout` is in SECONDS (scrape's `deadlineMs` is millis).
        return self._request(
            "POST", "/v1/map", body, timeout=_transport(body.get("timeout"))
        )

    def extract(self, urls: list[str], **kwargs: Any) -> dict[str, Any]:
        # The managed API runs extract synchronously and can legitimately spend
        # minutes on a long URL list, so the socket must outlast it. Kept under
        # Dify's own 300s invocation limit.
        return self._request(
            "POST", "/v1/extract", {"urls": urls, **kwargs}, timeout=SYNC_JOB_TIMEOUT
        )

    def extract_status(
        self,
        job_id: str,
        timeout: float = DEFAULT_HTTP_TIMEOUT,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "GET", f"/v1/extract/{job_id}", timeout=timeout, deadline=deadline
        )

    def poll(
        self,
        fetch: Any,
        job_id: str,
        budget: float = DEFAULT_POLL_BUDGET,
        interval: float = 3.0,
    ) -> dict[str, Any]:
        """Poll `fetch(job_id, timeout=...)` until the job reaches a terminal
        state or `budget` seconds elapse.

        On timeout this RETURNS the last status seen rather than raising: the
        job id and any pages already collected must reach the caller, or a job
        that is still running server-side becomes unreachable.
        """
        deadline = time.monotonic() + budget
        status: dict[str, Any] = {"success": True, "status": "processing", "id": job_id}
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return status
            try:
                status = fetch(
                    job_id,
                    timeout=min(DEFAULT_HTTP_TIMEOUT, remaining),
                    deadline=deadline,
                )
            except CrwError as exc:
                # Swallow ONLY the cases that leave the job plausibly alive:
                # no response at all (timeout, unreachable) or a 5xx. Anything
                # the server actually answered - a 404 for a job that is gone, a
                # 401, a non-JSON body from a misconfigured Base URL - is a real
                # error, and reporting "processing" for it would be a fabrication.
                #
                # 5xx is deliberately on the swallow side even though the server
                # did answer: an unhealthy status endpoint says nothing about the
                # job, which is very likely still running and billable. Losing
                # its id would strand it; the caller can re-poll with the id.
                if exc.status_code is not None and exc.status_code < 500:
                    raise
                return status
            if status.get("status") in ("completed", "failed", "cancelled"):
                return status
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return status
            time.sleep(min(interval, remaining))


def _sleep_within(seconds: float, deadline: float | None) -> bool:
    """Sleep for `seconds`, never past `deadline`. False when there is no time
    left, which tells the caller to stop retrying."""
    if deadline is None:
        time.sleep(seconds)
        return True
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return False
    time.sleep(min(seconds, remaining))
    return True


def _transport(request_timeout: float | None) -> float:
    """Transport deadline for a call carrying its own server-side timeout.

    A hard-coded 120s socket timeout silently caps any `timeout` the caller
    asked the server for, so derive it instead and leave headroom for the
    response body.
    """
    if not request_timeout:
        return DEFAULT_HTTP_TIMEOUT
    return max(DEFAULT_HTTP_TIMEOUT, float(request_timeout) + 15.0)


def get_array_params(params: dict[str, Any], key: str) -> list[str] | None:
    """Split a user-entered list on newlines and commas.

    Newlines matter because a comma is legal inside a URL, so a one-per-line URL
    list must work. Spaces are NOT separators: a CSS selector like
    `.content > p` is a single legitimate entry.
    """
    value = params.get(key)
    if not value or not isinstance(value, str):
        return None
    # A comma is legal inside a URL, so once the user has written one entry per
    # line, the newline is the separator and commas are content.
    #
    # `strip()` FIRST: a textarea almost always hands back a trailing newline,
    # and testing the raw value would read "a,b,c\n" as newline-separated and
    # return the single unsplit string "a,b,c".
    lines = [ln for ln in value.strip().splitlines() if ln.strip()]
    parts = lines if len(lines) > 1 else lines[0].split(",") if lines else []
    return [s.strip() for s in parts if s.strip()] or None


def get_json_params(params: dict[str, Any], key: str) -> Any | None:
    value = params.get(key)
    if not value or not isinstance(value, str):
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass
    # Rescue Python-dict-style single-quoted input. Only reached when the strict
    # parse already failed, so valid JSON containing an apostrophe is never
    # mangled by it.
    try:
        return json.loads(value.replace("'", '"'))
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in parameter '{key}'") from None


def as_int(params: dict[str, Any], key: str) -> int | None:
    """Dify number fields can arrive as strings; the API rejects those."""
    value = params.get(key)
    if value is None or value == "":
        return None
    if isinstance(value, float) and value != int(value):
        # Checked BEFORE the int() fast path: int(3.9) succeeds and would
        # silently truncate. Dify can hand back a real float, not just a string.
        raise ValueError(f"Parameter '{key}' must be a whole number, got {value!r}")
    try:
        # int() first so a large integer keeps full precision; float is only the
        # fallback for the "3.0" an LLM may emit for a `form: llm` number, where
        # int("3.0") raises. A genuinely fractional value stays an error rather
        # than a silent truncation the user never asked for.
        return int(value)
    except (TypeError, ValueError):
        pass
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"Parameter '{key}' must be a whole number, got {value!r}"
        ) from None
    if number != int(number):
        raise ValueError(f"Parameter '{key}' must be a whole number, got {value!r}")
    return int(number)
