"""
Manual Keyword Test — Hardcoded domains, no LLM.
Uses the same classifier, ranker, and storage as the main engine.
Tests with pre-defined keyword sets to diagnose classification issues.
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory so we can import from src/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Article
from src.collector import collect_all, get_source_count
from src.storage import save_articles, load_articles, update_articles, purge_expired_articles, get_article_count
from src.classifier import DomainClassifier, classify_articles
from src.ranker import rank_articles


# ============================================================================
# HARDCODED DOMAINS — Manual keyword sets (no LLM needed)
# ============================================================================
MANUAL_DOMAINS = {
    "generative_ai": {
        "keywords": [
            "generative ai", "genai", "large language model", "LLM",
            "ChatGPT", "GPT-4", "GPT-5", "Claude", "Gemini", "Copilot",
            "text generation", "image generation", "DALL-E", "Midjourney",
            "Stable Diffusion", "diffusion model", "transformer",
            "prompt engineering", "fine-tuning", "RLHF",
            "foundation model", "multimodal", "hallucination",
            "AI chatbot", "conversational AI", "OpenAI", "Anthropic",
            "text-to-image", "text-to-video", "Sora", "AI-generated"
        ],
        "description": "Generative AI including LLMs, image generation, and foundation models"
    },
    "machine_learning": {
        "keywords": [
            "machine learning", "ML", "supervised learning", "unsupervised learning",
            "reinforcement learning", "neural network", "deep learning",
            "random forest", "gradient boosting", "XGBoost", "classification",
            "regression", "clustering", "feature engineering",
            "training data", "model training", "hyperparameter",
            "overfitting", "cross-validation", "scikit-learn",
            "TensorFlow", "PyTorch", "model accuracy", "prediction",
            "inference", "edge AI", "MLOps", "AutoML"
        ],
        "description": "Machine learning algorithms, frameworks, and model training"
    },
    "natural_language_processing": {
        "keywords": [
            "natural language processing", "NLP", "text mining",
            "sentiment analysis", "named entity recognition", "NER",
            "tokenization", "word embedding", "BERT", "RoBERTa",
            "text classification", "language model", "speech recognition",
            "machine translation", "text summarization", "chatbot",
            "question answering", "information extraction",
            "semantic analysis", "spaCy", "NLTK", "Hugging Face",
            "text analytics", "conversational", "dialogue"
        ],
        "description": "Natural language processing and text analytics"
    },
    "deep_learning": {
        "keywords": [
            "deep learning", "neural network", "convolutional neural network",
            "CNN", "recurrent neural network", "RNN", "LSTM", "GAN",
            "generative adversarial", "autoencoder", "attention mechanism",
            "backpropagation", "gradient descent", "batch normalization",
            "dropout", "activation function", "ResNet", "YOLO",
            "object detection", "image recognition", "computer vision",
            "transfer learning", "pre-trained model", "GPU training",
            "CUDA", "neural architecture"
        ],
        "description": "Deep learning architectures and neural network research"
    },
    "data_science": {
        "keywords": [
            "data science", "data analytics", "big data", "data pipeline",
            "data visualization", "dashboard", "business intelligence",
            "pandas", "numpy", "matplotlib", "Jupyter", "notebook",
            "ETL", "data warehouse", "data lake", "SQL",
            "statistical analysis", "A/B testing", "data-driven",
            "data engineering", "Apache Spark", "Hadoop",
            "data mining", "predictive analytics", "Tableau", "Power BI"
        ],
        "description": "Data science, analytics, and data engineering"
    },
    "ai_ethics": {
        "keywords": [
            "AI ethics", "bias", "fairness", "responsible AI",
            "AI regulation", "AI safety", "AI governance", "deepfake",
            "misinformation", "AI policy", "explainable AI", "XAI",
            "algorithmic bias", "AI transparency", "EU AI Act",
            "AI rights", "surveillance", "facial recognition",
            "privacy", "data protection", "AI accountability",
            "autonomous weapons", "AI alignment", "existential risk"
        ],
        "description": "AI ethics, regulation, safety, and responsible AI"
    },
    "robotics": {
        "keywords": [
            "robot", "robotics", "autonomous vehicle", "self-driving",
            "drone", "humanoid", "robotic arm", "Boston Dynamics",
            "Tesla Bot", "industrial robot", "surgical robot",
            "swarm robotics", "ROS", "actuator", "sensor fusion",
            "LIDAR", "SLAM", "path planning", "manipulation",
            "warehouse robot", "delivery robot", "cobots",
            "automation", "robotic process automation", "RPA"
        ],
        "description": "Robotics, autonomous systems, and automation"
    }
}


# ============================================================================
# MAIN TEST
# ============================================================================
def main():
    print("\n" + "=" * 60)
    print("   MANUAL KEYWORD TEST -- No LLM, Hardcoded Domains")
    print("=" * 60)
    
    # Show domains
    print(f"\n  Loaded {len(MANUAL_DOMAINS)} manual domains:")
    for name, config in MANUAL_DOMAINS.items():
        print(f"    - {name}: {len(config['keywords'])} keywords")
    
    # Step 1: Collect articles
    print(f"\n{'=' * 60}")
    print(f"  Collecting from {get_source_count()} RSS sources...")
    print(f"{'=' * 60}")
    
    new_articles, cutoff_hours = collect_all()
    print(f"  Fetched: {len(new_articles)} articles (cutoff: {cutoff_hours}h)")
    
    # Step 2: Purge old articles
    purged = purge_expired_articles(max_age_hours=cutoff_hours)
    print(f"  Purged: {purged} expired articles")
    
    # Step 3: Save with dedup
    new_count = save_articles(new_articles)
    total = get_article_count()
    print(f"  New: {new_count} | Total in storage: {total}")
    
    # Step 4: Classify ALL articles with manual domains
    print(f"\n{'=' * 60}")
    print(f"  Classifying ALL {total} articles with manual keywords...")
    print(f"{'=' * 60}")
    
    all_articles = load_articles()
    classified = classify_articles(all_articles, threshold=0.15, domains=MANUAL_DOMAINS)
    update_articles(classified)
    
    # Step 5: Count matches per domain
    print(f"\n  Classification Results:")
    print(f"  {'-' * 50}")
    
    domain_counts = {}
    unmatched = 0
    for a in classified:
        if a.primary_domain:
            domain_counts[a.primary_domain] = domain_counts.get(a.primary_domain, 0) + 1
        else:
            unmatched += 1
    
    for domain_name in MANUAL_DOMAINS:
        count = domain_counts.get(domain_name, 0)
        bar = "#" * min(count, 40)
        print(f"    {domain_name:<30} {count:>4} articles  {bar}")
    
    print(f"    {'(unclassified)':<30} {unmatched:>4} articles")
    print(f"    {'TOTAL':<30} {len(classified):>4} articles")
    
    # Step 6: Show top 5 articles per domain with scores
    for domain_name in MANUAL_DOMAINS:
        matching = [a for a in classified if a.primary_domain == domain_name]
        if not matching:
            continue
        
        ranked = rank_articles(matching)
        top = ranked[:5]
        
        print(f"\n  {'=' * 60}")
        print(f"  TOP 5 -- {domain_name} ({len(matching)} total matches)")
        print(f"  {'=' * 60}")
        
        for i, (article, score) in enumerate(top, 1):
            print(f"\n    [{i}] {article.title[:80]}")
            print(f"        Score: {score:.3f} | Source: {article.source}")
            print(f"        Date:  {article.published_date[:19]}")
    
    # Step 7: Debug — show sample scores for first 3 articles
    print(f"\n  {'=' * 60}")
    print(f"  DEBUG: Classifier scores for 3 sample articles")
    print(f"  {'=' * 60}")
    
    classifier = DomainClassifier(threshold=0.15, domains=MANUAL_DOMAINS)
    samples = all_articles[:3]
    
    for article in samples:
        print(f"\n    Article: {article.title[:70]}...")
        scores = classifier.classify_with_scores(article)
        for domain, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            marker = " <<" if score >= 0.15 else ""
            print(f"      {domain:<30} {score:.4f}{marker}")
    
    print(f"\n{'=' * 60}")
    print(f"  Test complete.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
