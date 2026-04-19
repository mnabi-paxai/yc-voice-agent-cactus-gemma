#!/usr/bin/env python3
"""
Generate a relationship matrix showing connections between primary concepts.
"""

import json
from collections import defaultdict


def main():
    # Load the knowledge graph
    with open('knowledge-graph.json', 'r') as f:
        graph = json.load(f)

    concepts = {c['id']: c for c in graph['nodes']}
    relationships = graph['edges']

    # Get primary topics only
    primary_topics = {
        cid: concept for cid, concept in concepts.items()
        if concept['type'] == 'primary_topic'
    }

    print(f"Found {len(primary_topics)} primary topics")

    # Build relationship matrix
    matrix = defaultdict(lambda: defaultdict(list))

    for rel in relationships:
        source = rel['source']
        target = rel['target']
        rel_type = rel['relationship_type']

        # Only include if both are primary or one is primary
        if source in primary_topics and target in primary_topics:
            matrix[source][target].append(rel_type)
        elif source in primary_topics:
            # Find which primary topic the target belongs to
            target_concept = concepts.get(target)
            if target_concept:
                target_file = target_concept['source_file']
                # Find primary for this file
                for pid, pconcept in primary_topics.items():
                    if pconcept['source_file'] == target_file:
                        matrix[source][pid].append(rel_type)
                        break
        elif target in primary_topics:
            source_concept = concepts.get(source)
            if source_concept:
                source_file = source_concept['source_file']
                for pid, pconcept in primary_topics.items():
                    if pconcept['source_file'] == source_file:
                        matrix[pid][target].append(rel_type)
                        break

    # Generate markdown table
    output = "# Relationship Matrix: Primary Topics\n\n"
    output += "This matrix shows relationships between the primary topics in the knowledge graph.\n\n"
    output += "Legend: Number indicates relationship count. Hover in visualization for details.\n\n"

    # Sort topics for consistent ordering
    topic_ids = sorted(primary_topics.keys(), key=lambda x: primary_topics[x]['label'])
    topic_labels = [primary_topics[tid]['label'] for tid in topic_ids]

    # Create abbreviated labels for table
    abbrev = {}
    for i, tid in enumerate(topic_ids, 1):
        abbrev[tid] = f"T{i}"

    # Legend
    output += "## Topic Legend\n\n"
    for i, tid in enumerate(topic_ids, 1):
        output += f"- **T{i}**: {primary_topics[tid]['label']}\n"
    output += "\n---\n\n"

    # Table
    output += "## Relationship Matrix\n\n"
    output += "|   |" + "|".join([abbrev[tid] for tid in topic_ids]) + "|\n"
    output += "|" + "|".join(["---"] * (len(topic_ids) + 1)) + "|\n"

    for source_id in topic_ids:
        row = f"|**{abbrev[source_id]}**|"
        for target_id in topic_ids:
            if source_id == target_id:
                cell = "-"
            else:
                rels = matrix[source_id][target_id]
                if rels:
                    cell = str(len(rels))
                else:
                    cell = ""
            row += f"{cell}|"
        output += row + "\n"

    output += "\n---\n\n"

    # Detailed relationships
    output += "## Detailed Relationships\n\n"

    for source_id in topic_ids:
        source_label = primary_topics[source_id]['label']
        has_connections = False

        connections = []
        for target_id in topic_ids:
            if source_id != target_id:
                rels = matrix[source_id][target_id]
                if rels:
                    has_connections = True
                    target_label = primary_topics[target_id]['label']
                    rel_summary = ", ".join(set(rels))
                    connections.append(f"  - **{target_label}**: {rel_summary} ({len(rels)} connections)")

        if has_connections:
            output += f"### {source_label}\n\n"
            output += "\n".join(connections) + "\n\n"

    # Save
    with open('relationship-matrix.md', 'w') as f:
        f.write(output)

    print("Generated relationship-matrix.md")

    # Also generate statistics
    stats = {
        'most_connected_pairs': [],
        'relationship_density': 0,
    }

    # Find most connected pairs
    pair_counts = []
    for source_id in topic_ids:
        for target_id in topic_ids:
            if source_id < target_id:  # Avoid duplicates
                count = len(matrix[source_id][target_id]) + len(matrix[target_id][source_id])
                if count > 0:
                    pair_counts.append((
                        primary_topics[source_id]['label'],
                        primary_topics[target_id]['label'],
                        count
                    ))

    pair_counts.sort(key=lambda x: x[2], reverse=True)

    print("\nMost Connected Topic Pairs:")
    for source, target, count in pair_counts[:10]:
        print(f"  {source} <-> {target}: {count} connections")

    # Density
    n = len(topic_ids)
    max_edges = n * (n - 1)  # Directed graph
    actual_edges = sum(len(matrix[s][t]) for s in matrix for t in matrix[s])
    density = actual_edges / max_edges if max_edges > 0 else 0

    print(f"\nGraph Density: {density:.3f}")
    print(f"  (Actual edges: {actual_edges} / Maximum possible: {max_edges})")


if __name__ == '__main__':
    main()
