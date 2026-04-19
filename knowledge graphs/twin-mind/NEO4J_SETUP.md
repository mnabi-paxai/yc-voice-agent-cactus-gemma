# Neo4j Knowledge Graph Setup - OPTIMIZED

## 🎯 Optimization Priority: Speed > Volume > Accuracy

This setup uses **Neo4j + LlamaIndex + Gemini Flash** for maximum performance.

## Prerequisites

### 1. Install Dependencies

```bash
pip install llama-index llama-index-graph-stores-neo4j llama-index-llms-gemini llama-index-embeddings-gemini python-dotenv
```

### 2. Install Neo4j

**Option A: Neo4j Desktop (Recommended for beginners)**
1. Download: https://neo4j.com/download/
2. Install and open Neo4j Desktop
3. Create a new project
4. Create a new database (use password: "password" or update .env)
5. Start the database
6. Note the bolt URL (usually `bolt://localhost:7687`)

**Option B: Docker (Fast setup)**
```bash
docker run \
    --name neo4j \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

**Option C: Neo4j Aura (Cloud - Free tier available)**
1. Sign up: https://neo4j.com/cloud/aura/
2. Create a free database
3. Save the connection URL and credentials
4. Update .env with your Aura credentials

### 3. Configure Environment Variables

Edit `.env`:

```bash
# Gemini API Key (required)
GEMINI_API_KEY=your-gemini-api-key-here

# Neo4j Connection (update if different)
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
NEO4J_URL=bolt://localhost:7687
```

## 🚀 Quick Start

```bash
# Run the optimized builder
python3 build_neo4j_kg_optimized.py
```

## ⚡ Speed Optimizations

This script is optimized for **SPEED** with these settings:

1. **Gemini 1.5 Flash** - Fastest LLM (10x faster than Pro)
2. **Large chunks** (2048 tokens) - Fewer API calls
3. **High triplet extraction** (10 per chunk) - More entities per call
4. **Parallel processing** (4 workers) - Concurrent extraction
5. **Minimal overlap** (200 tokens) - Less redundancy

### Expected Performance

| PDF Size | Processing Time | Nodes | Relationships |
|----------|----------------|-------|---------------|
| ~50 pages | 3-5 minutes | 500-1000 | 1000-2000 |
| ~100 pages | 5-10 minutes | 1000-2000 | 2000-4000 |
| ~200 pages | 10-20 minutes | 2000-4000 | 4000-8000 |

DeepSeekMath PDF (~50 pages) should complete in **3-5 minutes**.

## 📊 Volume Optimization

To extract MORE entities and relationships:

Edit `build_neo4j_kg_optimized.py`:

```python
MAX_TRIPLETS_PER_CHUNK = 15  # Increase from 10
CHUNK_SIZE = 1024  # Decrease for more granular extraction
```

⚠️ **Trade-off**: More volume = slower processing

## 🎯 Accuracy Optimization

For higher accuracy (but slower):

```python
# In create_optimized_kg()
result = create_optimized_kg(
    PDF_PATH,
    speed_priority=False  # Uses Gemini 1.5 Pro instead of Flash
)
```

## 🔍 Querying Your Graph

### Method 1: Python API

```python
from build_neo4j_kg_optimized import create_optimized_kg, query_kg

# Load existing graph
index, graph_store = create_optimized_kg(PDF_PATH)

# Query
query_kg(index, "What is DeepSeekMath?")
```

### Method 2: Neo4j Browser

1. Open: http://localhost:7474
2. Login with credentials from .env
3. Run Cypher queries:

```cypher
// View all nodes
MATCH (n) RETURN n LIMIT 25

// Find specific entities
MATCH (n) WHERE n.name CONTAINS "DeepSeek" RETURN n

// Explore relationships
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 50

// Find central concepts (high degree nodes)
MATCH (n)-[r]-()
RETURN n.name, count(r) as connections
ORDER BY connections DESC
LIMIT 10
```

## 🔧 Troubleshooting

### "Connection refused" to Neo4j

Check if Neo4j is running:
```bash
# If using Docker
docker ps | grep neo4j

# If using Neo4j Desktop
# Check the database status in the UI
```

### "Out of memory" error

Reduce batch size:
```python
CHUNK_SIZE = 1024  # Reduce from 2048
MAX_TRIPLETS_PER_CHUNK = 5  # Reduce from 10
```

### Slow performance

1. **Use Gemini Flash** (not Pro)
2. **Increase chunk size** (fewer API calls)
3. **Check Neo4j memory** settings
4. **Use local Neo4j** (not cloud)

### Low extraction quality

1. **Switch to Gemini Pro**: `speed_priority=False`
2. **Reduce chunk size**: More context per extraction
3. **Add schema validation**: Define expected entities/relationships

## 📈 Comparison: Simple vs Neo4j

| Feature | SimpleGraphStore | Neo4jPropertyGraphStore |
|---------|------------------|-------------------------|
| **Setup** | ✅ Easy (no install) | ⚠️ Requires Neo4j |
| **Performance** | ⚠️ Slow queries | ✅ Fast queries |
| **Scalability** | ❌ Limited (<10K nodes) | ✅ Millions of nodes |
| **Query Language** | Python only | Cypher + Python |
| **Visualization** | ❌ None | ✅ Neo4j Browser |
| **Production Ready** | ❌ No | ✅ Yes |

**Use Neo4j if**: You want production-grade performance, visualization, and advanced queries
**Use Simple if**: Quick prototyping, small graphs, no database setup

## 🎓 Next Steps

1. **Visualize your graph** in Neo4j Browser
2. **Refine entity extraction** with custom schemas
3. **Add more PDFs** to expand the knowledge base
4. **Build a RAG system** on top of the graph
5. **Export insights** using Cypher queries

## 📚 Resources

- Neo4j Cypher Manual: https://neo4j.com/docs/cypher-manual/
- LlamaIndex PropertyGraph: https://docs.llamaindex.ai/en/stable/examples/property_graph/
- Gemini API Docs: https://ai.google.dev/docs

## 💡 Pro Tips

1. **Incremental Building**: Build graph in chunks for large PDFs
2. **Schema-guided Extraction**: Define entity types for better accuracy
3. **Vector + Graph Hybrid**: Combine vector search with graph traversal
4. **Caching**: Neo4j caches queries for faster repeated access
5. **Indexes**: Add Neo4j indexes on frequently queried properties
