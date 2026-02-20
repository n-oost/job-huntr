import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_knighthunter():
    print("🕵️  Scanning Knighthunter.com (London's Job Board)...")
    base_url = "https://www.knighthunter.com"
    # Search for "Developer"
    search_url = f"{base_url}/search.aspx?keywords=developer&location=London"
    
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; JobBot/1.0)'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    # Note: Selectors are hypothetical based on typical structure, needs adjustment if site changes
    # Looking for job listing containers
    listings = soup.find_all('div', class_='job-listing') 
    
    # If standard classes aren't found, try a more generic approach for Knighthunter's table structure
    if not listings:
        listings = soup.select('table.jobList tr')

    for item in listings:
        title_tag = item.find('a')
        if title_tag and len(title_tag.text.strip()) > 3:
            link = base_url + "/" + title_tag['href'] if title_tag['href'].startswith('/') else title_tag['href']
            jobs.append({
                "title": title_tag.text.strip(),
                "company": "Knighthunter Listing", # Knighthunter often puts company in a separate col
                "url": link,
                "source": "Knighthunter"
            })
            
    return jobs

def scrape_city_of_london():
    print("🕵️  Scanning City of London Careers...")
    # City of London uses an Oracle/Taleo or similar enterprise backend often difficult to scrape directly.
    # We will point to the main portal for now.
    return [{
        "title": "Check City Career Portal",
        "company": "City of London",
        "url": "https://careers.london.ca/job/search",
        "source": "City of London"
    }]

def save_jobs(jobs, filename):
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"💾  Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/jobs")
    parser.add_argument("--run-id", type=str, help="Unused but accepted for consistency")
    args = parser.parse_args()

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    all_jobs = []
    
    # Knighthunter
    try:
        kj = scrape_knighthunter()
        all_jobs.extend(kj)
        print(f"   > Found {len(kj)} on Knighthunter")
    except Exception as e:
        print(f"   > Knighthunter failed: {e}")

    # City of London
    all_jobs.extend(scrape_city_of_london())

    save_jobs(all_jobs, os.path.join(args.output_dir, "niche_boards_results.json"))
