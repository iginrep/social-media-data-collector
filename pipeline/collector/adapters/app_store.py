from pipeline.collector.base import RawSocialItem


class AppStoreAdapter:
    platform = "app_store"
    access_mode = "rss"
    cost_level = "free"
    risk_level = "low"
    enabled_by_default = True

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        # scaffold only. implementation target: iTunes Search API + customer reviews RSS.
        return []
