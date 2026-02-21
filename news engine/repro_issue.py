
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from src.classifier import DomainClassifier
from src.models import Article

# Mock Article (Glean)
# Based on user description: "Agentic artificial intelligence startup Glean Technologies Inc...."
glean_article = Article(
    id="test-1",
    title="Glean adds a bit more sheen to its enterprise AI assistant",
    summary="Agentic artificial intelligence startup Glean Technologies Inc. said today it’s boosting the capabilities of its digital coworker Glean Assistant, making it much more customizable than before.",
    url="http://test.com",
    published_date="2026-02-18T00:00:00Z",
    source="TechCrunch"
)

# Mock Domain Config (Geopolitics/USA)
# Keywords provided by user
usa_keywords = [
    "Congressional Hearing",
    "Federal Reserve",
    "US Senate",
    "National Security",
    "Election Cycle",
    "Trade Agreement",
    "Supreme Court",
    "CIA",
    "FBI",
    "Diplomatic Relations",
    "Immigration Reform",
    "US Military",
    "NATO Alliance",
    "State Department",
    "White House",
    "Pentagon",
    "US Economy",
    "Foreign Policy",
    "Bipartisan Bill",
    "Government Shutdown",
    "Presidential Election",
    "Border Control",
    "Terrorism Alert",
    "Cybersecurity Threat",
    "US Diplomacy",
    "International Cooperation",
    "UN General Assembly",
    "G7 Summit",
    "Global Leadership",
    "Geopolitical Tensions",
    "National Intelligence",
    "US Ambassador",
    "Embassy Row",
    "International Trade",
    "Sanctions Relief",
    "Nuclear Nonproliferation",
    "US Secretary",
    "Defense Spending",
    "Intelligence Community",
    "Homeland Security",
    "US Agency",
    "Global Governance",
    "International Law"
]

domains_config = {
    "usa": {
        "keywords": usa_keywords
    }
}

print("--- Testing Classification Logic ---")
classifier = DomainClassifier(domains=domains_config)
scores = classifier.classify_with_scores(glean_article)
print(f"Scores: {scores}")

# Determine 'why'
print("\n--- detailed breakdown ---")
text = f"{glean_article.title} {glean_article.summary}"
kw_score, matches = classifier._keyword_score(text, "usa")
tf_score = classifier._term_frequency_score(text, "usa")

print(f"Keyword Score (Exact match): {kw_score} (Matches: {matches})")
print(f"TF Score (Token match): {tf_score}")
print(f"Combined Score: {kw_score * 0.7 + tf_score * 0.3}")

# Analyze TF matches
print("\n--- TF Analysis ---")
tokens = classifier._tokenize(text)
print(f"Tokens: {tokens}")
from collections import Counter
token_counts = Counter(tokens)
total_keyword_freq = 0
matched_tokens = []
for keyword in usa_keywords:
    kw_tokens = keyword.lower().split()
    for kw_token in kw_tokens:
        if kw_token in token_counts:
            count = token_counts[kw_token]
            total_keyword_freq += count
            matched_tokens.append(f"{kw_token} (from '{keyword}')")

print(f"Total Keyword Freq: {total_keyword_freq}")
print(f"Matched Tokens: {matched_tokens}")
