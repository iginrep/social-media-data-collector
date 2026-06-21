from __future__ import annotations
from pipeline.sentiment.preprocess import clean_text
from pipeline.sentiment.rules import classify_rule_based


def classify(text: str) -> dict:
    cleaned = clean_text(text)
    result = classify_rule_based(cleaned)
    result["cleaned_text"] = cleaned
    result["method"] = "rule_based"
    result["model_version"] = "rules-v0.1"
    return result
