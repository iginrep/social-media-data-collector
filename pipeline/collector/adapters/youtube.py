from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Iterable

import httpx

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.normalizer import normalize_text


DEFAULT_CHANNEL_URLS = ["https://www.youtube.com/@BNI1946", "https://www.youtube.com/@bnisekuritas46"]
YOUTUBE_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
YOUTUBE_COMMENT_THREADS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def _load_env_value(name: str, env_path: str = ".env") -> str | None:
    value = os.getenv(name)
    if value:
        return value
    path = Path(env_path)
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, raw_value = stripped.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'") or None
    return None


def _find_text(entry: ET.Element, path: str) -> str | None:
    value = entry.findtext(path, namespaces=ATOM_NS)
    return value.strip() if value else None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_youtube_feed(xml_text: str, keyword: str, target_entity: str) -> list[RawSocialItem]:
    root = ET.fromstring(xml_text)
    items: list[RawSocialItem] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        video_id = _find_text(entry, "yt:videoId")
        channel_id = _find_text(entry, "yt:channelId")
        title = normalize_text(_find_text(entry, "atom:title") or "")
        if not video_id or not title:
            continue
        link_el = entry.find("atom:link", ATOM_NS)
        source_url = link_el.attrib.get("href") if link_el is not None else f"https://www.youtube.com/watch?v={video_id}"
        author_el = entry.find("atom:author", ATOM_NS)
        author_display_name = _find_text(author_el, "atom:name") if author_el is not None else None
        items.append(
            RawSocialItem(
                platform="youtube",
                source_type="video",
                source_id=video_id,
                root_source_id=video_id,
                conversation_id=video_id,
                depth=0,
                relation_type=None,
                keyword=keyword,
                target_entity=target_entity,
                author_id=channel_id,
                author_display_name=author_display_name,
                text=title,
                source_url=source_url,
                posted_at=_parse_datetime(_find_text(entry, "atom:published")),
                raw_payload={"channel_id": channel_id, "title": title},
                collection_method="rss",
                access_risk="low",
            )
        )
    return items


def parse_youtube_comment_threads(payload: dict, keyword: str, target_entity: str) -> list[RawSocialItem]:
    items: list[RawSocialItem] = []
    for thread in payload.get("items", []):
        snippet = thread.get("snippet", {})
        video_id = snippet.get("videoId")
        top_level = snippet.get("topLevelComment", {})
        comment_id = top_level.get("id") or thread.get("id")
        comment_snippet = top_level.get("snippet", {})
        text = normalize_text(comment_snippet.get("textOriginal") or unescape(comment_snippet.get("textDisplay") or ""))
        if not video_id or not comment_id or not text:
            continue
        author_channel = comment_snippet.get("authorChannelId") or {}
        items.append(
            RawSocialItem(
                platform="youtube",
                source_type="comment",
                source_id=comment_id,
                root_source_id=video_id,
                parent_source_id=None,
                conversation_id=video_id,
                depth=1,
                relation_type="comment",
                keyword=keyword,
                target_entity=target_entity,
                author_id=author_channel.get("value"),
                author_display_name=comment_snippet.get("authorDisplayName"),
                text=text,
                language="id",
                source_url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                posted_at=_parse_datetime(comment_snippet.get("publishedAt")),
                metrics={"like_count": comment_snippet.get("likeCount", 0), "reply_count": snippet.get("totalReplyCount", 0)},
                raw_payload=thread,
                collection_method="youtube_data_api",
                access_risk="low",
            )
        )
        for reply in (thread.get("replies") or {}).get("comments", []):
            reply_id = reply.get("id")
            reply_snippet = reply.get("snippet", {})
            reply_text = normalize_text(reply_snippet.get("textOriginal") or unescape(reply_snippet.get("textDisplay") or ""))
            if not reply_id or not reply_text:
                continue
            reply_author_channel = reply_snippet.get("authorChannelId") or {}
            items.append(
                RawSocialItem(
                    platform="youtube",
                    source_type="reply",
                    source_id=reply_id,
                    root_source_id=video_id,
                    parent_source_id=reply_snippet.get("parentId") or comment_id,
                    conversation_id=video_id,
                    depth=2,
                    relation_type="reply",
                    keyword=keyword,
                    target_entity=target_entity,
                    author_id=reply_author_channel.get("value"),
                    author_display_name=reply_snippet.get("authorDisplayName"),
                    text=reply_text,
                    language="id",
                    source_url=f"https://www.youtube.com/watch?v={video_id}&lc={reply_id}",
                    posted_at=_parse_datetime(reply_snippet.get("publishedAt")),
                    metrics={"like_count": reply_snippet.get("likeCount", 0)},
                    raw_payload=reply,
                    collection_method="youtube_data_api",
                    access_risk="low",
                )
            )
    return items


class YouTubeAdapter:
    platform = "youtube"
    access_mode = "rss+youtube_data_api"
    cost_level = "free_quota"
    risk_level = "low"
    enabled_by_default = True

    def __init__(self, channel_urls: Iterable[str] | None = None, client: httpx.Client | None = None) -> None:
        self.channel_urls = list(channel_urls or DEFAULT_CHANNEL_URLS)
        self.client = client or httpx.Client(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 BNI-BIONS-sentiment-monitor/0.1"})

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        video_items: list[RawSocialItem] = []
        for channel_url in self.channel_urls:
            channel_id = self.resolve_channel_id(channel_url)
            response = self.client.get(YOUTUBE_RSS_URL.format(channel_id=channel_id))
            if response.status_code in {401, 403, 429}:
                raise CollectorStopped(f"youtube rss stopped: status {response.status_code}")
            response.raise_for_status()
            video_items.extend(parse_youtube_feed(response.text, keyword=keyword, target_entity=target_entity))
            if len(video_items) >= limit:
                break
        api_key = _load_env_value("YOUTUBE_API_KEY")
        if not api_key:
            return video_items[:limit]
        comments: list[RawSocialItem] = []
        for video in video_items:
            comments.extend(self.collect_comments(video.source_id, keyword=keyword, target_entity=target_entity, limit=max(1, limit - len(comments)), api_key=api_key))
            if len(comments) >= limit:
                break
        return comments[:limit] or video_items[:limit]

    def collect_comments(self, video_id: str, keyword: str, target_entity: str, limit: int = 50, api_key: str | None = None) -> list[RawSocialItem]:
        key = api_key or _load_env_value("YOUTUBE_API_KEY")
        if not key:
            raise CollectorNotConfigured("YOUTUBE_API_KEY missing")
        response = self.client.get(
            YOUTUBE_COMMENT_THREADS_URL,
            params={
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": max(1, min(limit, 100)),
                "order": "time",
                "textFormat": "plainText",
                "key": key,
            },
        )
        if response.status_code in {401, 403, 429}:
            raise CollectorStopped(f"youtube comments stopped: status {response.status_code}")
        response.raise_for_status()
        return parse_youtube_comment_threads(response.json(), keyword=keyword, target_entity=target_entity)[:limit]

    def resolve_channel_id(self, channel_url: str) -> str:
        if "/channel/" in channel_url:
            return channel_url.rstrip("/").rsplit("/", 1)[-1]
        response = self.client.get(channel_url)
        if response.status_code in {401, 403, 429}:
            raise CollectorStopped(f"youtube channel resolve stopped: status {response.status_code}")
        response.raise_for_status()
        match = re.search(r'"browseId":"(UC[^"]+)"', response.text)
        if not match:
            raise CollectorStopped(f"youtube channel id not found for {channel_url}")
        return match.group(1)
