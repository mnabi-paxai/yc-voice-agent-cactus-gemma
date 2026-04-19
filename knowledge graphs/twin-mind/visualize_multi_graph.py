#!/usr/bin/env python3
"""
Visualize Multi-Paper Knowledge Graph
"""

import json
from pyvis.network import Network

# Load the graph
print("📂 Loading unified knowledge graph...")
with open("all_papers_kg/graph_store.json", "r") as f:
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
print("\n🎨 Creating interactive visualization...")
net = Network(
    height="1000px",
    width="100%",
    directed=True,
    bgcolor="#0a0a0a",
    font_color="white"
)

# Color nodes by type
def get_color(node):
    node_lower = node.lower()
    if any(x in node_lower for x in ["deepseek", "gpt", "llama", "model"]):
        return "#FF6B6B"  # Red for models
    elif any(x in node_lower for x in ["ppo", "dpo", "grpo", "optimization"]):
        return "#4ECDC4"  # Teal for algorithms
    elif any(x in node_lower for x in ["training", "learning", "method"]):
        return "#95E1D3"  # Green for methods
    elif any(x in node_lower for x in ["math", "reasoning", "proof"]):
        return "#F9CA24"  # Yellow for reasoning
    else:
        return "#C8D6E5"  # Gray for others

# Add nodes
for node in nodes:
    net.add_node(
        node,
        label=node[:50] + "..." if len(node) > 50 else node,
        title=node,
        color=get_color(node),
        size=20
    )

# Add edges
for source, target, label in edges:
    net.add_edge(source, target, label=label, color="#555555")

# Save
output = "all_papers_knowledge_graph.html"
net.save_graph(output)

print(f"\n✅ Visualization saved to: {output}")
print(f"\n💡 Open {output} in your browser!")
print(f"\n🎨 Color Legend:")
print(f"   🔴 Red - AI Models")
print(f"   🟦 Teal - Optimization Algorithms")
print(f"   🟩 Green - Training Methods")
print(f"   🟨 Yellow - Reasoning/Math")
print(f"   ⚪ Gray - Other Concepts")
