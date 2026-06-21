from __future__ import annotations
from pipeline.collector.run import collect_sample
from pipeline.sentiment.classifier import classify


if __name__ == "__main__":
    for item in collect_sample():
        print(item.text, "=>", classify(item.text))
