import time
import random
import json
import logging
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_linkedin_jobs(keywords, location, max_jobs=15):
    """
    Scrapes LinkedIn public job search using local Playwright.
    """
    logging.info(f"🕵️  Searching LinkedIn for '{keywords}' in '{location}' (Target: {max_jobs})...")
    
    jobs = []
    
    with sync_playwright() as p:
        # Launch browser - headless=True for speed, but sometimes False helps with detection
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        
        # Block resources to speed up
        await_resources = ['image', 'media', 'font']
        def route_intercept(route):
            if route.request.resource_type in await_resources:
                route.abort()
            else:
                route.continue_()
        
        page = context.new_page()
        page.route("**/*", route_intercept)
        
        # Construct URL
        # e.g. https://www.linkedin.com/jobs/search?keywords=python&location=London%2C%20Ontario%2C%20Canada
        url = f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}&redirect=false&position=1&pageNum=0"
        
        logging.info(f"Navigating to {url}")
        page.goto(url, timeout=60000)
        
        # Initial wait
        time.sleep(random.uniform(2, 4))
        
        previous_height = 0
        consecutive_scrolls = 0
        
        while len(jobs) < max_jobs and consecutive_scrolls < 5:
            # Parse visible jobs
            # LinkedIn public job cards usually have class 'base-card' or 'job-search-card'
            job_cards = page.locator(".base-card, .job-search-card").all()
            
            logging.info(f"Found {len(job_cards)} visible cards...")
            
            for card in job_cards:
                if len(jobs) >= max_jobs:
                    break
                    
                try:
                    title_el = card.locator(".base-search-card__title")
                    company_el = card.locator(".base-search-card__subtitle")
                    location_el = card.locator(".job-search-card__location")
                    link_el = card.locator("a.base-card__full-link")
                    date_el = card.locator("time")

                    if not title_el.count() or not link_el.count():
                        continue

                    job = {
                        "title": title_el.inner_text().strip(),
                        "company": company_el.inner_text().strip() if company_el.count() else "Unknown",
                        "location": location_el.inner_text().strip() if location_el.count() else location,
                        "url": link_el.get_attribute("href").split('?')[0], # Clean URL
                        "date": date_el.get_attribute("datetime") if date_el.count() else "Recently",
                        "source": "LinkedIn (Local)"
                    }
                    
                    # Dedup check
                    if not any(j['url'] == job['url'] for j in jobs):
                        jobs.append(job)
                        logging.info(f"   + Captured: {job['title']} at {job['company']}")
                        
                except Exception as e:
                    # Ignore partial render errors
                    continue
            
            # Scroll down
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(1.5, 3))
            
            # Check for "See more jobs" button
            try:
                see_more = page.locator("button.infinite-scroller__show-more-button")
                if see_more.is_visible():
                    see_more.click()
                    time.sleep(random.uniform(2, 4))
            except:
                pass

            # Check if we are stuck
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                consecutive_scrolls += 1
            else:
                consecutive_scrolls = 0
            previous_height = current_height

        browser.close()
        
    logging.info(f"✅  Scrape complete. Found {len(jobs)} jobs.")
    return jobs

def save_jobs(jobs, filename):
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    logging.info(f"💾  Saved {len(jobs)} jobs to {filename}")

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", default="Junior Developer")
    parser.add_argument("--location", default="London, Ontario, Canada")
    parser.add_argument("--max", type=int, default=15)
    parser.add_argument("--output-dir", default="data/jobs")
    parser.add_argument("--run-id", type=str, help="Unused but accepted for consistency")
    args = parser.parse_args()

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    jobs = scrape_linkedin_jobs(args.keywords, args.location, max_jobs=args.max)
    save_jobs(jobs, os.path.join(args.output_dir, "linkedin_local_results.json"))
