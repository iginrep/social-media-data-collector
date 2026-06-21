from __future__ import annotations

import hashlib
import os
import re
from typing import Any

import httpx

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.normalizer import normalize_text
from pipeline.collector.web_extract import env_csv


VIDEO_ID_RE = re.compile(r"/video/(\d+)")


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode()).hexdigest()[:16]}"


def _username_from_author_url(url: str | None) -> str | None:
    if not url:
        return None
    match = re.search(r"/@([^/?#]+)", url)
    return match.group(1) if match else None


def _video_id(url: str) -> str:
    match = VIDEO_ID_RE.search(url)
    return match.group(1) if match else _stable_id("tiktok", url)


def parse_tiktok_oembed(payload: dict[str, Any], url: str, keyword: str, target_entity: str) -> RawSocialItem:
    source_id = _video_id(url)
    text = normalize_text(str(payload.get("title") or ""))
    return RawSocialItem(
        platform="tiktok",
        source_type="video",
        source_id=source_id,
        root_source_id=source_id,
        conversation_id=source_id,
        depth=0,
        relation_type=None,
        keyword=keyword,
        target_entity=target_entity,
        author_username=_username_from_author_url(payload.get("author_url")) or payload.get("author_name"),
        author_display_name=payload.get("author_name"),
        text=text,
        source_url=url,
        raw_payload=payload | {"url": url},
        collection_method="public_oembed",
        access_risk="medium",
    )


class TikTokAdapter:
    platform = "tiktok"
    source_type = "video"
    access_mode = "public_oembed"
    cost_level = "free"
    risk_level = "medium"
    enabled_by_default = False

    def __init__(self, target_urls: list[str] | None = None, client: httpx.Client | None = None) -> None:
        self.target_urls = target_urls if target_urls is not None else env_csv(os.getenv("TIKTOK_TARGET_URLS"))
        self.client = client or httpx.Client(timeout=20.0, follow_redirects=True)

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.target_urls:
            raise CollectorNotConfigured("TIKTOK_TARGET_URLS missing")
        items: list[RawSocialItem] = []
        for url in self.target_urls[:limit]:
            response = self.client.get("https://www.tiktok.com/oembed", params={"url": url})
            if response.status_code in {401, 403, 429}:
                raise CollectorStopped(f"tiktok collector stopped: status {response.status_code}")
            response.raise_for_status()
            item = parse_tiktok_oembed(response.json(), url=url, keyword=keyword, target_entity=target_entity)
            if keyword.lower() in item.text.lower() or keyword.lower() in url.lower():
                items.append(item)
        return items


def parse_tiktok_research_comments(payload: dict[str, Any], keyword: str, target_entity: str) -> list[RawSocialItem]:
    rows: list[RawSocialItem] = []
    for raw in payload.get("data", {}).get("comments", []):
        comment_id = str(raw.get("id"))
        video_id = str(raw.get("video_id"))
        parent_id = str(raw.get("parent_comment_id")) if raw.get("parent_comment_id") else None
        posted_at = None
        if raw.get("create_time"):
            from datetime import datetime, timezone
            posted_at = datetime.fromtimestamp(int(raw["create_time"]), tz=timezone.utc)
        rows.append(RawSocialItem(
            platform="tiktok", source_type="comment", source_id=comment_id,
            root_source_id=video_id, parent_source_id=parent_id, conversation_id=video_id,
            depth=2 if parent_id else 1, relation_type="reply" if parent_id else "comment",
            keyword=keyword, target_entity=target_entity, text=normalize_text(str(raw.get("text", ""))),
            posted_at=posted_at, metrics={"like_count": raw.get("like_count", 0), "reply_count": raw.get("reply_count", 0)},
            source_url=f"https://www.tiktok.com/@_/video/{video_id}?comment={comment_id}",
            raw_payload=raw, collection_method="official_research_api", access_risk="low",
        ))
    return rows


class TikTokResearchAdapter:
    platform = "tiktok"
    source_type = "comment"
    access_mode = "official_research_api"
    cost_level = "free_or_limited"
    risk_level = "low"
    enabled_by_default = False

    def __init__(self, bearer_token: str | None = None, video_ids: list[str] | None = None, client: httpx.Client | None = None) -> None:
        self.bearer_token = bearer_token or os.getenv("TIKTOK_RESEARCH_ACCESS_TOKEN")
        self.video_ids = video_ids if video_ids is not None else env_csv(os.getenv("TIKTOK_VIDEO_IDS"))
        self.client = client or httpx.Client(timeout=20.0)

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.bearer_token:
            raise CollectorNotConfigured("TIKTOK_RESEARCH_ACCESS_TOKEN missing")
        if not self.video_ids:
            raise CollectorNotConfigured("TIKTOK_VIDEO_IDS missing")
        rows: list[RawSocialItem] = []
        for video_id in self.video_ids:
            response = self.client.post(
                "https://open.tiktokapis.com/v2/research/video/comment/list/",
                params={"fields": "id,video_id,text,parent_comment_id,like_count,reply_count,create_time"},
                headers={"Authorization": f"Bearer {self.bearer_token}", "Content-Type": "application/json"},
                json={"video_id": int(video_id), "max_count": min(limit, 100), "cursor": 0},
            )
            if response.status_code in {401, 403, 429}:
                raise CollectorStopped(f"tiktok research collector stopped: status {response.status_code}")
            response.raise_for_status()
            rows.extend(parse_tiktok_research_comments(response.json(), keyword, target_entity))
            if len(rows) >= limit:
                break
        return rows[:limit]
