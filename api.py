from fastapi import FastAPI, HTTPException

from web import fetch_urls

from fastapi.middleware.cors import CORSMiddleware
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
from fastapi import HTTPException
from web import fetch_urls ,crawl_sequential  ,get_urls_from_sitemap
# from mangum import Mangum


app = FastAPI()

# handler = Mangum(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/crawl")
async def chat(urls: list[str]):
    try:
        return await fetch_urls(urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/website-url")
async def website_url(url:str):
    try:
        urls = get_urls_from_sitemap(url)
        if urls:
            print(f"Found {len(urls)} URLs to crawl")
            await crawl_sequential(urls)
        else:
            print("No URLs found to crawl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Welcome to the API!"}
