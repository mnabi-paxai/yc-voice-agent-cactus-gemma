#!/usr/bin/env python3
"""
Interactive Knowledge Graph Explorer

Simple command-line tool to explore the extracted knowledge graph.
"""

import json
from collections import defaultdict


def load_graph():
    """Load the knowledge graph."""
    with open('knowledge-graph.json', 'r') as f:
        return json.load(f)


def find_concept(graph, query):
    """Find concepts matching a query."""
    query_lower = query.lower()
    matches = []
    for node in graph['nodes']:
        if query_lower in node['label'].lower():
            matches.append(node)
    return matches


def get_relationships(graph, concept_id):
    """Get all relationships for a concept."""
    nodes_dict = {n['id']: n for n in graph['nodes']}
    outgoing = []
    incoming = []

    for edge in graph['edges']:
        if edge['source'] == concept_id:
            target = nodes_dict[edge['target']]
            outgoing.append({
                'target': target['label'],
                'type': edge['relationship_type'],
                'confidence': edge['confidence']
            })
        elif edge['target'] == concept_id:
            source = nodes_dict[edge['source']]
            incoming.append({
                'source': source['label'],
                'type': edge['relationship_type'],
                'confidence': edge['confidence']
            })

    return outgoing, incoming


def print_concept_info(concept, outgoing, incoming):
    """Print detailed information about a concept."""
    print("\n" + "=" * 70)
    print(f"CONCEPT: {concept['label']}")
    print("=" * 70)
    print(f"Type: {concept['type']}")
    print(f"Source: {concept['source_file']}")
    print(f"Extraction: {concept['extraction_method']}")

    if concept['definition']:
        print(f"\nDefinition:")
        print(f"  {concept['definition'][:200]}...")

    print(f"\nConnections: {len(outgoing) + len(incoming)}")

    if outgoing:
        print(f"\n📤 Outgoing Relationships ({len(outgoing)}):")
        for rel in outgoing[:10]:
            print(f"  → {rel['target']}")
            print(f"    Type: {rel['type']} | Confidence: {rel['confidence']:.2f}")
        if len(outgoing) > 10:
            print(f"  ... and {len(outgoing) - 10} more")

    if incoming:
        print(f"\n📥 Incoming Relationships ({len(incoming)}):")
        for rel in incoming[:10]:
            print(f"  ← {rel['source']}")
            print(f"    Type: {rel['type']} | Confidence: {rel['confidence']:.2f}")
        if len(incoming) > 10:
            print(f"  ... and {len(incoming) - 10} more")

    print("=" * 70)


def show_statistics(graph):
    """Show graph statistics."""
    stats = graph['statistics']

    print("\n" + "=" * 70)
    print("KNOWLEDGE GRAPH STATISTICS")
    print("=" * 70)
    print(f"Total Concepts: {stats['total_concepts']}")
    print(f"Total Relationships: {stats['total_relationships']}")
    print(f"Avg Connections per Concept: {stats['avg_relationships_per_concept']:.2f}")

    print("\nConcepts by Type:")
    for ctype, count in sorted(stats['concepts_by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {ctype}: {count}")

    print("\nRelationships by Type:")
    for rtype, count in sorted(stats['relationships_by_type'].items(), key=lambda x: x[1], reverse=True):
        print(f"  - {rtype}: {count}")

    print("\nMost Connected Concepts:")
    for label, count in stats['most_connected_concepts'][:10]:
        print(f"  - {label}: {count} connections")

    print("=" * 70)


def list_primary_topics(graph):
    """List all primary topics."""
    primary = [n for n in graph['nodes'] if n['type'] == 'primary_topic']
    primary.sort(key=lambda x: x['label'])

    print("\n" + "=" * 70)
    print("PRIMARY TOPICS")
    print("=" * 70)
    for topic in primary:
        print(f"  • {topic['label']}")
        print(f"    File: {topic['source_file']}")
    print("=" * 70)


def main():
    """Main interactive loop."""
    print("\n" + "=" * 70)
    print("KNOWLEDGE GRAPH EXPLORER")
    print("=" * 70)
    print("\nLoading graph...")

    graph = load_graph()
    print(f"✓ Loaded {len(graph['nodes'])} concepts and {len(graph['edges'])} relationships")

    while True:
        print("\n" + "-" * 70)
        print("Commands:")
        print("  search <term>  - Search for concepts")
        print("  topics         - List primary topics")
        print("  stats          - Show statistics")
        print("  quit           - Exit")
        print("-" * 70)

        command = input("\nEnter command: ").strip().lower()

        if command == 'quit' or command == 'exit' or command == 'q':
            print("\nGoodbye!")
            break

        elif command == 'topics':
            list_primary_topics(graph)

        elif command == 'stats':
            show_statistics(graph)

        elif command.startswith('search '):
            query = command[7:].strip()
            if not query:
                print("Please provide a search term.")
                continue

            matches = find_concept(graph, query)

            if not matches:
                print(f"No concepts found matching '{query}'")
            elif len(matches) == 1:
                concept = matches[0]
                outgoing, incoming = get_relationships(graph, concept['id'])
                print_concept_info(concept, outgoing, incoming)
            else:
                print(f"\nFound {len(matches)} matches:")
                for i, match in enumerate(matches[:20], 1):
                    print(f"  {i}. {match['label']} ({match['type']})")
                if len(matches) > 20:
                    print(f"  ... and {len(matches) - 20} more")

                print("\nRefine your search or select a number to view details.")
                choice = input("Enter number (or press Enter to skip): ").strip()

                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(matches):
                        concept = matches[idx]
                        outgoing, incoming = get_relationships(graph, concept['id'])
                        print_concept_info(concept, outgoing, incoming)

        else:
            print("Unknown command. Try 'search <term>', 'topics', 'stats', or 'quit'")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
