const { MCPServer } = require('@modelcontextprotocol/server');
const { QdrantClient } = require('qdrant-js');
const { SentenceTransformer } = require('sentence-transformers');

// Configuration
const config = {
  // Embedding model configuration
  model: process.env.EMBEDDING_MODEL || 'nomic-embed-text',
  dimension: parseInt(process.env.MODEL_DIMENSION || '1536'),
  
  // Qdrant configuration
  qdrantUrl: process.env.QDRANT_URL || 'http://localhost:6333',
  qdrantApiKey: process.env.QDRANT_API_KEY || '',
  
  // Search configuration
  searchScoreThreshold: parseFloat(process.env.SEARCH_SCORE_THRESHOLD || '0.40'),
  maxSearchResults: parseInt(process.env.MAX_SEARCH_RESULTS || '50'),
  
  // Collection name for codebase indexing
  collectionName: process.env.COLLECTION_NAME || 'codebase_index'
};

// Initialize the embedding model
const model = new SentenceTransformer(config.model);

// Initialize Qdrant client
const qdrantClient = new QdrantClient({
  url: config.qdrantUrl,
  apiKey: config.qdrantApiKey
});

// Create MCP server
const server = new MCPServer({
  name: 'Embedding MCP Server',
  description: 'MCP server for text embedding and vector search to replace Ollama for codebase indexing'
});

// Tool: Generate embeddings for text
server.addTool({
  name: 'generate_embeddings',
  description: 'Generate embeddings for the provided text',
  inputSchema: {
    type: 'object',
    properties: {
      text: {
        type: 'string',
        description: 'The text to generate embeddings for'
      }
    },
    required: ['text']
  },
  handler: async ({ text }) => {
    try {
      const embedding = await model.encode(text);
      return {
        embedding: embedding.tolist(),
        dimension: embedding.length
      };
    } catch (error) {
      throw new Error(`Failed to generate embeddings: ${error.message}`);
    }
  }
});

// Tool: Index code file
server.addTool({
  name: 'index_code_file',
  description: 'Index a code file for semantic search',
  inputSchema: {
    type: 'object',
    properties: {
      filePath: {
        type: 'string',
        description: 'Path to the code file'
      },
      content: {
        type: 'string',
        description: 'Content of the code file'
      },
      language: {
        type: 'string',
        description: 'Programming language of the code file'
      }
    },
    required: ['filePath', 'content']
  },
  handler: async ({ filePath, content, language }) => {
    try {
      // Generate embedding for the file content
      const embedding = await model.encode(content);
      
      // Create collection if it doesn't exist
      try {
        await qdrantClient.getCollection(config.collectionName);
      } catch (error) {
        await qdrantClient.createCollection(config.collectionName, {
          vectors: {
            size: config.dimension,
            distance: 'Cosine'
          }
        });
      }
      
      // Create a unique ID for the file
      const id = Buffer.from(filePath).toString('base64');
      
      // Index the file
      await qdrantClient.upsert(config.collectionName, {
        points: [{
          id,
          vector: embedding.tolist(),
          payload: {
            filePath,
            language: language || 'unknown',
            size: content.length,
            timestamp: new Date().toISOString()
          }
        }]
      });
      
      return {
        success: true,
        filePath,
        id
      };
    } catch (error) {
      throw new Error(`Failed to index code file: ${error.message}`);
    }
  }
});

// Tool: Search codebase
server.addTool({
  name: 'search_codebase',
  description: 'Search the indexed codebase using semantic search',
  inputSchema: {
    type: 'object',
    properties: {
      query: {
        type: 'string',
        description: 'The search query'
      },
      limit: {
        type: 'number',
        description: 'Maximum number of results to return'
      },
      threshold: {
        type: 'number',
        description: 'Minimum similarity score threshold'
      }
    },
    required: ['query']
  },
  handler: async ({ query, limit, threshold }) => {
    try {
      // Generate embedding for the query
      const embedding = await model.encode(query);
      
      // Set defaults
      const searchLimit = limit || config.maxSearchResults;
      const searchThreshold = threshold || config.searchScoreThreshold;
      
      // Search the collection
      const searchResults = await qdrantClient.search(config.collectionName, {
        vector: embedding.tolist(),
        limit: searchLimit,
        filter: {
          must: []
        }
      });
      
      // Filter results by threshold
      const filteredResults = searchResults.filter(result => result.score >= searchThreshold);
      
      return {
        query,
        results: filteredResults.map(result => ({
          filePath: result.payload.filePath,
          score: result.score,
          language: result.payload.language,
          size: result.payload.size,
          timestamp: result.payload.timestamp
        })),
        total: filteredResults.length
      };
    } catch (error) {
      throw new Error(`Failed to search codebase: ${error.message}`);
    }
  }
});

// Tool: Get indexing status
server.addTool({
  name: 'get_indexing_status',
  description: 'Get the current status of codebase indexing',
  inputSchema: {
    type: 'object',
    properties: {}
  },
  handler: async () => {
    try {
      // Check if collection exists
      try {
        const collection = await qdrantClient.getCollection(config.collectionName);
        const count = await qdrantClient.count(config.collectionName);
        
        return {
          status: 'active',
          collection: config.collectionName,
          vectorSize: collection.config.params.vectors.size,
          indexedFiles: count.result,
          model: config.model,
          qdrantUrl: config.qdrantUrl
        };
      } catch (error) {
        return {
          status: 'not_initialized',
          error: error.message
        };
      }
    } catch (error) {
      throw new Error(`Failed to get indexing status: ${error.message}`);
    }
  }
});

// Start the server
server.start();
console.log('Embedding MCP Server started');