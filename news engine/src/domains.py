"""Domain definitions for article classification."""

from typing import Dict, List

# Domain configurations with keywords and descriptions
DOMAINS: Dict[str, Dict] = {
    "generative_ai": {
        "keywords": [
            "GPT", "LLM", "large language model", "diffusion", "generative",
            "ChatGPT", "DALL-E", "Stable Diffusion", "transformer", "prompt",
            "text generation", "image generation", "Claude", "Gemini", "Llama",
            "fine-tuning", "RLHF", "instruction tuning", "foundation model"
        ],
        "description": "Text and image generation models, LLMs, and generative systems"
    },
    "machine_learning": {
        "keywords": [
            "neural network", "deep learning", "training", "model",
            "supervised", "unsupervised", "classification", "regression",
            "gradient descent", "backpropagation", "CNN", "RNN", "LSTM",
            "reinforcement learning", "loss function", "optimizer", "epoch",
            "overfit", "underfit", "validation", "accuracy", "precision"
        ],
        "description": "Machine learning algorithms, training, and model development"
    },
    "data_science": {
        "keywords": [
            "data analysis", "visualization", "pandas", "statistics",
            "analytics", "dataset", "preprocessing", "feature engineering",
            "exploratory", "correlation", "hypothesis", "A/B test",
            "dashboard", "metrics", "KPI", "data pipeline", "ETL"
        ],
        "description": "Data processing, analysis, and business intelligence"
    },
    "nlp": {
        "keywords": [
            "natural language", "NLP", "text", "language model", "sentiment",
            "named entity", "NER", "tokenization", "embedding", "word2vec",
            "BERT", "parsing", "translation", "summarization", "question answering",
            "chatbot", "conversational", "speech", "semantic", "syntax"
        ],
        "description": "Natural language processing and text understanding"
    },
    "ai_business": {
        "keywords": [
            "startup", "funding", "investment", "valuation", "acquisition",
            "enterprise", "revenue", "billion", "million", "raises",
            "Series A", "Series B", "IPO", "CEO", "company", "business",
            "market", "industry", "partnership", "deal", "venture"
        ],
        "description": "AI industry news, funding, and business developments"
    },
    "robotics": {
        "keywords": [
            "robot", "robotics", "autonomous", "drone", "self-driving",
            "manipulation", "sensor", "actuator", "navigation", "SLAM",
            "humanoid", "automation", "control system", "motor", "gripper",
            "perception", "motion planning", "hardware", "embodied"
        ],
        "description": "Robotics, autonomous systems, and physical AI"
    }
}


def get_domain_names() -> List[str]:
    """Get list of all domain names."""
    return list(DOMAINS.keys())


def get_domain_keywords(domain: str) -> List[str]:
    """Get keywords for a specific domain."""
    if domain in DOMAINS:
        return DOMAINS[domain]["keywords"]
    return []


def get_all_keywords() -> Dict[str, List[str]]:
    """Get all domain keywords as a dictionary."""
    return {name: config["keywords"] for name, config in DOMAINS.items()}
