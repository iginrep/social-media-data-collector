from __future__ import annotations

from datetime import datetime, timezone

import pytest

from pipeline.collector.backfill import BackfillWindow, backfill_social_items
from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorStopped


pytestmark = pytest.mark.unit


class FakeCheckpointStore:
    def __init__(self, states: dict[tuple[str, datetime, datetime], str] | None = None) -> None:
        self.states = states or {}
        self.completed: list[tuple[str, datetime, datetime, int, int]] = []
        self.partial: list[tuple[str, datetime, datetime, int, int, str]] = []

    def get_status(self, platform: str, start: datetime, end: datetime) -> str | None:
        return self.states.get((platform, start, end))

    def mark_complete(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int) -> None:
        self.completed.append((platform, start, end, collected, inserted))

    def mark_partial(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int, error: str) -> None:
        self.partial.append((platform, start, end, collected, inserted, error))


class CountingAdapter:
    platform = "youtube"

    def __init__(self, stop: bool = False) -> None:
        self.calls = 0
        self.stop = stop

    def collect_backfill(self, keyword: str, target_entity: str, since: datetime, until: datetime, limit: int = 50) -> list[RawSocialItem]:
        self.calls += 1
        if self.stop:
            raise CollectorStopped("quota")
        return []


def test_complete_old_checkpoint_skips_provider_call() -> None:
    window = BackfillWindow(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 31, tzinfo=timezone.utc))
    adapter = CountingAdapter()
    checkpoints = FakeCheckpointStore({("youtube", window.start, window.end): "complete"})

    summary = backfill_social_items(
        adapters=[adapter],
        windows=[window],
        now=datetime(2026, 6, 22, tzinfo=timezone.utc),
        checkpoint_store=checkpoints,
        recent_overlap_days=7,
        write=True,
        persist_fn=lambda items: len(items),
    )

    assert adapter.calls == 0
    assert summary["youtube"]["skipped_windows"] == 1


def test_complete_recent_checkpoint_refreshes_overlap_window() -> None:
    window = BackfillWindow(datetime(2026, 6, 18, tzinfo=timezone.utc), datetime(2026, 6, 22, tzinfo=timezone.utc))
    adapter = CountingAdapter()
    checkpoints = FakeCheckpointStore({("youtube", window.start, window.end): "complete"})

    summary = backfill_social_items(
        adapters=[adapter],
        windows=[window],
        now=datetime(2026, 6, 22, tzinfo=timezone.utc),
        checkpoint_store=checkpoints,
        recent_overlap_days=7,
        write=True,
        persist_fn=lambda items: len(items),
    )

    assert adapter.calls == 1
    assert summary["youtube"]["windows"] == 1
    assert checkpoints.completed == [("youtube", window.start, window.end, 0, 0)]


def test_partial_checkpoint_refetches_and_stopped_run_marks_partial() -> None:
    window = BackfillWindow(datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 31, tzinfo=timezone.utc))
    adapter = CountingAdapter(stop=True)
    checkpoints = FakeCheckpointStore({("youtube", window.start, window.end): "partial"})

    summary = backfill_social_items(
        adapters=[adapter],
        windows=[window],
        now=datetime(2026, 6, 22, tzinfo=timezone.utc),
        checkpoint_store=checkpoints,
        write=True,
        persist_fn=lambda items: len(items),
    )

    assert adapter.calls == 1
    assert summary["youtube"]["status"] == "stopped"
    assert checkpoints.partial == [("youtube", window.start, window.end, 0, 0, "quota")]
