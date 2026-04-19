#!/usr/bin/env python3
"""
Filter knowledge graph by edge confidence threshold.
Creates a trimmed version with only high-confidence relationships.
"""

import json
from pathlib import Path
from collections import defaultdict


def filter_graph_by_confidence(input_file, output_file, min_confidence=0.85):
    """Filter knowledge graph to keep only edges above confidence threshold."""

    print(f"Loading knowledge graph from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    original_edges = len(graph['edges'])
    original_nodes = len(graph['nodes'])

    # Filter edges by confidence
    print(f"\nFiltering edges with confidence > {min_confidence}...")
    filtered_edges = [
        edge for edge in graph['edges']
        if edge['confidence'] > min_confidence
    ]

    print(f"  Original edges: {original_edges}")
    print(f"  Filtered edges: {len(filtered_edges)}")
    print(f"  Removed: {original_edges - len(filtered_edges)} ({100*(original_edges - len(filtered_edges))/original_edges:.1f}%)")

    # Find nodes that are still connected
    connected_node_ids = set()
    for edge in filtered_edges:
        connected_node_ids.add(edge['source'])
        connected_node_ids.add(edge['target'])

    # Filter nodes to keep only connected ones
    filtered_nodes = [
        node for node in graph['nodes']
        if node['id'] in connected_node_ids
    ]

    print(f"\n  Original nodes: {original_nodes}")
    print(f"  Filtered nodes: {len(filtered_nodes)}")
    print(f"  Removed: {original_nodes - len(filtered_nodes)} (isolated nodes)")

    # Compute statistics for filtered graph
    print("\nAnalyzing filtered graph...")

    # Degree distribution
    degree = defaultdict(int)
    for edge in filtered_edges:
        degree[edge['source']] += 1
        degree[edge['target']] += 1

    avg_degree = sum(degree.values()) / len(filtered_nodes) if filtered_nodes else 0
    max_degree = max(degree.values()) if degree else 0

    # Relationship type distribution
    rel_types = defaultdict(int)
    for edge in filtered_edges:
        rel_types[edge['relationship_type']] += 1

    # Confidence distribution
    confidence_ranges = {
        '0.85-0.90': 0,
        '0.90-0.95': 0,
        '0.95-1.00': 0
    }
    for edge in filtered_edges:
        conf = edge['confidence']
        if conf <= 0.90:
            confidence_ranges['0.85-0.90'] += 1
        elif conf <= 0.95:
            confidence_ranges['0.90-0.95'] += 1
        else:
            confidence_ranges['0.95-1.00'] += 1

    # Node type distribution
    node_types = defaultdict(int)
    for node in filtered_nodes:
        node_types[node['type']] += 1

    # Build filtered graph
    filtered_graph = {
        'metadata': {
            **graph['metadata'],
            'filtered': True,
            'min_confidence': min_confidence,
            'original_edges': original_edges,
            'original_nodes': original_nodes
        },
        'nodes': filtered_nodes,
        'edges': filtered_edges,
        'statistics': {
            'total_concepts': len(filtered_nodes),
            'total_relationships': len(filtered_edges),
            'average_degree': round(avg_degree, 2),
            'max_degree': max_degree,
            'node_types': dict(node_types),
            'relationship_types': dict(rel_types),
            'confidence_distribution': confidence_ranges
        }
    }

    # Save filtered graph
    print(f"\nSaving filtered graph to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_graph, f, indent=2, ensure_ascii=False)

    print("\nFiltered graph statistics:")
    print(f"  Nodes: {len(filtered_nodes)}")
    print(f"  Edges: {len(filtered_edges)}")
    print(f"  Average degree: {avg_degree:.2f}")
    print(f"  Max degree: {max_degree}")

    print("\nNode type distribution:")
    for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {node_type}: {count}")

    print("\nRelationship type distribution:")
    for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rel_type}: {count} ({100*count/len(filtered_edges):.1f}%)")

    print("\nConfidence distribution:")
    for range_name, count in confidence_ranges.items():
        print(f"  {range_name}: {count} ({100*count/len(filtered_edges):.1f}%)")

    # Find most connected nodes in filtered graph
    print("\nTop 10 most connected nodes in filtered graph:")
    sorted_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]
    node_id_to_label = {node['id']: node['label'] for node in filtered_nodes}

    for i, (node_id, deg) in enumerate(sorted_nodes, 1):
        label = node_id_to_label.get(node_id, 'Unknown')
        print(f"  {i}. {label} - {deg} connections")

    return filtered_graph


def generate_filtered_visualization(graph_file, output_html, title_suffix="(High Confidence)"):
    """Generate HTML visualization for filtered graph."""

    print(f"\nGenerating visualization from {graph_file}...")

    with open(graph_file, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    nodes = graph['nodes']
    edges = graph['edges']
    stats = graph['statistics']

    # Color mapping for node types
    color_map = {
        'primary_topic': '#e74c3c',      # Red
        'section_concept': '#3498db',     # Blue
        'domain_term': '#2ecc71',         # Green
        'emphasized_term': '#f39c12',     # Orange
        'linked_concept': '#9b59b6'       # Purple
    }

    # Build vis.js node list
    vis_nodes = []
    for node in nodes:
        color = color_map.get(node['type'], '#95a5a6')

        # Scale node size based on degree (count edges)
        degree = sum(1 for e in edges if e['source'] == node['id'] or e['target'] == node['id'])
        size = 10 + degree * 2  # Base size + scaling

        vis_nodes.append({
            'id': node['id'],
            'label': node['label'],
            'title': f"{node['label']}\nType: {node['type']}\nSource: {node['source_file']}\nConnections: {degree}",
            'color': color,
            'size': size
        })

    # Build vis.js edge list
    vis_edges = []
    for edge in edges:
        vis_edges.append({
            'from': edge['source'],
            'to': edge['target'],
            'title': f"{edge['relationship_type']}\nConfidence: {edge['confidence']:.2f}\n{edge.get('evidence_text', '')[:100]}...",
            'arrows': 'to',
            'color': {'opacity': min(edge['confidence'], 1.0)}
        })

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Graph Visualization {title_suffix}</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        #header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        #controls {{
            background: #ecf0f1;
            padding: 15px;
            text-align: center;
        }}
        #mynetwork {{
            width: 100%;
            height: 800px;
            border: 1px solid #ccc;
        }}
        #legend {{
            position: absolute;
            top: 100px;
            right: 20px;
            background: white;
            padding: 15px;
            border: 2px solid #2c3e50;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .legend-item {{
            margin: 5px 0;
        }}
        .legend-color {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            margin-right: 10px;
            vertical-align: middle;
        }}
        button {{
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            border-radius: 3px;
        }}
        button:hover {{
            background: #2980b9;
        }}
        .filter-badge {{
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>Knowledge Graph: RL & Post-Training {title_suffix}</h1>
        <p>{stats['total_concepts']} concepts | {stats['total_relationships']} relationships</p>
        <span class="filter-badge">Confidence > {graph['metadata']['min_confidence']}</span>
    </div>

    <div id="controls">
        <button onclick="network.fit()">Fit View</button>
        <button onclick="network.stabilize()">Stabilize</button>
        <button onclick="togglePhysics()">Toggle Physics</button>
        <label>
            <input type="checkbox" id="showLabels" checked onchange="toggleLabels()">
            Show Labels
        </label>
    </div>

    <div id="legend">
        <h3>Legend</h3>
        <div class="legend-item">
            <span class="legend-color" style="background: #e74c3c;"></span>
            Primary Topic
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #3498db;"></span>
            Section Concept
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #2ecc71;"></span>
            Domain Term
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #f39c12;"></span>
            Emphasized Term
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background: #9b59b6;"></span>
            Linked Concept
        </div>
    </div>

    <div id="mynetwork"></div>

    <script type="text/javascript">
        var nodes = new vis.DataSet({json.dumps(vis_nodes)});
        var edges = new vis.DataSet({json.dumps(vis_edges)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            nodes: {{
                shape: 'dot',
                font: {{
                    size: 12,
                    face: 'Arial'
                }},
                borderWidth: 2,
                borderWidthSelected: 4
            }},
            edges: {{
                font: {{
                    size: 10,
                    align: 'middle'
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                smooth: {{
                    type: 'continuous'
                }}
            }},
            physics: {{
                enabled: true,
                barnesHut: {{
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 150,
                    springConstant: 0.04
                }},
                stabilization: {{
                    iterations: 150
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                navigationButtons: true,
                keyboard: true
            }}
        }};

        var network = new vis.Network(container, data, options);

        var physicsEnabled = true;
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            network.setOptions({{physics: {{enabled: physicsEnabled}}}});
        }}

        function toggleLabels() {{
            var showLabels = document.getElementById('showLabels').checked;
            var allNodes = nodes.get();
            allNodes.forEach(function(node) {{
                nodes.update({{
                    id: node.id,
                    label: showLabels ? node.label : ''
                }});
            }});
        }}

        network.on("selectNode", function(params) {{
            console.log('Selected node:', params.nodes);
        }});

        network.on("selectEdge", function(params) {{
            console.log('Selected edge:', params.edges);
        }});
    </script>
</body>
</html>"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  ✓ Saved visualization to {output_html}")


def main():
    analysis_dir = Path("/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/wikis/analysis")

    input_file = analysis_dir / "knowledge-graph.json"
    output_file = analysis_dir / "knowledge-graph-filtered-0.85.json"
    output_html = analysis_dir / "graph-visualization-filtered-0.85.html"

    # Filter graph
    filtered_graph = filter_graph_by_confidence(
        input_file,
        output_file,
        min_confidence=0.85
    )

    # Generate visualization
    generate_filtered_visualization(
        output_file,
        output_html,
        title_suffix="(Confidence > 0.85)"
    )

    print("\n" + "=" * 80)
    print("FILTERING COMPLETE")
    print("=" * 80)
    print(f"\nFiltered graph saved to:")
    print(f"  - {output_file}")
    print(f"  - {output_html}")
    print(f"\nOpen the HTML file in a browser to view the filtered graph.")


if __name__ == '__main__':
    main()
