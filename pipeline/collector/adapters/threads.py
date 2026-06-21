from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime
from typing import Any

import httpx

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.normalizer import normalize_text
from pipeline.collector.web_extract import env_csv, fetch_public_html


CODE_RE = re.compile(r"threads\.net/@[^/]+/post/([^/?#]+)/?")
JSON_LD_RE = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S)


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode()).hexdigest()[:16]}"


def _code(url: str) -> str:
    match = CODE_RE.search(url)
    return match.group(1) if match else _stable_id("threads", url)


def _json_ld(html: str) -> dict[str, Any]:
    for match in JSON_LD_RE.finditer(html):
        try:
            data = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return {}


def _parse_meta_time(value: str | None):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_threads_public_post(html: str, url: str, keyword: str, target_entity: str) -> RawSocialItem:
    data = _json_ld(html)
    source_id = str(data.get("identifier") or _code(url))
    author_raw = data.get("author")
    author = author_raw if isinstance(author_raw, dict) else {}
    return RawSocialItem(
        platform="threads",
        source_type="post",
        source_id=source_id,
        root_source_id=source_id,
        conversation_id=source_id,
        depth=0,
        keyword=keyword,
        target_entity=target_entity,
        author_username=author.get("alternateName") or author.get("name"),
        author_display_name=author.get("name"),
        text=normalize_text(str(data.get("articleBody") or data.get("description") or "")),
        source_url=url,
        raw_payload={"url": url, "json_ld": data},
        collection_method="public_http",
        access_risk="high",
    )


def parse_threads_conversation(payload: dict[str, Any], media_id: str, keyword: str, target_entity: str) -> list[RawSocialItem]:
    rows: list[RawSocialItem] = []
    for raw in payload.get("data", []):
        source_id = str(raw.get("id"))
        is_reply = bool(raw.get("is_reply"))
        root_id = str(raw.get("root_post") or media_id)
        parent_id = str(raw.get("replied_to")) if raw.get("replied_to") else None
        rows.append(
            RawSocialItem(
                platform="threads",
                source_type="reply" if is_reply else "post",
                source_id=source_id,
                root_source_id=root_id,
                parent_source_id=parent_id,
                conversation_id=root_id,
                depth=1 if is_reply else 0,
                relation_type="reply" if is_reply else None,
                keyword=keyword,
                target_entity=target_entity,
                author_username=raw.get("username"),
                text=normalize_text(str(raw.get("text", ""))),
                posted_at=_parse_meta_time(raw.get("timestamp")),
                source_url=raw.get("permalink"),
                raw_payload=raw,
                collection_method="official_threads_api",
                access_risk="low",
            )
        )
    return rows


class ThreadsAdapter:
    platform = "threads"
    source_type = "reply"
    access_mode = "official_threads_api"
    cost_level = "free_or_limited"
    risk_level = "low"
    enabled_by_default = False

    def __init__(self, access_token: str | None = None, media_ids: list[str] | None = None, client: httpx.Client | None = None) -> None:
        self.access_token = access_token or os.getenv("THREADS_ACCESS_TOKEN")
        self.media_ids = media_ids if media_ids is not None else env_csv(os.getenv("THREADS_MEDIA_IDS"))
        self.client = client or httpx.Client(timeout=20.0)

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.access_token:
            raise CollectorNotConfigured("THREADS_ACCESS_TOKEN missing")
        if not self.media_ids:
            raise CollectorNotConfigured("THREADS_MEDIA_IDS missing")
        fields = "id,text,topic_tag,timestamp,media_product_type,media_type,media_url,shortcode,thumbnail_url,children,has_replies,root_post,replied_to,is_reply,permalink,username"
        rows: list[RawSocialItem] = []
        for media_id in self.media_ids:
            response = self.client.get(
                f"https://graph.threads.net/v1.0/{media_id}/conversation",
                params={"fields": fields, "reverse": "false", "access_token": self.access_token},
            )
            if response.status_code in {401, 403, 429}:
                raise CollectorStopped(f"threads collector stopped: status {response.status_code}")
            response.raise_for_status()
            rows.extend(parse_threads_conversation(response.json(), media_id, keyword, target_entity))
            if len(rows) >= limit:
                break
        return rows[:limit]
