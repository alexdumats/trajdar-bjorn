#!/usr/bin/env python3
"""
Script to use the ArXiv MCP Server with Claude for trading strategy research.
This script searches for trading strategy papers on arXiv and uses Claude to analyze them.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

class ClaudeArxivResearcher:
    """Class to use ArXiv MCP Server with Claude for trading strategy research."""
    
    def __init__(self):
        """Initialize the researcher."""
        self.arxiv_storage_path = os.environ.get(
            "ARXIV_STORAGE_PATH", 
            "/Users/alexdumats/trajdar_bjorn/mcp-servers/arxiv-mcp-server/papers"
        )
        
        # Ensure the storage path exists
        os.makedirs(self.arxiv_storage_path, exist_ok=True)
        
        print(f"Using ArXiv storage path: {self.arxiv_storage_path}")
    
    def call_arxiv_mcp(self, tool_name, arguments=None):
        """Call the ArXiv MCP server using the CLI."""
        if arguments is None:
            arguments = {}
            
        args_json = json.dumps(arguments)
        cmd = ["uv", "tool", "run", "arxiv-mcp-server", tool_name, args_json]
        
        result = None
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing ArXiv MCP command: {e}")
            print(f"Stderr: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response: {e}")
            if result:
                print(f"Output: {result.stdout}")
            return None
    
    def search_trading_papers(self, query, max_results=5, date_from=None, categories=None):
        """Search for trading strategy papers on arXiv."""
        if categories is None:
            categories = ["q-fin.TR", "q-fin.PM", "q-fin.ST", "cs.AI", "stat.ML"]
            
        search_args = {
            "query": query,
            "max_results": max_results,
            "categories": categories
        }
        
        if date_from:
            search_args["date_from"] = date_from
            
        print(f"Searching for papers with query: '{query}'")
        print(f"Categories: {', '.join(categories)}")
        if date_from:
            print(f"Date from: {date_from}")
        print(f"Max results: {max_results}")
        print("-" * 80)
        
        result = self.call_arxiv_mcp("search_papers", search_args)
        
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
            
            return papers
        else:
            print("No papers found or error in search")
            return []
    
    def download_paper(self, paper_id):
        """Download a paper by its arXiv ID."""
        print(f"Downloading paper {paper_id}...")
        
        download_args = {"paper_id": paper_id}
        result = self.call_arxiv_mcp("download_paper", download_args)
        
        if result and result.get("success"):
            print(f"✅ Successfully downloaded paper: {result.get('title', paper_id)}")
            return True
        else:
            error_msg = "Unknown error"
            if result and isinstance(result, dict):
                error_msg = result.get("error", "Unknown error")
            print(f"❌ Failed to download paper: {error_msg}")
            return False
    
    def read_paper(self, paper_id):
        """Read a paper by its arXiv ID."""
        print(f"Reading paper {paper_id}...")
        
        read_args = {"paper_id": paper_id}
        result = self.call_arxiv_mcp("read_paper", read_args)
        
        if result and "content" in result:
            content = result["content"]
            print(f"✅ Successfully read paper content ({len(content)} characters)")
            return content
        else:
            error_msg = "Unknown error"
            if result and isinstance(result, dict):
                error_msg = result.get("error", "Unknown error")
            print(f"❌ Failed to read paper content: {error_msg}")
            return None
    
    def analyze_with_claude(self, paper_content, paper_id, paper_title):
        """Analyze a paper with Claude."""
        print(f"Analyzing paper {paper_id} with Claude...")
        
        # Create a prompt for Claude
        prompt = f"""
        # Trading Strategy Analysis Request

        ## Paper Information
        - **Title**: {paper_title}
        - **ID**: {paper_id}

        ## Paper Content
        ```
        {paper_content[:10000]}  # Limit content to avoid token limits
        ```

        ## Analysis Request
        Please analyze this academic paper on trading strategies and provide:

        1. **Executive Summary**: A concise overview of the paper's key findings and contributions (2-3 paragraphs)
        
        2. **Trading Strategy Analysis**:
           - Core strategy mechanics and principles
           - Market conditions where this strategy performs best
           - Key parameters and variables that affect performance
           - Risk management considerations
        
        3. **Implementation Considerations**:
           - Technical requirements for implementing this strategy
           - Data sources needed
           - Computational complexity
           - Potential challenges in real-world deployment
        
        4. **Performance Evaluation**:
           - How the strategy was evaluated in the paper
           - Key performance metrics
           - Comparison to baseline or alternative strategies
           - Limitations of the evaluation methodology
        
        5. **Practical Applications**:
           - How this strategy could be applied to our trading system
           - Modifications needed for our specific use case
           - Integration points with existing components
           - Expected benefits and potential risks
        
        Please provide a comprehensive but concise analysis that focuses on practical implementation rather than theoretical aspects.
        """
        
        # Save the prompt to a file
        analysis_dir = Path("analysis")
        analysis_dir.mkdir(exist_ok=True)
        
        prompt_file = analysis_dir / f"{paper_id}_prompt.txt"
        with open(prompt_file, "w") as f:
            f.write(prompt)
        
        print(f"Prompt saved to {prompt_file}")
        print("To analyze with Claude, copy the prompt and paste it into Claude's interface.")
        print("Once Claude generates the analysis, save it to a file in the analysis directory.")
        
        return prompt_file
    
    def research_trading_strategies(self, query, max_results=3, date_from=None):
        """Research trading strategies using ArXiv and Claude."""
        # Search for papers
        papers = self.search_trading_papers(query, max_results, date_from)
        
        if not papers:
            print("No papers found. Try a different query or categories.")
            return
        
        # Process each paper
        for i, paper in enumerate(papers, 1):
            paper_id = paper["id"]
            paper_title = paper["title"]
            
            print(f"\nProcessing paper {i}/{len(papers)}: {paper_title}")
            
            # Download the paper
            if not self.download_paper(paper_id):
                print(f"Skipping analysis for paper {paper_id} due to download failure.")
                continue
            
            # Read the paper
            paper_content = self.read_paper(paper_id)
            if not paper_content:
                print(f"Skipping analysis for paper {paper_id} due to reading failure.")
                continue
            
            # Analyze with Claude
            prompt_file = self.analyze_with_claude(paper_content, paper_id, paper_title)
            print(f"Analysis prompt for paper {i}/{len(papers)} prepared: {prompt_file}")
            
            # Ask if user wants to continue to the next paper
            if i < len(papers):
                response = input("\nContinue to the next paper? (y/n): ")
                if response.lower() != 'y':
                    break

def main():
    """Main function to run the Claude ArXiv Researcher."""
    parser = argparse.ArgumentParser(description="Research trading strategies using ArXiv and Claude")
    parser.add_argument("--query", type=str, default="algorithmic trading strategies",
                        help="Search query for arXiv papers")
    parser.add_argument("--max-results", type=int, default=3,
                        help="Maximum number of papers to retrieve")
    parser.add_argument("--date-from", type=str, default="2023-01-01",
                        help="Only include papers published after this date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        researcher = ClaudeArxivResearcher()
        researcher.research_trading_strategies(args.query, args.max_results, args.date_from)
        
    except Exception as e:
        print(f"Error during research: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()