import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from readability import Document
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch(session, url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        async with session.get(url, headers=headers) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors
            html = await response.text()
            return extract_main_content(html)
    except aiohttp.ClientError as e:
        logger.error(f"ClientError for {url}: {e}")
        return f"ClientError: {e}"
    except aiohttp.http_exceptions.HttpProcessingError as e:
        logger.error(f"HttpProcessingError for {url}: {e}")
        return f"HttpProcessingError: {e}"
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.error(f"ClientConnectorError for {url}: {e}")
        return f"ClientConnectorError {e}"
    except Exception as e:
        logger.error(f"Exception for {url}: {e}")
        return f"Exception: {e}"

def clean_text(text):
    # Remove unreadable characters and excessive whitespace
    text = re.sub(r'\\[rnt]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_main_content(html):
    try:
        doc = Document(html)
        full_html = doc.content()
        
        # Create BeautifulSoup object and extract text
        soup = BeautifulSoup(full_html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        cleaned_text = clean_text(text)
        
        # Extract title and meta description if needed
        title = soup.title.string if soup.title else 'No title'
        meta_desc = ''
        if soup.find("meta", {"name": "description"}):
            meta_desc = soup.find("meta", {"name": "description"}).get("content", "")
        
        return {
            "title": title,
            "meta_description": meta_desc,
            "text": cleaned_text
        }
    except Exception as e:
        logger.error(f"Error extracting content: {e}")
        return f"Error extracting content: {e}"

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def main():
    # Read URLs from CSV
    df = pd.read_csv('data/urls_raw.csv')

    # Fetch content for each URL
    urls = df['URL'].tolist()
    contents = await fetch_all(urls)

    # Prepare data for JSONL
    data = [{"URL": url, "content": content} for url, content in zip(urls, contents)]

    # Write data to JSONL file
    with open('data/urls_with_content2.jsonl', 'w') as jsonl_file:
        for entry in data:
            jsonl_file.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    asyncio.run(main())
