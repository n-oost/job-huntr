import json
import os
import argparse

def filter_jobs(input_json, output_md, keywords, title_text):
    with open(input_json, 'r') as f:
        jobs = json.load(f)
    
    filtered_jobs = []
    for job in jobs:
        title = job.get("title", "") or ""
        snippet = job.get("snippet", "") or ""
        text = job.get("text", "") or ""
        
        combined_text = (title + " " + snippet + " " + text).lower()
        
        # Check if any keyword is in the combined text
        if any(kw.lower() in combined_text for kw in keywords):
            filtered_jobs.append(job)
    
    with open(output_md, 'w') as f:
        f.write(f"# 📋 {title_text}\n\n")
        f.write(f"**Total Captured:** {len(filtered_jobs)}\n")
        f.write(f"**Generated:** {os.popen('date').read().strip()}\n\n---\n\n")
        
        for job in filtered_jobs:
            url = job.get('url', '#')
            f.write(f"## {job.get('title', 'N/A')}\n")
            f.write(f"**Company:** {job.get('company', 'N/A')}\n")
            if job.get('location'):
                f.write(f"**Location:** {job['location']}\n")
            if job.get('date'):
                f.write(f"**Posted:** {job['date']}\n")
            if job.get('source'):
                f.write(f"**Source:** {job['source']}\n")
            
            f.write(f"\n[Apply Link]({url})  \n**URL:** {url}\n\n---\n\n")
    
    return len(filtered_jobs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter jobs by keywords")
    parser.add_argument("--keywords", nargs="+", required=True, help="List of keywords to search for")
    parser.add_argument("--output", required=True, help="Output Markdown file path")
    parser.add_argument("--title", default="Job Listings", help="Title for the Markdown report")
    
    args = parser.parse_args()
    
    count = filter_jobs("data/jobs/master_listings.json", args.output, args.keywords, args.title)
    print(f"✅ Filtered {count} jobs matching {args.keywords} and saved to {args.output}")
