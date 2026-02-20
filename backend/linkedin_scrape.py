import os
import json
from apify_client import ApifyClient

# Configuration
APIFY_TOKEN = os.getenv('APIFY_TOKEN')
if not APIFY_TOKEN:
    raise ValueError("APIFY_TOKEN not found. Please export it or add to .env")

client = ApifyClient(APIFY_TOKEN)

def scrape_linkedin_jobs(keywords, location, max_jobs=15):
    print(f"🕵️  Searching LinkedIn for '{keywords}' in '{location}'...")
    
    # Run the 'atomic/linkedin-jobs-scraper' actor (a reliable one)
    # Note: Actor names change, if this fails we might need to swap to 'hiring-lab/linkedin-jobs-scraper'
    run_input = {
        "keywords": keywords,
        "locationId": location, # Free text location work too usually
        "limit": max_jobs,
        "sortBy": "RELEVANCE"
    }
    
    # Start the actor and wait for it to finish
    # Using 'krasivo/linkedin-jobs-scraper' which is often reliable for public searches
    run = client.actor("krasivo/linkedin-jobs-scraper").call(run_input=run_input)
    
    # Fetch results from the dataset
    print(f"✅  Scrape complete. Fetching results...")
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    
    return dataset_items

def save_jobs(jobs, filename):
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"💾  Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    # London, Ontario specific search
    jobs = scrape_linkedin_jobs("Junior Developer", "London, Ontario, Canada", max_jobs=10)
    save_jobs(jobs, "tools/scrapers/linkedin_london_results.json")
