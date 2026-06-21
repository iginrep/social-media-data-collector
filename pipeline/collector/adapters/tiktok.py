from pipeline.collector.base import RawSocialItem

class TikTokAdapter:
    platform = "tiktok"
    access_level = "limited"
    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return []
