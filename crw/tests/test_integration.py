"""Integration tests against the live CRW API. Skipped without CRW_API_KEY."""

import os

import pytest
from tools.crw_client import CrwClient

pytestmark = pytest.mark.skipif(
    not os.getenv("CRW_API_KEY"),
    reason="CRW_API_KEY not set",
)


@pytest.fixture()
def client() -> CrwClient:
    return CrwClient(api_key=os.environ["CRW_API_KEY"])


def test_capabilities_validates_the_key(client: CrwClient) -> None:
    # This is the call the credential form makes; it must cost no credits.
    result = client.capabilities()
    assert result.get("formats")


def test_scrape(client: CrwClient) -> None:
    result = client.scrape("https://example.com")
    assert result["success"] is True
    assert len(result["data"]["markdown"]) > 0


def test_search(client: CrwClient) -> None:
    result = client.search("web scraping tools", limit=3)
    assert result["success"] is True
    assert isinstance(result["data"], list)
    assert "url" in result["data"][0]


def test_map(client: CrwClient) -> None:
    result = client.map("https://example.com")
    assert result["success"] is True
    assert "links" in result["data"]


def test_extract_is_synchronous_on_the_managed_api(client: CrwClient) -> None:
    """The managed API answers with `results` and no job id. If this ever starts
    returning an id instead, the extract tool's branch has to be revisited."""
    result = client.extract(
        ["https://example.com"],
        prompt="the page title",
        schema={"type": "object", "properties": {"title": {"type": "string"}}},
    )
    assert result["success"] is True
    assert "results" in result
    assert result["results"][0]["status"] == "completed"


def test_crawl(client: CrwClient) -> None:
    start = client.crawl("https://example.com", maxDepth=1, maxPages=2)
    assert start["success"] is True

    result = client.poll(client.crawl_status, start["id"], budget=120, interval=3)
    assert result["status"] == "completed"
    assert isinstance(result["data"], list)
