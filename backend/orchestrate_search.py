import subprocess
import sys
import time
import os
import argparse
import json

SCRIPTS_DIR = 'backend' # Now that scripts are in backend/
PYTHON_EXEC = sys.executable

def run_script(script_name, keywords=None, run_id=None, config_path=None):
    script_path = os.path.join(script_name) # Assuming we are in backend/ or scripts are in current dir
    if not os.path.exists(script_path):
        # Try looking in SCRIPTS_DIR if not found in current dir
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        if not os.path.exists(script_path):
             script_path = script_name # Fallback

    print(f"\n{'='*60}")
    print(f"🚀 Launching {script_name}...")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        # Pass environment variables
        env = os.environ.copy()
        env['PYTHONPATH'] = os.getcwd() 
        
        cmd = [PYTHON_EXEC, script_path]
        
        # Pass Run ID if provided
        if run_id:
            cmd.extend(["--output-dir", os.path.join("data", run_id)])
            cmd.extend(["--run-id", run_id])

        # Pass Config if provided
        if config_path:
            cmd.extend(["--config", config_path])
        
        # Argument Injection Logic for legacy scripts
        if keywords:
            if script_name in ['linkedin_local.py', 'indeed_local.py', 'backend/linkedin_local.py', 'backend/indeed_local.py']:
                cmd.extend(["--keywords", keywords])
                
            elif script_name in ['gmaps_scrape.py', 'backend/gmaps_scrape.py']:
                # Map query to Maps search
                cmd.extend(["--query", keywords])
                
            elif script_name in ['local_company_sniper.py', 'backend/local_company_sniper.py']:
                kw_list = keywords.split()
                if kw_list:
                    cmd.append("--keywords")
                    cmd.extend(kw_list)
                
                cmd.extend(["--inputs", "data/companies/London_Tech_Landscape.md", "data/companies/gmaps_discovered.json"])

        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, 
            env=env,
            capture_output=False, 
            text=True
        )
        
        duration = time.time() - start_time
        if result.returncode == 0:
            print(f"✅ {script_name} completed in {duration:.2f}s")
            return True
        else:
            print(f"❌ {script_name} failed with code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"💥 Critical error running {script_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="🛡️ Unified Job Search Pipeline Orchestrator")
    parser.add_argument("--linkedin", action="store_true", help="Scrape LinkedIn")
    parser.add_argument("--indeed", action="store_true", help="Scrape Indeed (Local)")
    parser.add_argument("--companies", action="store_true", help="Scrape Local Companies (Sniper)")
    parser.add_argument("--hn", action="store_true", help="Scrape Hacker News")
    parser.add_argument("--niche", action="store_true", help="Scrape Niche Boards")
    parser.add_argument("--rank", action="store_true", help="Merge and Rank results (Report generation)")
    parser.add_argument("--all", action="store_true", help="Run all modules (default if no flags)")
    parser.add_argument("--query", type=str, help="Search keywords (e.g. 'Cannabis Retail')")
    parser.add_argument("--config", type=str, help="Path to config JSON file")
    parser.add_argument("--run-id", type=str, help="Run ID for this session")

    args = parser.parse_args()

    # Load config if provided
    config_data = {}
    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config_data = json.load(f)

    # Override query if in config and not on CLI
    query = args.query or config_data.get('query')
    run_id = args.run_id or config_data.get('run_id') or f"run_{int(time.time())}"

    # Ensure data directory exists
    os.makedirs(os.path.join("data", run_id), exist_ok=True)

    # Determine what to run
    run_any = any([args.linkedin, args.indeed, args.companies, args.hn, args.niche, args.rank])
    do_all = args.all or not run_any

    print(f"🤖 Starting Job Search Pipeline (Run ID: {run_id}, Mode: {'Full' if do_all else 'Targeted'})...")

    tasks = []
    if do_all or args.linkedin: tasks.append('linkedin_local.py')
    if do_all or args.indeed: tasks.append('indeed_local.py')
    
    if do_all or args.companies:
        if query:
            tasks.append('gmaps_scrape.py')
        tasks.append('local_company_sniper.py')
        
    if do_all or args.hn: tasks.append('hn_scrape.py')
    if do_all or args.niche: tasks.append('niche_scrape.py')
    
    # Always run ranker and converter last if we ran any scraper, or if specifically requested
    if do_all or args.rank or (run_any and not args.rank):
        tasks.append('rank_jobs.py')
        tasks.append('json_to_md.py')

    failed = []
    for task in tasks:
        # Check if task is in current dir or backend/
        task_path = task
        if not os.path.exists(task_path):
            task_path = os.path.join('backend', task)
            
        success = run_script(task_path, keywords=query, run_id=run_id, config_path=args.config)
        if not success:
            failed.append(task)
            print(f"⚠️  Task {task} failed.")

    if failed:
        print(f"\n❌ Pipeline finished with failures in: {', '.join(failed)}")
    else:
        print(f"\n🎉 Pipeline Complete! Results in data/{run_id}/")

if __name__ == "__main__":
    main()
