"""Ranking Agent - scores and orders articles."""

from typing import List, Tuple

from src.agents.base import Agent, AgentResult
from src.ranker import rank_articles, get_top_articles
from src.models import Article


class RankingAgent(Agent):
    """
    Agent responsible for ranking articles by relevance.
    
    Input: List of Article objects
    Output: Ranked list of (Article, score) tuples
    """
    
    def __init__(self, verbose: bool = True):
        super().__init__("RankingAgent", verbose)
    
    def run(self, input_data: List[Article], **kwargs) -> AgentResult:
        """
        Rank articles by relevance score.
        
        Args:
            input_data: List of articles to rank
            limit: Maximum number of articles to return
            
        Returns:
            AgentResult with ranked (article, score) tuples
        """
        limit = kwargs.get("limit", 10)
        
        if not input_data:
            return AgentResult(success=False, error="No articles to rank")
        
        self.log(f"Ranking {len(input_data)} articles...")
        
        try:
            ranked = get_top_articles(input_data, n=limit)
            
            if ranked:
                top_score = ranked[0][1]
                avg_score = sum(s for _, s in ranked) / len(ranked)
            else:
                top_score = avg_score = 0
            
            self.log(f"Returned top {len(ranked)} articles (best score: {top_score})")
            
            return AgentResult(
                success=True,
                data=ranked,
                metadata={
                    "count": len(ranked),
                    "top_score": top_score,
                    "avg_score": round(avg_score, 3)
                }
            )
            
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult(success=False, error=str(e))
