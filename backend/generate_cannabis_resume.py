import markdown
import os
import asyncio
from playwright.async_api import async_playwright

# Professional CSS for a two-column resume matching your template style
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

* { box-sizing: border-box; }
body {
    font-family: 'Inter', sans-serif;
    line-height: 1.3;
    color: #333;
    margin: 0; padding: 0;
    background: #fff;
    font-size: 10pt;
}
.container {
    display: flex;
    flex-direction: row;
    min-height: 297mm;
}
/* Left Sidebar (1/3) - Following your template style */
.sidebar {
    width: 30%;
    background: #f8f9fa;
    padding: 30px 20px;
    border-right: 1px solid #eee;
}
/* Main Content (2/3) */
.main-content {
    width: 70%;
    padding: 30px 35px;
}
h1 {
    font-size: 24pt;
    font-weight: 700;
    margin: 0 0 5px 0;
    color: #000;
    text-transform: uppercase;
}
h2 {
    font-size: 12pt;
    font-weight: 700;
    margin: 20px 0 10px 0;
    color: #2c3e50;
    text-transform: uppercase;
    border-bottom: 2px solid #27ae60; /* Cannabis green accent */
    padding-bottom: 3px;
}
.sidebar h2 {
    font-size: 10pt;
    margin-top: 25px;
    border-bottom: 1px solid #ccc;
}
h3 {
    font-size: 11pt;
    font-weight: 700;
    margin: 15px 0 2px 0;
}
p { margin: 0 0 8px 0; }
ul {
    padding-left: 15px;
    margin: 5px 0 15px 0;
}
li { margin-bottom: 4px; }
.contact-info {
    font-size: 9pt;
    color: #555;
    margin-bottom: 20px;
}
.highlight-box {
    background: #e8f5e9;
    padding: 10px;
    border-radius: 4px;
    border-left: 4px solid #27ae60;
    margin-bottom: 15px;
}
@media print {
    body { -webkit-print-color-adjust: exact; }
    .sidebar { background: #f8f9fa !important; }
}
"""

async def generate_pdf(md_path, pdf_path):
    with open(md_path, 'r') as f:
        lines = f.readlines()

    # Simple Header Extraction
    name = lines[0].replace('# ', '').strip()
    contact = lines[1].strip()
    links = lines[2].strip()
    
    # Split content into Sidebar and Main
    content = "".join(lines[3:])
    sections = content.split('\n## ')
    
    main_html = f"<h1>{name}</h1>"
    main_html += f"<div class='contact-info'>{contact}<br>{links}</div>"
    
    sidebar_html = ""
    
    for section in sections:
        if not section.strip(): continue
        parts = section.split('\n', 1)
        title = parts[0].strip()
        body = parts[1].strip() if len(parts) > 1 else ""
        
        # Convert markdown to HTML
        content_html = markdown.markdown(body, extensions=['extra'])
        
        if title == "CERTIFICATIONS":
            # Add a highlight box for CannSell
            sidebar_html += f"<div class='section'><h2>{title}</h2>{content_html}</div>"
        elif title in ["EDUCATION", "SKILLS & LANGUAGES"]:
            sidebar_html += f"<div class='section'><h2>{title}</h2>{content_html}</div>"
        else:
            main_html += f"<div class='section'><h2>{title}</h2>{content_html}</div>"

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{CSS}</style>
    </head>
    <body>
        <div class="container">
            <div class="sidebar">
                {sidebar_html}
            </div>
            <div class="main-content">
                {main_html}
            </div>
        </div>
    </body>
    </html>
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(full_html)
        await page.pdf(path=pdf_path, format="Letter", print_background=True)
        await browser.close()

if __name__ == "__main__":
    md_file = "resumes/Noah_Oosting_Cannabis_Retail.md"
    pdf_file = "resumes/Noah_Oosting_Cannabis_Resume_2026.pdf"
    asyncio.run(generate_pdf(md_file, pdf_file))