import os
import json
import argparse
from apify_client import ApifyClient

# Configuration
APIFY_TOKEN = os.getenv('APIFY_TOKEN')

def scrape_gmaps_companies(search_term, location, max_places=20):
    if not APIFY_TOKEN:
        print("⚠️  APIFY_TOKEN not found. Skipping Google Maps scrape.")
        return []

    client = ApifyClient(APIFY_TOKEN)
    print(f"🌍  Scanning Google Maps for '{search_term}' in '{location}'...")
    
    # Run the 'compass/crawler-google-places' actor
    run_input = {
        "searchStringsArray": [f"{search_term} in {location}"],
        "maxCrawledPlaces": max_places,
        "language": "en",
        "scrapeWebsites": True
    }
    
    try:
        # Start the actor
        run = client.actor("compass/crawler-google-places").call(run_input=run_input)
        
        # Fetch results
        print(f"✅  Map scan complete. Fetching place details...")
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        # Clean the data
        places = []
        for item in dataset_items:
            # We only care about entries with websites
            if item.get("website"):
                places.append({
                    "name": item.get("title"),
                    "url": item.get("website"),
                    "address": item.get("address"),
                    "category": item.get("categoryName"),
                    "source": "Google Maps"
                })
            
        return places
    except Exception as e:
        print(f"❌  Google Maps scrape failed: {e}")
        return []

def save_places(places, filename):
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(places, f, indent=2)
    print(f"💾  Saved {len(places)} companies to {filename}")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Scrape Google Maps for businesses")

    parser.add_argument("--query", required=True, help="Search term (e.g. 'Software Company')")

    parser.add_argument("--location", default="London, Ontario", help="Location to search in")

    parser.add_argument("--output-dir", default="data/companies", help="Output directory")

    parser.add_argument("--run-id", type=str, help="Unused but accepted for consistency")

    parser.add_argument("--max", type=int, default=20, help="Max results")

    

    args = parser.parse_args()

    

    # Ensure output dir exists

    os.makedirs(args.output_dir, exist_ok=True)

    output_path = os.path.join(args.output_dir, "gmaps_discovered.json")

    

    results = scrape_gmaps_companies(args.query, args.location, args.max)

    

    if results:

        save_places(results, output_path)

    else:

        print("⚠️  No results found or Apify token missing.")
