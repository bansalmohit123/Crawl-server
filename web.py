from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
import requests
from xml.etree import ElementTree
import logging
from flask import Flask, jsonify, request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def fetch_urls(urls: List[str]) -> List[str]:
    """
    Fetch and process content from a list of URLs using crawl4ai.
    
    Args:
        urls (List[str]): List of URLs to crawl
        
    Returns:
        List[str]: List of processed markdown content for each URL
    """
    if not urls:
        return []
        
    try:
        config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=0.6),
                options={
                    "ignore_links": True,
                    "body_width": 1000,
                    "escape_html": True,
                    "skip_internal_links": True
                }
            )
        )
        
        contents = []
        async with AsyncWebCrawler() as crawler:
            for url in urls:
                try:
                    logger.info(f"Crawling URL: {url}")
                    result = await crawler.arun(url, config=config)
                    
                    if result.success:
                        md_object = result.markdown_v2
                        contents.append(md_object.fit_markdown)
                        logger.info(f"Successfully crawled: {url}")
                    else:
                        logger.error(f"Failed to crawl {url}: {result.error_message}")
                        contents.append("")
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    contents.append("")
                    
        return contents
    except Exception as e:
        logger.error(f"Error in fetch_urls: {str(e)}")
        return []

async def crawl_sequential(urls: List[str]) -> List[str]:
    """
    Crawl a list of URLs sequentially with session reuse and return the list of markdown content.
    
    Args:
        urls (List[str]): List of URLs to crawl
        
    Returns:
        List[str]: List of processed markdown content for each URL
    """
    logger.info("\n=== Sequential Crawling with Session Reuse ===")

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

    contents = []
    try:
        session_id = "session1"  # Reuse the same session across all URLs
        for url in urls:
            result = await crawler.arun(
                url=url,
                config=crawl_config,
                session_id=session_id
            )
            if result.success:
                logger.info(f"Successfully crawled: {url}")
                contents.append(result.markdown_v2.raw_markdown)
            else:
                logger.error(f"Failed: {url} - Error: {result.error_message}")
                contents.append("")
    finally:
        # After all URLs are done, close the crawler (and the browser)
        await crawler.close()
    
    return contents



def get_pydantic_ai_docs_urls(sitemap_url: str)-> List[str]:
    """
    Fetches all URLs from the Pydantic AI documentation.
    Uses the sitemap (https://ai.pydantic.dev/sitemap.xml) to get these URLs.
    
    Returns:
        List[str]: List of URLs
    """            
    # sitemap_url = "https://ai.pydantic.dev/sitemap.xml"
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