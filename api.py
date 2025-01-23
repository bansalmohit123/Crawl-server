from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List
from pydantic import BaseModel, HttpUrl, ValidationError
from web import fetch_urls, crawl_sitemap
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input validation models
class CrawlRequest(BaseModel):
    urls: List[HttpUrl]

class SitemapRequest(BaseModel):
    url: HttpUrl

app = Flask(__name__)
CORS(app)

@app.route("/crawl", methods=["POST"])
def crawl_urls():
    """
    Crawl a list of URLs and return their processed content.
    """
    try:
        data = request.json
        crawl_request = CrawlRequest(**data)
        logger.info(f"Received request to crawl {len(crawl_request.urls)} URLs")
        results = fetch_urls([str(url) for url in crawl_request.urls])
        return jsonify(results)
    except ValidationError as e:
        logger.error(f"Validation error in crawl endpoint: {str(e)}")
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in crawl endpoint: {str(e)}")
        return jsonify({"detail": str(e)}), 500

@app.route("/website-url", methods=["POST"])
def crawl_website():
    """
    Crawl an entire website using its sitemap.
    """
    try:
        data = request.json
        sitemap_request = SitemapRequest(**data)
        logger.info(f"Received request to crawl sitemap: {sitemap_request.url}")
        results = crawl_sitemap(str(sitemap_request.url))
        return jsonify(results)
    except ValidationError as e:
        logger.error(f"Validation error in website-url endpoint: {str(e)}")
        return jsonify({"detail": str(e)}), 400
    except Exception as e:
        logger.error(f"Error in website-url endpoint: {str(e)}")
        return jsonify({"detail": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    """
    return jsonify({"status": "healthy"})

@app.route("/", methods=["GET"])
def hello_world():
    """
    Hello World endpoint.
    """
    return jsonify({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
