"""Article data model for the news engine."""

from dataclasses import dataclass, asdict, field
from typing import List, Optional
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
    primary_domain: Optional[str] = None
    secondary_domain: Optional[str] = None
    external_reference_url: Optional[str] = None
    preview_image_url: Optional[str] = None  # OG/Twitter image for frontend cards
    relevance_score: Optional[float] = None  # Classification combined score
    
    @classmethod
    def create(cls, title: str, source: str, published_date: str, 
               url: str, summary: str, domains: List[str] = None,
               primary_domain: str = None, secondary_domain: str = None) -> "Article":
        """Factory method that auto-generates ID from URL."""
        article_id = hashlib.md5(url.encode()).hexdigest()
        
        # Ensure domains list is populated from primary/secondary if not provided
        if not domains and primary_domain:
            domains = [primary_domain]
            if secondary_domain:
                domains.append(secondary_domain)
                
        return cls(
            id=article_id,
            title=title,
            source=source,
            published_date=published_date,
            url=url,
            summary=summary or "",
            domains=domains or [],
            primary_domain=primary_domain,
            secondary_domain=secondary_domain
        )
    
    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        """Create article from dictionary."""
        # Handle legacy articles without optional fields
        if "domains" not in data:
            data["domains"] = []
        if "primary_domain" not in data:
            data["primary_domain"] = None
        if "secondary_domain" not in data:
            data["secondary_domain"] = None
        if "external_reference_url" not in data:
            data["external_reference_url"] = None
        if "preview_image_url" not in data:
            data["preview_image_url"] = None
        if "relevance_score" not in data:
            data["relevance_score"] = None
        return cls(**data)

