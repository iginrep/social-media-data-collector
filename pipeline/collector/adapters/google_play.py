from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable

from pipeline.collector.base import RawSocialItem
from pipeline.collector.exceptions import CollectorStopped
from pipeline.collector.normalizer import normalize_text


DEFAULT_PACKAGE_ID = "id.bions.bnis.android"


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def parse_google_play_reviews(reviews: Iterable[dict[str, Any]], keyword: str, target_entity: str) -> list[RawSocialItem]:
    items: list[RawSocialItem] = []
    for index, review in enumerate(reviews):
        text = normalize_text(str(review.get("content") or ""))
        if not text:
            continue
        review_id = str(review.get("reviewId") or review.get("id") or f"google_play_review_{index}")
        metrics: dict[str, Any] = {}
        if review.get("score") is not None:
            metrics["rating"] = review.get("score")
        if review.get("thumbsUpCount") is not None:
            metrics["thumbs_up"] = review.get("thumbsUpCount")
        raw_payload = dict(review)
        if review.get("appVersion") is not None:
            raw_payload["app_version"] = review.get("appVersion")
        items.append(
            RawSocialItem(
                platform="google_play",
                source_type="app_review",
                source_id=review_id,
                root_source_id=review_id,
                conversation_id=review_id,
                depth=0,
                relation_type=None,
                keyword=keyword,
                target_entity=target_entity,
                text=text,
                author_display_name=review.get("userName"),
                language="id",
                source_url=f"https://play.google.com/store/apps/details?id={DEFAULT_PACKAGE_ID}&reviewId={review_id}",
                posted_at=_parse_datetime(review.get("at")),
                metrics=metrics,
                raw_payload=raw_payload,
                collection_method="scraper",
                access_risk="low",
            )
        )
    return items


class GooglePlayAdapter:
    platform = "google_play"
    access_mode = "scraper"
    cost_level = "free"
    risk_level = "low"
    enabled_by_default = True

    def __init__(self, package_id: str = DEFAULT_PACKAGE_ID, lang: str = "id", country: str = "id", sort: str = "NEWEST") -> None:
        self.package_id = package_id
        self.lang = lang
        self.country = country
        self.sort = sort

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        try:
            from google_play_scraper import Sort, reviews
        except ImportError as exc:
            raise CollectorStopped("google-play-scraper package missing; install collector deps") from exc
        sort_value = getattr(Sort, self.sort, Sort.NEWEST)
        result, _continuation = reviews(
            self.package_id,
            lang=self.lang,
            country=self.country,
            sort=sort_value,
            count=max(0, min(limit, 200)),
        )
        return parse_google_play_reviews(result, keyword=keyword, target_entity=target_entity)[:limit]
