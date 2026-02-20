import asyncio
import re
import json
import os
import argparse
from playwright.async_api import async_playwright

DEFAULT_CACHE_FILE = 'data/companies/known_career_pages.json'
DEFAULT_OUTPUT_FILE = 'data/jobs/local_direct_sweep.json'
MAX_CONCURRENCY = 5

# Default keywords if none provided
DEFAULT_KEYWORDS = ["Developer", "Engineer", "Software", "Programmer", "Full Stack", "Backend", "Frontend", "Data", "AI", "Technician", "Support"]

def load_cache(cache_file):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache, cache_file):
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

async def extract_urls_from_md(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        content = f.read()
    matches = re.findall(r'\[(.*?)\]\((http[s]?://.*?)\)', content)
    return [{"name": m[0], "url": m[1]} for m in matches]

async def load_json_companies(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        data = json.load(f)
    # Normalize to {"name": ..., "url": ...}
    companies = []
    for item in data:
        if item.get('url'):
            companies.append({
                "name": item.get('name') or item.get('title'),
                "url": item.get('url')
            })
    return companies

async def check_site(context, company, keywords, cache):
    page = await context.new_page()
    jobs = []
    
    # 1. Resolve Target URL (Cache vs Discovery)
    target_url = cache.get(company['url'])
    
    try:
        if target_url:
            print(f"⚡ [Cache Hit] {company['name']} -> {target_url}")
        else:
            print(f"🔎 Scanning {company['name']} ({company['url']})...")
            try:
                await page.goto(company['url'], timeout=15000)
            except:
                print(f"   x Failed to load {company['name']}")
                await page.close()
                return []

            # Look for "Career", "Job", "Join", "Work with us"
            career_link = page.get_by_text(re.compile(r"Career|Job|Join|Work", re.IGNORECASE))
            
            if await career_link.count() > 0:
                for i in range(await career_link.count()):
                    element = career_link.nth(i)
                    if await element.is_visible():
                        href = await element.evaluate("el => el.closest('a')?.href")
                        if href:
                            target_url = href
                            break
            
            if not target_url:
                if "career" in page.url.lower() or "job" in page.url.lower():
                    target_url = page.url
                else:
                    print(f"   - No career link found for {company['name']}")
                    await page.close()
                    return []
            
            # Update cache found
            print(f"   -> Found new career page: {target_url}")
            cache[company['url']] = target_url

        # 2. Visit Career Page & Extract
        if page.url != target_url:
            try:
                await page.goto(target_url, timeout=15000)
            except:
                print(f"   x Failed to load career page: {target_url}")
                await page.close()
                return []

        # 3. Extract Jobs
        potential_elements = page.locator("a, h2, h3, h4, h5, li")
        count = await potential_elements.count()
        seen_titles = set()
        
        for i in range(min(count, 100)): # Scan first 100 elements max
            if len(jobs) >= 5: 
                break
            
            try:
                el = potential_elements.nth(i)
                if not await el.is_visible(): continue
                
                text = await el.inner_text()
                text = text.strip()
                
                if any(kw.lower() in text.lower() for kw in keywords) and 4 < len(text) < 100:
                    if text.lower() in ["careers", "jobs", "home", "contact", "about us", "join us", "read more"]:
                        continue
                        
                    if text not in seen_titles:
                        job_url = await el.evaluate("el => el.closest('a')?.href") or target_url
                        jobs.append({
                            "title": text,
                            "company": company['name'],
                            "url": job_url,
                            "location": "London, ON (Presumed)",
                            "source": "Direct Site"
                        })
                        seen_titles.add(text)
                        print(f"      + Found: {text}")
            except:
                continue

    except Exception as e:
        print(f"   x Error processing {company['name']}: {e}")
    finally:
        await page.close()
    
    return jobs

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", help="List of input files (JSON or MD)")
    parser.add_argument("--keywords", nargs="+", help="Keywords to search for")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    parser.add_argument("--run-id", type=str, help="Run ID")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    args = parser.parse_args()

    # Determine paths
    output_dir = args.output_dir
    cache_file = os.path.join(output_dir, 'known_career_pages.json')
    output_file = os.path.join(output_dir, 'local_direct_sweep.json')
    
    os.makedirs(output_dir, exist_ok=True)

    # Load resources
    cache = load_cache(cache_file)
    
    # Get keywords from args or config or default
    keywords = args.keywords
    if not keywords and args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
                keywords = list(config.get('positive_keywords', {}).keys())
        except:
            pass
    
    if not keywords:
        keywords = DEFAULT_KEYWORDS
    
    companies = []
    # Default inputs if none provided
    inputs = args.inputs if args.inputs else ['data/companies/London_Tech_Landscape.md']
    
    for filepath in inputs:
        if filepath.endswith('.md'):
            companies.extend(await extract_urls_from_md(filepath))
        elif filepath.endswith('.json'):
            companies.extend(await load_json_companies(filepath))
            
    # Dedup companies by URL
    unique_companies = {c['url']: c for c in companies}.values()
    print(f"🎯 Loaded {len(unique_companies)} unique companies from {inputs}")
    print(f"🔑 Filtering for keywords: {keywords}")
    
    all_jobs = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Process in chunks
        chunk_size = MAX_CONCURRENCY
        companies_list = list(unique_companies)
        
        for i in range(0, len(companies_list), chunk_size):
            chunk = companies_list[i:i + chunk_size]
            tasks = [check_site(context, company, keywords, cache) for company in chunk]
            results = await asyncio.gather(*tasks)
            
            for res in results:
                all_jobs.extend(res)
                
            # Periodic cache save
            save_cache(cache, cache_file)
                
        await browser.close()
        
    save_cache(cache, cache_file) # Final save
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(all_jobs, f, indent=2)
    print(f"✅ Sweep complete. Found {len(all_jobs)} jobs. Saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())