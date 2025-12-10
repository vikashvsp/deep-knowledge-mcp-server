import os
import json
import sys
import asyncio
from typing import Any, List, Optional
from mcp.server.fastmcp import FastMCP
from apify_client import ApifyClient
from apify import Actor

# Initialize FastMCP server
mcp = FastMCP("Deep Knowledge")

# Get client directly for tools
# We use os.environ directly here because tools might run outside Actor.main context contextually,
# but since we wrap main, we can ensure token is present.
apify_token = os.environ.get("APIFY_TOKEN")

@mcp.tool()
async def search_technical_docs(query: str, max_results: int = 5) -> str:
    """
    Search for technical documentation, libraries, and code repositories.
    
    Args:
        query: The search query. 
               - In MCP Mode: Provided by the LLM (e.g. Claude) based on your prompt.
               - In Standalone Mode: Provided by 'demo_query' in Apify Input.
        max_results: Maximum number of results to return (default: 5).
    """
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        return "Error: APIFY_TOKEN is not set in environment."

    print(f"Searching for: {query} (max: {max_results})", file=sys.stderr)
    
    client = ApifyClient(token=token)
    
    # Run Google Search Scraper
    run_input = {
        "queries": base_query_correction(query),
        "maxResults": max_results,
        "resultsPerPage": max_results,
        "languageCode": "en",
    }
    
    try:
        # Monetization: Charge for the search event
        # Event name should match what is configured in Apify Console for Pay-per-event
        await Actor.charge('search-technical-docs')
        Actor.log.info("Charged for event: search-technical-docs")

        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        if not run:
            return "Error: Search actor run failed to start."
            
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            return "Error: No dataset ID returned from search run."

        # Fetch results
        dataset_items = client.dataset(dataset_id).list_items().items
        
        results = []
        for item in dataset_items:
            organic_results = item.get("organicResults", [])
            if not organic_results and "organicResults" not in item:
                 # Fallback if structure is different
                 organic_results = [item] if item.get("title") else []

            for res in organic_results:
                if len(results) >= max_results:
                    break
                
                results.append({
                    "title": res.get("title", "No Title"),
                    "url": res.get("url", ""),
                    "description": res.get("description", "") or res.get("snippet", "")
                })
            if len(results) >= max_results:
                break
        
        if not results:
            return "No results found."
            
        return json.dumps(results, indent=2)
        
    except Exception as e:
        return f"Error searching documentation: {str(e)}"

@mcp.tool()
async def fetch_documentation(url: str) -> str:
    """
    Fetch and extract text content from a documentation web page.
    
    Args:
        url: The URL of the documentation page to fetch.
    """
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        return "Error: APIFY_TOKEN is not set."
        
    print(f"Fetching documentation from: {url}", file=sys.stderr)
    
    client = ApifyClient(token=token)
    
    # Run Website Content Crawler
    # usage: shallow crawl of a single page to get markdown
    run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlingDepth": 0,
        "saveMarkdown": True,
        "saveHtml": False,
        "saveScreenshots": False,
    }
    
    try:
        # Monetization: Charge for the fetch event
        await Actor.charge('fetch-documentation')
        Actor.log.info("Charged for event: fetch-documentation")

        run = client.actor("apify/website-content-crawler").call(run_input=run_input)
        
        if not run:
             return "Error: Crawler actor run failed."
             
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
             return "Error: No dataset ID returned from crawler run."
        
        # Fetch results
        dataset_items = client.dataset(dataset_id).list_items().items
        
        if dataset_items:
            item = dataset_items[0]
            markdown = item.get("markdown", "")
            if not markdown:
                 # Fallback strategies
                 markdown = item.get("text", "")
            
            # Add metadata
            title = item.get("metadata", {}).get("title") or item.get("title", "No Title")
            
            if not markdown:
                return f"No markdown or text content found for {url}"

            return f"# {title}\n\nURL: {url}\n\n{markdown}"
            
        return "No content found."

    except Exception as e:
        return f"Error fetching documentation: {str(e)}"

def base_query_correction(q: str) -> str:
    """Ensure query is valid for technical search."""
    if not q:
        return "latest technology documentation"
    
    q = q.strip()
    
    # If query is very short, append 'documentation' context
    if len(q.split()) == 1 and len(q) < 4:
         return f"{q} documentation"
         
    return q

async def main():
    async with Actor:
        # Check input
        actor_input = await Actor.get_input() or {}
        
        # Default to True if not specified
        is_mcp_server = actor_input.get("mcp_server", True)
        
        if is_mcp_server:
            print("Starting MCP Server...", file=sys.stderr)
            return True
        else:
            # Standalone Mode
            print("Running in Standalone Mode...", file=sys.stderr)
            query = actor_input.get("demo_query", "Apify MCP Server")
            max_res = actor_input.get("max_results", 3)
            
            result = await search_technical_docs(query, max_res)
            print("--- Demo Search Results ---")
            print(result)
            
            # Optionally push to dataset
            await Actor.push_data({"status": "Success", "mode": "Standalone", "query": query, "result": result})
            return False

if __name__ == "__main__":
    should_run_server = True
    try:
        # We use asyncio.run to execute the Actor input check
        should_run_server = asyncio.run(main())
    except Exception as e:
        # If running locally without 'apify' installed or strict env, 
        # main() might fail. We default to running the server.
        print(f"Notice: Actor initialization skipped or failed ({e}). Defaulting to MCP Server mode.", file=sys.stderr)
        should_run_server = True
        
    if should_run_server:
        # Check for Apify Cloud environment variables (APIFY_IS_AT_HOME or APIFY_ACTOR_ID)
        is_apify_cloud = os.environ.get("APIFY_IS_AT_HOME") or os.environ.get("APIFY_ACTOR_ID")
        
        if is_apify_cloud:
             print("Detected Apify Cloud environment. Starting MCP Server via SSE...", file=sys.stderr)
             # Use SSE transport for cloud hosting to keep the process alive and exposed via HTTP
             mcp.run(transport='sse')
        else:
             mcp.run()
