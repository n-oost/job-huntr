import os
import re
import sys
import argparse
import jinja2
import base64
import json
from google import genai
from google.genai import types
from playwright.sync_api import sync_playwright

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(BASE_DIR, 'resumes', 'Master_Profile.md')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'resumes', 'templates')
OUTPUT_BASE_DIR = os.path.join(BASE_DIR, 'resumes', 'applications')
PHOTO_PATH = os.path.join(TEMPLATE_DIR, 'noah_professional_shot.jpeg')

# AI Config
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyAL1jND4beZ8NRsrWMihw40Pl40VhGxzOs")
client = genai.Client(api_key=GEMINI_API_KEY)

def clean_md(text):
    """Remove Markdown bold/italic markers and handle whitespace."""
    if not text: return ""
    text = text.replace('**', '').replace('__', '').replace('*', '')
    return text.strip()

def clean_url(url):
    """Remove protocol and www for display."""
    if not url: return ""
    return url.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')

def extract_year(date_str):
    """Extract just the year from a date string like 2025-01-01 or Jan 2025."""
    if not date_str: return ""
    if "Present" in date_str: return "Present"
    match = re.search(r'\b(20\d{2})\b', date_str)
    return match.group(1) if match else date_str

def get_base64_image(image_path):
    """Convert image to base64 string for HTML embedding."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    return None

def parse_profile(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    data = {
        'name': 'Noah Oosting',
        'title': 'Software Developer',
        'contact': {},
        'summary': '',
        'experience': [],
        'projects': [],
        'education': [],
        'skills': [],
        'certifications': [],
        'profile_photo': get_base64_image(PHOTO_PATH),
        'keywords': []
    }

    def extract_field(field_name, content):
        esc_field = field_name.replace('(', r'\(').replace(')', r'\)')
        pattern = rf'\*\*({esc_field}):\*\*\s*(.*)'
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            val = match.group(2).strip()
            if '|' in val: val = val.split('|')[0].strip()
            val = re.sub(r'\s*\([^)]*\)', '', val).strip()
            return val
        return None

    data['name'] = extract_field('Full Name', text) or 'Noah Oosting'
    data['contact']['email'] = extract_field('Email', text)
    data['contact']['phone'] = extract_field('Phone', text)
    data['contact']['location'] = extract_field('Location', text)
    data['contact']['linkedin'] = extract_field('LinkedIn', text)
    data['contact']['github'] = extract_field(r'GitHub \(Primary\)', text) or extract_field('GitHub', text)
    data['contact']['portfolio'] = extract_field('Portfolio', text)

    for key in ['linkedin', 'github', 'portfolio']:
        if data['contact'].get(key):
            data['contact'][f'{key}_display'] = clean_url(data['contact'][key])

    summary_long = extract_field(r'Summary \(Long\)', text)
    summary_short = extract_field(r'Summary \(Short\)', text)
    data['summary'] = summary_long or summary_short or ""

    try:
        exp_section = text.split('## 3. Professional Experience')[1].split('## 4. Education')[0]
        exp_blocks = exp_section.split('###')[1:]
        for block in exp_blocks:
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            if not lines: continue
            role = clean_md(lines[0])
            company = ""
            period = ""
            desc_bullets = []
            for line in lines[1:]:
                if '**Company:**' in line:
                    company = clean_md(line.split('**Company:**')[1])
                elif '**Start Date:**' in line:
                    date_match = re.search(r'\*\*Start Date:\*\*\s*(.*?)\s*\|\s*\*\*End Date:\*\*\s*(.*)', line)
                    if date_match:
                        period = f"({extract_year(date_match.group(1))} – {extract_year(date_match.group(2))})"
                    else:
                        period = f"({extract_year(line.split('**Start Date:**')[1])})"
                elif '**Date:**' in line:
                    raw_date = line.split('**Date:**')[1].strip()
                    if '–' in raw_date or '-' in raw_date:
                        parts = re.split(r'[–-]', raw_date)
                        period = f"({extract_year(parts[0].strip())} – {extract_year(parts[1].strip())})"
                    else:
                        period = f"({extract_year(raw_date)})"
                elif 'Key Achievements:' in line:
                    parts = line.split('Key Achievements:')
                    if len(parts) > 1 and parts[1].strip():
                        content = parts[1].strip()
                        if ';' in content: desc_bullets.extend([clean_md(s) for s in content.split(';')])
                        else: desc_bullets.append(clean_md(content))
                elif line.strip().startswith('*') or line.strip().startswith('-'):
                    if not any(k in line for k in ['**Company:**', '**Location:**', '**Start Date:**', '**Date:**', '**Role Type:', 'Key Achievements:']):
                        clean_bullet = clean_md(line)
                        if clean_bullet: desc_bullets.append(clean_bullet)
            data['experience'].append({'role': role, 'company': company, 'period': period, 'description': desc_bullets, 'raw_text': block})
    except IndexError: pass

    try:
        proj_section = text.split('## 5. Projects & Portfolio')[1].split('## 6. Comprehensive Skills Inventory')[0]
        raw_items = re.split(r'\n### ', proj_section)
        if raw_items and not raw_items[0].strip(): raw_items = raw_items[1:]
        for item in raw_items:
            lines = [l.strip() for l in item.strip().split('\n') if l.strip()]
            if not lines: continue
            name = clean_md(lines[0].split('(')[0])
            if not name or "projects" in name.lower(): continue
            tech, desc = [], ""
            for line in lines[1:]:
                if '**Tech:**' in line: tech = [clean_md(t) for t in line.split('**Tech:**')[1].split(',')]
                elif '**Description:**' in line: desc += clean_md(line.split('**Description:**')[1]) + " "
                elif '**Hardest Problem:**' in line: desc += f" Solved challenge: {clean_md(line.split('**Hardest Problem:**')[1])}"
                elif line.strip().startswith('*') and not any(k in line for k in ['**Tech:**', '**Description:**', '**Hardest Problem:**']):
                     desc += " " + clean_md(line)
            data['projects'].append({'name': name, 'technologies': tech, 'description': desc.strip(), 'link': ''})
    except IndexError: pass

    try:
        edu_section = text.split('## 4. Education')[1].split('## 5. Projects & Portfolio')[0]
        edu_blocks = edu_section.split('###')[1:]
        for block in edu_blocks:
            lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
            if not lines: continue
            title = clean_md(lines[0])
            if any('**Institution:**' in l for l in lines):
                school, period = "", ""
                for line in lines:
                    if '**Institution:**' in line: school = clean_md(line.split('**Institution:**')[1])
                    elif '**Start Date:**' in line:
                        date_match = re.search(r'\*\*Start Date:\*\*\s*(.*?)\s*\|\s*\*\*End Date:\*\*\s*(.*)', line)
                        if date_match: period = f"({extract_year(date_match.group(1))} – {extract_year(date_match.group(2))})"
                        else: period = f"({extract_year(line.split('**Start Date:**')[1])})"
                data['education'].append({'institution': school, 'program': title, 'period': period, 'credentials': 'Diploma/Certificate'})
            elif "Certifications" in title or "OSSD" in title:
                for line in lines[1:]:
                    if line.startswith('*'):
                        cert_name = clean_md(line)
                        if cert_name: data['certifications'].append({'name': cert_name})
    except IndexError: pass

    try:
        skills_section = text.split('## 6. Comprehensive Skills Inventory')[1]
        for line in [l for l in skills_section.split('\n') if '**' in l]:
            if ':**' in line: data['skills'].extend([clean_md(s) for s in line.split(':**')[1].split(',')])
    except IndexError: pass

    return data

def extract_keywords(jd_text):
    if not jd_text: return []
    print("🤖 Extracting top 15 technical keywords...")
    prompt = f"Extract the top 15 technical keywords from this Job Description as a simple comma-separated list of terms (no explanation): {jd_text}"
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        return [k.strip() for k in response.text.split(',')]
    except Exception as e:
        print(f"⚠️ Keyword extraction failed: {e}")
        return []

def reword_with_ai(data, jd_text):
    print("🤖 Calling AI for intelligent rewording...")
    content_to_reword = {
        "summary": data['summary'],
        "experience": [{"role": e['role'], "description": e['description']} for e in data['experience']],
        "projects": [{"name": p['name'], "description": p['description']} for p in data['projects']]
    }
    
    prompt = f"""
    # Role
    You are an expert Executive Career Coach and ATS Specialist.
    # Objective
    Reword the provided summary, experience bullets, and project descriptions to perfectly match the Job Description.
    # Guidelines
    1. Truthfulness is mandatory. No hallucinating.
    2. Start bullets with strong action verbs.
    3. Output ONLY a valid JSON object matching the input schema.
    ---
    [Job Description]:
    {jd_text}
    ---
    [Data to Reword]:
    {json.dumps(content_to_reword, indent=2)}
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        ai_data = json.loads(response.text)
        data['summary'] = ai_data.get('summary', data['summary'])
        for i, exp in enumerate(ai_data.get('experience', [])):
            if i < len(data['experience']): data['experience'][i]['description'] = exp.get('description', data['experience'][i]['description'])
        for i, proj in enumerate(ai_data.get('projects', [])):
            if i < len(data['projects']): data['projects'][i]['description'] = proj.get('description', data['projects'][i]['description'])
        print("✅ AI Rewording Complete.")
        return data
    except Exception as e:
        print(f"⚠️ AI Rewording failed: {e}. Falling back to original content.")
        return data

def main():
    parser = argparse.ArgumentParser(description="Resume Tailor")
    parser.add_argument("--jd", type=str, help="Job Description")
    parser.add_argument("--title", type=str, help="Job Title", default="Job")
    parser.add_argument("--company", type=str, default="Target_Company", help="Company Name")
    parser.add_argument("--template", type=str, default="base_template.html", help="Template")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI rewording")
    args = parser.parse_args()
    
    data = parse_profile(PROFILE_PATH)
    jd_text = ""
    if args.jd:
        if os.path.exists(args.jd):
            with open(args.jd, 'r') as f: jd_text = f.read()
        else: jd_text = args.jd
    
    all_keywords = []
    if jd_text and not args.no_ai:
        all_keywords = extract_keywords(jd_text)
        data = reword_with_ai(data, jd_text)
    
    data['experience'] = sorted(data['experience'], key=lambda x: sum(1 for token in set(re.findall(r'\w+', (jd_text or "").lower())) if token in x['raw_text'].lower()), reverse=True)
    data['summary'] = clean_md(data['summary'])
    
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("base_template.html")

    safe_title = args.title.replace(' ', '_')
    safe_company = args.company.replace(' ', '_')
    # Updated naming convention: companyname_jobname
    job_dir = os.path.join(OUTPUT_BASE_DIR, f"{safe_company}_{safe_title}")
    os.makedirs(job_dir, exist_ok=True)

    # Updated filename convention: companyname_NoahOosting_resume
    base_filename = f"{safe_company}_NoahOosting_resume"

    print("🎨 Generating Human version...")
    data['keywords'] = []
    html_human = template.render(data)
    out_path_human = os.path.join(job_dir, f"{base_filename}_Human.pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html_human)
        page.wait_for_timeout(3000) 
        page.pdf(path=out_path_human, format="Letter", print_background=True)
        browser.close()
    print(f"✅ Generated Human: {out_path_human}")

    if all_keywords:
        print("🚀 Generating AI Boosted version...")
        data['keywords'] = all_keywords
        html_boosted = template.render(data)
        out_path_boosted = os.path.join(job_dir, f"{base_filename}_AI_Boosted.pdf")
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html_boosted)
            page.wait_for_timeout(3000) 
            page.pdf(path=out_path_boosted, format="Letter", print_background=True)
            browser.close()
        print(f"✅ Generated AI Boosted: {out_path_boosted}")

if __name__ == "__main__":
    main()
