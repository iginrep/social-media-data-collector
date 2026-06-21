from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def detect_target_entity(keyword: str, text: str) -> str:
    value = f"{keyword} {text}".lower()
    if "bions" in value:
        return "bions"
    return "bni_sekuritas"
