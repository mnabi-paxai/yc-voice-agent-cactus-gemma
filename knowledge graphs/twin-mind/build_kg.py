#!/usr/bin/env python3
"""
Non-interactive Knowledge Graph Builder
Builds the graph automatically without user input
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file!")
    sys.exit(1)

print("✅ Gemini API key loaded")
print("🚀 Starting knowledge graph builder...\n")

from knowledge_graph_simple import (
    create_knowledge_graph,
    load_existing_graph,
    query_graph,
    STORAGE_DIR
)

def main():
    # Check if graph already exists
    if Path(STORAGE_DIR).exists():
        print(f"📂 Found existing graph at: {STORAGE_DIR}")
        print("Loading existing graph...")
        kg_index = load_existing_graph()
    else:
        print("🆕 Creating new knowledge graph...")
        pdf_path = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/DeepSeekMath.pdf"

        if not os.path.exists(pdf_path):
            print(f"❌ PDF not found: {pdf_path}")
            sys.exit(1)

        print(f"📄 Processing: {pdf_path}")
        print("⏱️  This will take 2-5 minutes...\n")

        kg_index = create_knowledge_graph(pdf_path)

    # Run example queries
    print("\n" + "="*60)
    print("🔍 Testing Knowledge Graph with Sample Queries")
    print("="*60 + "\n")

    queries = [
        "What is DeepSeekMath?",
        "What are the main contributions of this paper?",
        "What benchmarks were used to evaluate the model?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*60}")
        print(f"Query {i}/{len(queries)}")
        print(f"{'='*60}")
        query_graph(kg_index, query)

    print("\n" + "="*60)
    print("✅ Knowledge Graph Build Complete!")
    print("="*60)
    print(f"\n📁 Graph saved to: {STORAGE_DIR}")
    print("\n💡 To query interactively, run:")
    print("   python3 query_kg.py")
    print("\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
