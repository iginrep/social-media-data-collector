from pipeline.collector.base import RawSocialItem


class GooglePlayAdapter:
    platform = "google_play"
    access_mode = "unofficial_api"
    cost_level = "free"
    risk_level = "medium"
    enabled_by_default = True

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        # scaffold only. implementation target: google-play-scraper or equivalent public review collector.
        return []
