import pytest
from pipeline.collector.normalizer import normalize_text, detect_target_entity
from pipeline.collector.dedupe import dedupe_items
from pipeline.collector.base import RawSocialItem


pytestmark = pytest.mark.unit

def test_normalize_text_collapses_whitespace():
    assert normalize_text("  BIONS   error  ") == "BIONS error"


def test_detect_target_entity_prefers_bions():
    assert detect_target_entity("bni sekuritas", "aplikasi bions error") == "bions"


def test_dedupe_items_by_platform_source_id():
    item = RawSocialItem(platform="youtube", source_type="comment", source_id="1", keyword="bions", target_entity="bions", text="ok")
    assert len(dedupe_items([item, item])) == 1


def test_raw_social_item_has_universal_thread_fields():
    item = RawSocialItem(
        platform="youtube",
        source_type="reply",
        source_id="reply-1",
        keyword="bions",
        target_entity="bions",
        text="ok",
        root_source_id="video-1",
        parent_source_id="comment-1",
        conversation_id="video-1",
        depth=2,
        relation_type="reply",
    )

    data = item.as_dict()

    assert data["root_source_id"] == "video-1"
    assert data["parent_source_id"] == "comment-1"
    assert data["depth"] == 2
    assert data["relation_type"] == "reply"
