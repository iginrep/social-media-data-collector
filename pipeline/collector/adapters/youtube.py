from __future__ import annotations
from pipeline.collector.base import RawSocialItem
from pipeline.collector.normalizer import normalize_text


class YouTubeAdapter:
    platform = "youtube"
    access_level = "official"

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        # scaffold sample. replace with commentThreads.list integration.
        sample = {
            "id": "yt_sample_1",
            "snippet": {
                "videoId": "sample_video",
                "topLevelComment": {
                    "id": "yt_comment_1",
                    "snippet": {
                        "textOriginal": "BIONS sekarang lebih lancar, order cepat.",
                        "authorDisplayName": "sample_user",
                        "authorChannelId": {"value": "sample_channel"},
                        "likeCount": 3,
                        "publishedAt": "2026-01-01T00:00:00Z"
                    }
                },
                "totalReplyCount": 0
            }
        }
        comment = sample["snippet"]["topLevelComment"]
        snippet = comment["snippet"]
        return [RawSocialItem(
            platform=self.platform,
            source_type="comment",
            source_id=comment["id"],
            conversation_id=sample["snippet"]["videoId"],
            keyword=keyword,
            target_entity=target_entity,
            author_id=snippet.get("authorChannelId", {}).get("value"),
            author_display_name=snippet.get("authorDisplayName"),
            text=normalize_text(snippet.get("textOriginal", "")),
            language="id",
            source_url=f"https://www.youtube.com/watch?v={sample['snippet']['videoId']}&lc={comment['id']}",
            metrics={"like_count": snippet.get("likeCount", 0), "reply_count": sample["snippet"].get("totalReplyCount", 0)},
            raw_payload=sample,
        )]
