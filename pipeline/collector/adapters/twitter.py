from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorNotConfigured, CollectorStopped
from pipeline.collector.normalizer import normalize_text
from pipeline.collector.web_extract import env_csv


TWEET_FIELDS = "id,text,created_at,lang,public_metrics,author_id,conversation_id,in_reply_to_user_id,referenced_tweets"
EXPANSIONS = "author_id,in_reply_to_user_id,referenced_tweets.id"
USER_FIELDS = "username,name,verified"


class TwitterAdapter:
    platform = "x"
    source_type = "tweet"
    access_mode = "official_api"
    cost_level = "paid_or_limited"
    risk_level = "medium"
    enabled_by_default = False

    def __init__(
        self,
        bearer_token: str | None = None,
        client: httpx.Client | None = None,
        official_usernames: list[str] | None = None,
        search_queries: list[str] | None = None,
        collect_public_mentions: bool | None = None,
        collect_official_post_replies: bool | None = None,
    ) -> None:
        self.bearer_token = bearer_token or os.getenv("X_BEARER_TOKEN")
        self.client = client or httpx.Client(timeout=20.0)
        self.official_usernames = official_usernames if official_usernames is not None else env_csv(os.getenv("X_OFFICIAL_USERNAMES"))
        self.search_queries = search_queries if search_queries is not None else env_csv(os.getenv("X_SEARCH_QUERIES"))
        self.collect_public_mentions = bool(self.search_queries) if collect_public_mentions is None else collect_public_mentions
        self.collect_official_post_replies = bool(self.official_usernames) if collect_official_post_replies is None else collect_official_post_replies

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        if not self.bearer_token:
            raise CollectorNotConfigured("X_BEARER_TOKEN missing")
        if not ((self.collect_public_mentions and self.search_queries) or (self.collect_official_post_replies and self.official_usernames)):
            raise CollectorNotConfigured("X_SEARCH_QUERIES or X_OFFICIAL_USERNAMES missing")

        rows: list[RawSocialItem] = []
        if self.collect_public_mentions:
            queries = self.search_queries or [f'"{keyword}" lang:id -is:retweet']
            for query in queries:
                rows.extend(self.collect_recent_mentions(query, keyword, target_entity, limit=max(limit - len(rows), 10)))
                if len(rows) >= limit:
                    return rows[:limit]

        if self.collect_official_post_replies:
            for username in self.official_usernames:
                user_id = self.lookup_user_id(username)
                for tweet in self.fetch_user_tweets(user_id, limit=min(10, limit)):
                    rows.extend(self.collect_conversation_replies(str(tweet["id"]), username, keyword, target_entity, limit=max(limit - len(rows), 10)))
                    if len(rows) >= limit:
                        return rows[:limit]
        return rows[:limit]

    def collect_recent_mentions(self, query: str, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        payload = self._get_json(self._recent_search_url(query, limit))
        return [self._to_item(row, keyword, target_entity) for row in payload.get("data", [])[:limit]]

    def collect_conversation_replies(self, tweet_id: str, username: str, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        query = f"conversation_id:{tweet_id} -from:{username}"
        payload = self._get_json(self._recent_search_url(query, limit))
        return [self._to_item(row, keyword, target_entity) for row in payload.get("data", [])[:limit]]

    def lookup_user_id(self, username: str) -> str:
        payload = self._get_json(f"https://api.x.com/2/users/by/username/{username}?user.fields={USER_FIELDS}")
        return str(payload["data"]["id"])

    def fetch_user_tweets(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        max_results = min(max(limit, 5), 100)
        payload = self._get_json(
            f"https://api.x.com/2/users/{user_id}/tweets?max_results={max_results}&tweet.fields={TWEET_FIELDS}&exclude=retweets,replies"
        )
        return list(payload.get("data", []))

    def _recent_search_url(self, query: str, limit: int) -> str:
        max_results = min(max(limit, 10), 100)
        return (
            "https://api.x.com/2/tweets/search/recent"
            f"?query={quote(query)}&max_results={max_results}"
            f"&tweet.fields={TWEET_FIELDS}&expansions={EXPANSIONS}&user.fields={USER_FIELDS}"
        )

    def _get_json(self, url: str) -> dict[str, Any]:
        response = self.client.get(url, headers={"Authorization": f"Bearer {self.bearer_token}"})
        if response.status_code in {401, 403, 429}:
            raise CollectorStopped(f"x collector stopped: status {response.status_code}")
        response.raise_for_status()
        return response.json()

    def _to_item(self, row: dict[str, Any], keyword: str, target_entity: str) -> RawSocialItem:
        posted_at = None
        if row.get("created_at"):
            posted_at = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        tweet_id = str(row.get("id"))
        referenced = row.get("referenced_tweets") or []
        parent_id = referenced[0].get("id") if referenced else None
        reference_type = referenced[0].get("type") if referenced else None
        relation = "reply" if reference_type == "replied_to" else reference_type
        return RawSocialItem(
            platform=self.platform,
            source_type=self.source_type,
            source_id=tweet_id,
            root_source_id=row.get("conversation_id") or tweet_id,
            parent_source_id=parent_id,
            conversation_id=row.get("conversation_id") or tweet_id,
            depth=1 if parent_id else 0,
            relation_type=relation,
            keyword=keyword,
            target_entity=target_entity,
            text=normalize_text(str(row.get("text", ""))),
            author_id=str(row.get("author_id")) if row.get("author_id") else None,
            language=row.get("lang"),
            source_url=f"https://x.com/i/web/status/{tweet_id}",
            posted_at=posted_at,
            metrics=row.get("public_metrics") or {},
            raw_payload=row,
            collection_method=self.access_mode,
            access_risk=self.risk_level,
        )
