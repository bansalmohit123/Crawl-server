from typing import List
from crawl4ai import AsyncWebCrawler,  BrowserConfig ,CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from fastapi import HTTPException
from crawl4ai.content_filter_strategy import PruningContentFilter
import requests
from xml.etree import ElementTree
async def fetch_urls(urls: list[str]) -> list[str]:
    if not urls:
        return []
        
    try:
        config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.6),
            options={"ignore_links": True, "body_width": 1000, "escape_html": True, "skip_internal_links": True}
            )
        )
        
        contents = []
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    result = await crawler.arun(url, config=config)
                    if result.success:
                        md_object = result.markdown_v2
                        contents.append(md_object.fit_markdown)
                    else:
                        print(f"Failed to crawl {url}: {result.error_message}")
                        contents.append("")
                except Exception as e:
                    print(f"Error processing {url}: {str(e)}")
                    contents.append("")
                    
        return contents
    except Exception as e:
        print(f"Error in fetch_urls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching URLs: {str(e)}")
    

async def crawl_sequential(urls: List[str]):
    print("\n=== Sequential Crawling with Session Reuse ===")

    browser_config = BrowserConfig(
        headless=True,
        # For better performance in Docker or low-memory environments:
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )

    crawl_config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )

    # Create the crawler (opens the browser)
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "session1"  # Reuse the same session across all URLs
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id
            )
            if result.success:
                print(f"Successfully crawled: {url}")
                # E.g. check markdown length
                print(f"Markdown length: {len(result.markdown_v2.raw_markdown)}")
            else:
                print(f"Failed: {url} - Error: {result.error_message}")
    finally:
        # After all URLs are done, close the crawler (and the browser)
        await crawler.close()

def get_urls_from_sitemap(sitemap_url: str) -> List[str]:
    """
    Fetches all URLs from the given sitemap URL.
    
    Args:
        sitemap_url (str): The URL of the sitemap.
    
    Returns:
        List[str]: List of URLs
    """            
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        # The namespace is usually defined in the root element
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []    
