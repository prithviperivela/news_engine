"""Query Agent - handles user requests and filtering."""

from typing import List, Optional

from src.agents.base import Agent, AgentResult
from src.filter import filter_by_keyword, filter_by_domain
from src.models import Article


class QueryAgent(Agent):
    """
    Agent responsible for handling user queries and filtering.
    
    Input: List of Article objects + query parameters
    Output: Filtered articles matching the query
    """
    
    def __init__(self, verbose: bool = True):
        super().__init__("QueryAgent", verbose)
    
    def run(self, input_data: List[Article], **kwargs) -> AgentResult:
        """
        Filter articles based on query parameters.
        
        Args:
            input_data: List of articles to filter
            keyword: Filter by keyword in title/summary
            domain: Filter by domain tag
            
        Returns:
            AgentResult with filtered articles
        """
        keyword = kwargs.get("keyword")
        domain = kwargs.get("domain")
        
        if not input_data:
            return AgentResult(success=False, error="No articles to query")
        
        try:
            filtered = input_data
            
            if keyword:
                self.log(f"Filtering by keyword: '{keyword}'")
                filtered = filter_by_keyword(filtered, keyword)
            
            if domain:
                self.log(f"Filtering by domain: '{domain}'")
                filtered = filter_by_domain(filtered, domain)
            
            self.log(f"Found {len(filtered)} matching articles")
            
            return AgentResult(
                success=True,
                data=filtered,
                metadata={
                    "count": len(filtered),
                    "keyword": keyword,
                    "domain": domain
                }
            )
            
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult(success=False, error=str(e))
