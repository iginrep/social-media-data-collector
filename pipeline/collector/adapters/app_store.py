from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from pipeline.collector.base import RawSocialItem
from pipeline.collector.normalizer import normalize_text


APP_STORE_REVIEWS_BASE = "https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"


def _label(data: dict[str, Any], key: str, default: str | None = None) -> str | None:
    value = data.get(key)
    if isinstance(value, dict):
        raw = value.get("label")
        return str(raw) if raw is not None else default
    if value is None:
        return default
    return str(value)


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_app_store_reviews(payload: dict[str, Any], keyword: str, target_entity: str) -> list[RawSocialItem]:
    entries = payload.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]

    items: list[RawSocialItem] = []
    for entry in entries:
        if not isinstance(entry, dict) or "content" not in entry:
            continue

        source_id = _label(entry, "id") or _label(entry, "updated") or ""
        title = _label(entry, "title", "") or ""
        content = _label(entry, "content", "") or ""
        text = normalize_text(f"{title}. {content}".strip())
        if not text:
            continue

        author = entry.get("author", {}) if isinstance(entry.get("author"), dict) else {}
        author_display_name = _label(author, "name")
        rating_raw = _label(entry, "im:rating")
        version = _label(entry, "im:version")
        updated = _label(entry, "updated")
        link = entry.get("link", {})
        source_url = None
        if isinstance(link, dict):
            attrs = link.get("attributes", {})
            if isinstance(attrs, dict):
                source_url = attrs.get("href")

        metrics: dict[str, Any] = {}
        if rating_raw is not None:
            try:
                metrics["rating"] = int(rating_raw)
            except ValueError:
                metrics["rating"] = rating_raw

        raw_payload = dict(entry)
        if version is not None:
            raw_payload["app_version"] = version

        items.append(
            RawSocialItem(
                platform="app_store",
                source_type="app_review",
                source_id=source_id,
                root_source_id=source_id,
                conversation_id=source_id,
                depth=0,
                relation_type=None,
                keyword=keyword,
                target_entity=target_entity,
                text=text,
                author_display_name=author_display_name,
                language="id",
                source_url=source_url,
                posted_at=_parse_datetime(updated),
                metrics=metrics,
                raw_payload=raw_payload,
                collection_method="rss",
                access_risk="low",
            )
        )
    return items


class AppStoreAdapter:
    platform = "app_store"
    access_mode = "rss"
    cost_level = "free"
    risk_level = "low"
    enabled_by_default = True

    def __init__(self, app_id: str = "6736508566", country: str = "id", timeout: float = 20.0) -> None:
        self.app_id = app_id
        self.country = country
        self.timeout = timeout

    def review_feed_url(self, page: int = 1) -> str:
        return APP_STORE_REVIEWS_BASE.format(country=self.country, page=page, app_id=self.app_id)

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        limit = max(0, min(limit, 500))
        if limit == 0:
            return []

        items: list[RawSocialItem] = []
        page = 1
        while len(items) < limit and page <= 10:
            response = httpx.get(self.review_feed_url(page), timeout=self.timeout)
            response.raise_for_status()
            page_items = parse_app_store_reviews(response.json(), keyword=keyword, target_entity=target_entity)
            if not page_items:
                break
            items.extend(page_items)
            page += 1
        return items[:limit]
