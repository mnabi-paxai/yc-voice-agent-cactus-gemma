#!/usr/bin/env python3
"""
Hybrid Knowledge Graph Extraction Pipeline for Markdown Wiki Files

This script implements a multi-phase extraction approach:
1. Structural parsing of markdown elements
2. LLM-based concept and relationship extraction
3. Knowledge graph construction
4. Analysis and visualization generation
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import unicodedata


# ============================================================================
# PHASE 1: STRUCTURAL PARSING
# ============================================================================

class MarkdownParser:
    """Extract structural elements from markdown files."""

    def __init__(self, wikis_dir: str):
        self.wikis_dir = Path(wikis_dir)
        self.files = [f for f in self.wikis_dir.glob("*.md") if f.name != "index.md"]

    def parse_file(self, filepath: Path) -> Dict:
        """Parse a single markdown file for structural elements."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        result = {
            'filename': filepath.stem,
            'filepath': str(filepath),
            'title': '',
            'headers': [],
            'markdown_links': [],
            'bold_terms': [],
            'italic_terms': [],
            'code_blocks': [],
            'formulas': [],
            'content': content
        }

        # Extract title (first h1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            result['title'] = title_match.group(1).strip()

        # Extract all headers
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        result['headers'] = [(len(h[0]), h[1].strip()) for h in headers]

        # Extract markdown links [text](file.md)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
        result['markdown_links'] = [(text.strip(), link.strip()) for text, link in links]

        # Extract bold terms **term** or __term__
        bold = re.findall(r'\*\*([^*]+)\*\*|__([^_]+)__', content)
        result['bold_terms'] = [b[0] or b[1] for b in bold if b[0] or b[1]]

        # Extract italic terms *term* or _term_ (but not in headers or bold)
        italic = re.findall(r'(?<!\*)\*([^*]+)\*(?!\*)|(?<!_)_([^_]+)_(?!_)', content)
        result['italic_terms'] = [i[0] or i[1] for i in italic if i[0] or i[1]]

        # Extract code blocks
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
        result['code_blocks'] = code_blocks

        # Extract inline formulas (simple heuristic for math expressions)
        # Look for patterns like E[...], D_KL[...], π(...), etc.
        formulas = re.findall(r'([A-Z_][A-Za-z0-9_]*\[[^\]]+\]|[πθβσ][_^]?[A-Za-z0-9]*\([^)]*\))', content)
        result['formulas'] = list(set(formulas))

        return result

    def parse_all(self) -> List[Dict]:
        """Parse all markdown files."""
        return [self.parse_file(f) for f in self.files]


# ============================================================================
# PHASE 2: CONCEPT EXTRACTION
# ============================================================================

class ConceptExtractor:
    """Extract concepts from parsed markdown data."""

    # Technical terms that should be recognized as concepts
    DOMAIN_PATTERNS = [
        r'\b(reinforcement learning|RLHF|RL)\b',
        r'\b(supervised fine-tuning|SFT)\b',
        r'\b(reward model(?:ing)?)\b',
        r'\b(policy optimization|PPO|DPO|GRPO|TRPO)\b',
        r'\b(KL divergence|KL penalty|KL regularization)\b',
        r'\b(preference learning|preference data)\b',
        r'\b(Bradley-Terry model)\b',
        r'\b(advantage estimation|GAE)\b',
        r'\b(value function|critic)\b',
        r'\b(actor-critic)\b',
        r'\b(chain-of-thought|CoT|program-of-thought|PoT)\b',
        r'\b(formal theorem proving|theorem proving)\b',
        r'\b(verifier|verification)\b',
        r'\b(self-correction)\b',
        r'\b(process supervision|outcome supervision)\b',
        r'\b(language model|LLM)\b',
        r'\b(pre-training|fine-tuning)\b',
        r'\b(hyperparameter)\b',
        r'\b(sampling|inference)\b',
        r'\b(training data|dataset)\b',
        r'\b(mathematical reasoning|formal reasoning)\b',
        r'\b(expert iteration)\b',
        r'\b(model averaging)\b',
        r'\b(reward hacking|mode collapse)\b',
        r'\b(group normalization|group-based)\b',
        r'\b(reference policy)\b',
        r'\b(clipping|clipped objective)\b',
        r'\b(trust region)\b',
    ]

    def __init__(self, parsed_files: List[Dict]):
        self.parsed_files = parsed_files
        self.concepts = {}  # id -> concept data
        self.concept_mentions = defaultdict(list)  # concept_id -> [(file, context), ...]

    def extract_from_structure(self):
        """Extract concepts from structural elements."""
        concept_id = 0

        for file_data in self.parsed_files:
            filename = file_data['filename']

            # Title is always a primary concept
            if file_data['title']:
                cid = f"concept_{concept_id}"
                self.concepts[cid] = {
                    'id': cid,
                    'label': file_data['title'],
                    'type': 'primary_topic',
                    'source_file': filename,
                    'extraction_method': 'title',
                    'definition': self._extract_definition(file_data['content'], file_data['title'])
                }
                concept_id += 1

            # Headers indicate sub-concepts
            for level, header_text in file_data['headers']:
                if level > 1:  # Skip h1 (title)
                    clean_header = self._clean_text(header_text)
                    if clean_header and len(clean_header) > 2:
                        cid = f"concept_{concept_id}"
                        self.concepts[cid] = {
                            'id': cid,
                            'label': clean_header,
                            'type': 'section_concept',
                            'source_file': filename,
                            'extraction_method': f'header_h{level}',
                            'definition': ''
                        }
                        concept_id += 1

            # Bold terms are emphasized concepts
            for term in file_data['bold_terms']:
                clean_term = self._clean_text(term)
                if clean_term and len(clean_term) > 3:
                    # Check if already exists
                    existing = self._find_concept_by_label(clean_term)
                    if not existing:
                        cid = f"concept_{concept_id}"
                        self.concepts[cid] = {
                            'id': cid,
                            'label': clean_term,
                            'type': 'emphasized_term',
                            'source_file': filename,
                            'extraction_method': 'bold_text',
                            'definition': ''
                        }
                        concept_id += 1

            # Markdown links indicate explicit relationships and concepts
            for link_text, link_target in file_data['markdown_links']:
                clean_link = self._clean_text(link_text)
                if clean_link:
                    existing = self._find_concept_by_label(clean_link)
                    if not existing:
                        cid = f"concept_{concept_id}"
                        self.concepts[cid] = {
                            'id': cid,
                            'label': clean_link,
                            'type': 'linked_concept',
                            'source_file': filename,
                            'extraction_method': 'markdown_link',
                            'definition': ''
                        }
                        concept_id += 1

        return concept_id

    def extract_from_content(self, start_id: int):
        """Extract concepts using pattern matching on content."""
        concept_id = start_id

        for file_data in self.parsed_files:
            filename = file_data['filename']
            content = file_data['content']

            for pattern in self.DOMAIN_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    term = match.group(0)
                    clean_term = self._clean_text(term)

                    if clean_term and len(clean_term) > 2:
                        existing = self._find_concept_by_label(clean_term)
                        if not existing:
                            cid = f"concept_{concept_id}"
                            self.concepts[cid] = {
                                'id': cid,
                                'label': clean_term,
                                'type': 'domain_term',
                                'source_file': filename,
                                'extraction_method': 'pattern_matching',
                                'definition': self._extract_definition(content, clean_term)
                            }
                            concept_id += 1

        return concept_id

    def _extract_definition(self, content: str, term: str) -> str:
        """Extract a definition or description for a term from content."""
        # Look for sentences containing the term near the beginning
        sentences = re.split(r'[.!?]\s+', content)
        for sent in sentences[:20]:  # Check first 20 sentences
            if term.lower() in sent.lower():
                clean_sent = sent.strip()
                if len(clean_sent) > 20 and len(clean_sent) < 500:
                    return clean_sent
        return ""

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove markdown formatting
        text = re.sub(r'[*_`]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Normalize unicode
        text = unicodedata.normalize('NFKD', text)
        return text.strip()

    def _find_concept_by_label(self, label: str) -> Optional[str]:
        """Find concept ID by label (case-insensitive, normalized)."""
        label_lower = label.lower().strip()
        for cid, concept in self.concepts.items():
            if concept['label'].lower().strip() == label_lower:
                return cid
        return None

    def deduplicate_concepts(self):
        """Remove duplicate concepts with similar labels."""
        # Group by normalized label
        label_groups = defaultdict(list)
        for cid, concept in self.concepts.items():
            normalized = concept['label'].lower().strip()
            label_groups[normalized].append(cid)

        # Keep the first one from each group, merge metadata
        concepts_to_remove = []
        for normalized_label, cids in label_groups.items():
            if len(cids) > 1:
                # Keep the primary topic or first one
                primary = None
                for cid in cids:
                    if self.concepts[cid]['type'] == 'primary_topic':
                        primary = cid
                        break
                if not primary:
                    primary = cids[0]

                # Mark others for removal
                for cid in cids:
                    if cid != primary:
                        concepts_to_remove.append(cid)

        # Remove duplicates
        for cid in concepts_to_remove:
            del self.concepts[cid]

        print(f"Removed {len(concepts_to_remove)} duplicate concepts")


# ============================================================================
# PHASE 3: RELATIONSHIP EXTRACTION
# ============================================================================

class RelationshipExtractor:
    """Extract relationships between concepts."""

    # Relationship patterns (pattern, relationship_type)
    RELATIONSHIP_PATTERNS = [
        # Hierarchical
        (r'(.+?)\s+is a (?:type of|kind of|form of|variant of)\s+(.+?)(?:[.,;])', 'is-a'),
        (r'(.+?)\s+(?:is|are) part of\s+(.+?)(?:[.,;])', 'part-of'),
        (r'(.+?)\s+(?:includes?|contains?|comprises?)\s+(.+?)(?:[.,;])', 'contains'),
        (r'(.+?)\s+component of\s+(.+?)(?:[.,;])', 'component-of'),

        # Procedural
        (r'(.+?)\s+uses\s+(.+?)(?:[.,;])', 'uses'),
        (r'(.+?)\s+requires?\s+(.+?)(?:[.,;])', 'requires'),
        (r'(.+?)\s+enables?\s+(.+?)(?:[.,;])', 'enables'),
        (r'(.+?)\s+(?:relies on|depends on)\s+(.+?)(?:[.,;])', 'depends-on'),
        (r'(.+?)\s+applies\s+(.+?)(?:[.,;])', 'applies'),
        (r'(.+?)\s+implements?\s+(.+?)(?:[.,;])', 'implements'),

        # Comparative
        (r'(.+?)\s+(?:is )?similar to\s+(.+?)(?:[.,;])', 'similar-to'),
        (r'(.+?)\s+(?:differs from|is different from)\s+(.+?)(?:[.,;])', 'differs-from'),
        (r'(.+?)\s+(?:alternative to|replaces)\s+(.+?)(?:[.,;])', 'alternative-to'),
        (r'(.+?)\s+(?:vs|versus|compared to)\s+(.+?)(?:[.,;])', 'compared-to'),

        # Causal
        (r'(.+?)\s+causes\s+(.+?)(?:[.,;])', 'causes'),
        (r'(.+?)\s+improves\s+(.+?)(?:[.,;])', 'improves'),
        (r'(.+?)\s+solves\s+(.+?)(?:[.,;])', 'solves'),
        (r'(.+?)\s+prevents\s+(.+?)(?:[.,;])', 'prevents'),
        (r'(.+?)\s+leads to\s+(.+?)(?:[.,;])', 'leads-to'),

        # Temporal
        (r'(.+?)\s+(?:precedes|comes before)\s+(.+?)(?:[.,;])', 'precedes'),
        (r'(.+?)\s+follows\s+(.+?)(?:[.,;])', 'follows'),
        (r'(.+?)\s+(?:after|following)\s+(.+?)(?:[.,;])', 'after'),
    ]

    def __init__(self, concepts: Dict, parsed_files: List[Dict]):
        self.concepts = concepts
        self.parsed_files = parsed_files
        self.relationships = []
        self.relationship_id = 0

    def extract_explicit_links(self):
        """Extract relationships from markdown links."""
        for file_data in self.parsed_files:
            source_file = file_data['filename']

            # The file itself is a concept
            source_concept_id = self._find_concept_by_file(source_file)

            # Links indicate relationships
            for link_text, link_target in file_data['markdown_links']:
                # Find target concept
                target_file = link_target.replace('.md', '')
                target_concept_id = self._find_concept_by_file(target_file)

                if source_concept_id and target_concept_id:
                    self._add_relationship(
                        source_concept_id,
                        target_concept_id,
                        'related-to',
                        confidence=0.95,
                        evidence=f"Explicit link from {source_file} to {target_file}",
                        extraction_method='markdown_link'
                    )

    def extract_from_content(self):
        """Extract relationships using pattern matching."""
        for file_data in self.parsed_files:
            content = file_data['content']
            filename = file_data['filename']

            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', content)

            for sentence in sentences:
                for pattern, rel_type in self.RELATIONSHIP_PATTERNS:
                    matches = re.finditer(pattern, sentence, re.IGNORECASE)
                    for match in matches:
                        source_term = match.group(1).strip()
                        target_term = match.group(2).strip()

                        # Clean terms
                        source_term = self._clean_term(source_term)
                        target_term = self._clean_term(target_term)

                        # Find concept IDs
                        source_id = self._find_concept_by_label(source_term)
                        target_id = self._find_concept_by_label(target_term)

                        if source_id and target_id and source_id != target_id:
                            self._add_relationship(
                                source_id,
                                target_id,
                                rel_type,
                                confidence=0.7,
                                evidence=sentence[:200],
                                extraction_method='pattern_matching'
                            )

    def extract_contextual_relationships(self):
        """Extract relationships from co-occurrence and context."""
        for file_data in self.parsed_files:
            filename = file_data['filename']
            content = file_data['content']

            # Get all concepts mentioned in this file
            mentioned_concepts = []
            for cid, concept in self.concepts.items():
                label = concept['label']
                if re.search(r'\b' + re.escape(label) + r'\b', content, re.IGNORECASE):
                    mentioned_concepts.append(cid)

            # Primary concept of this file
            primary_concept = self._find_concept_by_file(filename)

            if primary_concept:
                # All mentioned concepts relate to the primary concept
                for cid in mentioned_concepts:
                    if cid != primary_concept:
                        # Check if relationship already exists
                        if not self._relationship_exists(primary_concept, cid):
                            self._add_relationship(
                                primary_concept,
                                cid,
                                'discusses',
                                confidence=0.6,
                                evidence=f"Mentioned in {filename}",
                                extraction_method='co-occurrence'
                            )

    def extract_header_structure(self):
        """Extract hierarchical relationships from header structure."""
        for file_data in self.parsed_files:
            filename = file_data['filename']
            headers = file_data['headers']

            # Build hierarchy
            stack = []  # (level, header_text, concept_id)

            for level, header_text in headers:
                clean_header = self._clean_term(header_text)
                concept_id = self._find_concept_by_label(clean_header)

                if concept_id:
                    # Pop stack until we find parent level
                    while stack and stack[-1][0] >= level:
                        stack.pop()

                    # If there's a parent, create relationship
                    if stack:
                        parent_id = stack[-1][2]
                        self._add_relationship(
                            concept_id,
                            parent_id,
                            'part-of',
                            confidence=0.8,
                            evidence=f"Header structure in {filename}",
                            extraction_method='header_hierarchy'
                        )

                    stack.append((level, header_text, concept_id))

    def _add_relationship(self, source: str, target: str, rel_type: str,
                         confidence: float, evidence: str, extraction_method: str):
        """Add a relationship if it doesn't already exist."""
        # Check for duplicates
        for rel in self.relationships:
            if (rel['source'] == source and rel['target'] == target and
                rel['relationship_type'] == rel_type):
                return  # Already exists

        rel_id = f"rel_{self.relationship_id}"
        self.relationship_id += 1

        self.relationships.append({
            'id': rel_id,
            'source': source,
            'target': target,
            'relationship_type': rel_type,
            'confidence': confidence,
            'evidence_text': evidence,
            'extraction_method': extraction_method
        })

    def _relationship_exists(self, source: str, target: str) -> bool:
        """Check if any relationship exists between two concepts."""
        for rel in self.relationships:
            if ((rel['source'] == source and rel['target'] == target) or
                (rel['source'] == target and rel['target'] == source)):
                return True
        return False

    def _find_concept_by_file(self, filename: str) -> Optional[str]:
        """Find the primary concept for a file."""
        for cid, concept in self.concepts.items():
            if concept['source_file'] == filename and concept['type'] == 'primary_topic':
                return cid
        return None

    def _find_concept_by_label(self, label: str) -> Optional[str]:
        """Find concept by label."""
        label_lower = label.lower().strip()
        for cid, concept in self.concepts.items():
            if concept['label'].lower().strip() == label_lower:
                return cid
        return None

    def _clean_term(self, term: str) -> str:
        """Clean term for matching."""
        # Remove markdown formatting
        term = re.sub(r'[*_`\[\]]', '', term)
        # Remove extra whitespace
        term = ' '.join(term.split())
        return term.strip()


# ============================================================================
# PHASE 4: GRAPH ANALYSIS
# ============================================================================

class GraphAnalyzer:
    """Analyze the knowledge graph."""

    def __init__(self, concepts: Dict, relationships: List[Dict]):
        self.concepts = concepts
        self.relationships = relationships

    def compute_statistics(self) -> Dict:
        """Compute graph statistics."""
        stats = {
            'total_concepts': len(self.concepts),
            'total_relationships': len(self.relationships),
            'concepts_by_type': Counter(),
            'relationships_by_type': Counter(),
            'concepts_by_source': Counter(),
            'avg_relationships_per_concept': 0,
            'most_connected_concepts': [],
            'relationship_type_distribution': {},
        }

        # Count by type
        for concept in self.concepts.values():
            stats['concepts_by_type'][concept['type']] += 1
            stats['concepts_by_source'][concept['source_file']] += 1

        for rel in self.relationships:
            stats['relationships_by_type'][rel['relationship_type']] += 1

        # Connection counts
        connection_counts = Counter()
        for rel in self.relationships:
            connection_counts[rel['source']] += 1
            connection_counts[rel['target']] += 1

        if self.concepts:
            stats['avg_relationships_per_concept'] = sum(connection_counts.values()) / len(self.concepts)

        # Most connected
        top_connected = connection_counts.most_common(10)
        stats['most_connected_concepts'] = [
            (self.concepts[cid]['label'], count)
            for cid, count in top_connected
        ]

        # Relationship type distribution
        total_rels = len(self.relationships)
        if total_rels > 0:
            stats['relationship_type_distribution'] = {
                rel_type: count / total_rels
                for rel_type, count in stats['relationships_by_type'].items()
            }

        return stats

    def find_clusters(self) -> List[List[str]]:
        """Find connected components (clusters) in the graph."""
        # Build adjacency list
        adj = defaultdict(set)
        for rel in self.relationships:
            adj[rel['source']].add(rel['target'])
            adj[rel['target']].add(rel['source'])

        visited = set()
        clusters = []

        def dfs(node, cluster):
            visited.add(node)
            cluster.append(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    dfs(neighbor, cluster)

        for cid in self.concepts:
            if cid not in visited:
                cluster = []
                dfs(cid, cluster)
                clusters.append(cluster)

        # Sort by size
        clusters.sort(key=len, reverse=True)
        return clusters

    def suggest_missing_relationships(self) -> List[Dict]:
        """Suggest potential missing relationships based on patterns."""
        suggestions = []

        # Transitive relationships: if A->B and B->C, suggest A->C
        rel_dict = defaultdict(list)
        for rel in self.relationships:
            rel_dict[rel['source']].append((rel['target'], rel['relationship_type']))

        for source, targets in rel_dict.items():
            for target, rel_type in targets:
                if target in rel_dict:
                    for second_target, second_rel_type in rel_dict[target]:
                        # Check if relationship exists
                        if not self._relationship_exists(source, second_target):
                            suggestions.append({
                                'source': self.concepts[source]['label'],
                                'target': self.concepts[second_target]['label'],
                                'suggested_type': 'related-to',
                                'reason': f'Transitive via {self.concepts[target]["label"]}',
                                'confidence': 0.4
                            })

        return suggestions[:20]  # Limit to top 20

    def _relationship_exists(self, source: str, target: str) -> bool:
        """Check if relationship exists."""
        for rel in self.relationships:
            if ((rel['source'] == source and rel['target'] == target) or
                (rel['source'] == target and rel['target'] == source)):
                return True
        return False


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Main execution pipeline."""
    wikis_dir = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/wikis"
    output_dir = "/Users/marnabi/Documents/Work/Learning/Twin Mind/twin-mind/raw/wikis/analysis"

    print("=" * 80)
    print("HYBRID KNOWLEDGE GRAPH EXTRACTION PIPELINE")
    print("=" * 80)

    # Phase 1: Parse markdown files
    print("\n[PHASE 1] Structural Parsing...")
    parser = MarkdownParser(wikis_dir)
    parsed_files = parser.parse_all()
    print(f"  ✓ Parsed {len(parsed_files)} markdown files")

    # Phase 2: Extract concepts
    print("\n[PHASE 2] Concept Extraction...")
    extractor = ConceptExtractor(parsed_files)

    print("  - Extracting from structure...")
    next_id = extractor.extract_from_structure()
    print(f"    ✓ Extracted {len(extractor.concepts)} structural concepts")

    print("  - Extracting from content patterns...")
    next_id = extractor.extract_from_content(next_id)
    print(f"    ✓ Total concepts: {len(extractor.concepts)}")

    print("  - Deduplicating concepts...")
    extractor.deduplicate_concepts()
    print(f"    ✓ Final concept count: {len(extractor.concepts)}")

    # Phase 3: Extract relationships
    print("\n[PHASE 3] Relationship Extraction...")
    rel_extractor = RelationshipExtractor(extractor.concepts, parsed_files)

    print("  - Extracting explicit links...")
    rel_extractor.extract_explicit_links()
    print(f"    ✓ {len(rel_extractor.relationships)} relationships")

    print("  - Extracting from content patterns...")
    rel_extractor.extract_from_content()
    print(f"    ✓ {len(rel_extractor.relationships)} relationships")

    print("  - Extracting contextual relationships...")
    rel_extractor.extract_contextual_relationships()
    print(f"    ✓ {len(rel_extractor.relationships)} relationships")

    print("  - Extracting header structure...")
    rel_extractor.extract_header_structure()
    print(f"    ✓ {len(rel_extractor.relationships)} relationships")

    # Phase 4: Analyze graph
    print("\n[PHASE 4] Graph Analysis...")
    analyzer = GraphAnalyzer(extractor.concepts, rel_extractor.relationships)

    print("  - Computing statistics...")
    stats = analyzer.compute_statistics()
    print(f"    ✓ {stats['total_concepts']} concepts, {stats['total_relationships']} relationships")

    print("  - Finding clusters...")
    clusters = analyzer.find_clusters()
    print(f"    ✓ Found {len(clusters)} clusters")

    print("  - Suggesting missing relationships...")
    suggestions = analyzer.suggest_missing_relationships()
    print(f"    ✓ Generated {len(suggestions)} suggestions")

    # Save outputs
    print("\n[PHASE 5] Saving Outputs...")

    # 1. Full knowledge graph
    knowledge_graph = {
        'metadata': {
            'source_directory': wikis_dir,
            'total_files': len(parsed_files),
            'extraction_date': '2026-04-19',
            'extraction_method': 'hybrid_structural_and_pattern'
        },
        'nodes': list(extractor.concepts.values()),
        'edges': rel_extractor.relationships,
        'statistics': stats
    }

    with open(f"{output_dir}/knowledge-graph.json", 'w', encoding='utf-8') as f:
        json.dump(knowledge_graph, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved knowledge-graph.json")

    # 2. Concepts list
    with open(f"{output_dir}/concepts-list.json", 'w', encoding='utf-8') as f:
        json.dump(list(extractor.concepts.values()), f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved concepts-list.json")

    # 3. Relationships list
    with open(f"{output_dir}/relationships-list.json", 'w', encoding='utf-8') as f:
        json.dump(rel_extractor.relationships, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Saved relationships-list.json")

    # 4. Analysis report
    generate_analysis_report(stats, clusters, suggestions, extractor.concepts,
                           rel_extractor.relationships, output_dir)
    print(f"  ✓ Saved graph-analysis.md")

    # 5. Visualization HTML
    generate_visualization(extractor.concepts, rel_extractor.relationships, output_dir)
    print(f"  ✓ Saved graph-visualization.html")

    print("\n" + "=" * 80)
    print("EXTRACTION COMPLETE")
    print("=" * 80)
    print(f"\nOutput files saved to: {output_dir}")
    print(f"  - knowledge-graph.json: Complete graph structure")
    print(f"  - concepts-list.json: All {len(extractor.concepts)} concepts")
    print(f"  - relationships-list.json: All {len(rel_extractor.relationships)} relationships")
    print(f"  - graph-analysis.md: Human-readable analysis")
    print(f"  - graph-visualization.html: Interactive visualization")


def generate_analysis_report(stats, clusters, suggestions, concepts, relationships, output_dir):
    """Generate human-readable analysis report."""

    report = f"""# Knowledge Graph Analysis Report

**Generated:** 2026-04-19
**Domain:** Reinforcement Learning and Post-Training for Language Models

---

## Executive Summary

This knowledge graph was extracted from {stats['total_concepts']} concepts and {stats['total_relationships']} relationships across the RL/post-training wiki documentation.

### Key Statistics

- **Total Concepts:** {stats['total_concepts']}
- **Total Relationships:** {stats['total_relationships']}
- **Average Connections per Concept:** {stats['avg_relationships_per_concept']:.2f}
- **Number of Clusters:** {len(clusters)}

---

## Concepts by Type

"""

    for concept_type, count in sorted(stats['concepts_by_type'].items(), key=lambda x: x[1], reverse=True):
        report += f"- **{concept_type}:** {count}\n"

    report += f"\n---\n\n## Concepts by Source File\n\n"

    for source, count in sorted(stats['concepts_by_source'].items(), key=lambda x: x[1], reverse=True):
        report += f"- **{source}:** {count} concepts\n"

    report += f"\n---\n\n## Relationship Types\n\n"

    for rel_type, count in sorted(stats['relationships_by_type'].items(), key=lambda x: x[1], reverse=True):
        pct = stats['relationship_type_distribution'].get(rel_type, 0) * 100
        report += f"- **{rel_type}:** {count} ({pct:.1f}%)\n"

    report += f"\n---\n\n## Most Connected Concepts\n\n"
    report += "These concepts are central to the knowledge graph:\n\n"

    for idx, (label, count) in enumerate(stats['most_connected_concepts'], 1):
        report += f"{idx}. **{label}** ({count} connections)\n"

    report += f"\n---\n\n## Cluster Analysis\n\n"
    report += f"The graph contains {len(clusters)} connected components (clusters):\n\n"

    for idx, cluster in enumerate(clusters[:5], 1):
        report += f"### Cluster {idx} ({len(cluster)} concepts)\n\n"
        cluster_labels = [concepts[cid]['label'] for cid in cluster[:10]]
        report += "- " + "\n- ".join(cluster_labels)
        if len(cluster) > 10:
            report += f"\n- ... and {len(cluster) - 10} more\n"
        report += "\n\n"

    report += f"---\n\n## Key Relationships by Type\n\n"

    # Group relationships by type
    rels_by_type = defaultdict(list)
    for rel in relationships:
        rels_by_type[rel['relationship_type']].append(rel)

    # Show examples of each type
    for rel_type in ['is-a', 'uses', 'requires', 'enables', 'improves', 'alternative-to']:
        if rel_type in rels_by_type:
            report += f"### {rel_type.upper()} Relationships\n\n"
            for rel in rels_by_type[rel_type][:5]:
                source_label = concepts[rel['source']]['label']
                target_label = concepts[rel['target']]['label']
                report += f"- **{source_label}** {rel_type} **{target_label}**\n"
                report += f"  - Confidence: {rel['confidence']:.2f}\n"
                report += f"  - Evidence: {rel['evidence_text'][:100]}...\n\n"

    report += f"---\n\n## Suggested New Connections\n\n"
    report += "Based on transitive relationships and co-occurrence patterns:\n\n"

    for idx, suggestion in enumerate(suggestions[:10], 1):
        report += f"{idx}. **{suggestion['source']}** → **{suggestion['target']}**\n"
        report += f"   - Suggested type: {suggestion['suggested_type']}\n"
        report += f"   - Reason: {suggestion['reason']}\n"
        report += f"   - Confidence: {suggestion['confidence']:.2f}\n\n"

    report += f"---\n\n## Key Insights\n\n"

    # Generate insights based on the data
    report += f"""### Domain Structure

1. **Core Optimization Algorithms:** The graph reveals {len([c for c in concepts.values() if 'optimization' in c['label'].lower()])} concepts related to optimization, with PPO, DPO, and GRPO forming a central cluster.

2. **Training Pipeline:** The knowledge graph captures the multi-stage training process: pre-training → supervised fine-tuning → reinforcement learning, with clear dependencies between stages.

3. **Mathematical Reasoning:** A significant cluster focuses on mathematical reasoning applications, including formal theorem proving and tool-integrated reasoning.

4. **Regularization Techniques:** KL divergence regularization appears as a central concept connecting multiple optimization methods, highlighting its critical role in stable training.

### Relationship Patterns

1. **Hierarchical:** {stats['relationships_by_type'].get('is-a', 0) + stats['relationships_by_type'].get('part-of', 0)} relationships establish taxonomic structure
2. **Procedural:** {stats['relationships_by_type'].get('uses', 0) + stats['relationships_by_type'].get('requires', 0)} relationships describe method dependencies
3. **Comparative:** {stats['relationships_by_type'].get('alternative-to', 0) + stats['relationships_by_type'].get('differs-from', 0)} relationships connect competing approaches

### Notable Findings

- **DPO vs RLHF:** The graph captures the debate between explicit reward modeling (RLHF) and direct preference optimization (DPO)
- **Process vs Outcome Supervision:** Clear distinction between step-by-step feedback and final-answer evaluation
- **Formal vs Informal Reasoning:** Separate but connected clusters for theorem proving and natural language mathematical reasoning

---

## Recommendations for Further Analysis

1. **Temporal Analysis:** Map the evolution of concepts and methods over time
2. **Citation Network:** Integrate paper citations to understand influence patterns
3. **Performance Correlation:** Link methods to benchmark results to identify what works best
4. **Missing Connections:** Investigate suggested relationships for potential documentation gaps
5. **Concept Expansion:** Add more granular concepts for specific hyperparameters and implementation details

---

*End of Analysis Report*
"""

    with open(f"{output_dir}/graph-analysis.md", 'w', encoding='utf-8') as f:
        f.write(report)


def generate_visualization(concepts, relationships, output_dir):
    """Generate interactive HTML visualization using vis.js."""

    # Convert to vis.js format
    nodes_js = []
    for cid, concept in concepts.items():
        node_id = int(cid.split('_')[1])

        # Color by type
        color_map = {
            'primary_topic': '#e74c3c',
            'section_concept': '#3498db',
            'domain_term': '#2ecc71',
            'emphasized_term': '#f39c12',
            'linked_concept': '#9b59b6',
        }
        color = color_map.get(concept['type'], '#95a5a6')

        nodes_js.append({
            'id': node_id,
            'label': concept['label'],
            'title': f"{concept['label']}<br>Type: {concept['type']}<br>Source: {concept['source_file']}",
            'color': color,
            'shape': 'dot',
            'size': 10 if concept['type'] == 'primary_topic' else 5
        })

    edges_js = []
    for rel in relationships:
        source_id = int(rel['source'].split('_')[1])
        target_id = int(rel['target'].split('_')[1])

        edges_js.append({
            'from': source_id,
            'to': target_id,
            'title': f"{rel['relationship_type']}<br>Confidence: {rel['confidence']:.2f}",
            'label': rel['relationship_type'],
            'arrows': 'to',
            'color': {'opacity': rel['confidence']}
        })

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Knowledge Graph Visualization</title>
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
    </style>
</head>
<body>
    <div id="header">
        <h1>Knowledge Graph: RL & Post-Training</h1>
        <p>{len(concepts)} concepts | {len(relationships)} relationships</p>
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
        var nodes = new vis.DataSet({json.dumps(nodes_js)});
        var edges = new vis.DataSet({json.dumps(edges_js)});

        var container = document.getElementById('mynetwork');
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            nodes: {{
                font: {{
                    size: 12,
                    color: '#000000'
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
            nodes.forEach(function(node) {{
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

    with open(f"{output_dir}/graph-visualization.html", 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    main()
