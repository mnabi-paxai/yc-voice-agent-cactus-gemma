#!/usr/bin/env python3
"""
Simple Static Graph Visualizer
Creates a PNG image of the knowledge graph
"""

import json
import matplotlib.pyplot as plt
import networkx as nx

# Load the graph
print("📂 Loading knowledge graph...")
with open("deepseekmath_kg/graph_store.json", "r") as f:
    graph_data = json.load(f)

# Create NetworkX graph
G = nx.Graph()

# Parse the graph structure
if "graph_dict" in graph_data:
    graph_dict = graph_data["graph_dict"]

    for source, relations in graph_dict.items():
        G.add_node(source)

        for relation_type, relation_list in relations.items():
            for relation in relation_list:
                target = relation[1]
                G.add_node(target)
                G.add_edge(source, target, label=relation[0])

print(f"📊 Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

# Create visualization
print("🎨 Creating visualization...")
plt.figure(figsize=(20, 15))
pos = nx.spring_layout(G, k=2, iterations=50)

# Draw nodes
nx.draw_networkx_nodes(
    G, pos,
    node_color='lightblue',
    node_size=3000,
    alpha=0.9
)

# Draw edges
nx.draw_networkx_edges(
    G, pos,
    width=1,
    alpha=0.5,
    edge_color='gray'
)

# Draw labels (truncated)
labels = {node: node[:30] + "..." if len(node) > 30 else node for node in G.nodes()}
nx.draw_networkx_labels(
    G, pos,
    labels,
    font_size=8,
    font_weight='bold'
)

plt.title("DeepSeekMath Knowledge Graph", fontsize=20, fontweight='bold')
plt.axis('off')
plt.tight_layout()

# Save
output_file = "knowledge_graph.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\n✅ Static visualization saved to: {output_file}")

# Show
plt.show()
