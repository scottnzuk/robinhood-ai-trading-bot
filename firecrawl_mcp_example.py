#!/usr/bin/env python3
"""
Example script demonstrating how to use the FireCrawl MCP server.
"""
import json
import os
import sys
import requests

# MCP server configuration
MCP_SERVER = "firecrawl"
MCP_PORT = 9003  # Port for FireCrawl MCP server

def call_mcp_tool(tool_name, params):
    """Call an MCP tool on the FireCrawl server."""
    url = f"http://localhost:{MCP_PORT}/tools/{tool_name}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=params)
    
    if response.status_code != 200:
        print(f"Error calling {tool_name}: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()

def crawl_website(url, depth=1, max_pages=10):
    """Crawl a website using FireCrawl."""
    params = {
        "url": url,
        "depth": depth,
        "maxPages": max_pages
    }
    
    result = call_mcp_tool("crawl", params)
    if result:
        print(f"Successfully crawled {url}")
        print(f"Pages crawled: {len(result.get('pages', []))}")
        return result
    return None

def search_content(query, context=None):
    """Search for content using FireCrawl."""
    params = {
        "query": query
    }
    
    if context:
        params["context"] = context
    
    result = call_mcp_tool("search", params)
    if result:
        print(f"Successfully searched for '{query}'")
        print(f"Results found: {len(result.get('results', []))}")
        return result
    return None

def extract_data(url, selectors):
    """Extract data from a webpage using FireCrawl."""
    params = {
        "url": url,
        "selectors": selectors
    }
    
    result = call_mcp_tool("extract", params)
    if result:
        print(f"Successfully extracted data from {url}")
        print(f"Data extracted: {json.dumps(result.get('data', {}), indent=2)}")
        return result
    return None

def main():
    """Main function demonstrating FireCrawl MCP usage."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Crawl:   python firecrawl_mcp_example.py crawl <url> [depth] [max_pages]")
        print("  Search:  python firecrawl_mcp_example.py search <query>")
        print("  Extract: python firecrawl_mcp_example.py extract <url> <selector>")
        return
    
    mode = sys.argv[1]
    
    if mode == "crawl" and len(sys.argv) >= 3:
        url = sys.argv[2]
        depth = int(sys.argv[3]) if len(sys.argv) >= 4 else 1
        max_pages = int(sys.argv[4]) if len(sys.argv) >= 5 else 10
        crawl_website(url, depth, max_pages)
    
    elif mode == "search" and len(sys.argv) >= 3:
        query = sys.argv[2]
        search_content(query)
    
    elif mode == "extract" and len(sys.argv) >= 4:
        url = sys.argv[2]
        selector = sys.argv[3]
        extract_data(url, {
            "main": selector
        })
    
    else:
        print("Invalid mode or missing arguments")

if __name__ == "__main__":
    main()