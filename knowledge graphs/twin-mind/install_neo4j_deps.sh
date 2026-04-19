#!/bin/bash

# Install Neo4j dependencies for optimized knowledge graph
# Run this before using build_neo4j_kg_optimized.py

echo "🔧 Installing Neo4j dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install required packages
pip install llama-index-graph-stores-neo4j

echo ""
echo "✅ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Install Neo4j (see NEO4J_SETUP.md)"
echo "   2. Update .env with Neo4j credentials"
echo "   3. Run: python3 build_neo4j_kg_optimized.py"
