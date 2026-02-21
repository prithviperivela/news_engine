"""Domain filtering using BM25 and Hybrid Phrase Boosting."""

import re
from typing import List, Dict, Tuple
from rank_bm25 import BM25Okapi

from src.models import Article


class DomainFilter:
    """
    Filters articles based on domain relevance using a hybrid approach:
    1. BM25 Token-based scoring (Lexical relevance)
    2. Exact Phrase Boosting (Controlled multi-word boost)
    """
    
    # Configurable constants
    PERCENTILE_CUTOFF = 0.5   # Keep top 50% of scored candidates
    MIN_SCORE_FLOOR = 0.5     # Safety floor to reject garbage batches
    PHRASE_BOOST_WEIGHT = 1.5
    MAX_PHRASE_BOOST = 5.0
    
    def __init__(self):
        """Initialize filter."""
        pass
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        return re.findall(r'\b[a-z0-9]+\b', text.lower())

    def filter_articles(self, articles: List[Article], keywords: List[str], corpus: List[Article] = None) -> List[Article]:
        """
        Filter articles by relevance to the provided keywords.
        
        Args:
            articles: List of candidate articles to classify/filter.
            keywords: List of domain-specific keywords.
            corpus: Optional list of ALL articles (including stored ones) to build
                   a robust BM25 index (better IDF). If None, uses 'articles'.
            
        Returns:
            List of articles that passed the relevance threshold, sorted by score.
        """
        if not articles or not keywords:
            return []

        # 1. Prepare Corpus for BM25
        # Use full corpus if provided, otherwise fall back to candidates
        bm25_source_articles = corpus if corpus else articles
        
        tokenized_corpus = []
        for article in bm25_source_articles:
            text = f"{article.title} {article.summary}"
            tokens = self._tokenize(text)
            tokenized_corpus.append(tokens)
            
        # 2. Initialize BM25 Model
        try:
            bm25 = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"[ERROR] Failed to init BM25: {e}")
            return []
            
        # 3. Prepare Query
        # Flatten all keywords into a single bag of tokens for BM25
        query_tokens = []
        for kw in keywords:
            query_tokens.extend(self._tokenize(kw))
            
        # 4. Compute Base BM25 Scores for the SEARCH CORPUS
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Map IDs to their BM25 scores for O(1) lookup
        score_map = {
            bm25_source_articles[i].id: bm25_scores[i] 
            for i in range(len(bm25_source_articles))
        }
        
        filtered_articles = []
        
        # 5. Calculate Scores for All Candidates
        candidate_scores = []
        
        for article in articles:
            # Retrieve BM25 score from the map
            base_score = score_map.get(article.id, 0.0)
            
            # Calculate Phrase Boost
            full_text = f"{article.title} {article.summary}".lower()
            phrase_boost = 0.0
            
            for kw in keywords:
                if " " in kw: 
                    kw_lower = kw.lower()
                    if kw_lower in full_text:
                        phrase_boost += self.PHRASE_BOOST_WEIGHT
            
            phrase_boost = min(phrase_boost, self.MAX_PHRASE_BOOST)
            final_score = base_score + phrase_boost
            
            candidate_scores.append((article, final_score))
            
        # 6. Determine Dynamic Threshold
        # We want top 50% of candidates, but with a safety floor
        if not candidate_scores:
            return []
            
        # Sort by score descending to find the percentile cutoff
        processed_scores = [s for _, s in candidate_scores]
        processed_scores.sort(reverse=True)
        
        # Top 50%
        cutoff_index = int(len(processed_scores) * self.PERCENTILE_CUTOFF)
        # Ensure we keep at least 1 if we have candidates
        cutoff_index = max(1, cutoff_index)
        
        # Dynamic threshold is the score at the cutoff
        # (index is 0-based, so for top 1, index is 0. But cutoff logic: 'keep top N')
        # If cutoff is 1, we want score at index 0. If cutoff is 5, we want score at index 4.
        dynamic_threshold = processed_scores[cutoff_index - 1]
        
        # Apply strict safety floor (0.5) to filter out garbage batches
        final_threshold = max(dynamic_threshold, self.MIN_SCORE_FLOOR)
        
        print(f"      Dynamic Threshold: {final_threshold:.3f} (Top 50% cutoff: {dynamic_threshold:.3f})")

        # 7. Filter and Assign Scores
        for article, score in candidate_scores:
            if score >= final_threshold:
                article.relevance_score = round(score, 3)
                filtered_articles.append(article)
            else:
                article.relevance_score = 0.0
                
        # 8. Sort Results by Relevance
        filtered_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"      BM25+Phrase Filter: {len(filtered_articles)}/{len(articles)} passed (Dynamic Cutoff)")
        
        return filtered_articles
