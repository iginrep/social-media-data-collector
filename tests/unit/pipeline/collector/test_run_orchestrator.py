from __future__ import annotations

import pytest

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured
from pipeline.collector.run import collect_sample


pytestmark = pytest.mark.unit


class WorkingAdapter:
    platform = "working"
    enabled_by_default = True

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return [RawSocialItem(platform="working", source_type="post", source_id="1", keyword=keyword, target_entity=target_entity, text="bions works")]


class MissingConfigAdapter:
    platform = "missing"
    enabled_by_default = False

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        raise CollectorNotConfigured("missing token")


def test_collect_sample_returns_items_and_reports_configured_blockers():
    items, report = collect_sample(adapters=[WorkingAdapter(), MissingConfigAdapter()], include_risky=True, return_report=True)

    assert [item.platform for item in items] == ["working"]
    assert report["working"]["status"] == "ok"
    assert report["working"]["count"] == 1
    assert report["missing"]["status"] == "not_configured"
    assert report["missing"]["error"] == "missing token"
