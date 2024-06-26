import aiohttp
import asyncio
import pandas as pd
from bs4 import BeautifulSoup
from readability import Document
import json

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors
            html = await response.text()
            return extract_main_content(html)
    except aiohttp.ClientError as e:
        return f"ClientError: {e}"
    except aiohttp.http_exceptions.HttpProcessingError as e:
        return f"HttpProcessingError: {e}"
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return f"ClientConnectionError {e}"
    except Exception as e:
        return f"Exception: {e}"

def extract_main_content(html):
    try:
        doc = Document(html)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
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
    with open('data/urls_with_content.jsonl', 'w') as jsonl_file:
        for entry in data:
            jsonl_file.write(json.dumps(entry) + '\n')

if __name__ == "__main__":
    asyncio.run(main())
