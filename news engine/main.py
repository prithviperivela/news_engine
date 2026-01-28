"""News Engine - Main entry point."""

import argparse
import sys

from src.collector import collect_all
from src.storage import save_articles, load_articles, get_article_count, update_articles
from src.filter import filter_by_keyword, filter_by_domain
from src.classifier import classify_articles, DomainClassifier
from src.domains import get_domain_names
from src.ranker import rank_articles


def print_articles(articles, limit=10, show_domains=False, show_score=False):
    """Pretty print articles."""
    for i, item in enumerate(articles[:limit], 1):
        if isinstance(item, tuple):
            article, score = item
        else:
            article, score = item, None
            
        print(f"\n{'='*60}")
        title_line = f"[{i}] {article.title}"
        if show_score and score is not None:
            title_line += f" (Score: {score})"
        print(title_line)
        print(f"    Source: {article.source}")
        print(f"    Date: {article.published_date[:10]}")
        if show_domains and article.domains:
            print(f"    Domains: {', '.join(article.domains)}")
        print(f"    URL: {article.url}")
        if article.summary:
            print(f"    Summary: {article.summary[:150]}...")


def run_interactive_mode():
    """Run interactive menu-driven mode."""
    from src.agents.pipeline import run_pipeline
    
    print("\n" + "="*60)
    print("   NEWS ENGINE - Interactive Mode")
    print("="*60)
    
    while True:
        print("\n📰 What would you like to do?\n")
        print("  1. Collect new articles from RSS feeds")
        print("  2. Classify articles into domains")
        print("  3. Search by domain")
        print("  4. Search by keyword")
        print("  5. Show top ranked articles")
        print("  6. Show statistics")
        print("  7. Full pipeline (collect + classify + search)")
        print("  0. Exit")
        
        try:
            choice = input("\n👉 Enter choice [0-7]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if choice == "0":
            print("\nGoodbye! 👋")
            break
            
        elif choice == "1":
            # Collect
            print("\n⏳ Collecting articles from RSS feeds...\n")
            result = run_pipeline(collect=True, verbose=True)
            if result.success:
                print(f"\n✅ Collection complete!")
                
        elif choice == "2":
            # Classify
            print("\n⏳ Classifying articles...\n")
            result = run_pipeline(classify=True, verbose=True)
            if result.success:
                print(f"\n✅ Classification complete!")
                
        elif choice == "3":
            # Search by domain
            domains = get_domain_names()
            print("\n📂 Available domains:\n")
            for i, d in enumerate(domains, 1):
                print(f"  {i}. {d}")
            
            try:
                domain_choice = input(f"\n👉 Select domain [1-{len(domains)}]: ").strip()
                domain_idx = int(domain_choice) - 1
                if 0 <= domain_idx < len(domains):
                    selected_domain = domains[domain_idx]
                else:
                    print("❌ Invalid choice")
                    continue
            except (ValueError, EOFError):
                print("❌ Invalid input")
                continue
            
            try:
                limit = input("👉 How many results? [10]: ").strip()
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            
            rank_choice = input("👉 Rank by relevance? [Y/n]: ").strip().lower()
            do_rank = rank_choice != 'n'
            
            print(f"\n⏳ Searching domain '{selected_domain}'...\n")
            result = run_pipeline(
                domain=selected_domain, 
                rank=do_rank, 
                limit=limit,
                verbose=True
            )
            if result.success and result.data:
                print("\n" + "="*60)
                print("RESULTS")
                print("="*60)
                print_articles(result.data, limit, show_domains=True, show_score=do_rank)
                
        elif choice == "4":
            # Search by keyword
            try:
                keyword = input("\n👉 Enter keyword to search: ").strip()
            except EOFError:
                continue
                
            if not keyword:
                print("❌ Keyword cannot be empty")
                continue
            
            try:
                limit = input("👉 How many results? [10]: ").strip()
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            
            rank_choice = input("👉 Rank by relevance? [Y/n]: ").strip().lower()
            do_rank = rank_choice != 'n'
            
            print(f"\n⏳ Searching for '{keyword}'...\n")
            result = run_pipeline(
                keyword=keyword, 
                rank=do_rank, 
                limit=limit,
                verbose=True
            )
            if result.success and result.data:
                print("\n" + "="*60)
                print("RESULTS")
                print("="*60)
                print_articles(result.data, limit, show_domains=True, show_score=do_rank)
                
        elif choice == "5":
            # Top ranked
            try:
                limit = input("\n👉 How many top articles? [10]: ").strip()
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            
            print(f"\n⏳ Fetching top {limit} articles...\n")
            result = run_pipeline(rank=True, limit=limit, verbose=True)
            if result.success and result.data:
                print("\n" + "="*60)
                print("TOP RANKED ARTICLES")
                print("="*60)
                print_articles(result.data, limit, show_domains=True, show_score=True)
                
        elif choice == "6":
            # Stats
            articles = load_articles()
            domain_counts = {d: 0 for d in get_domain_names()}
            for article in articles:
                for domain in article.domains:
                    domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"\n📊 Storage Statistics")
            print(f"   Total articles: {len(articles)}")
            print(f"\n   Domain breakdown:")
            for d, c in domain_counts.items():
                print(f"     {d}: {c}")
            unclassified = sum(1 for a in articles if not a.domains)
            print(f"     (unclassified): {unclassified}")
            
        elif choice == "7":
            # Full pipeline
            domains = get_domain_names()
            print("\n📂 Select domain:\n")
            for i, d in enumerate(domains, 1):
                print(f"  {i}. {d}")
            print(f"  {len(domains)+1}. All domains (no filter)")
            
            try:
                domain_choice = input(f"\n👉 Select domain [1-{len(domains)+1}]: ").strip()
                domain_idx = int(domain_choice) - 1
                if 0 <= domain_idx < len(domains):
                    selected_domain = domains[domain_idx]
                elif domain_idx == len(domains):
                    selected_domain = None
                else:
                    print("❌ Invalid choice")
                    continue
            except (ValueError, EOFError):
                print("❌ Invalid input")
                continue
            
            try:
                limit = input("👉 How many results? [10]: ").strip()
                limit = int(limit) if limit else 10
            except ValueError:
                limit = 10
            
            print(f"\n⏳ Running full pipeline...\n")
            result = run_pipeline(
                collect=True,
                classify=True,
                domain=selected_domain,
                rank=True,
                limit=limit,
                verbose=True
            )
            if result.success and result.data:
                print("\n" + "="*60)
                print("RESULTS")
                print("="*60)
                print_articles(result.data, limit, show_domains=True, show_score=True)
        else:
            print("❌ Invalid choice. Please enter 0-7.")


def run_agent_mode(args):
    """Run in agent-based mode."""
    from src.agents.pipeline import run_pipeline
    
    print("\n" + "="*60)
    print("AGENT MODE")
    print("="*60 + "\n")
    
    result = run_pipeline(
        collect=args.collect,
        classify=args.classify,
        keyword=args.filter,
        domain=args.domain,
        rank=args.rank,
        limit=args.limit,
        verbose=True
    )
    
    if not result.success:
        print(f"\nPipeline failed: {result.error}")
        return
    
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if result.data:
        print_articles(result.data, args.limit, show_domains=True, show_score=args.rank)
    else:
        print("No articles found.")
    
    print(f"\nMetadata: {result.metadata}")


def run_classic_mode(args):
    """Run in classic (non-agent) mode."""
    if args.collect:
        print("Collecting articles from RSS feeds...\n")
        articles = collect_all()
        new_count = save_articles(articles)
        print(f"\nAdded {new_count} new articles to storage")
        print(f"Total articles in storage: {get_article_count()}")
    
    if args.classify:
        print("Classifying articles into domains...\n")
        articles = load_articles()
        classified = classify_articles(articles)
        update_articles(classified)
        
        domain_counts = {d: 0 for d in get_domain_names()}
        for article in classified:
            for domain in article.domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        print("Classification complete:")
        for domain, count in domain_counts.items():
            print(f"  {domain}: {count} articles")
        
        unclassified = sum(1 for a in classified if not a.domains)
        print(f"  (unclassified): {unclassified} articles")
    
    if args.filter:
        articles = load_articles()
        filtered = filter_by_keyword(articles, args.filter)
        
        if args.rank:
            ranked = rank_articles(filtered)
            print(f"\nTop {args.limit} articles matching '{args.filter}' (ranked):")
            print_articles(ranked, args.limit, show_domains=True, show_score=True)
        else:
            print(f"\nFound {len(filtered)} articles matching '{args.filter}':")
            print_articles(filtered, args.limit, show_domains=True)
    
    elif args.domain:
        articles = load_articles()
        filtered = filter_by_domain(articles, args.domain)
        
        if args.rank:
            ranked = rank_articles(filtered)
            print(f"\nTop {args.limit} articles in domain '{args.domain}' (ranked):")
            print_articles(ranked, args.limit, show_domains=True, show_score=True)
        else:
            print(f"\nFound {len(filtered)} articles in domain '{args.domain}':")
            print_articles(filtered, args.limit, show_domains=True)
    
    elif args.rank:
        articles = load_articles()
        ranked = rank_articles(articles)
        print(f"\nTop {args.limit} articles (ranked by relevance):")
        print_articles(ranked, args.limit, show_domains=True, show_score=True)
    
    if args.list and not args.filter and not args.domain and not args.rank:
        articles = load_articles()
        print(f"\nAll stored articles ({len(articles)} total):")
        print_articles(articles, args.limit, show_domains=True)
    
    if args.stats:
        articles = load_articles()
        count = len(articles)
        print(f"\nStorage Statistics:")
        print(f"  Total articles: {count}")
        
        domain_counts = {d: 0 for d in get_domain_names()}
        for article in articles:
            for domain in article.domains:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        print(f"\nDomain breakdown:")
        for domain, dcount in domain_counts.items():
            print(f"  {domain}: {dcount}")


def main():
    parser = argparse.ArgumentParser(
        description="News Engine - Collect, classify, filter, and rank news articles"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive menu mode"
    )
    parser.add_argument(
        "--agent", 
        action="store_true",
        help="Run in agent-based mode"
    )
    parser.add_argument(
        "--collect", 
        action="store_true",
        help="Collect articles from RSS feeds"
    )
    parser.add_argument(
        "--classify", 
        action="store_true",
        help="Classify all stored articles into domains"
    )
    parser.add_argument(
        "--filter", 
        type=str,
        metavar="KEYWORD",
        help="Filter articles by keyword"
    )
    parser.add_argument(
        "--domain", 
        type=str,
        metavar="DOMAIN",
        help=f"Filter by domain: {', '.join(get_domain_names())}"
    )
    parser.add_argument(
        "--rank", 
        action="store_true",
        help="Rank articles by relevance score"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="List all stored articles"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=10,
        help="Number of articles to display (default: 10)"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Show storage statistics"
    )
    
    args = parser.parse_args()
    
    # Default action: show interactive if no args
    if len(sys.argv) == 1:
        run_interactive_mode()
        return
    
    # Choose mode
    if args.interactive:
        run_interactive_mode()
    elif args.agent:
        run_agent_mode(args)
    else:
        run_classic_mode(args)


if __name__ == "__main__":
    main()
