"""
Optimized Knowledge Graph Builder using Neo4j + LlamaIndex + Gemini
Optimized for: Speed > Volume > Accuracy

Based on: https://neo4j.com/labs/genai-ecosystem/llamaindex/
Uses PropertyGraphIndex with Neo4jPropertyGraphStore for production-grade KG
"""

import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, PropertyGraphIndex, Settings
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.core.indices.property_graph import SimpleLLMPathExtractor
from typing import Literal

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PDF_PATH = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/DeepSeekMath.pdf"

# Neo4j Configuration (default local installation)
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://localhost:7687")

# SPEED OPTIMIZATIONS
CHUNK_SIZE = 2048  # Larger chunks = fewer API calls = faster
CHUNK_OVERLAP = 200  # Minimal overlap for speed
MAX_TRIPLETS_PER_CHUNK = 10  # High volume of extractions per chunk

def create_optimized_kg(
    pdf_path: str,
    speed_priority: bool = True
):
    """
    Create knowledge graph optimized for speed and volume

    Args:
        pdf_path: Path to PDF file
        speed_priority: If True, uses fastest Gemini model (Flash)
    """

    print("=" * 70)
    print("🚀 OPTIMIZED KNOWLEDGE GRAPH BUILDER")
    print("=" * 70)

    # Step 1: Initialize Neo4j Graph Store
    print("\n📊 Connecting to Neo4j...")
    try:
        graph_store = Neo4jPropertyGraphStore(
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            url=NEO4J_URL,
        )
        print("✅ Connected to Neo4j")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("\n💡 Quick fix:")
        print("   1. Install Neo4j Desktop: https://neo4j.com/download/")
        print("   2. Create a local database")
        print("   3. Start the database")
        print("   4. Update .env with credentials")
        return None

    # Step 2: Initialize Gemini (SPEED MODE)
    print("\n🤖 Initializing Gemini...")
    if speed_priority:
        model_name = "models/gemini-2.5-flash"  # Fastest model
        print("   Using: Gemini 2.5 Flash (⚡ FASTEST)")
    else:
        model_name = "models/gemini-2.5-pro"  # More accurate but slower
        print("   Using: Gemini 2.5 Pro (🎯 ACCURATE)")

    llm = Gemini(
        api_key=GEMINI_API_KEY,
        model=model_name,
        temperature=0  # Deterministic for consistency
    )

    embed_model = GeminiEmbedding(
        api_key=GEMINI_API_KEY,
        model_name="models/embedding-001"  # Embedding model
    )

    # Set global defaults
    Settings.llm = llm
    Settings.embed_model = embed_model
    Settings.chunk_size = CHUNK_SIZE
    Settings.chunk_overlap = CHUNK_OVERLAP

    # Step 3: Load PDF
    print(f"\n📄 Loading PDF: {pdf_path}")
    documents = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
    print(f"✅ Loaded {len(documents)} pages")

    # Step 4: Configure KG Extractor (HIGH VOLUME)
    print("\n🔧 Configuring graph extractor...")
    print(f"   Max triplets per chunk: {MAX_TRIPLETS_PER_CHUNK}")
    print(f"   Chunk size: {CHUNK_SIZE} tokens")

    kg_extractor = SimpleLLMPathExtractor(
        llm=llm,
        max_paths_per_chunk=MAX_TRIPLETS_PER_CHUNK,
        num_workers=4  # Parallel processing for speed
    )

    # Step 5: Build Knowledge Graph
    print("\n🔨 Building knowledge graph...")
    print("   This may take 3-10 minutes depending on PDF size")
    print("   ⏳ Processing...")

    index = PropertyGraphIndex.from_documents(
        documents,
        embed_model=embed_model,
        kg_extractors=[kg_extractor],
        property_graph_store=graph_store,
        show_progress=True,
    )

    print("\n✅ Knowledge graph created successfully!")

    # Step 6: Display Statistics
    print("\n📊 Graph Statistics:")
    try:
        # Query Neo4j for stats
        result = graph_store._driver.execute_query("""
            MATCH (n)
            RETURN count(n) as node_count
        """)
        node_count = result.records[0]["node_count"] if result.records else 0

        result = graph_store._driver.execute_query("""
            MATCH ()-[r]->()
            RETURN count(r) as rel_count
        """)
        rel_count = result.records[0]["rel_count"] if result.records else 0

        print(f"   Nodes: {node_count:,}")
        print(f"   Relationships: {rel_count:,}")
        print(f"   Density: {rel_count/max(node_count, 1):.2f} relationships/node")
    except Exception as e:
        print(f"   (Could not retrieve stats: {e})")

    return index, graph_store


def query_kg(index, query: str):
    """Query the knowledge graph"""
    print(f"\n🔍 Query: {query}")
    print("=" * 70)

    query_engine = index.as_query_engine(
        include_text=True,
        response_mode="tree_summarize",
        similarity_top_k=5
    )

    response = query_engine.query(query)
    print(f"\n💡 Answer:\n{response}\n")
    return response


def explore_graph(graph_store):
    """Explore the graph structure in Neo4j"""
    print("\n🔍 Sample Entities and Relationships:")
    print("=" * 70)

    try:
        # Get sample nodes
        result = graph_store._driver.execute_query("""
            MATCH (n)
            RETURN labels(n) as labels, n.name as name
            LIMIT 10
        """)

        print("\n📦 Sample Nodes:")
        for record in result.records:
            labels = record["labels"]
            name = record["name"]
            print(f"   {labels}: {name}")

        # Get sample relationships
        result = graph_store._driver.execute_query("""
            MATCH (a)-[r]->(b)
            RETURN a.name as source, type(r) as relationship, b.name as target
            LIMIT 10
        """)

        print("\n🔗 Sample Relationships:")
        for record in result.records:
            source = record["source"]
            rel = record["relationship"]
            target = record["target"]
            print(f"   {source} --[{rel}]--> {target}")

    except Exception as e:
        print(f"❌ Error exploring graph: {e}")


if __name__ == "__main__":
    import sys

    # Validate API key
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your-api-key-here":
        print("⚠️  Please set your GEMINI_API_KEY in .env file")
        print("   Get your key: https://makersuite.google.com/app/apikey")
        sys.exit(1)

    # Build the graph
    result = create_optimized_kg(
        PDF_PATH,
        speed_priority=True  # Set to False for more accuracy
    )

    if result is None:
        print("\n❌ Failed to create knowledge graph")
        sys.exit(1)

    index, graph_store = result

    # Explore the graph structure
    explore_graph(graph_store)

    # Example queries
    print("\n" + "=" * 70)
    print("📝 EXAMPLE QUERIES")
    print("=" * 70)

    queries = [
        "What is DeepSeekMath and what are its main contributions?",
        "Explain Group Relative Policy Optimization (GRPO)",
        "How does DeepSeekMath compare to other models like GPT-4?",
        "What benchmarks were used to evaluate DeepSeekMath?",
    ]

    for query in queries:
        query_kg(index, query)
        print("\n" + "-" * 70 + "\n")

    print("\n" + "=" * 70)
    print("✅ COMPLETE!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("   1. Open Neo4j Browser: http://localhost:7474")
    print("   2. Explore the graph visually")
    print("   3. Run custom Cypher queries")
    print("\n📊 Sample Cypher Query:")
    print("   MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25")
