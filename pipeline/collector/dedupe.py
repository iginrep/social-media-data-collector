from __future__ import annotations
from pipeline.collector.base import RawSocialItem


def dedupe_items(items: list[RawSocialItem]) -> list[RawSocialItem]:
    seen: set[tuple[str, str]] = set()
    output: list[RawSocialItem] = []
    for item in items:
        key = (item.platform, item.source_id or item.content_hash)
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output
