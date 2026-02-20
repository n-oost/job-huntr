import os
import json
from apify_client import ApifyClient

# Configuration
APIFY_TOKEN = os.getenv('APIFY_TOKEN')
if not APIFY_TOKEN:
    raise ValueError("APIFY_TOKEN not found. Please export it or add to .env")

client = ApifyClient(APIFY_TOKEN)

def scrape_indeed(position, location, max_jobs=10):
    print(f"🕵️  Searching Indeed for '{position}' in '{location}'...")
    
    # Run the 'apify/indeed-scraper' actor
    run_input = {
        "position": position,
        "country": "CA",
        "location": location,
        "maxConcurrency": 2,
        "maxItems": max_jobs,
        "parseCompanyDetails": False,
        "saveOnlyUniqueItems": True,
        "followApplyRedirects": False
    }
    
    # Start the actor and wait for it to finish
    run = client.actor("apify/indeed-scraper").call(run_input=run_input)
    
    # Fetch results from the dataset
    print(f"✅  Scrape complete. Fetching results...")
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    return dataset_items

def save_jobs(jobs, filename="indeed_jobs.json"):
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"💾  Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    jobs = scrape_indeed("Junior Software Developer", "Ontario", max_jobs=5)
    save_jobs(jobs, "tools/scrapers/indeed_results.json")
