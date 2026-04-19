"""Twin Mind — Learn Module

Extracts concepts from a session's transcript and visual observations,
generates structured wiki articles, and updates the knowledge index.
"""

import json
import os
import re

from cactus import cactus_complete


def slugify(title):
    """Convert a concept title to a filename-safe slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def read_existing_index(data_dir):
    """Read the current index.md and return its contents and list of existing articles."""
    index_path = os.path.join(data_dir, "index.md")
    if not os.path.exists(index_path):
        return "", []

    with open(index_path, "r") as f:
        content = f.read()

    articles = re.findall(r"\[([^\]]+)\]\(([^)]+\.md)\)", content)
    return content, articles


def extract_concepts(model, transcript, visual_summary, existing_articles):
    """Ask Gemma 4 to identify key concepts from the session."""
    existing_names = ", ".join(name for name, _ in existing_articles) if existing_articles else "none yet"

    prompt = (
        f"You observed a session with this transcript and visual context.\n\n"
        f"Transcript: \"{transcript}\"\n\n"
        f"Visual observations: {visual_summary}\n\n"
        f"Existing wiki articles: {existing_names}\n\n"
        f"Identify the key concepts discussed or shown in this session.\n"
        f"For each concept, provide:\n"
        f"- title: a clear, concise concept name\n"
        f"- summary: one sentence explaining the concept\n"
        f"- related: list of existing article titles this concept relates to\n\n"
        f"Respond in JSON format: [{{\"title\": \"...\", \"summary\": \"...\", \"related\": [\"...\"]}}]\n"
        f"Only return the JSON array, nothing else."
    )

    messages = [{"role": "user", "content": prompt}]
    response = cactus_complete(
        model,
        json.dumps(messages),
        json.dumps({"max_tokens": 500}),
        None, None,
    )
    raw = json.loads(response)["response"]

    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        print(f"  [WARN] Could not parse concepts from model output: {raw[:200]}")
        return []

    try:
        concepts = json.loads(match.group())
    except json.JSONDecodeError:
        print(f"  [WARN] Invalid JSON in concept extraction: {match.group()[:200]}")
        return []

    return concepts


def generate_article(model, concept, transcript, visual_summary, timestamp, existing_articles):
    """Generate a wiki-style markdown article for a single concept."""
    related_names = concept.get("related", [])
    related_links = []
    for name, filename in existing_articles:
        if name in related_names:
            related_links.append(f"- [{name}]({filename})")

    related_section = "\n".join(related_links) if related_links else "- (No related articles yet)"

    prompt = (
        f"Write a structured wiki article about: {concept['title']}\n\n"
        f"Context — this was learned from a session:\n"
        f"Transcript: \"{transcript}\"\n"
        f"Visual context: {visual_summary}\n\n"
        f"Write the article in this exact markdown format:\n\n"
        f"# {concept['title']}\n\n"
        f"## Overview\n"
        f"(Explain the concept in plain language, accessible to a junior researcher)\n\n"
        f"## Key Ideas\n"
        f"(Main points and evidence from the session)\n\n"
        f"## Source\n"
        f"- Session: {timestamp}\n"
        f"- Transcript excerpt: (relevant quote)\n"
        f"- Visual context: (what was observed)\n\n"
        f"## Related Concepts\n"
        f"{related_section}\n\n"
        f"Only return the markdown article, nothing else."
    )

    messages = [{"role": "user", "content": prompt}]
    response = cactus_complete(
        model,
        json.dumps(messages),
        json.dumps({"max_tokens": 800}),
        None, None,
    )
    return json.loads(response)["response"]


def save_article(data_dir, concept, article_content):
    """Save a wiki article as a markdown file in the data directory."""
    slug = slugify(concept["title"])
    filename = f"{slug}.md"
    filepath = os.path.join(data_dir, filename)

    with open(filepath, "w") as f:
        f.write(article_content)

    print(f"  Saved article: {filename}")
    return filename, slug


def update_index(data_dir, new_entries):
    """Append new article entries to index.md."""
    index_path = os.path.join(data_dir, "index.md")

    if not os.path.exists(index_path):
        content = "# Concept Wiki Index\n\n"
    else:
        with open(index_path, "r") as f:
            content = f.read()

    divider_pos = content.rfind("---")

    section = "\n## Learned from Sessions\n\n" if "Learned from Sessions" not in content else ""
    entries_text = section + "\n".join(
        f"- [{title}]({filename}) — {summary}"
        for title, filename, summary in new_entries
    ) + "\n"

    if divider_pos != -1 and "Learned from Sessions" not in content:
        content = content[:divider_pos] + entries_text + "\n" + content[divider_pos:]
    else:
        content = content.rstrip() + "\n" + entries_text

    with open(index_path, "w") as f:
        f.write(content)

    print(f"  Updated index.md with {len(new_entries)} new entries")


def learn_from_session(model, transcript, visual_summary, timestamp, data_dir):
    """Full learning pipeline: extract concepts, generate articles, update index."""
    print("\n=== LEARNING FROM SESSION ===\n")

    index_content, existing_articles = read_existing_index(data_dir)

    print("Extracting concepts...")
    concepts = extract_concepts(model, transcript, visual_summary, existing_articles)

    if not concepts:
        print("  No new concepts identified.")
        return []

    print(f"  Found {len(concepts)} concepts: {', '.join(c['title'] for c in concepts)}\n")

    new_entries = []
    for concept in concepts:
        print(f"Generating article: {concept['title']}...")
        article = generate_article(
            model, concept, transcript, visual_summary, timestamp, existing_articles
        )
        filename, slug = save_article(data_dir, concept, article)
        new_entries.append((concept["title"], filename, concept.get("summary", "")))

    if new_entries:
        update_index(data_dir, new_entries)

    print(f"\n=== LEARNED {len(new_entries)} NEW CONCEPTS ===\n")
    return new_entries
