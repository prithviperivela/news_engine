"""Article ranking engine with recency, domain, and source scoring."""

import math
from datetime import datetime
from typing import List, Tuple
from dateutil import parser as date_parser

from src.models import Article
from src.collector import (
    get_source_access_type, 
    ACCESS_OPEN, 
    ACCESS_PARTIAL, 
    ACCESS_SUBSCRIPTION
)


# Source reliability tiers (higher = more reliable)
SOURCE_RELIABILITY: dict = {
    # Tier 1: Primary Journalism (1.0 - 0.95)
    "MIT Technology Review": 1.0,
    
    # Tier 2: Primary Sources - Big Tech Labs & Global News (0.9 - 0.85)
    "Google AI Blog": 0.9,
    "OpenAI Blog": 0.9,
    "DeepMind Blog": 0.9,
    "Meta AI Blog": 0.88,
    "Microsoft AI Blog": 0.88,
    "Google Cloud AI": 0.85,
    "AWS Machine Learning": 0.85,
    "BBC News Technology": 0.85,
    "Reuters": 0.85,
    
    # Tier 3: Industry & Mainstream News (0.75 - 0.65)
    "VentureBeat AI": 0.75,
    "Al Jazeera": 0.75,
    "TechCrunch": 0.72,
    "SiliconANGLE": 0.72,
    "The Verge AI": 0.7,
    "Wired AI": 0.7,
    "Ars Technica": 0.7,
    "Times of India Tech": 0.7,
    "Economic Times Tech": 0.7,
    "The Hindu Sci-Tech": 0.7,
    "Indian Express Tech": 0.7,
    "BusinessLine": 0.65,
    "NBC News Tech": 0.65,
    
    # Tier 4: Educational/Tutorials & Secondary (0.65 - 0.55)
    "Towards Data Science": 0.65,
    "KDnuggets": 0.65,
    "Machine Learning Mastery": 0.6,
    "Analytics Vidhya": 0.6,
    "Dev.to AI": 0.55,
    "Digital Journal": 0.55,
    
    # Tier 5: Community (0.5)
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

# Access multiplier weights
ACCESS_WEIGHTS = {
    ACCESS_OPEN: 1.0,
    ACCESS_PARTIAL: 0.85,
    ACCESS_SUBSCRIPTION: 0.70
}


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
    """Get source reliability score from predefined tiers."""
    return SOURCE_RELIABILITY.get(source, DEFAULT_SOURCE_SCORE)


def calculate_domain_score(domains: List[str], max_domains: int = 3) -> float:
    """
    Calculate domain relevance score based on number of matched domains.
    Normalized to 0-1 range.
    """
    if not domains:
        return 0.0
    
    count = min(len(domains), max_domains)
    return count / max_domains


def calculate_final_score(article: Article) -> float:
    """
    Calculate final ranking score combining all signals.
    
    Signals:
        - 40% Recency (exponential decay, 7-day half-life)
        - 35% Domain match (how many domains the article matched)
        - 25% Source reliability (tiered publisher scores)
        × Paywall multiplier (open=1.0, partial=0.85, subscription=0.70)
    """
    recency = calculate_recency_score(article.published_date)
    source = calculate_source_score(article.source)
    domain = calculate_domain_score(article.domains)
    
    final_score = (
        recency * WEIGHT_RECENCY +
        domain * WEIGHT_DOMAIN +
        source * WEIGHT_SOURCE
    )
    
    # Apply access-based multiplier — open content favored, paywalled downranked
    access_type = get_source_access_type(article.source)
    multiplier = ACCESS_WEIGHTS.get(access_type, 1.0)
    
    final_score *= multiplier
    
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
    """Get top N ranked articles."""
    ranked = rank_articles(articles)
    return ranked[:n]
