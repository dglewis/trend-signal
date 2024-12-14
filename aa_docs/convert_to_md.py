import requests
from bs4 import BeautifulSoup

# URL of the HTML documentation (replace with the actual URL if needed)
url = "https://www.alphavantage.co/documentation/"

# Fetch the HTML content
response = requests.get(url)
html_content = response.text

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Function to convert HTML to Markdown
def convert_to_markdown(soup):
    # Initialize Markdown content
    markdown_content = "# API Documentation | Alpha Vantage\n\n"
    markdown_content += "## Overview\n"
    markdown_content += "Alpha Vantage offers free JSON APIs for realtime and historical stock market data & options data with over 50 technical indicators. Supports intraday, daily, weekly, and monthly stock quotes and technical analysis with charting-ready time series.\n\n"

    # Table of Contents
    markdown_content += "## Table of Contents\n"
    for header in soup.find_all(['h2', 'h3']):
        if header.name == 'h2':
            markdown_content += f"- [{header.text}](#{header.text.lower().replace(' ', '-')})\n"
        elif header.name == 'h3':
            markdown_content += f"  - [{header.text}](#{header.text.lower().replace(' ', '-')})\n"

    # Add sections
    for section in soup.find_all('h2'):
        markdown_content += f"\n## {section.text}\n"
        for content in section.find_next_siblings():
            if content.name == 'h2':
                break
            markdown_content += content.get_text(separator="\n", strip=True) + "\n\n"

    return markdown_content

# Convert HTML to Markdown
markdown_content = convert_to_markdown(soup)

# Save to aa_api.md
with open('aa_api.md', 'w') as md_file:
    md_file.write(markdown_content)

print("Conversion complete! The Markdown file 'aa_api.md' has been created.")