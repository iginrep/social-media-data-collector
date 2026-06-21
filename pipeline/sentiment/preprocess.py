from __future__ import annotations
import re

SLANG = {"gk": "tidak", "ga": "tidak", "nggak": "tidak", "lemot": "lambat"}


def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-z0-9@#_\s]", " ", text)
    words = [SLANG.get(word, word) for word in text.split()]
    return " ".join(words)
