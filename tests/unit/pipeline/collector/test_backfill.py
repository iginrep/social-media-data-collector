from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.collector.backfill import BackfillWindow, backfill_social_items, build_backfill_windows, retention_cutoff
from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured


pytestmark = pytest.mark.unit


class BackfillAdapter:
    platform = "backfillable"
    enabled_by_default = True

    def __init__(self) -> None:
        self.calls: list[tuple[datetime, datetime, int]] = []

    def collect_backfill(
        self,
        keyword: str,
        target_entity: str,
        since: datetime,
        until: datetime,
        limit: int = 50,
    ) -> list[RawSocialItem]:
        self.calls.append((since, until, limit))
        return [
            RawSocialItem(
                platform="backfillable",
                source_type="post",
                source_id=f"{since.date()}-{until.date()}",
                keyword=keyword,
                target_entity=target_entity,
                text="bions backfill",
                posted_at=since,
            )
        ]


class MissingBackfillAdapter:
    platform = "missing"
    enabled_by_default = True

    def collect_backfill(self, *args, **kwargs):
        raise CollectorNotConfigured("missing token")


class RecentOnlyAdapter:
    platform = "recent"
    enabled_by_default = True

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return [RawSocialItem(platform="recent", source_type="post", source_id="1", keyword=keyword, target_entity=target_entity, text="recent")]


def test_retention_cutoff_defaults_to_365_days():
    now = datetime(2026, 6, 22, tzinfo=timezone.utc)

    assert retention_cutoff(now=now).date().isoformat() == "2025-06-22"


def test_build_backfill_windows_chunks_oldest_to_newest():
    start = datetime(2025, 6, 22, tzinfo=timezone.utc)
    end = datetime(2025, 8, 5, tzinfo=timezone.utc)

    windows = build_backfill_windows(start=start, end=end, window_days=30)

    assert windows == [
        BackfillWindow(start=datetime(2025, 6, 22, tzinfo=timezone.utc), end=datetime(2025, 7, 22, tzinfo=timezone.utc)),
        BackfillWindow(start=datetime(2025, 7, 22, tzinfo=timezone.utc), end=datetime(2025, 8, 5, tzinfo=timezone.utc)),
    ]


def test_backfill_social_items_uses_backfill_api_and_persists_each_window():
    adapter = BackfillAdapter()
    persisted: list[RawSocialItem] = []
    windows = [
        BackfillWindow(datetime(2025, 6, 22, tzinfo=timezone.utc), datetime(2025, 7, 22, tzinfo=timezone.utc)),
        BackfillWindow(datetime(2025, 7, 22, tzinfo=timezone.utc), datetime(2025, 8, 21, tzinfo=timezone.utc)),
    ]

    summary = backfill_social_items(
        adapters=[adapter],
        keyword="bions",
        target_entity="bions",
        windows=windows,
        limit_per_window=25,
        persist_fn=lambda items: persisted.extend(items) or len(items),
    )

    assert len(adapter.calls) == 2
    assert adapter.calls[0] == (windows[0].start, windows[0].end, 25)
    assert summary["backfillable"]["status"] == "ok"
    assert summary["backfillable"]["collected"] == 2
    assert summary["backfillable"]["inserted"] == 2
    assert [item.source_id for item in persisted] == ["2025-06-22-2025-07-22", "2025-07-22-2025-08-21"]


def test_backfill_social_items_reports_missing_config_and_unsupported_adapters():
    summary = backfill_social_items(
        adapters=[MissingBackfillAdapter(), RecentOnlyAdapter()],
        keyword="bions",
        target_entity="bions",
        windows=[BackfillWindow(datetime(2025, 6, 22, tzinfo=timezone.utc), datetime(2025, 7, 22, tzinfo=timezone.utc))],
        persist_fn=lambda items: len(items),
    )

    assert summary["missing"]["status"] == "not_configured"
    assert summary["missing"]["error"] == "missing token"
    assert summary["recent"]["status"] == "unsupported"
    assert summary["recent"]["error"] == "adapter has no collect_backfill()"
