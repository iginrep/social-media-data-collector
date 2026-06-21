from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.collector.adapters.google_play import GooglePlayAdapter, parse_google_play_reviews
from pipeline.collector.adapters.youtube import YouTubeAdapter, parse_youtube_comment_threads, parse_youtube_feed
from pipeline.collector.run import remaining_platform_adapters


pytestmark = pytest.mark.unit


def test_parse_google_play_reviews_normalizes_review_dicts():
    reviews = [
        {
            "reviewId": "gp1",
            "userName": "bions user",
            "score": 1,
            "content": "Aplikasi BIONS sering error",
            "thumbsUpCount": 4,
            "appVersion": "1.0.0",
            "at": datetime(2026, 6, 1, tzinfo=timezone.utc),
        }
    ]

    items = parse_google_play_reviews(reviews, keyword="bions", target_entity="bions")

    assert len(items) == 1
    item = items[0]
    assert item.platform == "google_play"
    assert item.source_type == "app_review"
    assert item.source_id == "gp1"
    assert item.author_display_name == "bions user"
    assert item.metrics["rating"] == 1
    assert item.metrics["thumbs_up"] == 4
    assert item.raw_payload["app_version"] == "1.0.0"
    assert item.collection_method == "scraper"


def test_parse_youtube_feed_normalizes_video_entries():
    xml = """<?xml version='1.0' encoding='UTF-8'?>
    <feed xmlns='http://www.w3.org/2005/Atom' xmlns:yt='http://www.youtube.com/xml/schemas/2015'>
      <entry>
        <yt:videoId>abc123</yt:videoId>
        <yt:channelId>UC_TEST</yt:channelId>
        <title>BIONS tutorial terbaru</title>
        <link rel='alternate' href='https://www.youtube.com/watch?v=abc123'/>
        <author><name>BNI Sekuritas</name></author>
        <published>2026-06-01T00:00:00+00:00</published>
      </entry>
    </feed>"""

    items = parse_youtube_feed(xml, keyword="bions", target_entity="bions")

    assert len(items) == 1
    item = items[0]
    assert item.platform == "youtube"
    assert item.source_type == "video"
    assert item.source_id == "abc123"
    assert item.author_display_name == "BNI Sekuritas"
    assert item.source_url == "https://www.youtube.com/watch?v=abc123"
    assert item.collection_method == "rss"


def test_parse_youtube_comment_threads_normalizes_top_level_comments():
    payload = {
        "items": [
            {
                "id": "thread-1",
                "snippet": {
                    "videoId": "abc123",
                    "totalReplyCount": 2,
                    "topLevelComment": {
                        "id": "comment-1",
                        "snippet": {
                            "authorDisplayName": "public user",
                            "authorChannelId": {"value": "UC_AUTHOR"},
                            "textOriginal": "BIONS mobile app bagus",
                            "likeCount": 5,
                            "publishedAt": "2026-06-01T00:00:00Z",
                        },
                    },
                },
            }
        ]
    }

    items = parse_youtube_comment_threads(payload, keyword="bions", target_entity="bions")

    assert len(items) == 1
    item = items[0]
    assert item.platform == "youtube"
    assert item.source_type == "comment"
    assert item.source_id == "comment-1"
    assert item.conversation_id == "abc123"
    assert item.author_id == "UC_AUTHOR"
    assert item.metrics == {"like_count": 5, "reply_count": 2}
    assert item.root_source_id == "abc123"
    assert item.parent_source_id is None
    assert item.depth == 1
    assert item.relation_type == "comment"
    assert item.collection_method == "youtube_data_api"


def test_parse_youtube_comment_threads_normalizes_replies_as_children():
    payload = {
        "items": [
            {
                "id": "thread-1",
                "snippet": {
                    "videoId": "abc123",
                    "totalReplyCount": 1,
                    "topLevelComment": {
                        "id": "parent-1",
                        "snippet": {
                            "authorDisplayName": "parent user",
                            "textOriginal": "parent comment",
                        },
                    },
                },
                "replies": {
                    "comments": [
                        {
                            "id": "reply-1",
                            "snippet": {
                                "authorDisplayName": "reply user",
                                "authorChannelId": {"value": "UC_REPLY"},
                                "textOriginal": "child reply",
                                "likeCount": 2,
                                "parentId": "parent-1",
                                "publishedAt": "2026-06-02T00:00:00Z",
                            },
                        }
                    ]
                },
            }
        ]
    }

    items = parse_youtube_comment_threads(payload, keyword="bions", target_entity="bions")

    assert [item.source_type for item in items] == ["comment", "reply"]
    reply = items[1]
    assert reply.source_id == "reply-1"
    assert reply.parent_source_id == "parent-1"
    assert reply.conversation_id == "abc123"
    assert reply.root_source_id == "abc123"
    assert reply.depth == 2
    assert reply.relation_type == "reply"
    assert reply.source_url == "https://www.youtube.com/watch?v=abc123&lc=reply-1"


def test_adapter_registry_includes_youtube_and_google_play():
    platforms = [adapter.platform for adapter in remaining_platform_adapters(include_risky=True)]

    assert "youtube" in platforms
    assert "google_play" in platforms
    assert GooglePlayAdapter().enabled_by_default is True
    assert YouTubeAdapter().enabled_by_default is True
    assert YouTubeAdapter().access_mode == "rss+youtube_data_api"
