import os
import json
from firecrawl import FirecrawlApp

def scrape_local_companies():
    print("🚀 Starting local company job sweep...")
    
    # Initialize Firecrawl
    app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))
    
    # Load company list
    companies_file = 'Job_Search_2026/data/companies/London_Tech_Landscape.md'
    if not os.path.exists(companies_file):
        print("❌ Company file not found!")
        return

    with open(companies_file, 'r') as f:
        content = f.read()

    # Simple extraction of URLs from markdown
    import re
    urls = re.findall(r'\((http[s]?://.*?)\)', content)
    unique_urls = list(set(urls))
    
    print(f"🎯 Found {len(unique_urls)} unique company websites to check.")
    
    jobs = []
    
    for url in unique_urls[:15]: # Limit to 15 for this test run
        print(f"   🔎 Checking {url}...")
        try:
            # Using v2 API style map method
            map_result = app.map(url)
            
            career_links = [
                link for link in map_result.get('links', []) 
                if 'career' in link.lower() or 'job' in link.lower() or 'team' in link.lower()
            ]
            
            if not career_links:
                continue
                
            # Take the first likely career page
            target_page = career_links[0]
            print(f"      -> Found career page: {target_page}")
            
            # Scrape that page specifically for job listings
            scrape_result = app.scrape_url(target_page, params={
                'formats': ['json'],
                'jsonOptions': {
                    'prompt': 'Extract a list of open job positions. Return a list of objects with "title", "location", and "apply_link".'
                }
            })
            
            if scrape_result and 'json' in scrape_result:
                extracted_jobs = scrape_result['json'].get('jobs', [])
                if isinstance(scrape_result['json'], list):
                    extracted_jobs = scrape_result['json']
                
                for job in extracted_jobs:
                    if isinstance(job, dict) and 'title' in job:
                        job['company_url'] = url
                        job['source'] = 'Direct Company Site'
                        jobs.append(job)
                        print(f"         + Found Job: {job.get('title')}")

        except Exception as e:
            print(f"      x Error checking {url}: {str(e)[:50]}...")
            continue

    # Save results
    output_file = 'Job_Search_2026/data/jobs/local_direct_sweep.json'
    with open(output_file, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print(f"✅ Sweep complete. Found {len(jobs)} jobs. Saved to {output_file}")

if __name__ == "__main__":
    scrape_local_companies()