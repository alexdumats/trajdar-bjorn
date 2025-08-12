# Embedding MCP Server

An MCP server for text embedding and vector search to replace Ollama for codebase indexing in Claude Code.

## Features

- Generate embeddings for text using sentence-transformers
- Index code files for semantic search
- Search the indexed codebase using semantic queries
- Get the current status of codebase indexing
- Compatible with Qdrant vector database

## Installation

### Prerequisites

- Node.js 18 or higher
- Python 3.8 or higher
- Qdrant server running (default: http://localhost:6333)

### Using npm

```bash
# Clone the repository
git clone https://github.com/yourusername/embedding-mcp-server.git
cd embedding-mcp-server

# Install dependencies
npm install

# Start the server
npm start
```

### Using Docker

```bash
# Build the Docker image
docker build -t embedding-mcp-server .

# Run the Docker container
docker run -p 3000:3000 \
  -e QDRANT_URL=http://localhost:6333 \
  -e QDRANT_API_KEY=your_api_key \
  embedding-mcp-server
```

## Configuration

The server can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBEDDING_MODEL` | The sentence-transformers model to use | `nomic-embed-text` |
| `MODEL_DIMENSION` | The dimension of the embedding vectors | `1536` |
| `QDRANT_URL` | URL of the Qdrant server | `http://localhost:6333` |
| `QDRANT_API_KEY` | API key for the Qdrant server | `""` |
| `SEARCH_SCORE_THRESHOLD` | Minimum similarity score threshold | `0.40` |
| `MAX_SEARCH_RESULTS` | Maximum number of search results | `50` |
| `COLLECTION_NAME` | Name of the Qdrant collection | `codebase_index` |

## Usage with Claude Code

To use this server with Claude Code, add the following configuration to your Claude settings:

```yaml
embedding:
  name: "Embedding MCP Server"
  repository: "https://github.com/yourusername/embedding-mcp-server"
  type: "stdio"
  command: "node"
  args: ["src/index.js"]
  description: "Text embedding and vector search for codebase indexing"
  capabilities:
    - generate_embeddings
    - index_code_file
    - search_codebase
    - get_indexing_status
  env:
    QDRANT_URL: "http://localhost:6333"
    QDRANT_API_KEY: "your_api_key"
    EMBEDDING_MODEL: "nomic-embed-text"
    MODEL_DIMENSION: "1536"
    SEARCH_SCORE_THRESHOLD: "0.40"
    MAX_SEARCH_RESULTS: "50"
  autoApprove:
    - get_indexing_status
  disabled: false
```

## API

### generate_embeddings

Generate embeddings for the provided text.

**Input:**
```json
{
  "text": "const hello = 'world';"
}
```

**Output:**
```json
{
  "embedding": [0.1, 0.2, ...],
  "dimension": 1536
}
```

### index_code_file

Index a code file for semantic search.

**Input:**
```json
{
  "filePath": "src/index.js",
  "content": "const hello = 'world';",
  "language": "javascript"
}
```

**Output:**
```json
{
  "success": true,
  "filePath": "src/index.js",
  "id": "c3JjL2luZGV4LmpzCg=="
}
```

### search_codebase

Search the indexed codebase using semantic search.

**Input:**
```json
{
  "query": "function to say hello",
  "limit": 10,
  "threshold": 0.5
}
```

**Output:**
```json
{
  "query": "function to say hello",
  "results": [
    {
      "filePath": "src/index.js",
      "score": 0.85,
      "language": "javascript",
      "size": 23,
      "timestamp": "2025-08-12T03:14:55.839Z"
    }
  ],
  "total": 1
}
```

### get_indexing_status

Get the current status of codebase indexing.

**Input:**
```json
{}
```

**Output:**
```json
{
  "status": "active",
  "collection": "codebase_index",
  "vectorSize": 1536,
  "indexedFiles": 42,
  "model": "nomic-embed-text",
  "qdrantUrl": "http://localhost:6333"
}
```

## License

MIT