import json
import os
import glob
import argparse
from datetime import datetime

DEFAULT_DATA_DIR = 'data/jobs'
DEFAULT_HISTORY_FILE = 'data/applied_history.json'
DEFAULT_OUTPUT_MD_DIR = 'readable_summaries'

# Default Scoring Rules (if no config provided)
DEFAULT_POSITIVE_KEYWORDS = {
    "Python": 3,
    "TypeScript": 3,
    "Next.js": 3,
    "AI": 4,
    "Agent": 4,
    "LLM": 4,
    "Machine Learning": 3,
    "React": 2,
    "Godot": 2,
    "Automation": 2,
    "Junior": 2,
    "Remote": 2,
    "Cannabis": 5,
    "Retail": 3
}

DEFAULT_NEGATIVE_KEYWORDS = {
    "Senior": -5,
    "Lead": -3,
    "Manager": -3,
    "Staff": -5,
    "Principal": -5
}

def load_config(config_path):
    if not config_path or not os.path.exists(config_path):
        return DEFAULT_POSITIVE_KEYWORDS, DEFAULT_NEGATIVE_KEYWORDS
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            pos = config.get('positive_keywords', DEFAULT_POSITIVE_KEYWORDS)
            neg = config.get('negative_keywords', DEFAULT_NEGATIVE_KEYWORDS)
            return pos, neg
    except Exception as e:
        print(f"⚠️ Error loading config {config_path}: {e}. Using defaults.")
        return DEFAULT_POSITIVE_KEYWORDS, DEFAULT_NEGATIVE_KEYWORDS

def load_all_jobs(data_dir):
    all_jobs = []
    # Find all json files in data_dir ending in _results.json
    files = glob.glob(os.path.join(data_dir, '*_results.json'))
    
    print(f"📂 Found {len(files)} data files to merge.")
    
    for fpath in files:
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
                # Ensure it's a list
                if isinstance(data, list):
                    # Add source filename if not present
                    for job in data:
                        if 'source' not in job:
                            job['source'] = os.path.basename(fpath)
                    all_jobs.extend(data)
        except Exception as e:
            print(f"   x Error reading {fpath}: {e}")
            
    return all_jobs

def score_job(job, positive_keywords, negative_keywords):
    text = (job.get('title', '') + " " + job.get('description', '')).lower()
    score = 0
    matched = []
    
    # Positive
    for word, points in positive_keywords.items():
        if word.lower() in text:
            score += points
            matched.append(word)
            
    # Negative
    for word, points in negative_keywords.items():
        if word.lower() in text:
            # Simple check: if it's in the TITLE, it's a hard penalty.
            if word.lower() in job.get('title', '').lower():
                score += points
    
    return score, matched

def generate_markdown(jobs):
    lines = [f"# 🛡️ Daily Job Search Report - {datetime.now().strftime('%Y-%m-%d')}", ""]
    lines.append(f"**Total Jobs Found:** {len(jobs)}")
    lines.append("")
    
    # Group by score tiers
    high_priority = [j for j in jobs if j['score'] >= 5]
    medium_priority = [j for j in jobs if 2 <= j['score'] < 5]
    
    def print_group(group, title):
        if not group:
            return
        lines.append(f"## {title} ({len(group)})")
        for job in group:
            lines.append(f"### [{job.get('score')}] {job.get('title')} @ {job.get('company')}")
            lines.append(f"- **Location:** {job.get('location', 'Unknown')}")
            lines.append(f"- **Source:** {job.get('source')}")
            lines.append(f"- **Match:** {', '.join(job.get('matching_keywords', []))}")
            lines.append(f"- [Apply Here]({job.get('url')})")
            lines.append("")
            
    print_group(high_priority, "🔥 High Priority Matches")
    print_group(medium_priority, "⚠️ Medium Potential")
    
    return "\n".join(lines)

def load_history(history_file):
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def main():
    parser = argparse.ArgumentParser(description="⚖️ Rank and merge job listings")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--run-id", type=str, help="Run ID for this search session")
    parser.add_argument("--output-dir", type=str, help="Output directory (unused, for compatibility)")
    args = parser.parse_args()

    data_dir = DEFAULT_DATA_DIR
    output_md_dir = DEFAULT_OUTPUT_MD_DIR
    history_file = DEFAULT_HISTORY_FILE

    if args.run_id:
        data_dir = os.path.join('data', args.run_id)
        # Ensure output directories exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(output_md_dir, exist_ok=True)

    output_json = os.path.join(data_dir, 'master_listings.json')
    output_md = os.path.join(output_md_dir, f'Report_{args.run_id}.md' if args.run_id else 'Daily_Job_Report.md')

    pos_keywords, neg_keywords = load_config(args.config)

    print("⚖️  Ranking and merging jobs...")
    jobs = load_all_jobs(data_dir)
    history_urls = load_history(history_file)
    print(f"📜 Loaded {len(history_urls)} previously applied/seen jobs.")

    # Deduplicate by URL
    unique_jobs = {j.get('url'): j for j in jobs if j.get('url')}.values()
    processed_jobs = []
    
    for job in unique_jobs:
        if job.get('url') in history_urls:
            continue
            
        s, m = score_job(job, pos_keywords, neg_keywords)
        job['score'] = s
        job['matching_keywords'] = m
        processed_jobs.append(job)
        
    # Sort by score descending
    processed_jobs.sort(key=lambda x: x['score'], reverse=True)
    
    # Save Master JSON
    with open(output_json, 'w') as f:
        json.dump(processed_jobs, f, indent=2)
    print(f"✅ Saved {len(processed_jobs)} unique jobs to {output_json}")
    
    # Save Markdown
    md_content = generate_markdown(processed_jobs)
    with open(output_md, 'w') as f:
        f.write(md_content)
    print(f"📝 Report generated at {output_md}")

if __name__ == "__main__":
    main()
