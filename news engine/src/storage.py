"""JSON-based storage with deduplication."""

import json
import os
from typing import List, Optional
from pathlib import Path

from src.models import Article


DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_articles() -> List[Article]:
    """Load all articles from storage."""
    ensure_data_dir()
    
    if not ARTICLES_FILE.exists():
        return []
    
    try:
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [Article.from_dict(item) for item in data]
    except (json.JSONDecodeError, IOError):
        return []


def save_articles(articles: List[Article]) -> int:
    """
    Save articles to storage with deduplication.
    Returns number of new articles added.
    """
    ensure_data_dir()
    
    # Load existing articles
    existing = load_articles()
    existing_ids = {a.id for a in existing}
    
    # Find new articles
    new_articles = [a for a in articles if a.id not in existing_ids]
    
    # Merge and save
    all_articles = existing + new_articles
    
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in all_articles], f, indent=2, ensure_ascii=False)
    
    return len(new_articles)


def update_articles(articles: List[Article]) -> int:
    """
    Update existing articles in storage (e.g., with new domain tags).
    Returns number of articles updated.
    """
    ensure_data_dir()
    
    # Create lookup by ID
    updates = {a.id: a for a in articles}
    
    # Load and update existing
    existing = load_articles()
    updated_count = 0
    
    for i, article in enumerate(existing):
        if article.id in updates:
            existing[i] = updates[article.id]
            updated_count += 1
    
    # Save back
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in existing], f, indent=2, ensure_ascii=False)
    
    return updated_count


def get_article_count() -> int:
    """Get total number of stored articles."""
    return len(load_articles())


def clear_storage():
    """Clear all stored articles."""
    ensure_data_dir()
    if ARTICLES_FILE.exists():
        ARTICLES_FILE.unlink()

