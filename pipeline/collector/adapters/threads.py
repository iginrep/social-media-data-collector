from pipeline.collector.base import RawSocialItem

class ThreadsAdapter:
    platform = "threads"
    access_mode = "official_api"
    cost_level = "free"
    risk_level = "medium"
    enabled_by_default = False
    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return []
