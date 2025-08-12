#!/usr/bin/env python3
"""
Script to search for trading strategy and market analysis papers using the ArXiv MCP Server.
Uses the Python MCP client library for async communication.
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def search_papers(client, query, max_results=10, categories=None, date_from=None):
    """Search for papers on arXiv using the MCP client."""
    # Calculate date from if not provided (default to 2 years ago)
    if date_from is None:
        two_years_ago = datetime.now() - timedelta(days=2*365)
        date_from = two_years_ago.strftime("%Y-%m-%d")
    
    # Set default categories if not provided
    if categories is None:
        categories = ["q-fin.TR", "q-fin.PM", "q-fin.ST", "cs.AI", "stat.ML"]
    
    search_args = {
        "query": query,
        "max_results": max_results,
        "date_from": date_from,
        "categories": categories
    }
    
    print(f"Searching for papers with query: '{query}'")
    print(f"Categories: {', '.join(categories)}")
    print(f"Date from: {date_from}")
    print(f"Max results: {max_results}")
    print("-" * 80)
    
    try:
        result = await client.call_tool("arxiv", "search_papers", search_args)
        
        if "papers" in result:
            papers = result["papers"]
            print(f"Found {len(papers)} papers")
            
            for i, paper in enumerate(papers, 1):
                print(f"\n{i}. {paper['title']}")
                print(f"   ID: {paper['id']}")
                print(f"   Authors: {', '.join(paper['authors'])}")
                print(f"   Published: {paper['published']}")
                print(f"   Categories: {', '.join(paper['categories'])}")
                print(f"   Abstract: {paper['abstract'][:200]}...")
                
                # Add option to download the paper
                print(f"   To download: python -c \"import asyncio; from mcp import Client; asyncio.run(Client(config_path='config/mcp_servers.yaml').call_tool('arxiv', 'download_paper', {{'paper_id': '{paper['id']}'}}))")
                
                # Add option to analyze the paper
                print(f"   To analyze: python -c \"import asyncio; from mcp import Client; asyncio.run(Client(config_path='config/mcp_servers.yaml').call_prompt('arxiv', 'deep-paper-analysis', {{'paper_id': '{paper['id']}'}}))")
        else:
            print("No papers found or error in search")
    except Exception as e:
        print(f"Error searching for papers: {e}")

async def main():
    """Main function to search for trading papers."""
    try:
        from mcp import Client
        
        print("Initializing MCP client...")
        client = Client(config_path="config/mcp_servers.yaml")
        
        # Check if ArXiv MCP Server is available
        servers = await client.list_servers()
        if "arxiv" not in servers:
            print("❌ ArXiv MCP Server not found")
            print(f"Available servers: {', '.join(servers)}")
            return
        
        print("✅ Successfully connected to ArXiv MCP Server")
        
        # List of search queries related to trading strategies and market analysis
        queries = [
            "algorithmic trading strategies",
            "market microstructure high frequency trading",
            "machine learning stock prediction",
            "reinforcement learning trading",
            "quantitative finance risk management"
        ]
        
        # Categories related to quantitative finance and machine learning
        categories = ["q-fin.TR", "q-fin.PM", "q-fin.ST", "cs.AI", "stat.ML"]
        
        # Date from (papers published after this date)
        date_from = "2023-01-01"  # Papers from 2023 onwards
        
        # Max results per query
        max_results = 3
        
        for query in queries:
            await search_papers(client, query, max_results, categories, date_from)
            print("\n" + "=" * 80 + "\n")
    
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())