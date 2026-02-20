import requests
from bs4 import BeautifulSoup
import json
import os

def scrape_london_tech_jobs():
    print("🕵️  Scanning LondonTechJobs.ca...")
    url = "https://londontechjobs.ca/joblist.aspx"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch LondonTechJobs: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Based on the HTML structure analyzed
    cards = soup.find_all('div', class_='gm-card')
    print(f"   > Found {len(cards)} raw cards on the first page.")
    
    jobs = []
    for card in cards:
        try:
            title_elem = card.find('h4', class_='gm-card-title')
            company_elem = card.find('h3', class_='gm-card-subtitle')
            link_elem = card.find('a', class_='gm-card-link')
            date_elem = card.find('div', class_='gm-card-timestamp')
            
            if title_elem and company_elem:
                title = title_elem.get_text(strip=True).replace("NEW", "").strip()
                company = company_elem.get_text(strip=True)
                link = "https://londontechjobs.ca/" + link_elem['href'] if link_elem else ""
                date_str = date_elem.get_text(strip=True) if date_elem else "Recent"
                
                # Check for keywords relevant to Noah
                keywords = ["developer", "engineer", "programmer", "analyst", "ai", "software", "data", "web", "android"]
                if any(kw in title.lower() for kw in keywords):
                    jobs.append({
                        "title": title,
                        "company": company,
                        "url": link,
                        "posted": date_str,
                        "source": "LondonTechJobs.ca"
                    })
        except Exception as e:
            continue
            
    return jobs

def main():
    jobs = scrape_london_tech_jobs()
    output_path = 'tools/scrapers/london_tech_results.json'
    
    with open(output_path, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    print(f"✅ Saved {len(jobs)} relevant tech jobs from LondonTechJobs.ca to {output_path}")

if __name__ == "__main__":
    main()
