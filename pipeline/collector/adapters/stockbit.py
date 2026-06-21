from __future__ import annotations

import hashlib
import os
import re

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured
from pipeline.collector.normalizer import normalize_text
from pipeline.collector.web_extract import env_csv, fetch_public_html


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode()).hexdigest()[:16]}"


def parse_stockbit_public_page(html: str, url: str, keyword: str, target_entity: str) -> RawSocialItem:
    text = normalize_text(re.sub(r"<[^>]+>", " ", html))[:5000]
    source_id = _stable_id("stockbit", url + text[:200])
    return RawSocialItem(
        platform="stockbit",
        source_type="post",
        source_id=source_id,
        root_source_id=source_id,
        conversation_id=source_id,
        depth=0,
        keyword=keyword,
        target_entity=target_entity,
        text=text,
        source_url=url,
        raw_payload={"url": url},
        collection_method="public_http",
        access_risk="high",
    )


class StockbitAdapter:
    platform = "stockbit"
    source_type = "post"
    access_mode = "public_http"
    cost_level = "free"
    risk_level = "high"
    enabled_by_default = False

    def __init__(self, target_urls: list[str] | None = None) -> None:
        self.target_urls = target_urls if target_urls is not None else env_csv(os.getenv("STOCKBIT_TARGET_URLS"))

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.target_urls:
            raise CollectorNotConfigured("STOCKBIT_TARGET_URLS missing")
        items: list[RawSocialItem] = []
        for url in self.target_urls[:limit]:
            item = parse_stockbit_public_page(fetch_public_html(url), url, keyword, target_entity)
            if keyword.lower() in item.text.lower() or keyword.lower() in url.lower():
                items.append(item)
        return items
