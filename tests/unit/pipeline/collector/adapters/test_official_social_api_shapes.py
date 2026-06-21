from __future__ import annotations

from datetime import timezone

import httpx
import pytest

from pipeline.collector.adapters.instagram import InstagramAdapter, parse_instagram_comments
from pipeline.collector.adapters.threads import ThreadsAdapter, parse_threads_conversation
from pipeline.collector.adapters.tiktok import TikTokResearchAdapter, parse_tiktok_research_comments
from pipeline.collector.adapters.twitter import TwitterAdapter


pytestmark = pytest.mark.unit


def test_x_recent_search_request_uses_official_conversation_fields():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"data": []})

    TwitterAdapter(
        bearer_token="token",
        search_queries=['"bions" lang:id -is:retweet'],
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    ).collect("bions", "bions", limit=10)

    assert "https://api.x.com/2/tweets/search/recent" in seen["url"]
    assert "conversation_id" in seen["url"]
    assert "referenced_tweets" in seen["url"]
    assert "expansions=author_id,in_reply_to_user_id,referenced_tweets.id" in seen["url"]


def test_tiktok_research_comments_are_video_comment_tree_rows():
    rows = parse_tiktok_research_comments(
        {
            "data": {
                "comments": [
                    {"id": 11, "video_id": 99, "text": "BIONS bagus", "create_time": 1700000000, "like_count": 2, "reply_count": 1},
                    {"id": 12, "video_id": 99, "parent_comment_id": 11, "text": "setuju", "create_time": 1700000001},
                ]
            }
        },
        keyword="bions",
        target_entity="bions",
    )

    assert rows[0].source_type == "comment"
    assert rows[0].conversation_id == "99"
    assert rows[0].root_source_id == "99"
    assert rows[0].depth == 1
    assert rows[0].relation_type == "comment"
    assert rows[0].posted_at and rows[0].posted_at.tzinfo is timezone.utc
    assert rows[1].parent_source_id == "11"
    assert rows[1].depth == 2
    assert rows[1].relation_type == "reply"


def test_instagram_comments_support_top_level_and_replies():
    rows = parse_instagram_comments(
        {
            "data": [
                {
                    "id": "c1",
                    "text": "BIONS error",
                    "timestamp": "2026-06-22T01:02:03+0000",
                    "username": "u1",
                    "replies": {"data": [{"id": "r1", "text": "same", "timestamp": "2026-06-22T01:03:03+0000", "username": "u2"}]},
                }
            ]
        },
        media_id="m1",
        keyword="bions",
        target_entity="bions",
    )

    assert rows[0].source_type == "comment"
    assert rows[0].root_source_id == "m1"
    assert rows[0].parent_source_id is None
    assert rows[0].depth == 1
    assert rows[0].relation_type == "comment"
    assert rows[1].parent_source_id == "c1"
    assert rows[1].root_source_id == "m1"
    assert rows[1].depth == 2
    assert rows[1].relation_type == "reply"


def test_threads_conversation_is_flat_reply_tree_with_native_parent_fields():
    rows = parse_threads_conversation(
        {
            "data": [
                {"id": "t1", "text": "root BIONS", "timestamp": "2026-06-22T01:02:03+0000", "username": "brand", "is_reply": False, "permalink": "https://threads.net/x"},
                {"id": "t2", "text": "reply", "timestamp": "2026-06-22T01:03:03+0000", "username": "u", "is_reply": True, "root_post": "t1", "replied_to": "t1"},
            ]
        },
        media_id="t1",
        keyword="bions",
        target_entity="bions",
    )

    assert rows[0].source_type == "post"
    assert rows[0].depth == 0
    assert rows[0].relation_type is None
    assert rows[1].source_type == "reply"
    assert rows[1].conversation_id == "t1"
    assert rows[1].root_source_id == "t1"
    assert rows[1].parent_source_id == "t1"
    assert rows[1].depth == 1
    assert rows[1].relation_type == "reply"


def test_official_adapters_need_token_and_ids():
    assert TikTokResearchAdapter().access_mode == "official_research_api"
    assert InstagramAdapter().access_mode == "official_graph_api"
    assert ThreadsAdapter().access_mode == "official_threads_api"
