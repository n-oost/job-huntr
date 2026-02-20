import time
import random
import json
import logging
import urllib.parse
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_indeed_jobs(keywords, location, max_jobs=15):
    """
    Scrapes Indeed public job search using local Playwright with stealth techniques.
    Indeed is notoriously aggressive with bot detection (Cloudflare).
    """
    logging.info(f"🕵️  Searching Indeed for '{keywords}' in '{location}' (Target: {max_jobs})...")
    
    jobs = []
    
    # URL Encode parameters
    q = urllib.parse.quote(keywords)
    l = urllib.parse.quote(location)
    base_url = f"https://ca.indeed.com/jobs?q={q}&l={l}"
    
    with sync_playwright() as p:
        # Launch browser - Headless often triggers detection, but let's try stealth args
        # Sometimes 'headful' is actually safer for Indeed
        browser = p.chromium.launch(
            headless=False, # Indeed blocks headless aggressively. We need a visible window (can be minimized)
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ]
        )
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
            locale="en-CA",
            timezone_id="America/Toronto"
        )
        
        # Add stealth script
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logging.info(f"Navigating to {base_url}")
        
        try:
            page.goto(base_url, timeout=60000)
            
            # Human-like delay
            time.sleep(random.uniform(3, 6))
            
            # Check for Cloudflare challenge
            if "challenge" in page.title().lower() or "verify" in page.title().lower():
                logging.warning("⚠️  Cloudflare Challenge Detected! Waiting for manual intervention or auto-solve...")
                time.sleep(10) # Give it a moment, sometimes it auto-clears
            
            # Handle "Where" popup if it exists
            try:
                page.get_by_label("Close").click(timeout=2000)
            except:
                pass

            consecutive_failures = 0
            
            while len(jobs) < max_jobs and consecutive_failures < 3:
                # Indeed job cards usually have class 'job_seen_beacon' or 'cardOutline'
                job_cards = page.locator(".job_seen_beacon, .resultContent").all()
                
                logging.info(f"Found {len(job_cards)} visible cards on this page...")
                
                if not job_cards:
                    logging.warning("No job cards found. Page structure might have changed or we are blocked.")
                    # Dump debug info
                    # page.screenshot(path="indeed_debug.png") 
                    consecutive_failures += 1
                    break
                
                for card in job_cards:
                    if len(jobs) >= max_jobs:
                        break
                        
                    try:
                        title_el = card.locator("h2.jobTitle span").first
                        company_el = card.locator("[data-testid='company-name']")
                        location_el = card.locator("[data-testid='text-location']")
                        link_el = card.locator("h2.jobTitle a") # Usually the link is on the title
                        
                        # Sometimes link is parent
                        if not link_el.count():
                            link_el = card.locator("a").first
                            
                        # Extract Text
                        title = title_el.inner_text().strip() if title_el.count() else "Unknown Title"
                        company = company_el.inner_text().strip() if company_el.count() else "Unknown Company"
                        loc = location_el.inner_text().strip() if location_el.count() else location
                        
                        # Extract URL
                        raw_url = link_el.get_attribute("href")
                        if raw_url:
                            # Indeed URLs are messy. Clean them up.
                            if not raw_url.startswith("http"):
                                url = "https://ca.indeed.com" + raw_url
                            else:
                                url = raw_url
                        else:
                            continue

                        # Dedup
                        if not any(j['url'] == url for j in jobs):
                            jobs.append({
                                "title": title,
                                "company": company,
                                "location": loc,
                                "url": url,
                                "source": "Indeed (Local)"
                            })
                            logging.info(f"   + Captured: {title} at {company}")

                    except Exception as e:
                        continue

                # Pagination
                try:
                    # Find 'Next' button
                    next_btn = page.locator("[data-testid='pagination-page-next']")
                    if next_btn.is_visible() and len(jobs) < max_jobs:
                        logging.info("Clicking Next Page...")
                        next_btn.click()
                        time.sleep(random.uniform(4, 7)) # Long delay for Indeed
                        
                        # Check popup again
                        try:
                            page.locator("#mosaic-desktop-serpjapopup button[aria-label='close']").click(timeout=1000)
                        except:
                            pass
                    else:
                        break
                except:
                    logging.info("No next page or error navigating.")
                    break
            
        except Exception as e:
            logging.error(f"Scrape failed: {e}")
            
        finally:
            browser.close()
            
    logging.info(f"✅  Indeed Scrape complete. Found {len(jobs)} jobs.")
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
    parser.add_argument("--location", default="London, Ontario")
    parser.add_argument("--max", type=int, default=15)
    parser.add_argument("--output-dir", default="data/jobs")
    parser.add_argument("--run-id", type=str, help="Unused but accepted for consistency")
    args = parser.parse_args()

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    jobs = scrape_indeed_jobs(args.keywords, args.location, max_jobs=args.max)
    save_jobs(jobs, os.path.join(args.output_dir, "indeed_local_results.json"))
