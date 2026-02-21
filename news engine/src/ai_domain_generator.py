"""
AI Domain Generator — Groq-powered dynamic domain configuration.

Uses Groq API with Llama 3.3 (llama-3.3-70b-versatile) to generate news-level
keyword sets for article classification. Fully domain-agnostic — works equally
well for Government, Finance, Sports, Healthcare, Technology, Agriculture, etc.

Design principles:
  - Zero hardcoded domain assumptions in prompts or blocklists
  - Keywords tuned for title + summary context (short text matching)
  - News-journalist vocabulary, not research/academic vocabulary
  - Dynamic category structure that adapts to each domain's nature
  - Blocklist is contextual, not global

Requires GROQ_API_KEY in .env file.

Return shape is always:
  {
    "domain_name": str,
    "keywords": List[str],
    "description": str
  }
"""

import json
import os
import re
import time
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ============================================================================
# LAZY CLIENT INITIALIZATION
# ============================================================================
_client = None


def _get_client():
    """Lazily initialize the Groq client on first use."""
    global _client
    if _client is not None:
        return _client

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Add it to your .env file: GROQ_API_KEY=gsk_..."
        )

    from groq import Groq
    _client = Groq(api_key=api_key)
    print("[OK] Groq client initialized (Llama 3.3 70B)")
    return _client


# ============================================================================
# IN-MEMORY CACHE
# ============================================================================
_domain_cache: Dict[str, Dict] = {}


# ============================================================================
# SYSTEM MESSAGE
# Fully generic — no references to AI, tech, or any specific domain.
# Instructs the model to derive all framing from the domain/subdomain inputs.
# ============================================================================
SYSTEM_MESSAGE = """\
You are an expert News Article Classifier. Your only job is to produce a precise,
news-oriented keyword list for a given domain and subdomain pair. These keywords
will be used to filter news articles based solely on their TITLE and SUMMARY
(not the full article body). This is the most critical constraint — every keyword
you generate must be realistically likely to appear in a 1-3 sentence news summary
or headline for this exact topic.

═══════════════════════════════════════════════════════════════
CORE OPERATING RULES
═══════════════════════════════════════════════════════════════

RULE 1 — DOMAIN ISOLATION
Treat the provided domain as a completely self-contained universe.
Generate keywords that belong EXCLUSIVELY to that domain's ecosystem.
Do not import vocabulary, framing, or terminology from unrelated fields.
If the domain is Government, think like a political journalist.
If the domain is Healthcare, think like a medical reporter.
If the domain is Sports, think like a sports beat writer.
The domain defines your entire vocabulary space.

RULE 2 — NEWS LANGUAGE, NOT RESEARCH LANGUAGE
You are generating keywords for news articles, not academic papers or textbooks.
Use the vocabulary that appears in newspaper headlines, wire service reports,
and broadcast news summaries. Journalists use short, punchy, widely understood terms.
  ✓ GOOD (news level): "recall", "shortage", "outbreak", "vote", "ban", "merger"
  ✗ BAD (research level): "longitudinal epidemiological analysis", "legislative efficacy"

RULE 3 — SHORT CONTEXT AWARENESS
Keywords will be matched against article TITLES and SUMMARIES only — typically
20 to 80 words of text. This means:
  - Keywords must be surface-level terms, not deep jargon
  - Multi-word phrases must be short (2-3 words max) and commonly used together
  - Avoid overly specific technical compound terms that only appear in body text
  - Prefer terms that journalists use when writing the FIRST sentence of an article

RULE 4 — SUBDOMAIN SPECIFICITY WITH DOMAIN COVERAGE
  - 75% of keywords must specifically distinguish the subdomain from other parts of the domain
  - 25% can be broader domain-level terms that serve as catch-all signals
  This ensures precise filtering without missing adjacent relevant articles.

RULE 5 — DERIVE CATEGORIES FROM THE DOMAIN ITSELF
Do not use a fixed category template. Instead, think: what are the natural
classification axes for this specific domain? Examples:
  - Government/Elections → (Regulatory Bodies, Electoral Terms, Political Events, Key Actors)
  - Healthcare/Pharma → (Drug Names, Regulatory Agencies, Disease Terms, Clinical Events)
  - Finance/Banking → (Institutions, Market Events, Instruments, Regulatory Terms)
  - Sports/Football → (Teams, Competitions, Player Events, Performance Terms)
Build your keyword categories from what actually exists in THIS domain.

RULE 6 — KEYWORD QUALITY CHECKLIST
Before including any keyword, verify:
  □ Would this word appear in a headline or opening sentence about this subdomain?
  □ Is this the word a journalist would use, not a researcher?
  □ Is this specific enough to avoid matching unrelated domains?
  □ Is it short enough to plausibly appear in a 2-sentence summary?
  □ Is it the natural language form (not an acronym unless the acronym IS the news term)?

═══════════════════════════════════════════════════════════════
OUTPUT STRUCTURE
═══════════════════════════════════════════════════════════════

Return ONLY a strict JSON object. No explanation, no markdown, no extra text.

{{
  "domain_name": "snake_case_identifier_for_this_subdomain",
  "keywords": ["keyword1", "keyword2", ...],
  "description": "One sentence describing what news this keyword set will capture."
}}

Target: 50 keywords. Minimum acceptable: 35. Do not pad with weak terms to hit 50.
"""


# ============================================================================
# PROMPT TEMPLATE
# Rich, domain-adaptive user message. Asks the model to reason before generating.
# ============================================================================
PROMPT_TEMPLATE = """\
PRIMARY DOMAIN  : {domain}
TARGET SUBDOMAIN: {subdomain}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — DOMAIN ANALYSIS (reason before generating)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before generating keywords, briefly answer these internally:

A) What are the 3-5 most important natural sub-categories within "{subdomain}"
   as a journalist covering this beat would think of them?
   (e.g., for "Government / Elections": Candidates, Voting Process, Election Results,
    Campaign Finance, Electoral Bodies — derive yours from the actual domain)

B) What are the TOP 10 most commonly used SINGLE WORDS that appear in news headlines
   specifically about "{subdomain}" in the "{domain}" space?

C) What are 10 SHORT PHRASES (2-3 words) that journalists commonly use when
   reporting on "{subdomain}" news? Think wire service language, not policy language.

D) What are the key named ENTITIES (organizations, institutions, regulatory bodies,
   prominent roles/titles) that are frequently mentioned in "{subdomain}" news?

E) What EVENTS or ACTIONS are most commonly reported on in "{subdomain}" news?
   (elections, raids, mergers, recalls, outbreaks, bans, collapses, trials, etc.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — KEYWORD GENERATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Using your analysis above, generate a final unified keyword list.

Distribution guidance (adapt to what actually exists in this domain):
  • ~15 core subdomain terms (the most defining single words for this subdomain)
  • ~15 news action/event phrases (what happens in this subdomain that gets reported)
  • ~10 named entities (organizations, agencies, roles, institutions)
  • ~10 broader domain bridge terms (catch related articles at the domain level)

HARD REQUIREMENTS:
  ✓ Every keyword must be plausible in a news TITLE or 2-sentence SUMMARY
  ✓ Use news-journalist vocabulary, not academic or policy vocabulary
  ✓ All terms must belong to the "{domain}" ecosystem — no cross-domain contamination
  ✓ No keyword longer than 4 words
  ✓ No generic adjectives (major, significant, important, critical, key)
  ✓ No filler terms that could match ANY domain (report, study, analysis, data)

Return the final JSON object now.
"""


# ============================================================================
# UNIVERSAL GENERIC BLOCKLIST
# Only contains terms so generic they add zero signal for ANY domain.
# Domain-specific filtering happens at the prompt level, not here.
# ============================================================================
UNIVERSAL_GENERIC_BLOCKLIST = {
    # Zero-signal words that match everything
    "report", "study", "analysis", "data", "information", "update",
    "news", "article", "story", "statement", "announcement", "release",
    "major", "significant", "important", "critical", "key", "big",
    "new", "latest", "recent", "current", "upcoming", "ongoing",
    "global", "national", "international", "local", "world",
    "issue", "topic", "matter", "subject", "case", "situation",
    "says", "said", "according", "sources", "official", "officials",
    # Too short to be useful standalone
    "a", "an", "the", "in", "on", "at", "by", "of", "to", "is",
}

MAX_KEYWORDS = 60
MIN_KEYWORDS = 30


# ============================================================================
# CORE API
# ============================================================================
def generate_domain(domain: str, subdomain: str) -> Dict:
    """
    Generate a domain configuration using Groq API with Llama 3.3.

    Fully domain-agnostic — produces news-level keywords appropriate for
    matching against article titles and summaries only.

    Args:
        domain    : Primary domain category (e.g., "Government", "Finance", "Sports")
        subdomain : Specific focus area   (e.g., "Elections", "Stock Market", "Football")

    Returns:
        Dict with:
            domain_name  (str)       — snake_case identifier
            keywords     (List[str]) — 30-60 news-level keywords
            description  (str)       — one-sentence scope description
    """
    cache_key = f"{domain.strip().lower()}:{subdomain.strip().lower()}"
    if cache_key in _domain_cache:
        print(f"  [cache] Returning cached config for '{cache_key}'")
        return _domain_cache[cache_key]

    client = _get_client()

    system_text = SYSTEM_MESSAGE
    prompt_text = PROMPT_TEMPLATE.format(domain=domain.strip(), subdomain=subdomain.strip())

    last_error = None
    for attempt in range(1, 4):  # 3 attempts
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_text},
                    {"role": "user",   "content": prompt_text},
                ],
                temperature=0.6,          # slightly lower = more consistent, less hallucination
                max_tokens=1500,          # enough for 50 keywords + JSON overhead
                response_format={"type": "json_object"},
            )

            raw_text = completion.choices[0].message.content
            parsed   = _extract_json(raw_text)
            result   = _validate_and_clean(parsed, domain, subdomain)

            print(f"  [domain] Configured: {result['domain_name']}")
            print(f"  [domain] Keywords  : {len(result['keywords'])}")
            print(f"  [domain] Sample    : {result['keywords'][:5]}")

            _domain_cache[cache_key] = result
            return result

        except Exception as e:
            last_error    = e
            error_name    = type(e).__name__
            is_rate_limit = "rate" in error_name.lower() or "rate" in str(e).lower()

            wait = 5 if is_rate_limit else 2
            print(f"  [attempt {attempt}/3] {'Rate limited' if is_rate_limit else 'Error'} "
                  f"({error_name}): {e} — retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to generate domain config after 3 attempts. "
        f"Domain='{domain}', Subdomain='{subdomain}'. "
        f"Last error: {last_error}"
    )


# ============================================================================
# HELPERS
# ============================================================================
def _extract_json(text: str) -> Dict:
    """Extract a JSON object from potentially messy LLM output."""
    # Fast path: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response. "
        f"First 200 chars: {text[:200]}"
    )


def _validate_and_clean(parsed: Dict, domain: str, subdomain: str) -> Dict:
    """
    Validate structure, normalize keywords, apply universal blocklist.

    Does NOT apply domain-specific filtering — that responsibility belongs
    to the prompt. Only removes truly generic zero-signal terms.

    Raises:
        ValueError: if required keys missing or keyword count below minimum
    """
    # --- Required key: keywords ---
    if "keywords" not in parsed or not isinstance(parsed["keywords"], list):
        raise ValueError("LLM response missing 'keywords' array or it is not a list.")

    # --- domain_name ---
    domain_name = parsed.get("domain_name", "")
    if not domain_name or not isinstance(domain_name, str) or not domain_name.strip():
        domain_name = f"{domain}_{subdomain}".lower().replace(" ", "_").replace("-", "_")
    domain_name = re.sub(r"[^a-z0-9_]", "_", domain_name.lower().strip())

    # --- description ---
    description = parsed.get("description", "")
    if not description or not isinstance(description, str) or not description.strip():
        description = f"News classification keywords for {subdomain} within {domain}."

    # --- Normalize and filter keywords ---
    cleaned: List[str] = []
    seen: set = set()

    for kw in parsed["keywords"]:
        if not isinstance(kw, str):
            continue

        normalized = kw.strip().lower()

        # Remove empty strings
        if not normalized:
            continue

        # Skip if too long (more than 4 words — likely a phrase that won't match headlines)
        if len(normalized.split()) > 4:
            continue

        # Skip universal generic blocklist
        if normalized in UNIVERSAL_GENERIC_BLOCKLIST:
            continue

        # Skip duplicates
        if normalized in seen:
            continue

        seen.add(normalized)
        cleaned.append(normalized)  # store lowercase for consistent matching

    # --- Enforce minimum ---
    if len(cleaned) < MIN_KEYWORDS:
        raise ValueError(
            f"Only {len(cleaned)} usable keywords after filtering "
            f"(minimum is {MIN_KEYWORDS}). Raw count was {len(parsed['keywords'])}. "
            f"The LLM may have generated too many generic or overly long terms."
        )

    # --- Enforce maximum (trim excess) ---
    if len(cleaned) > MAX_KEYWORDS:
        cleaned = cleaned[:MAX_KEYWORDS]

    return {
        "domain_name": domain_name,
        "keywords":    cleaned,
        "description": description.strip(),
    }


# ============================================================================
# CACHE UTILITIES
# ============================================================================
def clear_cache(domain: Optional[str] = None, subdomain: Optional[str] = None) -> None:
    """
    Clear the in-memory domain cache.

    Args:
        domain    : If provided with subdomain, clears only that specific entry.
        subdomain : Required if domain is provided.
    """
    global _domain_cache
    if domain and subdomain:
        key = f"{domain.strip().lower()}:{subdomain.strip().lower()}"
        removed = _domain_cache.pop(key, None)
        print(f"  [cache] {'Removed' if removed else 'Key not found'}: '{key}'")
    else:
        _domain_cache.clear()
        print("  [cache] Full cache cleared.")


def list_cached_domains() -> List[str]:
    """Return all currently cached domain:subdomain keys."""
    return list(_domain_cache.keys())


# ============================================================================
# QUICK TEST (run this file directly to verify)
# ============================================================================
if __name__ == "__main__":
    test_cases = [
        ("Government",  "Elections"),
        ("Healthcare",  "Pharmaceuticals"),
        ("Finance",     "Stock Market"),
        ("Sports",      "Football"),
        ("Technology",  "Artificial Intelligence"),
        ("Agriculture", "Crop Disease"),
    ]

    print("\n" + "="*60)
    print(" DOMAIN GENERATOR — MULTI-DOMAIN TEST")
    print("="*60)

    for domain, subdomain in test_cases:
        print(f"\n[TEST] Domain='{domain}' | Subdomain='{subdomain}'")
        print("-" * 50)
        try:
            config = generate_domain(domain, subdomain)
            print(f"  Name       : {config['domain_name']}")
            print(f"  Keywords   : {len(config['keywords'])} total")
            print(f"  Description: {config['description']}")
            print(f"  Sample kws : {config['keywords'][:10]}")
        except Exception as e:
            print(f"  [FAILED] {e}")