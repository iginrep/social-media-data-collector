from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.normalizer import normalize_text
from pipeline.collector.web_extract import env_csv, fetch_public_html
import httpx
from datetime import datetime


SHORTCODE_RE = re.compile(r"instagram\.com/(?:p|reel)/([^/?#]+)/?")
JSON_LD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode()).hexdigest()[:16]}"


def _shortcode(url: str) -> str:
    match = SHORTCODE_RE.search(url)
    return match.group(1) if match else _stable_id("instagram", url)


def _json_ld(html: str) -> dict[str, Any]:
    for match in JSON_LD_RE.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _metric(stats: Any, name: str) -> int | None:
    if not isinstance(stats, list):
        return None
    for stat in stats:
        if name.lower() in str(stat.get("interactionType", "")).lower():
            try:
                return int(stat.get("userInteractionCount"))
            except (TypeError, ValueError):
                return None
    return None


def parse_instagram_public_post(html: str, url: str, keyword: str, target_entity: str) -> RawSocialItem:
    data = _json_ld(html)
    source_id = str(data.get("identifier") or _shortcode(url))
    author = data.get("author") if isinstance(data.get("author"), dict) else {}
    text = normalize_text(str(data.get("articleBody") or data.get("caption") or data.get("description") or ""))
    likes = _metric(data.get("interactionStatistic"), "Like")
    metrics = {"likes": likes} if likes is not None else {}
    return RawSocialItem(
        platform="instagram",
        source_type="post",
        source_id=source_id,
        root_source_id=source_id,
        conversation_id=source_id,
        depth=0,
        keyword=keyword,
        target_entity=target_entity,
        author_username=author.get("alternateName") or author.get("name"),
        author_display_name=author.get("name"),
        text=text,
        source_url=url,
        metrics=metrics,
        raw_payload={"url": url, "json_ld": data},
        collection_method="public_http",
        access_risk="high",
    )


def _parse_meta_time(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _ig_comment_item(raw: dict[str, Any], media_id: str, keyword: str, target_entity: str, parent_id: str | None = None) -> RawSocialItem:
    comment_id = str(raw.get("id"))
    return RawSocialItem(
        platform="instagram", source_type="comment", source_id=comment_id,
        root_source_id=media_id, parent_source_id=parent_id, conversation_id=media_id,
        depth=2 if parent_id else 1, relation_type="reply" if parent_id else "comment",
        keyword=keyword, target_entity=target_entity, text=normalize_text(str(raw.get("text", ""))),
        author_username=raw.get("username"), posted_at=_parse_meta_time(raw.get("timestamp")),
        source_url=f"https://www.instagram.com/p/{media_id}/comments/{comment_id}",
        raw_payload=raw, collection_method="official_graph_api", access_risk="low",
    )


def parse_instagram_comments(payload: dict[str, Any], media_id: str, keyword: str, target_entity: str) -> list[RawSocialItem]:
    rows: list[RawSocialItem] = []
    for raw in payload.get("data", []):
        parent = _ig_comment_item(raw, media_id, keyword, target_entity)
        rows.append(parent)
        for reply in raw.get("replies", {}).get("data", []):
            rows.append(_ig_comment_item(reply, media_id, keyword, target_entity, parent_id=parent.source_id))
    return rows


class InstagramAdapter:
    platform = "instagram"
    source_type = "comment"
    access_mode = "official_graph_api"
    cost_level = "free_or_limited"
    risk_level = "low"
    enabled_by_default = False

    def __init__(self, access_token: str | None = None, media_ids: list[str] | None = None, client: httpx.Client | None = None) -> None:
        self.access_token = access_token or os.getenv("INSTAGRAM_GRAPH_ACCESS_TOKEN")
        self.media_ids = media_ids if media_ids is not None else env_csv(os.getenv("INSTAGRAM_MEDIA_IDS"))
        self.client = client or httpx.Client(timeout=20.0)

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.access_token:
            raise CollectorNotConfigured("INSTAGRAM_GRAPH_ACCESS_TOKEN missing")
        if not self.media_ids:
            raise CollectorNotConfigured("INSTAGRAM_MEDIA_IDS missing")
        rows: list[RawSocialItem] = []
        fields = "id,text,timestamp,username,replies{id,text,timestamp,username}"
        for media_id in self.media_ids:
            response = self.client.get(
                f"https://graph.facebook.com/v25.0/{media_id}/comments",
                params={"fields": fields, "access_token": self.access_token},
            )
            if response.status_code in {401, 403, 429}:
                raise CollectorStopped(f"instagram collector stopped: status {response.status_code}")
            response.raise_for_status()
            rows.extend(parse_instagram_comments(response.json(), media_id, keyword, target_entity))
            if len(rows) >= limit:
                break
        return rows[:limit]
