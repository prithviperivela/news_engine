"""Classification Agent - assigns domain tags to articles."""

from typing import List

from src.agents.base import Agent, AgentResult
from src.classifier import classify_articles, DomainClassifier
from src.models import Article
from src.domains import get_domain_names


class ClassificationAgent(Agent):
    """
    Agent responsible for classifying articles into domains.
    
    Input: List of Article objects
    Output: Articles with domain tags assigned
    """
    
    def __init__(self, verbose: bool = True):
        super().__init__("ClassificationAgent", verbose)
        self.classifier = DomainClassifier()
    
    def run(self, input_data: List[Article], **kwargs) -> AgentResult:
        """
        Classify articles into domains.
        
        Args:
            input_data: List of articles to classify
            
        Returns:
            AgentResult with classified articles
        """
        if not input_data:
            return AgentResult(success=False, error="No articles to classify")
        
        self.log(f"Classifying {len(input_data)} articles...")
        
        try:
            classified = classify_articles(input_data)
            
            # Count by domain
            domain_counts = {d: 0 for d in get_domain_names()}
            for article in classified:
                for domain in article.domains:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            classified_count = sum(1 for a in classified if a.domains)
            self.log(f"Classified {classified_count} articles into domains")
            
            return AgentResult(
                success=True,
                data=classified,
                metadata={
                    "domain_counts": domain_counts,
                    "classified_count": classified_count,
                    "unclassified_count": len(classified) - classified_count
                }
            )
            
        except Exception as e:
            self.log(f"Error: {e}")
            return AgentResult(success=False, error=str(e))
