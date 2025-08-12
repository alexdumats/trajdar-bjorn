#!/usr/bin/env python3
"""
Updated test script for the ArXiv MCP Server integration.
This script tests the ArXiv MCP Server functionality with fallback mechanisms.
It tries to use the MCP client library first, and if that fails, it falls back to using the MCP CLI tool.
"""

import asyncio
import json
import os
import sys
import subprocess
from pathlib import Path
import importlib.util

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

class ArxivMCPTester:
    """Class to test ArXiv MCP Server functionality with fallback mechanisms."""
    
    def __init__(self):
        """Initialize the tester with configuration."""
        self.config_path = "config/mcp_servers.yaml"
        self.use_client_lib = True
        self.client = None
        
    async def initialize(self):
        """Initialize the MCP client or prepare for CLI usage."""
        print("Initializing ArXiv MCP tester...")
        
        # Try to import the MCP client library
        try:
            if importlib.util.find_spec("mcp") is not None:
                # Import within try block to handle import errors
                from mcp import Client
                print("✅ MCP client library found, using it for testing")
                self.client = Client(config_path=self.config_path)
                self.use_client_lib = True
            else:
                print("⚠️ MCP client library not found, falling back to CLI")
                self.use_client_lib = False
                
                # Check if MCP CLI is available
                try:
                    result = subprocess.run(["mcp", "--version"], capture_output=True, text=True)
                    print(f"✅ MCP CLI found: {result.stdout.strip()}")
                except (subprocess.SubprocessError, FileNotFoundError):
                    print("❌ MCP CLI not found. Please install it first.")
                    return False
        except ImportError:
            print("⚠️ MCP client library not found, falling back to CLI")
            self.use_client_lib = False
            
            # Check if MCP CLI is available
            try:
                result = subprocess.run(["mcp", "--version"], capture_output=True, text=True)
                print(f"✅ MCP CLI found: {result.stdout.strip()}")
            except (subprocess.SubprocessError, FileNotFoundError):
                print("❌ MCP CLI not found. Please install it first.")
                return False
        
        # Check if ArXiv MCP Server is available
        if self.use_client_lib:
            try:
                if self.client is not None:
                    servers = await self.client.list_servers()
                    if "arxiv" not in servers:
                        print("❌ ArXiv MCP Server not found")
                        print(f"Available servers: {', '.join(servers)}")
                        return False
                    print("✅ Successfully connected to ArXiv MCP Server")
                    return True
                else:
                    print("❌ Client is None, falling back to CLI approach")
                    self.use_client_lib = False
            except Exception as e:
                print(f"❌ Error connecting to MCP servers: {e}")
                print("⚠️ Falling back to CLI approach")
                self.use_client_lib = False
        
        # If using CLI, check if arxiv server is available
        if not self.use_client_lib:
            try:
                result = subprocess.run(["mcp", "list-servers"], capture_output=True, text=True)
                if "arxiv" in result.stdout:
                    print("✅ ArXiv MCP Server found via CLI")
                    return True
                else:
                    print("❌ ArXiv MCP Server not found via CLI")
                    print(f"Available servers: {result.stdout}")
                    return False
            except subprocess.SubprocessError as e:
                print(f"❌ Error checking servers via CLI: {e}")
                return False
        
        return True
    
    async def call_tool(self, server_name, tool_name, arguments=None):
        """Call an MCP tool using either the client library or CLI."""
        if arguments is None:
            arguments = {}
            
        if self.use_client_lib:
            try:
                if self.client is not None:
                    return await self.client.call_tool(server_name, tool_name, arguments)
                else:
                    print("❌ Client is None, using CLI instead")
                    return self._call_tool_cli(server_name, tool_name, arguments)
            except Exception as e:
                print(f"❌ Error using client library: {e}")
                print("⚠️ Falling back to CLI for this call")
                # Fall back to CLI for this call
                return self._call_tool_cli(server_name, tool_name, arguments)
        else:
            return self._call_tool_cli(server_name, tool_name, arguments)
    
    def _call_tool_cli(self, server_name, tool_name, arguments):
        """Call an MCP tool using the CLI."""
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
            stdout = "No output" if result is None else result.stdout
            print(f"Error decoding JSON response: {stdout}")
            return None
    
    async def test_search_papers(self):
        """Test the search_papers functionality."""
        print("\n1. Testing paper search functionality...")
        search_args = {
            "query": "transformer architecture",
            "max_results": 3,
            "date_from": "2023-01-01",
            "categories": ["cs.AI", "cs.LG"]
        }
        
        search_result = await self.call_tool("arxiv", "search_papers", search_args)
        
        if search_result and "papers" in search_result:
            print(f"✅ Found {len(search_result['papers'])} papers")
            for i, paper in enumerate(search_result["papers"], 1):
                print(f"  {i}. {paper['title']} (ID: {paper['id']})")
            return search_result["papers"][0]["id"] if search_result["papers"] else None
        else:
            print("❌ Failed to search for papers")
            return None
    
    async def test_download_paper(self, paper_id):
        """Test the download_paper functionality."""
        if not paper_id:
            print("❌ Cannot test download_paper: No paper ID available")
            return False
            
        print(f"\n2. Testing paper download functionality for {paper_id}...")
        download_args = {"paper_id": paper_id}
        
        download_result = await self.call_tool("arxiv", "download_paper", download_args)
        
        if download_result and isinstance(download_result, dict) and download_result.get("success"):
            print(f"✅ Successfully downloaded paper: {download_result.get('title', paper_id)}")
            return True
        else:
            error_msg = "Unknown error"
            if download_result and isinstance(download_result, dict):
                error_msg = download_result.get("error", "Unknown error")
            print(f"❌ Failed to download paper: {error_msg}")
            return False
    
    async def test_read_paper(self, paper_id):
        """Test the read_paper functionality."""
        if not paper_id:
            print("❌ Cannot test read_paper: No paper ID available")
            return
            
        print(f"\n3. Testing paper reading functionality for {paper_id}...")
        read_args = {"paper_id": paper_id}
        
        read_result = await self.call_tool("arxiv", "read_paper", read_args)
        
        if read_result and isinstance(read_result, dict) and "content" in read_result:
            content_preview = read_result["content"][:200] + "..." if len(read_result["content"]) > 200 else read_result["content"]
            print(f"✅ Successfully read paper content: \n{content_preview}")
        else:
            error_msg = "Unknown error"
            if read_result and isinstance(read_result, dict):
                error_msg = read_result.get("error", "Unknown error")
            print(f"❌ Failed to read paper content: {error_msg}")
    
    async def test_list_papers(self):
        """Test the list_papers functionality."""
        print("\n4. Testing paper listing functionality...")
        
        list_result = await self.call_tool("arxiv", "list_papers", {})
        
        if list_result and isinstance(list_result, dict) and "papers" in list_result:
            print(f"✅ Found {len(list_result['papers'])} downloaded papers")
            for i, paper in enumerate(list_result["papers"][:3], 1):
                print(f"  {i}. {paper['title']} (ID: {paper['id']})")
        else:
            error_msg = "Unknown error"
            if list_result and isinstance(list_result, dict):
                error_msg = list_result.get("error", "Unknown error")
            print(f"❌ Failed to list papers: {error_msg}")

async def main():
    """Main function to run the ArXiv MCP tests."""
    try:
        tester = ArxivMCPTester()
        if not await tester.initialize():
            print("❌ Failed to initialize ArXiv MCP tester")
            return
        
        # Run the tests
        paper_id = await tester.test_search_papers()
        if paper_id:
            download_success = await tester.test_download_paper(paper_id)
            if download_success:
                await tester.test_read_paper(paper_id)
        
        await tester.test_list_papers()
        
        print("\nAll tests completed!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())