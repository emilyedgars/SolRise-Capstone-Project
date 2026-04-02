import sys
import os
import asyncio
from pipeline_v4 import AtlanticDigitalPipeline

# Mock DB not needed for this test
pipeline = AtlanticDigitalPipeline(mongodb_uri=None)

async def test_url(url):
    print(f"\\n🧪 Testing cleaning logic on: {url}")
    print("=" * 50)
    
    # 1. Scrape
    print("1. Scraping...")
    # Manually calling the internal scrape to get raw text
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        html = result.html
        markdown = result.markdown
    
    print(f"   -> Raw HTML size: {len(html)} chars")
    print(f"   -> Markdown size: {len(markdown)} chars")

    # 2. Preprocess
    print("\\n2. Preprocessing & Tokenizing...")
    # We need to temporarily expose the internal processing logic if it's not easily accessible, 
    # or just run the public method
    
    analyzed = pipeline._preprocess(markdown)
    tokens = analyzed.split()
    
    print(f"   -> Tokens found: {len(tokens)}")
    print(f"   -> First 50 tokens: {tokens[:50]}")

    # 3. TF-IDF Simulation (just frequency here for quick check)
    from collections import Counter
    freq = Counter(tokens)
    print("\\n3. Top 20 Most Frequent Items:")
    for word, count in freq.most_common(20):
        print(f"   - {word}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_model.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    asyncio.run(test_url(url))
