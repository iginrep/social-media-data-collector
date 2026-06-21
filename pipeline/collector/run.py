from __future__ import annotations
from pipeline.collector.adapters.youtube import YouTubeAdapter
from pipeline.collector.adapters.twitter import TwitterAdapter
from pipeline.collector.dedupe import dedupe_items


def collect_sample():
    adapters = [YouTubeAdapter(), TwitterAdapter()]
    items = []
    for adapter in adapters:
        items.extend(adapter.collect(keyword="bions", target_entity="bions", limit=10))
    return dedupe_items(items)


if __name__ == "__main__":
    for item in collect_sample():
        print(item.as_json())
