"""News Engine — Single Pipeline Entry Point.

Workflow:
    Phase 1: Session Initialization
        1. Prompt user for domain + subdomain
        2. Generate keywords via Groq LLM (Llama 3.3 70B)
        3. Build runtime DOMAINS dictionary
        4. Initialize DomainFilter (once, cached)

    Phase 2: Continuous Pipeline Loop (every 15 minutes)
        a. Fetch articles from RSS feeds (with freshness cutoff)
        b. Auto-purge expired articles from storage
        c. Deduplicate and save new articles
        d. Filter newly added articles (BM25 + Phrase Boost)
        e. Select matched articles
        f. Rank by combined score
        g. Display top articles
        h. Sleep 15 minutes

    Phase 3: Graceful Shutdown (Ctrl+C)
"""

import json
import signal
import sys
import time
import traceback
from datetime import datetime

from src.collector import collect_all, get_source_count
from src.storage import save_articles, load_articles, update_articles, purge_expired_articles, get_article_count
from src.filtering import DomainFilter
from src.domains import build_domains_from_user_input
from src.ranker import rank_articles


# ============================================================================
# CONFIGURATION
# ============================================================================
POLL_INTERVAL = 900  # 15 minutes in seconds
TOP_N_DISPLAY = 20   # Number of top articles to display per cycle


# ============================================================================
# PHASE 1 — SESSION INITIALIZATION
# ============================================================================
def initialize_session():
    """
    Prompt user for domain/subdomain, generate keywords, build filter.
    
    Returns:
        (domains_dict, filter_engine, domain_name)
    """
    print("\n" + "=" * 60)
    print("   NEWS ENGINE -- Session Initialization")
    print("=" * 60)
    
    # Step 1: User input
    try:
        user_domain = input("\n  Enter primary domain: ").strip()
        user_subdomain = input("  Enter subdomain: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  Using default: technology / artificial intelligence")
        user_domain = "technology"
        user_subdomain = "artificial intelligence"
    
    if not user_domain:
        user_domain = "technology"
    if not user_subdomain:
        user_subdomain = "artificial intelligence"
    
    print(f"\n  Domain: {user_domain}")
    print(f"  Subdomain: {user_subdomain}")
    
    # Step 2 & 3: Generate keywords via LLM and build DOMAINS dict
    print("\n  [*] Generating domain keywords via Groq LLM...")
    domains_dict = build_domains_from_user_input(user_domain, user_subdomain)
    
    domain_name = list(domains_dict.keys())[0]
    keywords = domains_dict[domain_name]["keywords"]
    description = domains_dict[domain_name]["description"]
    
    print(f"\n  [OK] Domain: {domain_name}")
    print(f"  [OK] Keywords generated: {len(keywords)}")
    print(f"  [OK] Description: {description}")
    print(f"\n  Keywords: {json.dumps(keywords, indent=4)}")
    
    # Step 4: Initialize filter engine
    filter_engine = DomainFilter()
    print(f"\n  [OK] Filter engine initialized (BM25 + Hybrid Phrase Boosting)")
    print("=" * 60)
    
    return domains_dict, filter_engine, domain_name


# ============================================================================
# PHASE 2 — SINGLE PIPELINE CYCLE
# ============================================================================
def run_pipeline_cycle(filter_engine, domain_name, domains_dict, cycle_number):
    """
    Execute one full pipeline cycle:
        Collect → Purge → Save → Filter → Rank → Display
    
    Args:
        filter_engine: Pre-initialized DomainFilter
        domain_name: Active domain name to filter for
        domains_dict: Active domains dictionary
        cycle_number: Current cycle number for display
    """
    cycle_start = datetime.now()
    
    print(f"\n{'=' * 60}")
    print(f"  CYCLE {cycle_number} -- {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}")
    
    # Step (a): Fetch articles from RSS feeds (with freshness cutoff)
    print(f"\n  [a] Fetching articles from {get_source_count()} RSS sources...")
    new_articles, cutoff_hours = collect_all()
    print(f"      Fetched: {len(new_articles)} articles (freshness cutoff: {cutoff_hours}h)")
    
    # Step (b): Auto-purge expired articles — aligned with freshness cutoff
    print(f"\n  [b] Purging articles older than {cutoff_hours}h from storage...")
    purged = purge_expired_articles(max_age_hours=cutoff_hours)
    print(f"      Purged: {purged} expired articles")
    
    # Step (c): Deduplicate and save new articles
    print(f"\n  [c] Saving new articles (with deduplication)...")
    new_count = save_articles(new_articles)
    total = get_article_count()
    print(f"      New: {new_count} | Total in storage: {total}")
    
    # Step (d):  Filter articles (BM25 + Phrase Boost)
    # Cycle 1: filtering ALL articles (new session = new domain keywords)
    # Cycle 2+: filtering only newly added articles
    all_articles = load_articles()
    
    if cycle_number == 1:
        print(f"\n  [d] Filtering ALL articles (new session)...")
        to_process = all_articles
    else:
        print(f"\n  [d] Filtering newly added articles...")
        # Only process articles that haven't been processed for this domain yet
        # (Naive check: if they have no domain set, they are candidates)
        to_process = [a for a in all_articles if not a.primary_domain]

    if to_process:
        keywords = domains_dict[domain_name]["keywords"]
        
        # Reset previous classification state for these articles
        for article in to_process:
            article.primary_domain = None
            article.domains = []
            article.relevance_score = 0.0
            
        # Run BM25 Filter
        # This returns ONLY the articles that passed the threshold
        # It also updates their .relevance_score in place
        # We pass 'all_articles' as corpus to ensure BM25 IDF is calculated against the implementation's full knowledge
        matched_articles = filter_engine.filter_articles(to_process, keywords, corpus=all_articles)
        
        # Tag the matches
        for article in matched_articles:
            article.primary_domain = domain_name
            article.domains = [domain_name]
            
        # Update storage with new tags (for ALL processed, to save the 'None' state too if needed)
        # But efficiently, we definitely need to save the matches.
        # To prevent reprocessing the non-matches in the future (if we only look for empty domains),
        # we might want to mark them? 
        # For this design: we just save the updates.
        update_articles(to_process)
        
        print(f"      Matched: {len(matched_articles)}/{len(to_process)} articles")
    else:
        print(f"      No articles to process")
    
    # =========================================================================
    # Step (e) & (f): Fresh Selection & Ranking
    # CRITICAL: Always reload from storage to ensure we rank the latest state
    # (including effects of purge, new fetches, and filtering updates)
    # =========================================================================
    print(f"\n  [e] Loading fresh data for ranking...")
    all_articles = load_articles()
    
    print(f"      Selecting articles for domain: '{domain_name}'...")
    matching = [a for a in all_articles if a.primary_domain == domain_name]
    print(f"      Total Active Matches: {len(matching)}")
    
    # Step (f): Rank by combined score (recency + source + relevance)
    print(f"\n  [f] Ranking results...")
    ranked = rank_articles(matching)
    top_ranked = ranked[:TOP_N_DISPLAY]
    
    # Step (g): Display top N articles
    print(f"\n{'=' * 60}")
    print(f"  TOP {len(top_ranked)} ARTICLES -- Domain: {domain_name}")
    print(f"{'=' * 60}")
    
    if not top_ranked:
        print("\n  No matching articles found in this cycle.")
    else:
        for i, (article, score) in enumerate(top_ranked, 1):
            print(f"\n  [{i}] {article.title}")
            print(f"      Date:  {article.published_date[:19]}")
            print(f"      URL:   {article.url}")
            print(f"      Score: {score:.3f} (Content Relevance: {article.relevance_score})")
            if article.summary:
                print(f"      Summary: {article.summary[:200]}...")
    
    # Cycle stats
    cycle_duration = (datetime.now() - cycle_start).total_seconds()
    print(f"\n{'-' * 60}")
    print(f"  Cycle {cycle_number} completed in {cycle_duration:.1f}s")
    print(f"  Total stored: {total} | Matches: {len(matching)} | Displayed: {len(top_ranked)}")
    print(f"{'-' * 60}")


# ============================================================================
# PHASE 3 — MAIN LOOP + GRACEFUL SHUTDOWN
# ============================================================================
def main():
    """Run the News Engine."""
    
    # Graceful shutdown handler
    def signal_handler(sig, frame):
        print(f"\n\n{'=' * 60}")
        print("  NEWS ENGINE -- Shutting down gracefully...")
        print(f"{'=' * 60}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Phase 1: Session initialization (runs once)
    domains_dict, filter_engine, domain_name = initialize_session()
    
    # Phase 2: Continuous pipeline loop
    cycle = 0
    
    while True:
        cycle += 1
        
        try:
            run_pipeline_cycle(filter_engine, domain_name, domains_dict, cycle)
        except Exception as e:
            print(f"\n  [ERROR] Pipeline cycle failed: {e}")
            traceback.print_exc()
            print("  [WARN] Continuing to next cycle after sleep interval...")
        
        # Sleep announcement
        next_time = datetime.now().timestamp() + POLL_INTERVAL
        next_str = datetime.fromtimestamp(next_time).strftime('%H:%M:%S')
        print(f"\n  [*] Next poll at {next_str} ({POLL_INTERVAL // 60} min)...")
        print(f"     Press Ctrl+C to stop.\n")
        
        # Sleep in small increments for responsive shutdown
        remaining = POLL_INTERVAL
        while remaining > 0:
            time.sleep(min(5, remaining))
            remaining -= 5


if __name__ == "__main__":
    main()
