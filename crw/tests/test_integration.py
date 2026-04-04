"""Integration tests for CRW API via CrwClient."""

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


def test_scrape(client: CrwClient) -> None:
    result = client.scrape("https://example.com")
    assert result["success"] is True
    assert "markdown" in result["data"]
    assert len(result["data"]["markdown"]) > 0


def test_search(client: CrwClient) -> None:
    result = client.search("web scraping tools", limit=3)
    assert result["success"] is True
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert "url" in result["data"][0]
    assert "title" in result["data"][0]


def test_map(client: CrwClient) -> None:
    result = client.map("https://example.com")
    assert result["success"] is True
    assert "links" in result.get("data", result)


def test_crawl(client: CrwClient) -> None:
    # Start a crawl with minimal limits
    start = client.crawl("https://example.com", maxDepth=1, maxPages=2)
    assert start["success"] is True
    job_id = start["id"]

    # Poll until done
    result = client.poll_crawl(job_id, interval=3)
    assert result["status"] == "completed"
    assert isinstance(result["data"], list)
