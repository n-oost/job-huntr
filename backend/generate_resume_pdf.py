import markdown
import os
import asyncio
from playwright.async_api import async_playwright

# Professional CSS from professional-style.json
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&display=swap');

body { 
    font-family: 'Lato', sans-serif; 
    margin: 0; 
    padding: 0; 
    color: #333; 
} 
.resume-container { 
    display: flex; 
    flex-direction: row; 
    min-height: 100vh; 
} 
.sidebar { 
    width: 32%; 
    background-color: #2c3e50; 
    color: #ecf0f1; 
    padding: 40px 25px; 
    box-sizing: border-box; 
} 
.main-content { 
    width: 68%; 
    padding: 40px 40px; 
    background-color: #ffffff; 
    box-sizing: border-box; 
} 
.profile-pic-placeholder { 
    width: 80px; 
    height: 80px; 
    background: #ecf0f1; 
    color: #2c3e50; 
    border-radius: 50%; 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    margin-bottom: 30px; 
} 
.profile-pic-placeholder h1 { 
    font-size: 28px; 
    margin: 0; 
} 
.sidebar h2 { 
    font-size: 14px; 
    text-transform: uppercase; 
    letter-spacing: 2px; 
    border-bottom: 1px solid #34495e; 
    padding-bottom: 5px; 
    margin-top: 30px; 
    margin-bottom: 15px; 
    color: #bdc3c7; 
} 
.sidebar p, .sidebar li { 
    font-size: 13px; 
    line-height: 1.6; 
    color: #dfe6e9; 
    list-style: none; 
    margin-bottom: 8px; 
} 
.sidebar strong { 
    color: #ffffff; 
    font-weight: 700; 
} 
.sidebar a { 
    color: #3498db; 
    text-decoration: none; 
} 
.header-name h1 { 
    font-size: 42px; 
    font-weight: 900; 
    text-transform: uppercase; 
    margin: 0; 
    color: #2c3e50; 
    letter-spacing: 1px; 
    line-height: 1; 
} 
.header-name h2 { 
    font-size: 18px; 
    font-weight: 400; 
    text-transform: uppercase; 
    letter-spacing: 3px; 
    color: #2980b9; 
    margin-top: 10px; 
    margin-bottom: 40px; 
} 
.main-content h2 { 
    font-size: 16px; 
    font-weight: 700; 
    text-transform: uppercase; 
    letter-spacing: 1px; 
    border-bottom: 2px solid #2980b9; 
    padding-bottom: 5px; 
    margin-top: 35px; 
    margin-bottom: 20px; 
    color: #2c3e50; 
} 
h3 { 
    font-size: 15px; 
    font-weight: 700; 
    margin: 20px 0 5px 0; 
    color: #000; 
} 
h3 strong { 
    font-weight: 900; 
} 
p { 
    margin: 0 0 10px 0; 
    font-size: 14px; 
    line-height: 1.6; 
    color: #455a64; 
} 
ul { 
    padding-left: 18px; 
    margin-top: 5px; 
} 
li { 
    margin-bottom: 6px; 
    font-size: 14px; 
    color: #455a64; 
}
@media print {
    body { -webkit-print-color-adjust: exact; }
    .sidebar { background-color: #2c3e50 !important; }
}
"""

async def convert_md_to_pdf(md_path, pdf_path):
    with open(md_path, 'r') as f:
        text = f.read()

    # Parse Sections
    sections = text.split('\n## ')
    header = sections[0]
    
    sidebar_html = ""
    main_html = ""
    
    # Process Header
    lines = [l.strip() for l in header.split('\n') if l.strip()]
    name = lines[0].replace('# ', '')
    contact_info = lines[1:]
    
    initials = "".join([n[0] for n in name.split() if n])
    
    # Sidebar starts with Initials placeholder and contact info
    sidebar_html += f"<div class='profile-pic-placeholder'><h1>{initials}</h1></div>"
    sidebar_html += "<div class='contact-info'>"
    for item in contact_info:
        clean_item = item.replace('**', '').replace('*', '').replace('|', '<br>')
        # Convert markdown links to HTML links
        import re
        clean_item = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', clean_item)
        sidebar_html += f"<p>{clean_item}</p>"
    sidebar_html += "</div>"
    
    # Main content starts with Header Name and Title
    main_html += f"<div class='header-name'><h1>{name}</h1><h2>Software Developer</h2></div>"

    # Distribute sections
    for section in sections[1:]:
        lines = section.split('\n')
        title = lines[0].strip()
        body = '\n'.join(lines[1:])
        content_html = markdown.markdown(body, extensions=['extra'])
        
        if any(kw in title.upper() for kw in ['SKILL', 'EDUCATION', 'CERTIFICATION']):
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
        <div class="resume-container">
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

    # Use playwright to render PDF
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(full_html)
        await page.pdf(path=pdf_path, format="Letter", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        await browser.close()

if __name__ == "__main__":
    import sys
    md_file = sys.argv[1] if len(sys.argv) > 1 else "resumes/md/EventConnect_Laravel_Developer.md"
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else "resumes/pdf/EventConnect_Laravel_Developer.pdf"
    
    if not os.path.exists(os.path.dirname(pdf_file)):
        os.makedirs(os.path.dirname(pdf_file))

    asyncio.run(convert_md_to_pdf(md_file, pdf_file))
    print(f"Successfully converted {md_file} to {pdf_file}")