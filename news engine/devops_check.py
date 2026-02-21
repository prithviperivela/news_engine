
import sys
import os
import time

# Add root to path so we can import src
sys.path.append(os.getcwd())

try:
    from src.ai_domain_generator import generate_domain
    from src.collector import RSS_FEEDS
    from src.ranker import SOURCE_RELIABILITY
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def check_devops_support():
    print("=== 1. Testing Keyword Generation for 'Software / DevOps' ===")
    try:
        # We need the API key from .env, but the module loads it.
        # Assuming the environment is set up correctly as verified previously.
        result = generate_domain("software", "devops")
        keywords = result.get("keywords", [])
        print(f"\n[OK] Generated {len(keywords)} keywords.")
        print(f"Sample: {keywords[:10]}")
        
        # Check for key DevOps terms
        expected = ["kubernetes", "docker", "ci/cd", "pipeline", "jenkins", "terraform", "ansible", "devops"]
        found = [k for k in keywords if any(e in k for e in expected)]
        print(f"\n[Analysis] Found {len(found)} core DevOps terms in keywords: {found[:5]}...")
        
    except Exception as e:
        print(f"\n[FAIL] Keyword generation failed: {e}")

    print("\n=== 2. Testing RSS Feed Coverage ===")
    # specific devops substrings
    devops_terms = ["devops", "cloud", "sre", "infrastructure", "platform", "engineering"]
    
    relevant_feeds = []
    for name, url in RSS_FEEDS.items():
        score = 0
        name_lower = name.lower()
        if any(t in name_lower for t in devops_terms):
            relevant_feeds.append(name)
    
    print(f"Found {len(relevant_feeds)} potentially relevant feeds in existing configuration:")
    for f in relevant_feeds:
        print(f" - {f}")

    if len(relevant_feeds) < 3:
        print("\n[WARNING] Very few explicit DevOps feeds found. Content may be scarce.")

    print("\n=== 3. Testing Ranker Source Tiers ===")
    # Check if we have specific high-tier devops sources
    tier_matches = []
    for source, score in SOURCE_RELIABILITY.items():
        if any(t in source.lower() for t in devops_terms):
            tier_matches.append(f"{source} ({score})")
            
    print(f"Ranked sources matching DevOps terms: {tier_matches}")

if __name__ == "__main__":
    check_devops_support()
