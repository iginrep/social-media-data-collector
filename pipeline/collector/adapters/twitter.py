from __future__ import annotations
from pipeline.collector.base import RawSocialItem
from pipeline.collector.normalizer import normalize_text


class TwitterAdapter:
    platform = "x"
    access_level = "limited"

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        sample = {
            "id": "x_sample_1",
            "text": "BIONS error lagi pas mau order, bikin kesel.",
            "author_id": "user_1",
            "created_at": "2026-01-01T00:00:00Z",
            "lang": "id",
            "conversation_id": "x_conv_1",
            "public_metrics": {"reply_count": 1, "retweet_count": 0, "like_count": 2, "quote_count": 0}
        }
        return [RawSocialItem(
            platform=self.platform,
            source_type="tweet",
            source_id=sample["id"],
            conversation_id=sample.get("conversation_id"),
            keyword=keyword,
            target_entity=target_entity,
            author_id=sample.get("author_id"),
            text=normalize_text(sample["text"]),
            language=sample.get("lang"),
            source_url=f"https://x.com/i/web/status/{sample['id']}",
            metrics=sample.get("public_metrics", {}),
            raw_payload=sample,
        )]
