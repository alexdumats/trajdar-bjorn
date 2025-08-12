#!/usr/bin/env python3
"""
Script to search for trading strategy and market analysis papers using the ArXiv MCP Server.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta

def run_mcp_command(server_name, tool_name, arguments=None):
    """Run an MCP command using the mcp CLI tool."""
    if arguments is None:
        arguments = {}
    
    args_json = json.dumps(arguments)
    cmd = ["mcp", "call-tool", server_name, tool_name, args_json]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing MCP command: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON response")
        return None

def search_papers(query, max_results=10, categories=None, date_from=None):
    """Search for papers on arXiv."""
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
    
    result = run_mcp_command("arxiv", "search_papers", search_args)
    
    if result and "papers" in result:
        papers = result["papers"]
        print(f"Found {len(papers)} papers")
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title']}")
            print(f"   ID: {paper['id']}")
            print(f"   Authors: {', '.join(paper['authors'])}")
            print(f"   Published: {paper['published']}")
            print(f"   Categories: {', '.join(paper['categories'])}")
            print(f"   Abstract: {paper['abstract'][:200]}...")
    else:
        print("No papers found or error in search")

def main():
    """Main function to search for trading papers."""
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
        search_papers(query, max_results, categories, date_from)
        print("\n" + "=" * 80 + "\n")

if __name__ == "__main__":
    main()