from pipeline.collector.base import RawSocialItem

class StockbitAdapter:
    platform = "stockbit"
    access_level = "unofficial"
    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]:
        return []
