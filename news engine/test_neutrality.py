
import sys
import os
import time
sys.path.insert(0, os.path.abspath("."))

from src.ai_domain_generator import generate_domain

def test():
    print("============================================================")
    print("TEST: Neutral Domain Generation (Anti-AI Constraint)")
    print("============================================================")
    
    # 1. TECH DOMAIN (Should have AI terms)
    print("\n--- Generating: Technology / NLP ---")
    nlp_data = generate_domain("Technology", "Natural Language Processing")
    print(f"Keywords ({len(nlp_data.get('keywords', []))}):")
    for k in nlp_data.get('keywords', [])[:10]:
        print(f"  - {k}")
    
    # 2. NON-TECH DOMAIN (Should NOT have AI terms)
    print("\n--- Generating: Energy / Wind Power ---")
    wind_data = generate_domain("Energy", "Wind Power")
    keywords = wind_data.get('keywords', [])
    print(f"Keywords ({len(keywords)}):")
    for k in keywords[:10]:
        print(f"  - {k}")
        
    # Validation
    forbidden = ["algorithm", "model", "data", "training", "ai", "machine learning"]
    violations = [k for k in keywords if any(f in k.lower() for f in forbidden)]
    
    if violations:
        print(f"\n[FAIL] Found AI jargon in Energy domain: {violations}")
    else:
        print("\n[PASS] No AI jargon found in Energy domain.")

if __name__ == "__main__":
    test()
