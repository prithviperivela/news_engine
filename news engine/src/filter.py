"""Keyword and domain-based article filtering."""

from typing import List

from src.models import Article


def filter_by_keyword(articles: List[Article], keyword: str) -> List[Article]:
    """
    Filter articles that contain the keyword in title or summary.
    Case-insensitive matching.
    """
    keyword_lower = keyword.lower()
    
    filtered = []
    for article in articles:
        text = f"{article.title} {article.summary}".lower()
        if keyword_lower in text:
            filtered.append(article)
    
    return filtered


def filter_by_keywords(articles: List[Article], keywords: List[str]) -> List[Article]:
    """
    Filter articles matching ANY of the provided keywords.
    """
    if not keywords:
        return articles
    
    keywords_lower = [k.lower() for k in keywords]
    
    filtered = []
    for article in articles:
        text = f"{article.title} {article.summary}".lower()
        if any(kw in text for kw in keywords_lower):
            filtered.append(article)
    
    return filtered


def filter_by_domain(articles: List[Article], domain: str) -> List[Article]:
    """
    Filter articles that have been tagged with a specific domain.
    Articles must be classified first using the classifier module.
    """
    domain_lower = domain.lower().replace(" ", "_")
    
    filtered = []
    for article in articles:
        if domain_lower in article.domains:
            filtered.append(article)
    
    return filtered


def filter_by_domains(articles: List[Article], domains: List[str]) -> List[Article]:
    """
    Filter articles matching ANY of the provided domains.
    """
    if not domains:
        return articles
    
    domains_lower = [d.lower().replace(" ", "_") for d in domains]
    
    filtered = []
    for article in articles:
        if any(d in article.domains for d in domains_lower):
            filtered.append(article)
    
    return filtered

