"""Domain definitions for article classification.

This module provides dynamic domain configuration built from AI-generated
keywords at runtime, replacing the former static hardcoded taxonomy.

Usage:
    from src.domains import build_domains_from_user_input, get_domain_names

    DOMAINS = build_domains_from_user_input("technology", "artificial intelligence")
    names = get_domain_names(DOMAINS)
"""

from typing import Dict, List

from src.ai_domain_generator import generate_domain


# Runtime domain store — populated by build_domains_from_user_input()
DOMAINS: Dict[str, Dict] = {}


def build_domains_from_user_input(domain: str, subdomain: str) -> Dict[str, Dict]:
    """
    Build dynamic DOMAINS dictionary using AI-generated keywords.

    Args:
        domain: Primary domain category (e.g., "technology")
        subdomain: Specific subdomain focus (e.g., "artificial intelligence")

    Returns:
        Dict in the shape expected by DomainClassifier:
        {
            "<domain_name>": {
                "keywords": List[str],
                "description": str
            }
        }
    """
    global DOMAINS

    generated = generate_domain(domain, subdomain)

    DOMAINS = {
        generated["domain_name"]: {
            "keywords": generated["keywords"],
            "description": generated["description"]
        }
    }

    return DOMAINS


def get_domain_names(domains_dict: Dict[str, Dict] = None) -> List[str]:
    """
    Get list of all domain names.

    Args:
        domains_dict: Optional domains dictionary. Falls back to module-level DOMAINS.

    Returns:
        List of domain name strings.
    """
    source = domains_dict if domains_dict is not None else DOMAINS
    return list(source.keys())
