#!/usr/bin/env python3
"""
FAST Knowledge Graph Builder - Uses pre-parsed text
Much faster than parsing PDF repeatedly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found!")
    sys.exit(1)

from llama_index.core import Document, KnowledgeGraphIndex, StorageContext, Settings
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Paths
PARSED_TEXT = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/Parsed Data/DeepSeekMath_parsed.txt"
STORAGE_DIR = "./graph_storage"

print("✅ Gemini API key loaded")
print("🚀 Fast Knowledge Graph Builder\n")

# Check for existing graph
if Path(STORAGE_DIR).exists():
    print(f"📂 Graph already exists at: {STORAGE_DIR}")
    print("Delete it first if you want to rebuild")
    sys.exit(0)

print("📄 Loading pre-parsed text...")
with open(PARSED_TEXT, 'r', encoding='utf-8') as f:
    text = f.read()

# Create a single document
documents = [Document(text=text)]
print(f"✅ Loaded {len(text)} characters")

# Initialize models
print("🤖 Initializing Gemini Flash...")
llm = Gemini(
    api_key=GEMINI_API_KEY,
    model="models/gemini-flash-latest",
    temperature=0
)

embed_model = GeminiEmbedding(
    api_key=GEMINI_API_KEY,
    model_name="models/gemini-embedding-001"
)

Settings.llm = llm
Settings.embed_model = embed_model

# Aggressive chunking - creates fewer nodes
print("✂️  Chunking text (creating ~100-200 nodes instead of 1200)...")
text_splitter = SentenceSplitter(
    chunk_size=4096,  # Very large chunks
    chunk_overlap=200
)

# Initialize graph
print("📁 Setting up graph storage...")
graph_store = SimpleGraphStore()
storage_context = StorageContext.from_defaults(graph_store=graph_store)

# Build knowledge graph
print("🔨 Building knowledge graph...")
print("⏱️  Estimated time: 10-20 minutes\n")

kg_index = KnowledgeGraphIndex.from_documents(
    documents,
    storage_context=storage_context,
    llm=llm,
    embed_model=embed_model,
    max_triplets_per_chunk=2,
    transformations=[text_splitter],
    show_progress=True,
    include_embeddings=True
)

# Save
print(f"\n💾 Saving graph to {STORAGE_DIR}...")
kg_index.storage_context.persist(persist_dir=STORAGE_DIR)

print("\n" + "="*60)
print("✅ Knowledge Graph Complete!")
print("="*60)
print(f"\n📁 Saved to: {STORAGE_DIR}")
print("\n💡 Query it with:")
print("   python3 query_kg.py")
