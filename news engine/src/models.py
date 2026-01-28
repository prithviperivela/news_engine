"""Article data model for the news engine."""

from dataclasses import dataclass, asdict, field
from typing import List
import hashlib


@dataclass
class Article:
    """Represents a news article."""
    
    id: str
    title: str
    source: str
    published_date: str
    url: str
    summary: str
    domains: List[str] = field(default_factory=list)
    
    @classmethod
    def create(cls, title: str, source: str, published_date: str, 
               url: str, summary: str, domains: List[str] = None) -> "Article":
        """Factory method that auto-generates ID from URL."""
        article_id = hashlib.md5(url.encode()).hexdigest()
        return cls(
            id=article_id,
            title=title,
            source=source,
            published_date=published_date,
            url=url,
            summary=summary or "",
            domains=domains or []
        )
    
    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create article from dictionary."""
        # Handle legacy articles without domains field
        if "domains" not in data:
            data["domains"] = []
        return cls(**data)

