#!/usr/bin/env python3
"""
Test script for the ArXiv MCP Server integration.
This script tests the basic functionality of the ArXiv MCP Server.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def test_arxiv_mcp():
    """Test the ArXiv MCP Server integration."""
    try:
        from mcp import Client
        
        print("Initializing MCP client...")
        client = Client(config_path="config/mcp_servers.yaml")
        
        print("\n1. Testing connection to ArXiv MCP Server...")
        servers = await client.list_servers()
        if "arxiv" in servers:
            print("✅ Successfully connected to ArXiv MCP Server")
        else:
            print("❌ Failed to connect to ArXiv MCP Server")
            print(f"Available servers: {', '.join(servers)}")
            return
        
        print("\n2. Testing paper search functionality...")
        search_result = await client.call_tool("arxiv", "search_papers", {
            "query": "transformer architecture",
            "max_results": 3,
            "date_from": "2023-01-01",
            "categories": ["cs.AI", "cs.LG"]
        })
        
        print(f"✅ Found {len(search_result['papers'])} papers")
        for i, paper in enumerate(search_result["papers"], 1):
            print(f"  {i}. {paper['title']} (ID: {paper['id']})")
        
        if search_result["papers"]:
            paper_id = search_result["papers"][0]["id"]
            
            print(f"\n3. Testing paper download functionality for {paper_id}...")
            download_result = await client.call_tool("arxiv", "download_paper", {
                "paper_id": paper_id
            })
            
            if download_result.get("success"):
                print(f"✅ Successfully downloaded paper: {download_result.get('title', paper_id)}")
                
                print(f"\n4. Testing paper reading functionality for {paper_id}...")
                read_result = await client.call_tool("arxiv", "read_paper", {
                    "paper_id": paper_id
                })
                
                if read_result.get("content"):
                    content_preview = read_result["content"][:200] + "..." if len(read_result["content"]) > 200 else read_result["content"]
                    print(f"✅ Successfully read paper content: \n{content_preview}")
                else:
                    print(f"❌ Failed to read paper content: {read_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Failed to download paper: {download_result.get('error', 'Unknown error')}")
        
        print("\n5. Testing paper listing functionality...")
        list_result = await client.call_tool("arxiv", "list_papers", {})
        
        if "papers" in list_result:
            print(f"✅ Found {len(list_result['papers'])} downloaded papers")
            for i, paper in enumerate(list_result["papers"][:3], 1):
                print(f"  {i}. {paper['title']} (ID: {paper['id']})")
        else:
            print(f"❌ Failed to list papers: {list_result.get('error', 'Unknown error')}")
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_arxiv_mcp())