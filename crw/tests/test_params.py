"""Pure-function coverage for the parameter helpers. No network, runs in CI."""

import time

import pytest
from tools.crw_client import CrwClient, as_int, get_array_params, get_json_params


def test_json_keeps_apostrophes_in_valid_json() -> None:
    # The blind quote-swap rescue used to corrupt this into invalid JSON.
    value = '{"properties": {"title": {"description": "The article\'s title"}}}'
    assert get_json_params({"k": value}, "k") == {
        "properties": {"title": {"description": "The article's title"}}
    }


def test_json_still_rescues_single_quoted_input() -> None:
    assert get_json_params({"k": "{'a': 1}"}, "k") == {"a": 1}


def test_json_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        get_json_params({"k": "not json at all {"}, "k")


def test_json_empty_is_none() -> None:
    assert get_json_params({"k": ""}, "k") is None
    assert get_json_params({}, "k") is None


def test_array_splits_on_newlines_as_well_as_commas() -> None:
    # A comma is legal inside a URL, so newlines must work as separators.
    value = "https://a.example/x\nhttps://b.example/y"
    assert get_array_params({"k": value}, "k") == [
        "https://a.example/x",
        "https://b.example/y",
    ]


def test_array_trims_and_drops_blanks() -> None:
    assert get_array_params({"k": " a , , b "}, "k") == ["a", "b"]
    assert get_array_params({"k": "  "}, "k") is None


def test_as_int_accepts_dify_string_numbers() -> None:
    # Dify number fields can arrive as strings; the API rejects those.
    assert as_int({"k": "2"}, "k") == 2
    assert as_int({"k": 0}, "k") == 0
    assert as_int({"k": ""}, "k") is None
    assert as_int({}, "k") is None


def test_as_int_rejects_nonsense() -> None:
    with pytest.raises(ValueError):
        as_int({"k": "two"}, "k")


def test_poll_returns_last_status_on_deadline_instead_of_raising() -> None:
    """A running job's id must reach the caller, or the job is unreachable and
    keeps burning credits."""
    client = CrwClient(api_key="x")
    calls = []

    def never_finishes(job_id, timeout=None, deadline=None):
        calls.append(timeout)
        return {"success": True, "status": "scraping", "id": job_id, "data": [1]}

    started = time.monotonic()
    out = client.poll(never_finishes, "job-1", budget=0.5, interval=0.05)
    assert time.monotonic() - started < 3
    assert out["id"] == "job-1"
    assert out["data"] == [1]
    # Every attempt is capped to the remaining budget, never the full 120s.
    assert all(t is not None and t <= 0.5 for t in calls)


def test_poll_treats_cancelled_as_terminal() -> None:
    client = CrwClient(api_key="x")
    seen = {"n": 0}

    def cancelled(job_id, timeout=None, deadline=None):
        seen["n"] += 1
        return {"success": True, "status": "cancelled", "id": job_id}

    out = client.poll(cancelled, "job-2", budget=5, interval=0.01)
    assert out["status"] == "cancelled"
    assert seen["n"] == 1


def test_array_keeps_css_selectors_containing_spaces() -> None:
    # Splitting on spaces would shred a legitimate descendant selector.
    assert get_array_params({"k": ".content > p, #main"}, "k") == [
        ".content > p",
        "#main",
    ]


def test_map_timeout_does_not_collide_with_the_transport_kwarg(monkeypatch) -> None:
    """`timeout` rides in the map body and also sets the socket deadline.
    Passing it as a separate kwarg raised TypeError the moment a user filled it in."""
    client = CrwClient(api_key="x")
    seen = {}

    def fake(method, path, data=None, timeout=None):
        seen.update(method=method, path=path, data=data, timeout=timeout)
        return {"success": True, "data": {"links": []}}

    monkeypatch.setattr(client, "_request", fake)
    client.map(url="https://example.com", timeout=200, limit=5)
    assert seen["data"] == {"url": "https://example.com", "timeout": 200, "limit": 5}
    assert seen["timeout"] >= 200


def test_scrape_transport_deadline_follows_deadline_ms(monkeypatch) -> None:
    client = CrwClient(api_key="x")
    seen = {}

    def fake(method, path, data=None, timeout=None):
        seen.update(timeout=timeout, data=data)
        return {"success": True, "data": {}}

    monkeypatch.setattr(client, "_request", fake)
    client.scrape(url="https://example.com", deadlineMs=45000)
    # 45s server budget must not be cut short by a fixed socket timeout.
    assert seen["timeout"] >= 45


def test_as_int_accepts_whole_decimals_an_llm_might_emit() -> None:
    assert as_int({"k": "3.0"}, "k") == 3
    assert as_int({"k": 3.0}, "k") == 3


def test_as_int_rejects_genuinely_fractional_values() -> None:
    # Truncating 3.9 to 3 would give the user neither what they asked for nor
    # an error, so this is a hard failure.
    with pytest.raises(ValueError):
        as_int({"k": "3.9"}, "k")


def test_poll_returns_last_status_when_the_status_read_fails() -> None:
    """A failing poll must not strand a running, billable job."""
    from tools.crw_client import CrwError

    client = CrwClient(api_key="x")
    calls = {"n": 0}

    def flaky(job_id, timeout=None, deadline=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"success": True, "status": "scraping", "id": job_id, "data": [1]}
        raise CrwError("502 from the status endpoint")

    out = client.poll(flaky, "job-3", budget=5, interval=0.01)
    assert out["id"] == "job-3"
    assert out["data"] == [1]


def test_poll_never_overruns_its_budget_across_retries(monkeypatch) -> None:
    """_request retries GETs 3x. Without an absolute deadline shared by all
    attempts, a 240s budget takes 360s and Dify kills the invocation."""
    import tools.crw_client as m

    clock = [0.0]
    monkeypatch.setattr(m.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(m.time, "sleep", lambda n: clock.__setitem__(0, clock[0] + n))

    def always_times_out(*a, **k):
        clock[0] += k["timeout"]
        raise m.requests.Timeout("x")

    monkeypatch.setattr(m.requests, "request", always_times_out)
    client = m.CrwClient(api_key="x")
    out = client.poll(client.crawl_status, "job", budget=240)
    # Exact, not "close enough": a loose bound here is what hid the
    # uncapped retry backoff that pushed a 240s budget to 240.6s.
    assert clock[0] <= 240, f"overran the budget: {clock[0]}s"
    assert out["id"] == "job"


def test_poll_does_not_fabricate_a_status_for_a_job_that_does_not_exist(
    monkeypatch,
) -> None:
    import tools.crw_client as m

    class NotFound:
        status_code = 404
        text = ""
        reason = "Not Found"

        def json(self):
            return {"success": False, "error": "job not found"}

    monkeypatch.setattr(m.requests, "request", lambda *a, **k: NotFound())
    client = m.CrwClient(api_key="x")
    with pytest.raises(m.CrwError):
        client.poll(client.crawl_status, "ghost", budget=5, interval=0.01)


def test_search_reads_the_self_hosted_engine_envelope() -> None:
    """Managed returns a flat `data` list with `answer` on top; the engine nests
    both under `data.results` / `data.answer`."""
    from tools.search import _answer, _flatten

    engine = {
        "success": True,
        "data": {
            "results": [{"url": "https://example.com", "title": "Example"}],
            "answer": "ok",
        },
    }
    assert len(_flatten(engine["data"])) == 1
    assert _answer(engine) == "ok"

    managed = {
        "success": True,
        "data": [{"url": "https://example.com"}],
        "answer": "ok",
    }
    assert len(_flatten(managed["data"])) == 1
    assert _answer(managed) == "ok"

    grouped = {"web": [{"url": "a"}], "news": [{"url": "b"}]}
    assert len(_flatten(grouped)) == 2


def test_url_list_with_a_comma_in_the_url_survives_newline_separation() -> None:
    value = "https://example.com/a,b\nhttps://example.org/c"
    assert get_array_params({"k": value}, "k") == [
        "https://example.com/a,b",
        "https://example.org/c",
    ]


def test_as_int_keeps_large_integers_exact() -> None:
    # Going through float would round this to ...992.
    assert as_int({"k": "9007199254740993"}, "k") == 9007199254740993


def test_poll_surfaces_a_misconfigured_base_url_instead_of_faking_progress(
    monkeypatch,
) -> None:
    """A 200 that is not JSON means the Base URL points at something that is not
    a CRW server. Reporting "processing" would hide the misconfiguration."""
    import tools.crw_client as m

    class HtmlPage:
        status_code = 200
        text = "<html>nginx</html>"
        reason = "OK"

        def json(self):
            raise ValueError("not json")

    monkeypatch.setattr(m.requests, "request", lambda *a, **k: HtmlPage())
    client = m.CrwClient(api_key="x")
    with pytest.raises(m.CrwError, match="does not look like a CRW server"):
        client.poll(client.crawl_status, "job", budget=5, interval=0.01)


def test_array_trailing_newline_does_not_defeat_comma_splitting() -> None:
    """A textarea almost always returns a trailing newline. Reading that as
    "newline mode" turned "a,b,c" into one garbled entry."""
    assert get_array_params({"k": "url1,url2,url3\n"}, "k") == ["url1", "url2", "url3"]
    assert get_array_params({"k": "markdown\n"}, "k") == ["markdown"]
    assert get_array_params({"k": "a\n\n\nb\n"}, "k") == ["a", "b"]


def test_flatten_survives_a_pathological_envelope() -> None:
    """base_url is user-configurable, so a misbehaving self-hosted server must
    not be able to raise RecursionError, which nothing here would wrap."""
    from tools.search import _flatten

    deep = {"results": None}
    node = deep
    for _ in range(2000):
        node["results"] = {"results": None}
        node = node["results"]
    assert _flatten(deep) == []


def _crawl_messages(monkeypatch, status: str) -> list[str]:
    """Drive the real CrawlTool._invoke with a stubbed client, so the message
    branch under test is the shipped one and not a copy of it."""
    import tools.crawl as crawl_mod

    class StubClient:
        def __init__(self, *a, **k): ...

        def crawl(self, url, **kw):
            return {"success": True, "id": "job-9"}

        crawl_status = None

        def poll(self, fetch, job_id, **kw):
            return {
                "success": True,
                "id": job_id,
                "status": status,
                "data": [{}, {}],
                "total": 5,
                "completed": 2,
            }

    monkeypatch.setattr(crawl_mod, "CrwClient", StubClient)
    tool = crawl_mod.CrawlTool.__new__(crawl_mod.CrawlTool)
    tool.runtime = type("R", (), {"credentials": {"api_key": "x"}})()
    tool.create_text_message = lambda text: {"kind": "text", "text": text}
    tool.create_json_message = lambda payload: {"kind": "json"}
    tool.create_variable_message = lambda name, value: {"kind": "var"}
    out = list(tool._invoke({"url": "https://example.com"}))
    return [m["text"] for m in out if m["kind"] == "text"]


def test_unfinished_crawl_tells_the_agent_how_to_get_its_results(monkeypatch) -> None:
    """The API answers `accepted` then `scraping`, never `processing`. Matching
    on "processing" made this branch dead in the exact case it exists for."""
    for status in ("scraping", "accepted", "processing"):
        text = _crawl_messages(monkeypatch, status)[0]
        assert "Job ID: job-9" in text, status
        assert "Crawl Status tool" in text, status
        assert "2 pages collected" in text, status


def test_finished_and_failed_crawls_keep_their_own_messages(monkeypatch) -> None:
    assert "completed: 2/5" in _crawl_messages(monkeypatch, "completed")[0]
    assert _crawl_messages(monkeypatch, "failed")[0] == "Crawl failed. Job ID: job-9"
    assert (
        _crawl_messages(monkeypatch, "cancelled")[0] == "Crawl cancelled. Job ID: job-9"
    )


def test_as_int_rejects_a_real_fractional_float() -> None:
    """int(3.9) succeeds, so the int-first fast path had to be guarded: Dify can
    hand back an actual float, not only a string."""
    with pytest.raises(ValueError):
        as_int({"k": 3.9}, "k")


def test_a_lone_get_cannot_multiply_its_timeout_by_the_retry_count(monkeypatch) -> None:
    """capabilities() and a standalone crawl_status() take no deadline argument,
    so _request must impose one or 3 retries turn 120s into 360s."""
    import tools.crw_client as m

    clock = [0.0]
    monkeypatch.setattr(m.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(m.time, "sleep", lambda n: clock.__setitem__(0, clock[0] + n))

    def always_times_out(*a, **k):
        clock[0] += k["timeout"]
        raise m.requests.Timeout("x")

    monkeypatch.setattr(m.requests, "request", always_times_out)
    client = m.CrwClient(api_key="x")
    with pytest.raises(m.CrwError):
        client.capabilities()
    assert clock[0] <= m.DEFAULT_HTTP_TIMEOUT, f"one GET took {clock[0]}s"
