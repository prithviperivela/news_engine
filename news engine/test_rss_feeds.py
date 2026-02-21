
import sys
import os
import feedparser
import time
from datetime import datetime

# Add root to path so we can import src
sys.path.append(os.getcwd())

try:
    from src.collector import RSS_FEEDS
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def test_feeds():
    print(f"=== Testing {len(RSS_FEEDS)} RSS Feeds ===\n")
    
    results = {
        "success": [],
        "empty": [],
        "failed": []
    }
    
    print("-" * 80)
    print(f"{'Source Name':<30} | {'Status':<10} | {'Entries':<7} | {'Message'}")
    print("-" * 80)

    for name, url in RSS_FEEDS.items():
        try:
            # Set a custom user agent to avoid being blocked by some servers
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            
            status = "OK"
            entries = len(feed.entries)
            message = ""
            
            if feed.bozo:
                # Bozo header means there was a parsing error, but feedparser might still have gotten data
                status = "WARN"
                message = f"Parsing warning: {feed.bozo_exception}"
            
            # Check for HTTP errors if available
            if hasattr(feed, 'status'):
                if feed.status >= 400:
                    status = "HTTP_ERR"
                    message = f"HTTP {feed.status}"
            
            # Categorize
            if status == "HTTP_ERR" or (status == "WARN" and entries == 0):
                results["failed"].append((name, url, message))
                print(f"{name:<30} | X {status:<8} | {entries:<7} | {message}")
            elif entries == 0:
                results["empty"].append((name, url))
                print(f"{name:<30} | ! EMPTY   | {entries:<7} | No entries found")
            else:
                results["success"].append((name, entries))
                # Only print errors/warnings to keep output clean, valid feeds are expected
                # print(f"{name:<30} | OK {status:<8} | {entries:<7} | {message}")
                pass
                
        except Exception as e:
            results["failed"].append((name, url, str(e)))
            print(f"{name:<30} | X ERROR    | -       | {e}")
            
    print("-" * 80)
    print(f"\nSummary:")
    print(f"OK Successful: {len(results['success'])}")
    print(f"!  Empty:      {len(results['empty'])}")
    print(f"X  Failed:     {len(results['failed'])}")
    
    if results['failed']:
        print("\n=== Detailed Failures ===")
        for name, url, msg in results['failed']:
            print(f"• {name}: {url}\n  -> {msg}")

    if results['empty']:
        print("\n=== Empty Feeds (Might be valid but currently no items) ===")
        for name, url in results['empty']:
             print(f"• {name}: {url}")

if __name__ == "__main__":
    test_feeds()
