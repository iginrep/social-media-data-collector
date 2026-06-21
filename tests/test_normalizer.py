from pipeline.collector.normalizer import normalize_text, detect_target_entity
from pipeline.collector.dedupe import dedupe_items
from pipeline.collector.base import RawSocialItem


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  BIONS   error  ") == "BIONS error"


def test_detect_target_entity_prefers_bions():
    assert detect_target_entity("bni sekuritas", "aplikasi bions error") == "bions"


def test_dedupe_items_by_platform_source_id():
    item = RawSocialItem(platform="youtube", source_type="comment", source_id="1", keyword="bions", target_entity="bions", text="ok")
    assert len(dedupe_items([item, item])) == 1
