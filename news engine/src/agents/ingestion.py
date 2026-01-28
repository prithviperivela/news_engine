"""Ingestion Agent - fetches news from RSS feeds."""

from typing import List, Optional

from src.agents.base import Agent, AgentResult
from src.collector import collect_all, fetch_feed, RSS_FEEDS
from src.models import Article


class IngestionAgent(Agent):
    """
    Agent responsible for fetching articles from RSS feeds.
    
    Input: Optional list of feed URLs (defaults to all configured feeds)
    Output: List of raw Article objects
    """
    
    def __init__(self, verbose: bool = True):
        super().__init__("IngestionAgent", verbose)
    
    def run(self, input_data: Optional[List[str]] = None, **kwargs) -> AgentResult:
        """
        Fetch articles from RSS feeds.
        
        Args:
            input_data: Optional list of specific feed URLs to fetch
            
        Returns:
            AgentResult with list of Article objects
        """
        self.log("Starting article collection...")
        
        try:
            if input_data:
                # Fetch specific feeds
                articles = []
                for url in input_data:
                    source_name = next(
                        (name for name, u in RSS_FEEDS.items() if u == url),
                        "Unknown"
                    )
                    articles.extend(fetch_feed(source_name, url))
            else:
                # Fetch all configured feeds
                articles = collect_all()
            
            self.log(f"Collected {len(articles)} articles")
            
            return AgentResult(
                success=True,
                data=articles,
                metadata={"article_count": len(articles)}
            )
            
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult(success=False, error=str(e))
