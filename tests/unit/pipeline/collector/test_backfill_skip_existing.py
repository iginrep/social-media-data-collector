from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.collector.backfill import BackfillWindow, backfill_social_items
from pipeline.collector.base import RawSocialItem


pytestmark = pytest.mark.unit


class CountingAdapter:
    platform = "youtube"

    def __init__(self) -> None:
        self.calls = 0

    def collect_backfill(self, keyword: str, target_entity: str, since: datetime, until: datetime, limit: int = 50) -> list[RawSocialItem]:
        self.calls += 1
        return []


def test_backfill_skips_existing_windows_before_collecting() -> None:
    adapter = CountingAdapter()
    windows = [
        BackfillWindow(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc)),
        BackfillWindow(datetime(2026, 2, 1, tzinfo=timezone.utc), datetime(2026, 3, 1, tzinfo=timezone.utc)),
    ]

    summary = backfill_social_items(
        adapters=[adapter],
        windows=windows,
        write=False,
        window_has_items_fn=lambda platform, start, end: platform == "youtube" and start.month == 1,
    )

    assert adapter.calls == 1
    assert summary["youtube"]["windows"] == 1
    assert summary["youtube"]["skipped_windows"] == 1


def test_backfill_can_refetch_existing_windows_when_requested() -> None:
    adapter = CountingAdapter()
    windows = [BackfillWindow(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 2, 1, tzinfo=timezone.utc))]

    summary = backfill_social_items(
        adapters=[adapter],
        windows=windows,
        write=False,
        skip_existing_windows=False,
        window_has_items_fn=lambda platform, start, end: True,
    )

    assert adapter.calls == 1
    assert summary["youtube"]["windows"] == 1
    assert summary["youtube"]["skipped_windows"] == 0
