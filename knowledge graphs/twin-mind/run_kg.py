#!/usr/bin/env python3
"""
Interactive Knowledge Graph Builder
Run locally on your machine - no Docker needed!
Powered by Google Gemini
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check for Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your-gemini-api-key-here":
    print("\n" + "="*60)
    print("⚠️  GEMINI_API_KEY not found!")
    print("="*60)
    print("\nPlease create a .env file with your Gemini API key:")
    print("\n  1. Copy .env.example to .env:")
    print("     cp .env.example .env")
    print("\n  2. Edit .env and add your API key:")
    print("     GEMINI_API_KEY=your-actual-key-here")
    print("\n  3. Get your API key from:")
    print("     https://makersuite.google.com/app/apikey")
    print("\nThen run this script again:")
    print("  python3 run_kg.py")
    print("\n" + "="*60)
    sys.exit(1)

# Now import the knowledge graph module
from knowledge_graph_simple import (
    create_knowledge_graph,
    load_existing_graph,
    query_graph,
    update_graph,
    STORAGE_DIR
)

def main_menu():
    """Interactive menu for knowledge graph operations"""

    print("\n" + "="*60)
    print("📚 Local Knowledge Graph Manager")
    print("="*60)

    # Check if graph exists
    graph_exists = Path(STORAGE_DIR).exists()

    if graph_exists:
        print("✅ Found existing graph at:", STORAGE_DIR)
        print("\nOptions:")
        print("  1. Load and query existing graph")
        print("  2. Add new PDF to graph")
        print("  3. Delete graph and start fresh")
        print("  4. Exit")
        choice = input("\nYour choice (1-4): ").strip()
    else:
        print("🆕 No existing graph found")
        print("\nOptions:")
        print("  1. Create new graph from PDF")
        print("  2. Exit")
        choice = input("\nYour choice (1-2): ").strip()

    return choice, graph_exists


def create_new_graph():
    """Create a new knowledge graph"""
    pdf_path = input("\nEnter PDF path (or press Enter for DeepSeekMath.pdf): ").strip()

    if not pdf_path:
        pdf_path = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/DeepSeekMath.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return None

    print(f"\n🚀 Creating knowledge graph from: {pdf_path}")
    print("⏱️  This will take 2-5 minutes...\n")

    kg_index = create_knowledge_graph(pdf_path)
    return kg_index


def query_interactive(kg_index):
    """Interactive query mode"""
    print("\n" + "="*60)
    print("💬 Query Mode (type 'quit' to exit)")
    print("="*60)

    example_queries = [
        "What is DeepSeekMath?",
        "What are the main contributions?",
        "How does the training work?",
        "What benchmarks were used?"
    ]

    print("\n💡 Example queries:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")

    while True:
        query = input("\n🔍 Your question (or number 1-4, or 'quit'): ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        # Handle numbered selections
        if query.isdigit() and 1 <= int(query) <= len(example_queries):
            query = example_queries[int(query) - 1]

        if query:
            try:
                query_graph(kg_index, query)
            except Exception as e:
                print(f"❌ Error: {e}")


def add_pdf_to_graph(kg_index):
    """Add a new PDF to existing graph"""
    pdf_path = input("\nEnter path to new PDF: ").strip()

    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return

    print(f"\n🔄 Adding {pdf_path} to graph...")
    update_graph(kg_index, pdf_path)
    print("✅ PDF added successfully!")


def delete_graph():
    """Delete existing graph"""
    import shutil

    confirm = input(f"\n⚠️  Delete graph at {STORAGE_DIR}? (yes/no): ").strip().lower()

    if confirm == 'yes':
        shutil.rmtree(STORAGE_DIR)
        print("🗑️  Graph deleted!")
    else:
        print("❌ Cancelled")


def main():
    """Main application loop"""

    print("\n🎯 Starting Local Knowledge Graph Manager...")

    kg_index = None

    while True:
        choice, graph_exists = main_menu()

        if not graph_exists:
            # No existing graph
            if choice == '1':
                kg_index = create_new_graph()
                if kg_index:
                    query_interactive(kg_index)
            elif choice == '2':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
        else:
            # Existing graph found
            if choice == '1':
                if kg_index is None:
                    kg_index = load_existing_graph()
                query_interactive(kg_index)
            elif choice == '2':
                if kg_index is None:
                    kg_index = load_existing_graph()
                add_pdf_to_graph(kg_index)
            elif choice == '3':
                delete_graph()
                kg_index = None
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
