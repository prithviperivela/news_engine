"""Processing Agent - stores and deduplicates articles."""

from typing import List

from src.agents.base import Agent, AgentResult
from src.storage import save_articles, load_articles, update_articles
from src.models import Article


class ProcessingAgent(Agent):
    """
    Agent responsible for storing and deduplicating articles.
    
    Input: List of Article objects
    Output: Deduplicated articles (saved to storage)
    """
    
    def __init__(self, verbose: bool = True):
        super().__init__("ProcessingAgent", verbose)
    
    def run(self, input_data: List[Article] = None, **kwargs) -> AgentResult:
        """
        Process and store articles with deduplication.
        
        Args:
            input_data: List of articles to process
            mode: 'save' (new articles) or 'update' (modify existing)
            
        Returns:
            AgentResult with processed articles
        """
        mode = kwargs.get("mode", "save")
        
        try:
            if input_data is None:
                # Load existing articles
                self.log("Loading articles from storage...")
                articles = load_articles()
                self.log(f"Loaded {len(articles)} articles")
                return AgentResult(
                    success=True,
                    data=articles,
                    metadata={"article_count": len(articles), "mode": "load"}
                )
            
            if mode == "save":
                self.log(f"Saving {len(input_data)} articles...")
                new_count = save_articles(input_data)
                self.log(f"Added {new_count} new articles")
                
                return AgentResult(
                    success=True,
                    data=load_articles(),
                    metadata={"new_count": new_count, "mode": "save"}
                )
                
            elif mode == "update":
                self.log(f"Updating {len(input_data)} articles...")
                updated = update_articles(input_data)
                self.log(f"Updated {updated} articles")
                
                return AgentResult(
                    success=True,
                    data=input_data,
                    metadata={"updated_count": updated, "mode": "update"}
                )
                
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult(success=False, error=str(e))
