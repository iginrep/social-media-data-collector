from pipeline.collector.base import RawSocialItem

class StockbitAdapter:
    platform = "stockbit"
    access_mode = "automation"
    cost_level = "free"
    risk_level = "high"
    enabled_by_default = False
    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return []
