import json
import os
from playwright.sync_api import sync_playwright
import time
import random

OUTPUT_DIR = 'data/jobs/descriptions'
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_job_text(page, url):
    try:
        print(f"   -> Navigating to {url[:60]}...")
        page.goto(url, timeout=30000)
        page.wait_for_load_state('domcontentloaded')
        
        # Indeed specific handling
        if "indeed" in url:
            try:
                # Click "Read more" if description is truncated (common on mobile views, less on desktop)
                # But mostly we just want #jobDescriptionText
                desc = page.locator('#jobDescriptionText').inner_text()
                return desc
            except:
                return page.inner_text("body")
        
        # LinkedIn specific
        elif "linkedin" in url:
            try:
                page.locator('.show-more-less-html__button').click(timeout=2000)
            except: pass
            try:
                return page.locator('.description__text').inner_text()
            except:
                return page.inner_text("body")
                
        # Generic fallback
        return page.inner_text("body")
        
    except Exception as e:
        print(f"   x Error fetching: {e}")
        return None

def main():
    with open('data/jobs/master_listings.json', 'r') as f:
        jobs = json.load(f)
    
    # Filter for real postings (Indeed/LinkedIn) that we haven't applied to
    # And specifically "Junior" or "Developer" roles
    targets = []
    with open('data/applied_history.json', 'r') as f:
        history = json.load(f)
        
    for job in jobs:
        url = job.get('url')
        if not url: continue
        if url in history: continue
        if 'google.com/maps' in url: continue # Skip generic company leads
        
        # Prioritize local
        if 'London' not in job.get('location', ''): continue
        
        targets.append(job)
        
    # Sort by score
    targets.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Take top 5
    top_5 = targets[:5]
    
    print(f"🕷️  Fetching descriptions for top {len(top_5)} active listings...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        page = context.new_page()
        
        results = []
        
        for i, job in enumerate(top_5, 1):
            print(f"[{i}/{len(top_5)}] {job['title']} @ {job['company']}")
            text = get_job_text(page, job['url'])
            
            if text:
                filename = f"{job['company'].replace(' ', '_')}_{i}.txt"
                filepath = os.path.join(OUTPUT_DIR, filename)
                with open(filepath, 'w') as f:
                    f.write(text)
                
                results.append({
                    "title": job['title'],
                    "company": job['company'],
                    "file": filepath,
                    "preview": text[:200].replace('\n', ' ') + "..."
                })
            
            time.sleep(random.uniform(2, 5))
            
        browser.close()
        
    print("\n✅ Fetch complete. Summaries:")
    for r in results:
        print(f"* {r['title']} (@ {r['company']}) -> Saved to {r['file']}")

if __name__ == "__main__":
    main()
