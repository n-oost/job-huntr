import sys
import os
import json
import argparse
from playwright.sync_api import sync_playwright
import time

# Constants
HISTORY_FILE = os.path.join('data', 'applied_history.json')

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def run_apply_bot(url, resume_path):
    print(f"🤖 Starting Application Bot for: {url}")
    
    with sync_playwright() as p:
        # Launch Headed for User Interaction
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("🌐 Navigating to page...")
            page.goto(url)
            page.wait_for_load_state("networkidle")

            print("📝 Attempting to Auto-Fill (Best Effort)...")
            
            # Common Selectors
            fill_map = {
                'First Name': ['input[name*="first"]', 'input[id*="first"]', 'input[label*="First"]'],
                'Last Name': ['input[name*="last"]', 'input[id*="last"]', 'input[label*="Last"]'],
                'Email': ['input[name*="email"]', 'input[type="email"]'],
                'Phone': ['input[name*="phone"]', 'input[type="tel"]'],
                'LinkedIn': ['input[name*="linkedin"]', 'input[name*="website"]']
            }
            
            data_map = {
                'First Name': 'Noah',
                'Last Name': 'Oosting',
                'Email': 'noahoos@gmail.com',
                'Phone': '548-502-0177',
                'LinkedIn': 'https://www.linkedin.com/in/noahoosting/'
            }

            for field, selectors in fill_map.items():
                for selector in selectors:
                    try:
                        if page.is_visible(selector):
                            page.fill(selector, data_map[field])
                            print(f"   ✅ Filled {field}")
                            break
                    except:
                        continue

            # File Upload
            print("📂 Checking for File Upload...")
            file_inputs = page.query_selector_all('input[type="file"]')
            if file_inputs and resume_path:
                print(f"   📄 Uploading: {resume_path}")
                file_inputs[0].set_input_files(resume_path)
            else:
                print("   ⚠️ No file input found or no resume provided.")

            print("
🛑 HANDOVER TO USER")
            print("1. Review the form.")
            print("2. Make corrections.")
            print("3. Click 'Submit' manually.")
            print("4. Close the browser window when done.")

            # Wait for browser closure
            while context.pages:
                time.sleep(1)
            
            # Post-Action
            print("🔒 Browser closed. Recording application...")
            history = load_history()
            if url not in history:
                history.append(url)
                save_history(history)
                print("✅ Added to Applied History.")
            else:
                print("ℹ️  Already in history.")

        except Exception as e:
            print(f"💥 Error: {e}")
            input("Press Enter to close browser...")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Job Application URL")
    parser.add_argument("--resume", help="Path to PDF Resume", default=None)
    args = parser.parse_args()

    run_apply_bot(args.url, args.resume)

if __name__ == "__main__":
    main()
