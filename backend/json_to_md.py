import json
import os
import glob
import argparse

DEFAULT_DATA_DIR = 'data/jobs'
DEFAULT_OUTPUT_DIR = 'readable_summaries'

def json_to_md(json_path, output_dir):
    filename = os.path.basename(json_path)
    md_filename = filename.replace('.json', '.md')
    md_path = os.path.join(output_dir, md_filename)
    
    print(f"📄 Converting {filename} -> {md_filename}...")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        if not isinstance(data, list):
            print(f"   ⚠️ Skipping {filename}: Not a list of items.")
            return

        lines = [f"# 📋 Job Listings from {filename.replace('_', ' ').title()}", ""]
        lines.append(f"**Total Entries:** {len(data)}")
        lines.append("")
        
        for item in data:
            title = item.get('title') or item.get('id') or "Untitled"
            company = item.get('company') or item.get('by') or "N/A"
            url = item.get('url') or (f"https://news.ycombinator.com/item?id={item.get('id')}" if 'id' in item else "#")
            
            lines.append(f"### {title}")
            lines.append(f"- **Company/Author:** {company}")
            if 'location' in item:
                lines.append(f"- **Location:** {item['location']}")
            if 'date' in item or 'time' in item:
                lines.append(f"- **Posted:** {item.get('date') or item.get('time')}")
            
            lines.append(f"- [Link to Job]({url})")
            
            # For HN or detailed posts
            if 'text' in item:
                lines.append("\n**Snippet:**")
                lines.append(f"> {item['text'][:500]}...")
            
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(md_path, 'w') as f:
            f.write("\n".join(lines))
            
    except Exception as e:
        print(f"   ❌ Error converting {filename}: {e}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=DEFAULT_DATA_DIR, help="Directory containing JSON files")
    parser.add_argument("--run-id", type=str, help="Run ID")
    args = parser.parse_args()

    data_dir = args.output_dir
    output_md_dir = DEFAULT_OUTPUT_DIR
    
    if not os.path.exists(output_md_dir):
        os.makedirs(output_md_dir)
        
    json_files = glob.glob(os.path.join(data_dir, '*.json'))
    for f in json_files:
        json_to_md(f, output_md_dir)
    
    print(f"\n✨ All conversions complete. Check '{output_md_dir}'")

if __name__ == "__main__":
    main()