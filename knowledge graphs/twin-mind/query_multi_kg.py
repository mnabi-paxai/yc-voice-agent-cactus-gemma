#!/usr/bin/env python3
"""
Query Multi-Paper Knowledge Graph
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

from llama_index.core import load_index_from_storage, StorageContext, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding

STORAGE_DIR = "./all_papers_kg"

# Check if graph exists
if not Path(STORAGE_DIR).exists():
    print("❌ No knowledge graph found!")
    print("Run: python3 build_multi_paper_kg.py")
    sys.exit(1)

# Initialize models
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

# Load graph
print("📂 Loading unified knowledge graph...")
storage_context = StorageContext.from_defaults(persist_dir=STORAGE_DIR)
kg_index = load_index_from_storage(storage_context)
print("✅ Graph loaded!\n")

print("="*60)
print("💬 Multi-Paper Knowledge Graph Query Interface")
print("="*60)
print("\nType your questions (or 'quit' to exit)")
print("\n💡 Example queries:")
print("  - Compare PPO and DPO optimization methods")
print("  - What is DeepSeekMath and how does it work?")
print("  - Explain the relationship between GRPO and PPO")
print("  - What are the main contributions across all papers?")
print("")

query_engine = kg_index.as_query_engine(
    include_text=True,
    response_mode="tree_summarize"
)

while True:
    try:
        query = input("🔍 Your question: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break

        if not query:
            continue

        print("\n💭 Thinking...")
        response = query_engine.query(query)
        print(f"\n💡 Answer:\n{response}\n")

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
