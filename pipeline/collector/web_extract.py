from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from typing import Iterable

import httpx

from pipeline.collector.exceptions import CollectorStopped


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self._chunks.append(text)

    def text(self) -> str:
        return " ".join(self._chunks)


def fetch_public_html(url: str, client: httpx.Client | None = None) -> str:
    http = client or httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 BNI-BIONS-sentiment-monitor/0.1"})
    response = http.get(url)
    if response.status_code in {401, 403, 429}:
        raise CollectorStopped(f"public fetch stopped for {url}: status {response.status_code}")
    response.raise_for_status()
    body = response.text.lower()
    if "captcha" in body or "login" in body and "password" in body:
        raise CollectorStopped(f"public fetch stopped for {url}: captcha/login wall")
    return response.text


def fetch_public_text(url: str, client: httpx.Client | None = None) -> str:
    parser = TextExtractor()
    parser.feed(fetch_public_html(url, client=client))
    return parser.text()


def env_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
