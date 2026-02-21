"""Quick test: compare keywords for two different subdomains to verify differentiation."""
import sys
sys.path.insert(0, ".")

from src.ai_domain_generator import generate_domain
import json

print("=" * 60)
print("TEST: Subdomain Differentiation")
print("=" * 60)

# Test 1: NLP
print("\n--- Generating: generative ai / nlp ---")
r1 = generate_domain("generative ai", "nlp")
print(f"Domain: {r1['domain_name']}")
print(f"Keywords ({len(r1['keywords'])}):")
for kw in r1["keywords"]:
    print(f"  - {kw}")

# Test 2: Machine Learning
print("\n--- Generating: data science / machine learning ---")
r2 = generate_domain("data science", "machine learning")
print(f"Domain: {r2['domain_name']}")
print(f"Keywords ({len(r2['keywords'])}):")
for kw in r2["keywords"]:
    print(f"  - {kw}")

# Compare overlap
s1 = set(k.lower() for k in r1["keywords"])
s2 = set(k.lower() for k in r2["keywords"])
overlap = s1 & s2

print(f"\n{'=' * 60}")
print(f"NLP keywords:   {len(r1['keywords'])}")
print(f"ML keywords:    {len(r2['keywords'])}")
print(f"Overlap:        {len(overlap)} keywords")
if overlap:
    print(f"Overlapping:    {overlap}")
else:
    print("NO OVERLAP -- perfect differentiation!")
print(f"Overlap %:      {len(overlap)/min(len(s1),len(s2))*100:.0f}%")
print(f"{'=' * 60}")
