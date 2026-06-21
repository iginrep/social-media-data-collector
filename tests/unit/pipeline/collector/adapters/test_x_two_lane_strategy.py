from __future__ import annotations

import httpx
import pytest

from pipeline.collector.adapters.twitter import TwitterAdapter


pytestmark = pytest.mark.unit


def test_x_collects_public_mentions_and_official_conversation_replies():
    urls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        urls.append(str(request.url))
        if "/users/by/username/" in str(request.url):
            return httpx.Response(200, json={"data": {"id": "u1", "username": "bnisekuritas46", "name": "BNI Sekuritas"}})
        if "/users/u1/tweets" in str(request.url):
            return httpx.Response(200, json={"data": [{"id": "root1", "text": "official BIONS post", "conversation_id": "root1", "author_id": "u1"}]})
        return httpx.Response(200, json={"data": [{"id": "reply1", "text": "BIONS app error", "conversation_id": "root1", "author_id": "u2", "referenced_tweets": [{"type": "replied_to", "id": "root1"}]}]})

    adapter = TwitterAdapter(
        bearer_token="token",
        official_usernames=["bnisekuritas46"],
        search_queries=['"BIONS" lang:id -is:retweet'],
        collect_public_mentions=True,
        collect_official_post_replies=True,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    rows = adapter.collect("BIONS", "BIONS", limit=10)

    assert any("tweets/search/recent" in url and "%22BIONS%22" in url for url in urls)
    assert any("/users/by/username/bnisekuritas46" in url for url in urls)
    assert any("/users/u1/tweets" in url for url in urls)
    assert any("conversation_id%3Aroot1" in url for url in urls)
    assert rows[-1].source_id == "reply1"
    assert rows[-1].conversation_id == "root1"
    assert rows[-1].root_source_id == "root1"
    assert rows[-1].parent_source_id == "root1"
    assert rows[-1].relation_type == "reply"


def test_x_disabled_lanes_raise_clear_config_error():
    adapter = TwitterAdapter(bearer_token="token", search_queries=[], official_usernames=[])
    with pytest.raises(Exception, match="X_SEARCH_QUERIES or X_OFFICIAL_USERNAMES missing"):
        adapter.collect("BIONS", "BIONS", limit=1)
