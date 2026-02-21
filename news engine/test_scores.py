
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from src.classifier import DomainClassifier
from src.models import Article

# Mock domains dict with "Hybrid" style keywords
domains_dict = {
    "nlp": {
        "keywords": ["chatgpt", "large language model", "bert", "transformer architecture", "openai"],
        "description": "NLP"
    }
}

classifier = DomainClassifier(threshold=0.15, domains=domains_dict)

# Case 1: Strong match (3 keywords: ChatGPT, LLM, Transformer)
a1 = Article(
    id="1",
    title="ChatGPT and Large Language Models using Transformer architecture",
    source="Test Source",
    published_date="2024-01-01",
    url="http://test.com/1",
    summary="OpenAI released a new BERT model."
)

# Case 2: Weak match (1 keyword: ChatGPT)
a2 = Article(
    id="2",
    title="Basic intro to ChatGPT",
    source="Test Source",
    published_date="2024-01-01",
    url="http://test.com/2",
    summary="It is a chatbot."
)

print(f"Threshold: {classifier.threshold}")
print("\n--- Test Scores ---")
scores1 = classifier.classify(a1)
# Note: Article doesn't store score directly until we assign it, so we check the return value
print(f"Article 1 (Strong - 3 matches): {scores1} (Assigned: {a1.relevance_score})")

scores2 = classifier.classify(a2)
print(f"Article 2 (Weak - 1 match): {scores2} (Assigned: {a2.relevance_score})")
