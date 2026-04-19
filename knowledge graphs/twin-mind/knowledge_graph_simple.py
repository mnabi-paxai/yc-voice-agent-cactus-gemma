"""
Simple Knowledge Graph Builder - NO DOCKER NEEDED
Uses in-memory graph with disk persistence
Good for: Medium-sized graphs, local development
Powered by Google Gemini
"""

import os
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, KnowledgeGraphIndex, StorageContext, Settings
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Load environment variables from .env file
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PDF_PATH = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/DeepSeekMath.pdf"
STORAGE_DIR = "./graph_storage"

def create_knowledge_graph(
    pdf_path: str,
    storage_dir: str = STORAGE_DIR,
    max_triplets_per_chunk: int = 2,  # Reduced for speed
    chunk_size: int = 1024  # Larger chunks = fewer nodes = faster
):
    """
    Create knowledge graph with local file storage (no database needed)
    """

    # Initialize simple graph store (saves to disk)
    print("📁 Setting up local graph storage...")
    graph_store = SimpleGraphStore()
    storage_context = StorageContext.from_defaults(graph_store=graph_store)

    # Initialize Gemini LLM (Balanced speed and quality)
    print("🤖 Initializing Gemini Flash (fast model with good quality)...")
    llm = Gemini(
        api_key=GEMINI_API_KEY,
        model="models/gemini-flash-latest",  # Fast model for quicker processing
        temperature=0
    )

    embed_model = GeminiEmbedding(
        api_key=GEMINI_API_KEY,
        model_name="models/gemini-embedding-001"
    )

    # Set global defaults
    Settings.llm = llm
    Settings.embed_model = embed_model

    # Load documents
    print(f"📄 Loading PDF: {pdf_path}")
    documents = SimpleDirectoryReader(input_files=[pdf_path]).load_data()
    print(f"✅ Loaded {len(documents)} document sections")

    # Build knowledge graph
    print("🔨 Building knowledge graph...")
    kg_index = KnowledgeGraphIndex.from_documents(
        documents,
        storage_context=storage_context,
        llm=llm,
        embed_model=embed_model,
        max_triplets_per_chunk=max_triplets_per_chunk,
        chunk_size=chunk_size,
        show_progress=True,
        include_embeddings=True
    )

    # Save to disk
    print(f"💾 Saving graph to {storage_dir}...")
    kg_index.storage_context.persist(persist_dir=storage_dir)

    print("✅ Knowledge graph created and saved!")
    return kg_index


def load_existing_graph(storage_dir: str = STORAGE_DIR):
    """
    Load previously created graph from disk
    """
    from llama_index.core import load_index_from_storage, StorageContext

    print(f"📂 Loading graph from {storage_dir}...")
    storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
    kg_index = load_index_from_storage(storage_context)
    print("✅ Graph loaded!")
    return kg_index


def query_graph(kg_index, query: str):
    """Query the knowledge graph"""
    print(f"\n🔍 Query: {query}")

    query_engine = kg_index.as_query_engine(
        include_text=True,
        response_mode="tree_summarize"
    )

    response = query_engine.query(query)
    print(f"\n💡 Answer:\n{response}\n")
    return response


def update_graph(kg_index, new_pdf_path: str, storage_dir: str = STORAGE_DIR):
    """Add new documents to existing graph"""
    print(f"🔄 Adding new document: {new_pdf_path}")
    new_docs = SimpleDirectoryReader(input_files=[new_pdf_path]).load_data()
    kg_index.insert_documents(new_docs)

    # Save updated graph
    kg_index.storage_context.persist(persist_dir=storage_dir)
    print("✅ Graph updated and saved!")


if __name__ == "__main__":
    import sys

    # Check OpenAI API key
    if OPENAI_API_KEY == "your-api-key-here":
        print("⚠️  Please set your OPENAI_API_KEY environment variable")
        print("   export OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    # Check if graph already exists
    import os.path
    if os.path.exists(STORAGE_DIR):
        print("📂 Found existing graph. Loading...")
        kg_index = load_existing_graph()
    else:
        print("🆕 Creating new graph...")
        kg_index = create_knowledge_graph(PDF_PATH)

    # Example queries
    queries = [
        "What is DeepSeekMath?",
        "What are the main contributions of this paper?",
        "How does Group Relative Policy Optimization work?",
    ]

    for query in queries:
        query_graph(kg_index, query)

    print("\n" + "="*60)
    print("✅ Done! Graph saved to:", STORAGE_DIR)
    print("="*60)
    print("\nTo query again without rebuilding:")
    print("  python3 -c \"from knowledge_graph_simple import load_existing_graph, query_graph; kg=load_existing_graph(); query_graph(kg, 'your question')\"")
