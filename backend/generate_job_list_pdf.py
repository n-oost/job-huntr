import markdown
import os
import asyncio
from playwright.async_api import async_playwright

# Simple, clean CSS for job listings
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');

body { 
    font-family: 'Roboto', sans-serif; 
    margin: 0; 
    padding: 40px; 
    color: #333; 
    line-height: 1.6;
} 
h1 {
    font-size: 28px;
    border-bottom: 2px solid #2c3e50;
    padding-bottom: 10px;
    margin-bottom: 30px;
    color: #2c3e50;
}
h2 {
    font-size: 20px;
    color: #2980b9;
    margin-top: 30px;
    margin-bottom: 10px;
    border-left: 4px solid #2980b9;
    padding-left: 10px;
}
strong {
    color: #555;
}
a {
    color: #3498db;
    text-decoration: none;
}
a:hover {
    text-decoration: underline;
}
hr {
    border: 0;
    border-top: 1px solid #eee;
    margin: 30px 0;
}
"""

async def convert_md_to_pdf(md_path, pdf_path):
    with open(md_path, 'r') as f:
        text = f.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(text, extensions=['extra'])

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>{CSS}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Use playwright to render PDF
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(full_html)
        await page.pdf(path=pdf_path, format="Letter", print_background=True, margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"})
        await browser.close()

if __name__ == "__main__":
    import sys
    
    # Default paths if not provided
    input_file = "readable_summaries/hr_jobs.md"
    output_file = "readable_summaries/hr_jobs.pdf"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))

    print(f"📄 Converting {input_file} to PDF...")
    asyncio.run(convert_md_to_pdf(input_file, output_file))
    print(f"✅ Successfully created {output_file}")
