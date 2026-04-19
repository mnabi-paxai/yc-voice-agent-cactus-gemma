#!/usr/bin/env python3
"""
Simple Query Interface for Knowledge Graph
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file!")
    sys.exit(1)

from knowledge_graph_simple import load_existing_graph, query_graph, STORAGE_DIR

def main():
    # Check if graph exists
    if not Path(STORAGE_DIR).exists():
        print("❌ No knowledge graph found!")
        print("Please run: python3 build_kg.py")
        sys.exit(1)

    print("📂 Loading knowledge graph...")
    kg_index = load_existing_graph()

    print("\n" + "="*60)
    print("💬 Interactive Query Mode")
    print("="*60)
    print("\nType your questions (or 'quit' to exit)")
    print("\n💡 Example queries:")
    print("  - What is DeepSeekMath?")
    print("  - How does the training work?")
    print("  - What are the main results?")
    print("  - Explain the GRPO method")
    print("")

    while True:
        try:
            query = input("\n🔍 Your question: ").strip()

            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break

            if not query:
                continue

            query_graph(kg_index, query)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
