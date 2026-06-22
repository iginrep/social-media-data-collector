# Architecture

Media sosial -> collector adapters -> normalized social_items -> preprocessing -> sentiment engine -> database -> api -> dashboard/export.

Backfill flow:

```txt
backfill runner (pipeline/collector/backfill.py)
  -> adapter.collect_backfill() per window
  -> checkpoint store (complete/partial per window)
  -> social_items persistence (Mongo upsert)
  -> recent overlap refresh (7d default)
  -> skip complete old windows
  -> resume partial windows on rerun
```

Core design rule: keep platform payload raw, then normalize to one canonical contract.

Collector rule: cheapest useful source first. Official/paid APIs are promotion targets after the source proves value.

Storage: `pipeline/storage/social_items.py` (canonical items), `pipeline/storage/backfill_checkpoints.py` (window status).
