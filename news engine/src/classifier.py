"""Domain classifier using TF-IDF and keyword matching."""

import re
from typing import List, Dict, Tuple
from collections import Counter

from src.models import Article
from src.domains import DOMAINS, get_domain_names


class DomainClassifier:
    """
    Classifies articles into domains using a hybrid approach:
    - Keyword matching (weighted)
    - TF-IDF-like term frequency scoring
    
    No external ML dependencies required.
    """
    
    def __init__(self, threshold: float = 0.15):
        """
        Initialize classifier.
        
        Args:
            threshold: Minimum score to assign a domain (0-1)
        """
        self.threshold = threshold
        self.domains = DOMAINS
        
        # Precompute lowercase keywords for matching
        self._keyword_cache: Dict[str, List[str]] = {}
        for domain, config in self.domains.items():
            self._keyword_cache[domain] = [kw.lower() for kw in config["keywords"]]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        text = text.lower()
        tokens = re.findall(r'\b[a-z0-9]+\b', text)
        return tokens
    
    def _keyword_score(self, text: str, domain: str) -> Tuple[float, int]:
        """
        Calculate keyword match score.
        Returns (score, match_count).
        """
        text_lower = text.lower()
        keywords = self._keyword_cache[domain]
        
        matches = 0
        for keyword in keywords:
            if keyword in text_lower:
                matches += 1
        
        # Normalize by number of keywords
        score = matches / len(keywords) if keywords else 0
        return score, matches
    
    def _term_frequency_score(self, text: str, domain: str) -> float:
        """
        Calculate TF-IDF-like score based on term frequency.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return 0.0
        
        token_counts = Counter(tokens)
        keywords = self._keyword_cache[domain]
        
        # Count how many keyword tokens appear and their frequency
        total_keyword_freq = 0
        for keyword in keywords:
            # Handle multi-word keywords
            kw_tokens = keyword.split()
            for kw_token in kw_tokens:
                if kw_token in token_counts:
                    total_keyword_freq += token_counts[kw_token]
        
        # Normalize by total tokens
        score = total_keyword_freq / len(tokens)
        return min(score, 1.0)  # Cap at 1.0
    
    def classify(self, article: Article) -> List[str]:
        """
        Classify an article into domains.
        
        Returns list of matching domain names.
        """
        text = f"{article.title} {article.summary}"
        matched_domains = []
        
        for domain in get_domain_names():
            # Combine keyword matching (60%) and term frequency (40%)
            kw_score, matches = self._keyword_score(text, domain)
            tf_score = self._term_frequency_score(text, domain)
            
            combined_score = (kw_score * 0.6) + (tf_score * 0.4)
            
            if combined_score >= self.threshold or matches >= 2:
                matched_domains.append(domain)
        
        return matched_domains
    
    def classify_with_scores(self, article: Article) -> Dict[str, float]:
        """
        Classify an article and return scores for all domains.
        Useful for debugging and analysis.
        """
        text = f"{article.title} {article.summary}"
        scores = {}
        
        for domain in get_domain_names():
            kw_score, _ = self._keyword_score(text, domain)
            tf_score = self._term_frequency_score(text, domain)
            scores[domain] = (kw_score * 0.6) + (tf_score * 0.4)
        
        return scores


def classify_articles(articles: List[Article], threshold: float = 0.15) -> List[Article]:
    """
    Classify a list of articles and update their domain tags.
    
    Returns the same articles with updated domains field.
    """
    classifier = DomainClassifier(threshold=threshold)
    
    for article in articles:
        domains = classifier.classify(article)
        article.domains = domains
    
    return articles
