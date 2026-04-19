#!/usr/bin/env python3
"""
Knowledge Graph Visualizer
Creates interactive HTML visualization
"""

import json
from pyvis.network import Network

# Load the graph
print("📂 Loading knowledge graph...")
with open("deepseekmath_kg/graph_store.json", "r") as f:
    graph_data = json.load(f)

graph_dict = graph_data["graph_dict"]

# Count stats
nodes = set()
edges = []

for source, relations in graph_dict.items():
    nodes.add(source)
    for relation in relations:
        relation_type = relation[0]
        target = relation[1]
        nodes.add(target)
        edges.append((source, target, relation_type))

print(f"✅ Loaded graph")
print(f"\n📊 Statistics:")
print(f"   - Entities: {len(nodes)}")
print(f"   - Relationships: {len(edges)}")

# Create visualization
print("\n🎨 Creating visualization...")
net = Network(height="900px", width="100%", directed=True)

# Add nodes
for node in nodes:
    net.add_node(node, label=node, title=node)

# Add edges
for source, target, label in edges:
    net.add_edge(source, target, label=label)

# Save
output = "knowledge_graph.html"
net.save_graph(output)

print(f"\n✅ Visualization saved to: {output}")
print(f"\n💡 Open {output} in your browser!")
