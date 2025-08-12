#!/usr/bin/env python3
"""
Simple test script for the ArXiv MCP Server integration.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def run_mcp_command(server_name, tool_name, arguments=None):
    """Run an MCP command using the mcp CLI tool."""
    if arguments is None:
        arguments = {}
    
    args_json = json.dumps(arguments)
    cmd = ["mcp", "call-tool", server_name, tool_name, args_json]
    
    result = None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing MCP command: {e}")
        print(f"Stderr: {e.stderr}")
        return None
    except json.JSONDecodeError:
        if result:
            print(f"Error decoding JSON response: {result.stdout}")
        else:
            print("Error decoding JSON response: No result available")
        return None

def main():
    """Test the ArXiv MCP Server integration."""
    print("Testing ArXiv MCP Server integration...")
    
    # Test search_papers
    print("\n1. Testing paper search functionality...")
    search_args = {
        "query": "transformer architecture",
        "max_results": 3,
        "date_from": "2023-01-01",
        "categories": ["cs.AI", "cs.LG"]
    }
    search_result = run_mcp_command("arxiv", "search_papers", search_args)
    
    if search_result and "papers" in search_result:
        print(f"✅ Found {len(search_result['papers'])} papers")
        for i, paper in enumerate(search_result["papers"], 1):
            print(f"  {i}. {paper['title']} (ID: {paper['id']})")
        
        if search_result["papers"]:
            paper_id = search_result["papers"][0]["id"]
            
            # Test download_paper
            print(f"\n2. Testing paper download functionality for {paper_id}...")
            download_args = {"paper_id": paper_id}
            download_result = run_mcp_command("arxiv", "download_paper", download_args)
            
            if download_result and download_result.get("success"):
                print(f"✅ Successfully downloaded paper: {download_result.get('title', paper_id)}")
                
                # Test read_paper
                print(f"\n3. Testing paper reading functionality for {paper_id}...")
                read_args = {"paper_id": paper_id}
                read_result = run_mcp_command("arxiv", "read_paper", read_args)
                
                if read_result and "content" in read_result:
                    content_preview = read_result["content"][:200] + "..." if len(read_result["content"]) > 200 else read_result["content"]
                    print(f"✅ Successfully read paper content: \n{content_preview}")
                else:
                    print(f"❌ Failed to read paper content")
            else:
                print(f"❌ Failed to download paper")
    else:
        print(f"❌ Failed to search for papers")
    
    # Test list_papers
    print("\n4. Testing paper listing functionality...")
    list_result = run_mcp_command("arxiv", "list_papers", {})
    
    if list_result and "papers" in list_result:
        print(f"✅ Found {len(list_result['papers'])} downloaded papers")
        for i, paper in enumerate(list_result["papers"][:3], 1):
            print(f"  {i}. {paper['title']} (ID: {paper['id']})")
    else:
        print(f"❌ Failed to list papers")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()