"""Article ranking engine with recency, domain, and source scoring."""

import math
from datetime import datetime
from typing import List, Tuple
from dateutil import parser as date_parser

from src.models import Article


# Source reliability tiers (higher = more reliable)
SOURCE_RELIABILITY: dict = {
    # Tier 1: Academic/Research
    "MIT Technology Review": 1.0,
    "arXiv CS.AI": 0.95,
    
    # Tier 2: Primary Sources
    "Google AI Blog": 0.85,
    "OpenAI Blog": 0.85,
    
    # Tier 3: Industry News
    "VentureBeat AI": 0.7,
    "TechCrunch": 0.7,
    "Towards Data Science": 0.65,
    
    # Tier 4: Community
    "Hacker News Best": 0.5,
}

# Default score for unknown sources
DEFAULT_SOURCE_SCORE = 0.5

# Scoring weights
WEIGHT_RECENCY = 0.40
WEIGHT_DOMAIN = 0.35
WEIGHT_SOURCE = 0.25

# Recency decay constant (days)
RECENCY_HALF_LIFE = 7


def calculate_recency_score(published_date: str) -> float:
    """
    Calculate recency score using exponential decay.
    Score = e^(-age_days / half_life)
    
    Returns value between 0 and 1 (1 = today, decays over time).
    """
    try:
        pub_date = date_parser.parse(published_date)
        now = datetime.now(pub_date.tzinfo) if pub_date.tzinfo else datetime.now()
        age_days = (now - pub_date).days
        
        # Exponential decay
        score = math.exp(-age_days / RECENCY_HALF_LIFE)
        return max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        return 0.5  # Default for unparseable dates


def calculate_source_score(source: str) -> float:
    """
    Get source reliability score from predefined tiers.
    """
    return SOURCE_RELIABILITY.get(source, DEFAULT_SOURCE_SCORE)


def calculate_domain_score(domains: List[str], max_domains: int = 3) -> float:
    """
    Calculate domain relevance score based on number of matched domains.
    Normalized to 0-1 range.
    """
    if not domains:
        return 0.0
    
    # Score based on domain count (capped at max_domains)
    count = min(len(domains), max_domains)
    return count / max_domains


def calculate_final_score(article: Article) -> float:
    """
    Calculate final ranking score combining all signals.
    """
    recency = calculate_recency_score(article.published_date)
    source = calculate_source_score(article.source)
    domain = calculate_domain_score(article.domains)
    
    final_score = (
        recency * WEIGHT_RECENCY +
        domain * WEIGHT_DOMAIN +
        source * WEIGHT_SOURCE
    )
    
    return round(final_score, 3)


def rank_articles(articles: List[Article]) -> List[Tuple[Article, float]]:
    """
    Rank articles by calculated score.
    Returns list of (article, score) tuples sorted by score descending.
    """
    scored = [(article, calculate_final_score(article)) for article in articles]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


def get_top_articles(articles: List[Article], n: int = 10) -> List[Tuple[Article, float]]:
    """
    Get top N ranked articles.
    """
    ranked = rank_articles(articles)
    return ranked[:n]
