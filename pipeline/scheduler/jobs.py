from __future__ import annotations
from pipeline.collector.run import collect_sample
from pipeline.sentiment.classifier import classify


def collect_and_analyze() -> list[dict]:
    results = []
    for item in collect_sample():
        results.append({"item": item.as_dict(), "sentiment": classify(item.text)})
    return results
