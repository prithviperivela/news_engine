"""Domain classifier using TF-IDF and keyword matching."""

import re
from typing import List, Dict, Tuple
from collections import Counter

from src.models import Article


class DomainClassifier:
    """
    Classifies articles into domains using a hybrid approach:
    - Keyword matching (weighted)
    - TF-IDF-like term frequency scoring
    
    No external ML dependencies required.
    """
    
    def __init__(self, threshold: float = 0.12, domains: Dict[str, Dict] = None):
        """
        Initialize classifier.
        
        Args:
            threshold: Minimum score to assign a domain (0-1)
            domains: Domain configuration dict. If None, falls back to
                     module-level DOMAINS from src.domains.
        """
        self.threshold = threshold
        
        # Accept domains as parameter or fall back to global
        if domains is not None:
            self.domains = domains
        else:
            from src.domains import DOMAINS
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
        
        Updates article.primary_domain, article.secondary_domain,
        and article.relevance_score (combined classification score).
        Returns list of matching domain names [primary, secondary].
        """
        text = f"{article.title} {article.summary}"
        scores: List[Tuple[str, float]] = []
        
        # Calculate scores for all domains
        for domain in list(self.domains.keys()):
            # Combine keyword matching (60%) and term frequency (40%)
            kw_score, matches = self._keyword_score(text, domain)
            tf_score = self._term_frequency_score(text, domain)
            
            combined_score = (kw_score * 0.6) + (tf_score * 0.4)
            
            # Boost score if explicit matches found
            if matches >= 2:
                combined_score += 0.1
                
            if combined_score >= self.threshold:
                scores.append((domain, combined_score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        if not scores:
            article.relevance_score = 0.0
            return []
            
        # Select Primary Domain (Highest Score)
        primary_domain = scores[0][0]
        primary_score = scores[0][1]
        secondary_domain = None
        
        # Select Secondary Domain
        if len(scores) > 1:
            candidate_domain = scores[1][0]
            candidate_score = scores[1][1]
            
            # Check if candidate is valid secondary
            if candidate_domain != primary_domain:
                 # Ensure score is strong enough relative to primary
                 if candidate_score >= self.threshold:
                     secondary_domain = candidate_domain
        
        # Assign to article
        article.primary_domain = primary_domain
        article.secondary_domain = secondary_domain
        article.relevance_score = round(primary_score, 4)
        
        # Construct legacy list
        domains = [primary_domain]
        if secondary_domain:
            domains.append(secondary_domain)
            
        return domains
    
    def classify_with_scores(self, article: Article) -> Dict[str, float]:
        """
        Classify an article and return scores for all domains.
        Useful for debugging and analysis.
        """
        text = f"{article.title} {article.summary}"
        scores = {}
        
        for domain in list(self.domains.keys()):
            kw_score, _ = self._keyword_score(text, domain)
            tf_score = self._term_frequency_score(text, domain)
            scores[domain] = (kw_score * 0.6) + (tf_score * 0.4)
        
        return scores


def classify_articles(articles: List[Article], threshold: float = 0.15, domains: Dict[str, Dict] = None) -> List[Article]:
    """
    Classify a list of articles and update their domain tags.
    
    Args:
        articles: List of Article objects to classify
        threshold: Minimum score to assign a domain
        domains: Optional domain configuration dict. If None, uses module-level DOMAINS.
    
    Returns the same articles with updated domains field.
    """
    classifier = DomainClassifier(threshold=threshold, domains=domains)
    
    for article in articles:
        domains_list = classifier.classify(article)
        article.domains = domains_list
        # primary/secondary are set inside classify(article)
    
    return articles
