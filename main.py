import aiohttp
import asyncio
import pandas as pd



async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors
            return await response.text()
    except aiohttp.ClientError as e:
        return f"ClientError: {e}"
    except aiohttp.http_exceptions.HttpProcessingError as e:
        return f"HttpProcessingError: {e}"
    except aiohttp.client_exceptions.ClientConnectorError as e:
        return f"ClientConnectionError {e}"
    except Exception as e:
        return f"Exception: {e}"

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            tasks.append(fetch(session, url))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

async def main():
    contents = await fetch_all(urls)
    for i, content in enumerate(contents):
        print(f"Content from URL {urls[i]}:\n{content[:500]}\n")  # Print the first 500 characters of each content

if __name__ == "__main__":
    # Load URLs from CSV file
    csv_file = 'data/london_music_venues.csv'  # Path to your CSV file
    urls_df = pd.read_csv(csv_file)
    urls = urls_df['URL'].tolist()  # Assuming the column name is 'URLs'

    asyncio.run(main())
