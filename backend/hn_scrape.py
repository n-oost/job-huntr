import requests
import json
import time

def fetch_hn_jobs():
    print("🕵️  Fetching 'Who is Hiring' from Hacker News...")
    
    # 1. Get the latest 'Who is Hiring' story ID
    user_url = "https://hacker-news.firebaseio.com/v0/user/whoishiring.json"
    user_data = requests.get(user_url).json()
    # The first submission is usually the latest monthly post
    latest_story_id = user_data['submitted'][0] 
    
    # 2. Get the story details to confirm title
    story_url = f"https://hacker-news.firebaseio.com/v0/item/{latest_story_id}.json"
    story = requests.get(story_url).json()
    print(f"📄  Found: {story.get('title')}")
    
    # 3. Get the top-level comments (job posts)
    comment_ids = story.get('kids', [])[:50] # Limit to top 50 for quick test
    print(f"    Scanning {len(comment_ids)} top-level posts...")
    
    jobs = []
    for cid in comment_ids:
        comment_url = f"https://hacker-news.firebaseio.com/v0/item/{cid}.json"
        comment = requests.get(comment_url).json()
        
        if comment and 'text' in comment:
            text = comment['text']
            # Simple keyword filter for Canada/Remote
            if "Canada" in text or "Remote" in text or "London" in text:
                jobs.append({
                    "id": cid,
                    "by": comment.get('by'),
                    "time": comment.get('time'),
                    "text": text[:500] + "..." # Truncate for preview
                })
        time.sleep(0.1) # Be nice to API
        
    return jobs

def save_jobs(jobs, filename):
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"💾  Saved {len(jobs)} relevant jobs to {filename}")

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/jobs")
    parser.add_argument("--run-id", type=str, help="Unused but accepted for consistency")
    args = parser.parse_args()

    # Ensure output dir exists
    os.makedirs(args.output_dir, exist_ok=True)

    jobs = fetch_hn_jobs()
    save_jobs(jobs, os.path.join(args.output_dir, "hn_results.json"))
