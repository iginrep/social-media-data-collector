from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
import hashlib
import json


@dataclass(slots=True)
class RawSocialItem:
    platform: str
    source_type: str
    source_id: str
    keyword: str
    target_entity: str
    text: str
    root_source_id: str | None = None
    parent_source_id: str | None = None
    conversation_id: str | None = None
    depth: int = 0
    relation_type: str | None = None
    author_id: str | None = None
    author_username: str | None = None
    author_display_name: str | None = None
    language: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metrics: dict[str, Any] = field(default_factory=dict)
    raw_payload: dict[str, Any] = field(default_factory=dict)
    content_hash: str = ""
    collection_method: str = "official_api"
    access_risk: str = "low"
    collector_version: str = "v0.1"

    def __post_init__(self) -> None:
        if not self.content_hash:
            payload = f"{self.platform}|{self.source_id}|{self.text}".encode()
            self.content_hash = hashlib.sha256(payload).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("posted_at", "collected_at"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return data

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), ensure_ascii=False, sort_keys=True)


class CollectorAdapter(Protocol):
    platform: str
    access_mode: str
    cost_level: str
    risk_level: str
    enabled_by_default: bool

    def collect(self, keyword: str, target_entity: str, limit: int = 50) -> list[RawSocialItem]: ...
