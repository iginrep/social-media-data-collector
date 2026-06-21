from __future__ import annotations

import pytest

from pipeline.collector.adapters.instagram import parse_instagram_public_post
from pipeline.collector.adapters.stockbit import parse_stockbit_public_page
from pipeline.collector.adapters.threads import parse_threads_public_post
from pipeline.collector.adapters.tiktok import parse_tiktok_oembed
from pipeline.collector.adapters.twitter import TwitterAdapter


pytestmark = pytest.mark.unit


def test_parse_tiktok_oembed_normalizes_video_root():
    item = parse_tiktok_oembed(
        {"title": "BIONS login error", "author_name": "bniuser", "author_url": "https://www.tiktok.com/@bniuser"},
        url="https://www.tiktok.com/@bniuser/video/1234567890",
        keyword="bions",
        target_entity="bions",
    )

    assert item.platform == "tiktok"
    assert item.source_type == "video"
    assert item.source_id == "1234567890"
    assert item.root_source_id == "1234567890"
    assert item.conversation_id == "1234567890"
    assert item.depth == 0
    assert item.author_username == "bniuser"
    assert "login error" in item.text


def test_parse_instagram_public_post_extracts_caption_from_embedded_json():
    html = '<script type="application/ld+json">{"@type":"SocialMediaPosting","identifier":"ABC123","articleBody":"BIONS susah login","author":{"alternateName":"bnitest"},"interactionStatistic":[{"interactionType":"LikeAction","userInteractionCount":7}]}</script>'

    item = parse_instagram_public_post(html, url="https://www.instagram.com/p/ABC123/", keyword="bions", target_entity="bions")

    assert item.platform == "instagram"
    assert item.source_type == "post"
    assert item.source_id == "ABC123"
    assert item.root_source_id == "ABC123"
    assert item.author_username == "bnitest"
    assert item.metrics["likes"] == 7
    assert item.text == "BIONS susah login"


def test_parse_threads_public_post_extracts_thread_from_embedded_json():
    html = '<script type="application/ld+json">{"@type":"SocialMediaPosting","identifier":"THREAD1","articleBody":"BIONS maintenance lagi","author":{"alternateName":"bniuser"}}</script>'

    item = parse_threads_public_post(html, url="https://www.threads.net/@bniuser/post/THREAD1", keyword="bions", target_entity="bions")

    assert item.platform == "threads"
    assert item.source_type == "post"
    assert item.source_id == "THREAD1"
    assert item.root_source_id == "THREAD1"
    assert item.conversation_id == "THREAD1"
    assert item.author_username == "bniuser"


def test_parse_stockbit_public_page_extracts_keyword_snapshot():
    html = "<html><body><article data-id='post-1'>BBNI BIONS error login hari ini</article></body></html>"

    item = parse_stockbit_public_page(html, url="https://stockbit.com/post/1", keyword="bions", target_entity="bions")

    assert item.platform == "stockbit"
    assert item.source_type == "post"
    assert item.source_id.startswith("stockbit_")
    assert item.root_source_id == item.source_id
    assert "BIONS error" in item.text


def test_x_adapter_maps_relation_type_for_replies():
    item = TwitterAdapter()._to_item(
        {
            "id": "tweet-2",
            "text": "reply about bions",
            "conversation_id": "tweet-1",
            "referenced_tweets": [{"type": "replied_to", "id": "tweet-1"}],
        },
        keyword="bions",
        target_entity="bions",
    )

    assert item.source_type == "tweet"
    assert item.root_source_id == "tweet-1"
    assert item.parent_source_id == "tweet-1"
    assert item.relation_type == "reply"
    assert item.depth == 1
