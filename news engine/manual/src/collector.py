"""RSS feed collector for fetching news articles."""

import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Any

from src.models import Article


# Articles per feed limit
ARTICLES_PER_FEED = 50  # Increased from 20


# RSS feed sources (article-based publishers only)
RSS_FEEDS: Dict[str, str] = {
    # === AI Research & Labs ===
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Google AI Blog": "https://blog.google/technology/ai/rss/",
    "OpenAI Blog": "https://openai.com/blog/rss/",
    "DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "Meta AI Blog": "https://ai.meta.com/blog/rss/",
    "Microsoft AI Blog": "https://blogs.microsoft.com/ai/feed/",
    "Nvidia AI Blog": "https://blogs.nvidia.com/feed/",
    "IBM Research": "https://research.ibm.com/blog/rss.xml",
    "IEEE Spectrum AI": "https://spectrum.ieee.org/feeds/topic/artificial-intelligence.rss",
    "IEEE Spectrum Robotics": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    "IEEE Spectrum Computing": "https://spectrum.ieee.org/feeds/topic/computing.rss",
    
    # === Indian & Asian News ===
    "Times of India Tech": "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
    "Economic Times Tech": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "The Hindu Sci-Tech": "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
    "Indian Express Tech": "https://indianexpress.com/section/technology/feed/",
    
    # === Global Mainstream News ===
    "BBC News Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "Al Jazeera Tech": "https://www.aljazeera.com/tag/science-and-technology/rss.xml",
    "Reuters Tech": "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best",
    
    # === Enterprise & Screenshot Sources ===
    "SiliconANGLE": "https://siliconangle.com/feed/",
    "BusinessLine": "https://www.thehindubusinessline.com/info-tech/feeder/default.rss",
    "Digital Journal": "https://www.digitaljournal.com/feed",
    "NBC News Tech": "https://feeds.nbcnews.com/nbcnews/public/tech",
    "VentureBeat Enterprise": "https://venturebeat.com/category/enterprise/feed/",
    "InfoWorld Cloud": "https://www.infoworld.com/category/cloud-computing/index.rss",
    "InfoWorld Data": "https://www.infoworld.com/category/data-management/index.rss",
    "ZDNet Enterprise": "https://www.zdnet.com/topic/enterprise-software/rss.xml",
    "CIO.com AI": "https://www.cio.com/category/artificial-intelligence/index.rss",
    
    # === Industry News ===
    "VentureBeat AI": "https://venturebeat.com/category/ai/feed/",

    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge AI": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "Wired AI": "https://www.wired.com/feed/tag/ai/latest/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "ZDNet AI": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml",
    "InfoWorld AI": "https://www.infoworld.com/category/artificial-intelligence/index.rss",
    "The Register AI": "https://www.theregister.com/software/ai_ml/headlines.atom",
    "Semafor Tech": "https://www.semafor.com/rss.xml",
    "The Atlantic Tech": "https://www.theatlantic.com/feed/channel/technology/",
    
    # === Newsletters & Curated ===
    "Towards Data Science": "https://towardsdatascience.com/feed",
    "KDnuggets": "https://www.kdnuggets.com/feed",
    "Machine Learning Mastery": "https://machinelearningmastery.com/feed/",
    "Analytics Vidhya": "https://www.analyticsvidhya.com/feed/",
    "DataCamp Blog": "https://www.datacamp.com/blog/rss.xml",
    
    
    # === Cloud & MLOps ===
    "AWS Machine Learning": "https://aws.amazon.com/blogs/machine-learning/feed/",
    "Google Cloud AI": "https://cloud.google.com/blog/products/ai-machine-learning/rss",
    "Azure AI Blog": "https://techcommunity.microsoft.com/gxcuf89792/rss/board?board.id=Azure-AI-Services",
    
    # === Security & Enterprise ===
    "Krebs on Security": "https://krebsonsecurity.com/feed/",
    "SecurityWeek": "https://feeds.feedburner.com/securityweek",
    "Dark Reading": "https://www.darkreading.com/rss.xml",
}


# Source Access Types
ACCESS_OPEN = "open"
ACCESS_PARTIAL = "partial_paywall"
ACCESS_SUBSCRIPTION = "subscription_required"

SOURCE_ACCESS_TYPES: Dict[str, str] = {
    # === AI Research & Labs (Mostly Open) ===
    "MIT Technology Review": ACCESS_PARTIAL, # 3 articles/month
    "Google AI Blog": ACCESS_OPEN,
    "OpenAI Blog": ACCESS_OPEN,
    "DeepMind Blog": ACCESS_OPEN,
    "Meta AI Blog": ACCESS_OPEN,
    "Microsoft AI Blog": ACCESS_OPEN,
    "Nvidia AI Blog": ACCESS_OPEN,
    "IBM Research": ACCESS_OPEN,
    "IEEE Spectrum AI": ACCESS_PARTIAL,
    "IEEE Spectrum Robotics": ACCESS_PARTIAL,
    "IEEE Spectrum Computing": ACCESS_PARTIAL,

    # === Indian & Asian News (Mixed) ===
    "Times of India Tech": ACCESS_OPEN,
    "Economic Times Tech": ACCESS_PARTIAL, # ET Prime often locked
    "The Hindu Sci-Tech": ACCESS_PARTIAL, # Limited free articles
    "Indian Express Tech": ACCESS_OPEN,

    # === Global Mainstream News ===
    "BBC News Technology": ACCESS_OPEN,
    "Al Jazeera Tech": ACCESS_OPEN,
    "Reuters Tech": ACCESS_OPEN, # Registration sometimes, but mostly open

    # === Enterprise & Screenshot Sources ===
    "SiliconANGLE": ACCESS_OPEN,
    "BusinessLine": ACCESS_PARTIAL,
    "Digital Journal": ACCESS_OPEN,
    "NBC News Tech": ACCESS_OPEN,
    "VentureBeat Enterprise": ACCESS_OPEN, # Mostly open
    "InfoWorld Cloud": ACCESS_OPEN, # Registration for some
    "InfoWorld Data": ACCESS_OPEN,
    "ZDNet Enterprise": ACCESS_OPEN,
    "CIO.com AI": ACCESS_OPEN,

    # === Industry News ===
    "VentureBeat AI": ACCESS_OPEN,
    "TechCrunch AI": ACCESS_OPEN,
    "TechCrunch": ACCESS_OPEN,
    "The Verge AI": ACCESS_OPEN,
    "Wired AI": ACCESS_PARTIAL, # Strict metering
    "Ars Technica": ACCESS_OPEN, # Some pro content but mostly open
    "ZDNet AI": ACCESS_OPEN,
    "InfoWorld AI": ACCESS_OPEN,
    "The Register AI": ACCESS_OPEN,
    "Semafor Tech": ACCESS_OPEN,
    "The Atlantic Tech": ACCESS_PARTIAL, # Strict metering

    # === Newsletters & Curated ===
    "Towards Data Science": ACCESS_PARTIAL, # Medium metered
    "KDnuggets": ACCESS_OPEN,
    "Machine Learning Mastery": ACCESS_OPEN,
    "Analytics Vidhya": ACCESS_OPEN,
    "DataCamp Blog": ACCESS_OPEN,

    # === Cloud & MLOps ===
    "AWS Machine Learning": ACCESS_OPEN,
    "Google Cloud AI": ACCESS_OPEN,
    "Azure AI Blog": ACCESS_OPEN,

    # === Security & Enterprise ===
    "Krebs on Security": ACCESS_OPEN,
    "SecurityWeek": ACCESS_OPEN,
    "Dark Reading": ACCESS_OPEN,
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
        
        for entry in feed.entries[:ARTICLES_PER_FEED]:
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            summary = entry.get("summary", entry.get("description", ""))
            
            # Clean summary (remove HTML tags)
            if summary:
                import re
                summary = re.sub(r'<[^>]+>', '', summary)[:500]
            
            if not link:
                continue
            
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





def collect_all() -> tuple:
    """
    Fetch articles from all configured RSS feeds with adaptive freshness filtering.
    
    Returns:
        (articles, cutoff_hours) — the filtered articles and the freshness cutoff used.
        Use cutoff_hours to align storage purge threshold.
    """
    all_articles = []
    
    for source_name, feed_url in RSS_FEEDS.items():
        print(f"Fetching: {source_name}...")
        articles = fetch_feed(source_name, feed_url)
        all_articles.extend(articles)
        print(f"  Found {len(articles)} articles")
    
    print(f"\nTotal collected (raw): {len(all_articles)} articles")
    
    # Apply adaptive freshness filter
    filtered, cutoff_hours = filter_by_freshness(all_articles)
    
    return filtered, cutoff_hours


def filter_by_freshness(articles: List[Article]) -> tuple:
    """
    Apply adaptive freshness cutoff based on article count.
    
    Thresholds:
        >= 1200 articles → keep only ≤ 24 hours old
        < 1200 articles  → expand to ≤ 36 hours
        < 500 articles   → expand to ≤ 48 hours
    
    Returns:
        (filtered_articles, max_age_hours) — so purge threshold can be aligned.
    """
    total = len(articles)
    
    if total >= 1200:
        max_age_hours = 24
    elif total >= 500:
        max_age_hours = 36
    else:
        max_age_hours = 48
    
    now = datetime.now()
    fresh = []
    
    for article in articles:
        try:
            pub_date = date_parser.parse(article.published_date)
            # Make timezone-naive for comparison
            if pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=None)
            age_hours = (now - pub_date).total_seconds() / 3600
            if age_hours <= max_age_hours:
                fresh.append(article)
        except (ValueError, TypeError):
            # If date can't be parsed, include the article (benefit of doubt)
            fresh.append(article)
    
    print(f"Freshness filter: {max_age_hours}h cutoff -> {len(fresh)} articles kept (dropped {total - len(fresh)})")
    return fresh, max_age_hours


def get_source_count() -> int:
    """Get number of configured sources."""
    return len(RSS_FEEDS)


def get_source_access_type(source: str) -> str:
    """Get access type for a source (default: open)."""
    return SOURCE_ACCESS_TYPES.get(source, ACCESS_OPEN)
