# Claude Code MCP Servers

This document provides detailed information on setting up and using the recommended MCP (Model Context Protocol) servers with Claude Code. These servers enhance Claude's capabilities by providing access to external tools and resources.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [MCP Server Details](#mcp-server-details)
   - [Fetch MCP Server](#fetch-mcp-server)
   - [Filesystem MCP Server](#filesystem-mcp-server)
   - [Memory MCP Server](#memory-mcp-server)
   - [Git MCP Server](#git-mcp-server)
   - [Sequential Thinking MCP Server](#sequential-thinking-mcp-server)
   - [Time MCP Server](#time-mcp-server)
   - [Context7 Documentation Server](#context7-documentation-server)
5. [Troubleshooting](#troubleshooting)

## Overview

Model Context Protocol (MCP) servers extend Claude's capabilities by providing access to external tools and resources. The servers recommended in this document cover a wide range of functionalities:

- Web content access
- File system operations
- Persistent memory
- Git version control
- Enhanced reasoning
- Time-related operations
- Documentation access

## Installation

To install all the recommended MCP servers, run the provided setup script:

```bash
chmod +x scripts/setup_claude_code_mcps.sh
./scripts/setup_claude_code_mcps.sh
```

This script will:
- Install all necessary Node.js and Python packages
- Create a default configuration file
- Set up required directories

## Configuration

The MCP servers are configured in `config/claude_code_mcp_servers.yaml`. This file contains all the necessary settings for each server, including:

- Server name and description
- Repository URL
- Command and arguments to run the server
- Capabilities provided by the server
- Auto-approve settings for specific capabilities

Environment variables are stored in `.env.mcp`. You may need to modify this file to set specific values for your environment.

## MCP Server Details

### Fetch MCP Server

The Fetch MCP Server allows Claude to retrieve and process web content.

**Key Capabilities:**
- Fetching web content from URLs
- Converting HTML to markdown for easier consumption
- Handling pagination and content chunking

**Example Usage:**
```
<use_mcp_tool>
<server_name>fetch</server_name>
<tool_name>fetch</tool_name>
<arguments>
{
  "url": "https://example.com"
}
</arguments>
</use_mcp_tool>
```

### Filesystem MCP Server

The Filesystem MCP Server provides comprehensive file system operations.

**Key Capabilities:**
- Reading and writing files
- Creating and listing directories
- Searching for files
- Getting file metadata

**Example Usage:**
```
<use_mcp_tool>
<server_name>filesystem</server_name>
<tool_name>read_text_file</tool_name>
<arguments>
{
  "path": "example.txt"
}
</arguments>
</use_mcp_tool>
```

### Memory MCP Server

The Memory MCP Server enables persistent storage of information across sessions.

**Key Capabilities:**
- Creating and managing entities and relationships
- Adding observations to entities
- Searching and retrieving stored information

**Example Usage:**
```
<use_mcp_tool>
<server_name>memory</server_name>
<tool_name>create_entities</tool_name>
<arguments>
{
  "entities": [
    {
      "name": "Project X",
      "entityType": "project",
      "observations": ["Started on 2025-08-01", "High priority"]
    }
  ]
}
</arguments>
</use_mcp_tool>
```

### Git MCP Server

The Git MCP Server provides Git version control operations.

**Key Capabilities:**
- Cloning repositories
- Pulling and pushing changes
- Creating and checking out branches
- Viewing diffs and history

**Example Usage:**
```
<use_mcp_tool>
<server_name>git</server_name>
<tool_name>clone_repository</tool_name>
<arguments>
{
  "url": "https://github.com/example/repo.git",
  "directory": "repo"
}
</arguments>
</use_mcp_tool>
```

### Sequential Thinking MCP Server

The Sequential Thinking MCP Server enhances Claude's reasoning capabilities.

**Key Capabilities:**
- Step-by-step reasoning framework
- Dynamic thought revision and branching
- Hypothesis generation and verification

**Example Usage:**
```
<use_mcp_tool>
<server_name>sequentialthinking</server_name>
<tool_name>sequentialthinking</tool_name>
<arguments>
{
  "thought": "First, I need to understand the problem...",
  "nextThoughtNeeded": true,
  "thoughtNumber": 1,
  "totalThoughts": 5
}
</arguments>
</use_mcp_tool>
```

### Time MCP Server

The Time MCP Server provides time-related operations.

**Key Capabilities:**
- Getting current time in different timezones
- Converting time between timezones

**Example Usage:**
```
<use_mcp_tool>
<server_name>time</server_name>
<tool_name>get_current_time</tool_name>
<arguments>
{
  "timezone": "America/New_York"
}
</arguments>
</use_mcp_tool>
```

### Context7 Documentation Server

The Context7 Documentation Server provides access to up-to-date documentation for thousands of libraries and frameworks.

**Key Capabilities:**
- Resolving library IDs
- Retrieving library documentation

**Example Usage:**
```
<use_mcp_tool>
<server_name>context7</server_name>
<tool_name>resolve-library-id</tool_name>
<arguments>
{
  "libraryName": "react"
}
</arguments>
</use_mcp_tool>
```

## Troubleshooting

If you encounter issues with any of the MCP servers:

1. Check that the server is installed correctly
2. Verify that the environment variables are set properly in `.env.mcp`
3. Ensure that the server is running and accessible
4. Check the server logs for any error messages

For more detailed information, refer to the documentation for each specific MCP server.