# News Engine 📰

A modular news aggregation and filtering engine that collects AI/ML news from RSS feeds, classifies them into domains, and ranks by relevance.

## Features

- 🔄 **Collect** articles from 8 free RSS sources (MIT Tech Review, arXiv, Google AI Blog, etc.)
- 🏷️ **Classify** into domains: Generative AI, Machine Learning, NLP, Data Science, AI Business, Robotics
- 📊 **Rank** by relevance (recency + source reliability + domain match)
- 🤖 **Agent-based** pipeline orchestration
- 💬 **Interactive** menu-driven CLI

## Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/news-engine.git
cd news-engine

# Install dependencies
pip install -r requirements.txt

# Run interactive mode
python main.py
```

## Usage

### Interactive Mode (Recommended for demos)
```bash
python main.py
# or
python main.py --interactive
```

### Command Line Mode
```bash
# Collect articles
python main.py --collect

# Classify into domains
python main.py --classify

# Search by domain
python main.py --domain generative_ai --rank --limit 10

# Search by keyword
python main.py --filter "LLM" --rank

# Show statistics
python main.py --stats
```

### Agent Mode (Pipeline orchestration)
```bash
python main.py --agent --collect --classify --domain generative_ai --rank
```

## Project Structure

```
news-engine/
├── src/
│   ├── collector.py      # RSS feed fetching
│   ├── storage.py        # JSON persistence
│   ├── classifier.py     # Domain classification
│   ├── ranker.py         # Relevance scoring
│   ├── filter.py         # Keyword/domain filtering
│   ├── domains.py        # Domain definitions
│   ├── models.py         # Article dataclass
│   └── agents/           # Agent-based orchestration
│       ├── base.py
│       ├── ingestion.py
│       ├── processing.py
│       ├── classification.py
│       ├── ranking.py
│       ├── query.py
│       └── pipeline.py
├── data/                 # Stored articles (auto-generated)
├── main.py               # Entry point
├── requirements.txt
└── README.md
```

## Domains

| Domain | Description |
|--------|-------------|
| generative_ai | LLMs, GPT, diffusion models |
| machine_learning | Neural networks, training |
| nlp | Text processing, NER, sentiment |
| data_science | Analytics, visualization |
| ai_business | Funding, startups, industry |
| robotics | Autonomous systems |

## License

MIT
