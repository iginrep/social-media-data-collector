from __future__ import annotations

import pytest

from pipeline.collector.adapters.instagram import InstagramAdapter
from pipeline.collector.adapters.stockbit import StockbitAdapter
from pipeline.collector.adapters.threads import ThreadsAdapter
from pipeline.collector.adapters.tiktok import TikTokAdapter, TikTokResearchAdapter
from pipeline.collector.adapters.twitter import TwitterAdapter
from pipeline.collector.exceptions import CollectorNotConfigured


pytestmark = pytest.mark.integration


def test_script_collectors_stop_without_required_runtime_config(monkeypatch):
    for name in (
        "STOCKBIT_TARGET_URLS",
        "X_BEARER_TOKEN",
        "TIKTOK_TARGET_URLS",
        "TIKTOK_RESEARCH_ACCESS_TOKEN",
        "TIKTOK_VIDEO_IDS",
        "INSTAGRAM_GRAPH_ACCESS_TOKEN",
        "INSTAGRAM_MEDIA_IDS",
        "THREADS_ACCESS_TOKEN",
        "THREADS_MEDIA_IDS",
    ):
        monkeypatch.delenv(name, raising=False)

    adapters = [StockbitAdapter(), TwitterAdapter(), TikTokAdapter(), TikTokResearchAdapter(), InstagramAdapter(), ThreadsAdapter()]

    for adapter in adapters:
        with pytest.raises(CollectorNotConfigured):
            adapter.collect("BIONS", "BIONS", limit=1)


def test_collectors_are_disabled_and_risk_tagged():
    expected = {
        "stockbit": (StockbitAdapter(["https://example.com"]), "public_http", "high"),
        "tiktok_public": (TikTokAdapter(["https://www.tiktok.com/@x/video/123"]), "public_oembed", "medium"),
        "tiktok_research": (TikTokResearchAdapter("token", ["123"]), "official_research_api", "low"),
        "instagram": (InstagramAdapter("token", ["17895695668004550"]), "official_graph_api", "low"),
        "threads": (ThreadsAdapter("token", ["123"]), "official_threads_api", "low"),
    }

    for _name, (adapter, access_mode, risk_level) in expected.items():
        assert adapter.access_mode == access_mode
        assert adapter.risk_level == risk_level
        assert adapter.enabled_by_default is False
