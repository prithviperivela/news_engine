"""RSS feed collector for fetching news articles."""

import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Any

from src.models import Article


# Free and legal RSS feed sources
RSS_FEEDS: Dict[str, str] = {
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "arXiv CS.AI": "http://export.arxiv.org/rss/cs.AI",
    "Hacker News Best": "https://hnrss.org/best",
    "TechCrunch": "https://techcrunch.com/feed/",
    "OpenAI Blog": "https://openai.com/blog/rss/",
    "Towards Data Science": "https://towardsdatascience.com/feed",
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",
}


def parse_date(date_string: str) -> str:
    """Parse various date formats to ISO format."""
    if not date_string:
        return datetime.now().isoformat()
    try:
        parsed = date_parser.parse(date_string)
        return parsed.isoformat()
    except (ValueError, TypeError):
        return datetime.now().isoformat()


def fetch_feed(source_name: str, feed_url: str) -> List[Article]:
    """Fetch and parse a single RSS feed."""
    articles = []
    try:
        feed = feedparser.parse(feed_url)
        
        for entry in feed.entries[:20]:  # Limit to 20 per source
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            summary = entry.get("summary", entry.get("description", ""))
            
            # Clean summary (remove HTML tags)
            if summary:
                import re
                summary = re.sub(r'<[^>]+>', '', summary)[:500]
            
            if link:  # Only add if we have a URL
                article = Article.create(
                    title=title,
                    source=source_name,
                    published_date=parse_date(published),
                    url=link,
                    summary=summary
                )
                articles.append(article)
                
    except Exception as e:
        print(f"Error fetching {source_name}: {e}")
    
    return articles


def collect_all() -> List[Article]:
    """Fetch articles from all configured RSS feeds."""
    all_articles = []
    
    for source_name, feed_url in RSS_FEEDS.items():
        print(f"Fetching: {source_name}...")
        articles = fetch_feed(source_name, feed_url)
        all_articles.extend(articles)
        print(f"  Found {len(articles)} articles")
    
    print(f"\nTotal collected: {len(all_articles)} articles")
    return all_articles
