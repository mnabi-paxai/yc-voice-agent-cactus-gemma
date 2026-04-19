# Knowledge Graph Analysis - README

## Overview

This directory contains a comprehensive knowledge graph extraction and analysis for the RL/post-training wiki documentation. The pipeline uses a hybrid approach combining structural parsing and pattern-based extraction to identify concepts and relationships.

## Extraction Date

**Generated:** 2026-04-19

## Pipeline Phases

### Phase 1: Structural Parsing
- Parsed 8 markdown files (excluding index.md)
- Extracted: headers, markdown links, bold/italic terms, code blocks, formulas
- Built initial concept list from document structure

### Phase 2: Concept Extraction
- **Structural concepts:** Extracted from titles, headers, emphasized terms, links
- **Content concepts:** Pattern matching for domain-specific technical terms
- **Deduplication:** Merged similar concepts with normalized labels
- **Final count:** 432 unique concepts

### Phase 3: Relationship Extraction
- **Explicit links:** Markdown cross-references between files (31 relationships)
- **Pattern matching:** Linguistic patterns indicating relationships (hierarchical, procedural, comparative, causal, temporal)
- **Contextual:** Co-occurrence and document structure relationships (525 relationships)
- **Header hierarchy:** Parent-child relationships from document structure (216 relationships)
- **Total:** 772 relationships

### Phase 4: Graph Analysis
- Computed graph statistics (centrality, clustering, distributions)
- Identified 171 connected components (1 major cluster of 262 concepts)
- Generated 20 suggestions for missing relationships
- Created relationship matrix for primary topics

## Output Files

### 1. knowledge-graph.json (313 KB)
**Complete knowledge graph structure**

Contains:
- Metadata (source directory, extraction method, date)
- Nodes: All 432 concepts with full metadata
  - `id`: Unique identifier
  - `label`: Human-readable concept name
  - `type`: Concept classification (primary_topic, section_concept, domain_term, etc.)
  - `source_file`: Origin wiki file
  - `extraction_method`: How it was extracted
  - `definition`: Context or definition text
- Edges: All 772 relationships
  - `source` and `target`: Concept IDs
  - `relationship_type`: Type of relationship
  - `confidence`: Extraction confidence (0.0-1.0)
  - `evidence_text`: Supporting text snippet
  - `extraction_method`: How it was extracted
- Statistics: Graph-level metrics

### 2. concepts-list.json (94 KB)
**Structured list of all concepts**

Array of 432 concept objects with full metadata. Useful for:
- Searching for specific concepts
- Filtering by type or source file
- Building custom visualizations

### 3. relationships-list.json (197 KB)
**Structured list of all relationships**

Array of 772 relationship objects. Useful for:
- Analyzing relationship patterns
- Filtering by relationship type
- Understanding confidence distributions

### 4. graph-analysis.md (6.2 KB)
**Human-readable analysis report**

Includes:
- Executive summary with key statistics
- Concept and relationship type distributions
- Source file contribution analysis
- Most connected concepts (top 10)
- Cluster analysis (top 5 clusters)
- Example relationships by type
- Suggested new connections
- Key insights and findings
- Recommendations for further analysis

### 5. graph-visualization.html (186 KB)
**Interactive graph visualization**

Features:
- Interactive network visualization using vis.js
- Node colors by concept type:
  - Red: Primary topics (main wiki pages)
  - Blue: Section concepts (headers)
  - Green: Domain terms (technical vocabulary)
  - Orange: Emphasized terms (bold text)
  - Purple: Linked concepts (cross-references)
- Edge arrows showing relationship direction
- Hover tooltips with details
- Controls:
  - Fit view: Auto-zoom to show full graph
  - Stabilize: Re-run physics simulation
  - Toggle physics: Enable/disable force-directed layout
  - Show/hide labels: Toggle node labels
- Click nodes/edges for selection
- Drag to pan, scroll to zoom

### 6. relationship-matrix.md (Generated)
**Matrix of relationships between primary topics**

Shows:
- 8x8 matrix of connections between main wiki pages
- Topic legend with abbreviations
- Detailed relationship breakdown by type
- Most connected topic pairs
- Graph density metric

## Key Statistics

- **Total Concepts:** 432
- **Total Relationships:** 772
- **Average Connections per Concept:** 3.57
- **Number of Clusters:** 171 (1 major cluster)
- **Graph Density:** 11.625 (actual edges / maximum possible)

## Concept Type Distribution

| Type | Count | Description |
|------|-------|-------------|
| Emphasized Term | 211 | Bold text indicating important concepts |
| Section Concept | 168 | Extracted from document headers |
| Domain Term | 34 | Technical vocabulary (pattern-matched) |
| Linked Concept | 11 | Cross-referenced in markdown links |
| Primary Topic | 8 | Main wiki page topics |

## Relationship Type Distribution

| Type | Count | Percentage | Description |
|------|-------|------------|-------------|
| discusses | 525 | 68.0% | Topic mentions/discusses another concept |
| part-of | 216 | 28.0% | Hierarchical structure from headers |
| related-to | 31 | 4.0% | Explicit cross-references between files |

## Most Connected Concepts

These concepts are central to the knowledge graph:

1. **Group Relative Policy Optimization (GRPO)** - 100 connections
2. **Reward Modeling** - 94 connections
3. **KL Divergence Regularization** - 90 connections
4. **Formal Theorem Proving** - 90 connections
5. **Proximal Policy Optimization (PPO)** - 89 connections
6. **Mathematical Reasoning with Language Models** - 79 connections
7. **Direct Preference Optimization (DPO)** - 71 connections
8. **Reinforcement Learning from Human Feedback (RLHF)** - 70 connections

## Most Connected Topic Pairs

1. **Reward Modeling ↔ Direct Preference Optimization (DPO)** - 34 connections
2. **Reward Modeling ↔ Reinforcement Learning from Human Feedback (RLHF)** - 30 connections
3. **Reward Modeling ↔ Group Relative Policy Optimization (GRPO)** - 29 connections
4. **Reward Modeling ↔ Proximal Policy Optimization (PPO)** - 28 connections
5. **Reward Modeling ↔ KL Divergence Regularization** - 27 connections
6. **Formal Theorem Proving ↔ Mathematical Reasoning with Language Models** - 26 connections

## Key Insights

### 1. Central Role of Reward Modeling
Reward Modeling is the most connected primary topic, serving as a hub that connects to all major optimization methods (PPO, DPO, GRPO) and the broader RLHF framework.

### 2. Two Main Application Domains
The graph reveals two major application clusters:
- **Natural Language Mathematical Reasoning:** DeepSeekMath-style approaches
- **Formal Theorem Proving:** Goedel-Prover-style approaches

These are strongly connected, showing they share many underlying techniques.

### 3. KL Divergence as Universal Regularizer
KL Divergence Regularization appears as a critical shared component across all optimization methods, highlighting its essential role in stable RL training.

### 4. Method Evolution and Alternatives
The graph captures relationships between traditional RLHF (with explicit reward models) and newer alternatives (DPO, GRPO), documenting both similarities and key differences.

### 5. Hierarchical Structure
The 216 "part-of" relationships capture the hierarchical organization of concepts within each wiki page, showing how complex methods decompose into components.

## Usage Examples

### Query Concepts by Type
```python
import json

with open('concepts-list.json', 'r') as f:
    concepts = json.load(f)

# Get all primary topics
primary_topics = [c for c in concepts if c['type'] == 'primary_topic']
for topic in primary_topics:
    print(f"- {topic['label']}")
```

### Find Relationships for a Concept
```python
import json

with open('knowledge-graph.json', 'r') as f:
    graph = json.load(f)

# Find concept by label
target_concept = None
for node in graph['nodes']:
    if node['label'] == 'Direct Preference Optimization (DPO)':
        target_concept = node['id']
        break

# Find all relationships
if target_concept:
    relationships = [
        edge for edge in graph['edges']
        if edge['source'] == target_concept or edge['target'] == target_concept
    ]
    print(f"Found {len(relationships)} relationships")
```

### Analyze Relationship Types
```python
from collections import Counter

with open('relationships-list.json', 'r') as f:
    relationships = json.load(f)

rel_types = Counter(r['relationship_type'] for r in relationships)
for rel_type, count in rel_types.most_common():
    print(f"{rel_type}: {count}")
```

## Extraction Scripts

### extract_knowledge_graph.py (43 KB)
Main extraction pipeline script. Run with:
```bash
python3 extract_knowledge_graph.py
```

Features:
- `MarkdownParser`: Parse structural elements from markdown
- `ConceptExtractor`: Extract and deduplicate concepts
- `RelationshipExtractor`: Extract relationships using multiple strategies
- `GraphAnalyzer`: Compute statistics and generate insights

### generate_relationship_matrix.py
Generate relationship matrix for primary topics. Run with:
```bash
python3 generate_relationship_matrix.py
```

## Limitations and Future Work

### Current Limitations
1. **Pattern-based extraction:** May miss implicit relationships not matching patterns
2. **No temporal information:** Doesn't capture when concepts were introduced or evolved
3. **Limited semantic understanding:** No deep NLP or LLM-based semantic analysis
4. **Confidence scores:** Based on extraction method, not validated accuracy

### Potential Enhancements
1. **LLM-based extraction:** Use language models to extract implicit relationships and definitions
2. **Citation network:** Integrate paper citations to understand influence
3. **Temporal analysis:** Track concept evolution over time
4. **Performance linking:** Connect methods to benchmark results
5. **Cross-document coherence:** Resolve terminology variations across files
6. **Entity disambiguation:** Better handling of acronyms and alternative names
7. **Relationship validation:** Human review or LLM validation of extracted relationships

### Suggested Next Steps
1. **Manual review:** Validate extracted relationships, especially lower-confidence ones
2. **Expand corpus:** Include more wiki pages or research papers
3. **Deep dive analysis:** Focus on specific clusters (e.g., optimization algorithms)
4. **Integration:** Link to external knowledge bases (papers, implementations)
5. **Dynamic updates:** Track changes as wiki evolves

## Contact and Contributions

This knowledge graph was generated as part of the Twin Mind project's documentation analysis. The extraction pipeline is designed to be reusable for other markdown documentation sets.

To re-run the extraction:
```bash
cd /path/to/wikis/analysis
python3 extract_knowledge_graph.py
python3 generate_relationship_matrix.py
```

## License

This analysis and extraction code inherits the license of the parent Twin Mind project.

---

**Generated by:** Hybrid Knowledge Graph Extraction Pipeline  
**Date:** 2026-04-19  
**Version:** 1.0
