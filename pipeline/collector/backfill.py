from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Protocol

from pipeline.collector.base import CollectorAdapter, RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.run import remaining_platform_adapters
from pipeline.storage.backfill_checkpoints import MongoBackfillCheckpointStore
from pipeline.storage.social_items import persist_social_items, social_items_exist


@dataclass(frozen=True, slots=True)
class BackfillWindow:
    start: datetime
    end: datetime


class BackfillAdapter(Protocol):
    platform: str

    def collect_backfill(
        self,
        keyword: str,
        target_entity: str,
        since: datetime,
        until: datetime,
        limit: int = 50,
    ) -> list[RawSocialItem]: ...


class BackfillCheckpointStore(Protocol):
    def get_status(self, platform: str, start: datetime, end: datetime) -> str | None: ...

    def mark_complete(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int) -> None: ...

    def mark_partial(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int, error: str) -> None: ...


class NullBackfillCheckpointStore:
    def get_status(self, platform: str, start: datetime, end: datetime) -> str | None:
        return None

    def mark_complete(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int) -> None:
        return None

    def mark_partial(self, platform: str, start: datetime, end: datetime, collected: int, inserted: int, error: str) -> None:
        return None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def retention_cutoff(days: int = 365, now: datetime | None = None) -> datetime:
    anchor = _utc(now or datetime.now(timezone.utc))
    return anchor - timedelta(days=days)


def build_backfill_windows(start: datetime, end: datetime, window_days: int = 30) -> list[BackfillWindow]:
    if window_days <= 0:
        raise ValueError("window_days must be > 0")
    cursor = _utc(start)
    finish = _utc(end)
    if cursor >= finish:
        return []

    windows: list[BackfillWindow] = []
    step = timedelta(days=window_days)
    while cursor < finish:
        window_end = min(cursor + step, finish)
        windows.append(BackfillWindow(start=cursor, end=window_end))
        cursor = window_end
    return windows


def _platform(adapter: object) -> str:
    return str(getattr(adapter, "platform", adapter.__class__.__name__))


def backfill_social_items(
    adapters: Iterable[CollectorAdapter] | None = None,
    keyword: str = "bions",
    target_entity: str = "bions",
    windows: list[BackfillWindow] | None = None,
    retention_days: int = 365,
    window_days: int = 30,
    limit_per_window: int = 100,
    include_risky: bool = True,
    write: bool = True,
    persist_fn: Callable[[list[RawSocialItem]], int] | None = None,
    skip_existing_windows: bool = True,
    window_has_items_fn: Callable[[str, datetime, datetime], bool] | None = None,
    checkpoint_store: BackfillCheckpointStore | None = None,
    recent_overlap_days: int = 7,
    now: datetime | None = None,
) -> dict[str, dict[str, object]]:
    active_adapters = list(adapters) if adapters is not None else remaining_platform_adapters(include_risky=include_risky)
    active_windows = windows or build_backfill_windows(
        start=retention_cutoff(days=retention_days, now=now),
        end=_utc(now or datetime.now(timezone.utc)),
        window_days=window_days,
    )
    sink = persist_fn or persist_social_items
    has_items = window_has_items_fn or social_items_exist
    checkpoints = checkpoint_store or (MongoBackfillCheckpointStore() if adapters is None else NullBackfillCheckpointStore())
    anchor = _utc(now or datetime.now(timezone.utc))
    refresh_cutoff = anchor - timedelta(days=recent_overlap_days)
    summary: dict[str, dict[str, object]] = {}

    for adapter in active_adapters:
        platform = _platform(adapter)
        collect_backfill = getattr(adapter, "collect_backfill", None)
        if collect_backfill is None:
            summary[platform] = {"status": "unsupported", "collected": 0, "inserted": 0, "error": "adapter has no collect_backfill()"}
            continue

        collected_count = 0
        inserted_count = 0
        windows_done = 0
        skipped_windows = 0
        current_window: BackfillWindow | None = None
        try:
            for window in active_windows:
                current_window = window
                status = checkpoints.get_status(platform, window.start, window.end)
                if skip_existing_windows and status == "complete" and window.end <= refresh_cutoff:
                    skipped_windows += 1
                    continue
                if checkpoint_store is None and skip_existing_windows and has_items(platform, window.start, window.end) and window.end <= refresh_cutoff:
                    if write:
                        checkpoints.mark_complete(platform, window.start, window.end, 0, 0)
                    skipped_windows += 1
                    continue
                items = collect_backfill(keyword, target_entity, window.start, window.end, limit=limit_per_window)
                collected_count += len(items)
                inserted_this_window = 0
                if write:
                    inserted_this_window = sink(items)
                    inserted_count += inserted_this_window
                if write:
                    checkpoints.mark_complete(platform, window.start, window.end, len(items), inserted_this_window)
                windows_done += 1
        except CollectorNotConfigured as exc:
            summary[platform] = {"status": "not_configured", "collected": collected_count, "inserted": inserted_count, "windows": windows_done, "skipped_windows": skipped_windows, "error": str(exc)}
            continue
        except CollectorStopped as exc:
            if write and current_window is not None:
                checkpoints.mark_partial(platform, current_window.start, current_window.end, collected_count, inserted_count, str(exc))
            summary[platform] = {"status": "stopped", "collected": collected_count, "inserted": inserted_count, "windows": windows_done, "skipped_windows": skipped_windows, "error": str(exc)}
            continue

        summary[platform] = {"status": "ok", "collected": collected_count, "inserted": inserted_count, "windows": windows_done, "skipped_windows": skipped_windows}

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill social collector data into MongoDB")
    parser.add_argument("--retention-days", type=int, default=365)
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--limit-per-window", type=int, default=100)
    parser.add_argument("--keyword", default="bions")
    parser.add_argument("--target-entity", default="bions")
    parser.add_argument("--recent-overlap-days", type=int, default=7)
    parser.add_argument("--refetch-existing-windows", action="store_true", help="call APIs even when MongoDB already has rows for the platform/window")
    parser.add_argument("--dry-run", action="store_true", help="collect/report without writing to MongoDB")
    args = parser.parse_args()

    summary = backfill_social_items(
        keyword=args.keyword,
        target_entity=args.target_entity,
        retention_days=args.retention_days,
        window_days=args.window_days,
        limit_per_window=args.limit_per_window,
        skip_existing_windows=not args.refetch_existing_windows,
        recent_overlap_days=args.recent_overlap_days,
        write=not args.dry_run,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
