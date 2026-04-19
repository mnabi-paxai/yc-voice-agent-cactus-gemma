#!/usr/bin/env python3
"""
Multi-Paper Knowledge Graph Builder
Processes all papers and creates a unified knowledge graph
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from glob import glob

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found!")
    sys.exit(1)

from llama_index.core import SimpleDirectoryReader, Document, KnowledgeGraphIndex, StorageContext, Settings
from llama_index.core.graph_stores import SimpleGraphStore
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

# Configuration
PAPERS_DIR = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/Papers"
STORAGE_DIR = "./all_papers_kg"

print("="*60)
print("📚 Multi-Paper Knowledge Graph Builder")
print("="*60)

# Check for existing graph
if Path(STORAGE_DIR).exists():
    print(f"\n⚠️  Graph already exists at: {STORAGE_DIR}")
    response = input("Delete and rebuild? (yes/no): ").strip().lower()
    if response != "yes":
        print("❌ Cancelled")
        sys.exit(0)
    import shutil
    shutil.rmtree(STORAGE_DIR)
    print("🗑️  Deleted existing graph")

# Find all PDFs (exclude very large ones)
print(f"\n📂 Scanning papers directory: {PAPERS_DIR}")
all_pdfs = glob(f"{PAPERS_DIR}/*.pdf")

# Filter out papers larger than 10MB (NASA paper is 58MB)
pdf_files = []
excluded = []

for pdf in all_pdfs:
    size_mb = os.path.getsize(pdf) / (1024 * 1024)
    if size_mb < 10:  # Only process papers < 10MB
        pdf_files.append(pdf)
    else:
        excluded.append((pdf, size_mb))

print(f"✅ Found {len(pdf_files)} PDF files to process:")
for i, pdf in enumerate(pdf_files, 1):
    name = os.path.basename(pdf)
    size_mb = os.path.getsize(pdf) / (1024 * 1024)
    print(f"   {i}. {name} ({size_mb:.1f} MB)")

if excluded:
    print(f"\n⚠️  Excluded {len(excluded)} large file(s):")
    for pdf, size_mb in excluded:
        print(f"   - {os.path.basename(pdf)} ({size_mb:.1f} MB) - too large")

# Initialize models
print("\n🤖 Initializing Gemini Flash...")
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

# Load all documents
print("\n📄 Loading all PDFs...")
all_documents = []

for pdf in pdf_files:
    name = os.path.basename(pdf)
    print(f"   Loading {name}...")
    try:
        docs = SimpleDirectoryReader(input_files=[pdf]).load_data()

        # Add metadata to identify source
        for doc in docs:
            doc.metadata["source"] = name

        all_documents.extend(docs)
        print(f"      ✅ Loaded {len(docs)} sections")
    except Exception as e:
        print(f"      ❌ Error: {e}")

print(f"\n✅ Total loaded: {len(all_documents)} document sections")

# VERY aggressive chunking for speed - fewer nodes
print("\n✂️  Chunking documents (very large chunks for fast processing)...")
text_splitter = SentenceSplitter(
    chunk_size=16384,  # VERY large chunks (16KB per chunk)
    chunk_overlap=400
)

# Initialize graph storage
print("\n📁 Setting up graph storage...")
graph_store = SimpleGraphStore()
storage_context = StorageContext.from_defaults(graph_store=graph_store)

# Build knowledge graph
print("\n🔨 Building unified knowledge graph...")
print("⏱️  This will take 20-40 minutes for all papers...")
print("💡 Progress will be shown below:\n")

kg_index = KnowledgeGraphIndex.from_documents(
    all_documents,
    storage_context=storage_context,
    llm=llm,
    embed_model=embed_model,
    max_triplets_per_chunk=3,  # Extract more relationships per chunk
    transformations=[text_splitter],
    show_progress=True,
    include_embeddings=True
)

# Save
print(f"\n💾 Saving unified graph to {STORAGE_DIR}...")
kg_index.storage_context.persist(persist_dir=STORAGE_DIR)

# Get statistics
with open(f"{STORAGE_DIR}/graph_store.json", "r") as f:
    import json
    graph_data = json.load(f)
    nodes = set()
    edges = 0

    for source, relations in graph_data["graph_dict"].items():
        nodes.add(source)
        for relation in relations:
            nodes.add(relation[1])
            edges += 1

print("\n" + "="*60)
print("✅ Unified Knowledge Graph Complete!")
print("="*60)
print(f"\n📊 Statistics:")
print(f"   - Papers processed: {len(pdf_files)}")
print(f"   - Total entities: {len(nodes)}")
print(f"   - Total relationships: {edges}")
print(f"\n📁 Saved to: {STORAGE_DIR}/")
print(f"\n💡 Next steps:")
print(f"   1. Visualize: python3 visualize_multi_graph.py")
print(f"   2. Query: python3 query_multi_kg.py")
