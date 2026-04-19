"""Twin Mind — Tools Module

Defines the tools available to Twin Mind agents for querying,
searching, and analyzing the markdown knowledge base.
Each tool has a JSON definition (for Cactus function calling)
and a Python implementation.
"""

import json
import os
import re

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_articles",
            "description": "List all articles in the knowledge base with titles and summaries",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_article",
            "description": "Read the full content of a wiki article by filename",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The markdown filename, e.g. reward-modeling.md",
                    }
                },
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_articles",
            "description": "Search all articles for a keyword or phrase, returns matching excerpts",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search term or phrase",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_person",
            "description": "Find all knowledge related to a specific person by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The person's name to search for",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_by_date",
            "description": "Find knowledge from sessions on a specific date",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date to search for, e.g. 2026-04-18 or 'yesterday'",
                    }
                },
                "required": ["date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_patterns",
            "description": "Detect recurring patterns and themes about a person or topic across all knowledge",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {
                        "type": "string",
                        "description": "The person or topic to find patterns about",
                    }
                },
                "required": ["subject"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_session_log",
            "description": "Read the transcript and observations from a capture session",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session timestamp ID, e.g. 2026-04-18_223309. Use 'latest' for the most recent.",
                    }
                },
                "required": ["session_id"],
            },
        },
    },
]

MAX_RESULT_CHARS = 1500


def _read_all_articles(data_dir):
    """Read all markdown files in data_dir, return list of (filename, content)."""
    articles = []
    for f in sorted(os.listdir(data_dir)):
        if f.endswith(".md") and f != "index.md":
            path = os.path.join(data_dir, f)
            with open(path, "r") as fh:
                articles.append((f, fh.read()))
    return articles


def _extract_context_lines(content, query, context=2):
    """Find lines matching query and return them with surrounding context."""
    lines = content.split("\n")
    query_lower = query.lower()
    matches = []
    for i, line in enumerate(lines):
        if query_lower in line.lower():
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            snippet = "\n".join(lines[start:end])
            if snippet not in matches:
                matches.append(snippet)
    return matches


def list_articles(data_dir, **kwargs):
    index_path = os.path.join(data_dir, "index.md")
    if not os.path.exists(index_path):
        return "No articles found. The knowledge base is empty."
    with open(index_path, "r") as f:
        return f.read()[:MAX_RESULT_CHARS]


def read_article(data_dir, filename, **kwargs):
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        return f"Article '{filename}' not found."
    with open(path, "r") as f:
        return f.read()[:MAX_RESULT_CHARS]


def search_articles(data_dir, query, **kwargs):
    results = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, query)
        if matches:
            excerpts = "\n---\n".join(matches[:3])
            results.append(f"## {filename}\n{excerpts}")
    if not results:
        return f"No results found for '{query}'."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def search_by_person(data_dir, name, **kwargs):
    results = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, name, context=3)
        if matches:
            excerpts = "\n---\n".join(matches[:3])
            results.append(f"## {filename}\n{excerpts}")
    if not results:
        return f"No mentions of '{name}' found in the knowledge base."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def search_by_date(data_dir, date, base_dir=None, **kwargs):
    results = []

    # Search session directories for matching dates
    if base_dir:
        sessions_dir = os.path.join(base_dir, "sessions")
        if os.path.exists(sessions_dir):
            for session in sorted(os.listdir(sessions_dir)):
                if date in session:
                    summary_path = os.path.join(sessions_dir, session, "summary.json")
                    if os.path.exists(summary_path):
                        with open(summary_path, "r") as f:
                            summary = json.load(f)
                        results.append(
                            f"## Session {session}\n"
                            f"Transcript: {summary.get('transcript', 'N/A')[:300]}\n"
                            f"New articles: {', '.join(a[0] for a in summary.get('new_articles', []))}"
                        )

    # Search articles for date mentions
    for filename, content in _read_all_articles(data_dir):
        if date in content:
            matches = _extract_context_lines(content, date)
            if matches:
                results.append(f"## {filename}\n" + "\n".join(matches[:2]))

    if not results:
        return f"No knowledge found for date '{date}'."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def get_patterns(data_dir, subject, model=None, **kwargs):
    """Collect all mentions of a subject, then use Gemma 4 to identify patterns."""
    all_mentions = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, subject, context=3)
        if matches:
            for m in matches[:2]:
                all_mentions.append(f"[{filename}] {m}")

    if not all_mentions:
        return f"No mentions of '{subject}' found to analyze patterns."

    mentions_text = "\n\n".join(all_mentions)[:2000]

    if model:
        from cactus import cactus_complete
        prompt = (
            f"Here are all mentions of '{subject}' from the knowledge base:\n\n"
            f"{mentions_text}\n\n"
            f"Identify recurring patterns, trends, or themes about '{subject}'. "
            f"Be specific and concise."
        )
        messages = json.dumps([{"role": "user", "content": prompt}])
        options = json.dumps({"max_tokens": 300, "temperature": 0.0})
        response = cactus_complete(model, messages, options, None, None)
        return json.loads(response).get("response", mentions_text)

    return f"Mentions of '{subject}':\n\n{mentions_text}"


def read_session_log(base_dir, session_id, **kwargs):
    sessions_dir = os.path.join(base_dir, "sessions")
    if not os.path.exists(sessions_dir):
        return "No sessions found."

    if session_id == "latest":
        sessions = sorted(os.listdir(sessions_dir))
        sessions = [s for s in sessions if not s.startswith(".")]
        if not sessions:
            return "No sessions found."
        session_id = sessions[-1]

    summary_path = os.path.join(sessions_dir, session_id, "summary.json")
    if not os.path.exists(summary_path):
        return f"No summary found for session '{session_id}'."

    with open(summary_path, "r") as f:
        summary = json.load(f)

    output = (
        f"Session: {summary.get('timestamp', session_id)}\n"
        f"Transcript: {summary.get('transcript', 'N/A')}\n"
        f"Visual summary: {summary.get('visual_summary', 'N/A')[:500]}\n"
        f"New articles: {', '.join(a[0] for a in summary.get('new_articles', []))}"
    )
    return output[:MAX_RESULT_CHARS]


TOOL_FUNCTIONS = {
    "list_articles": list_articles,
    "read_article": read_article,
    "search_articles": search_articles,
    "search_by_person": search_by_person,
    "search_by_date": search_by_date,
    "get_patterns": get_patterns,
    "read_session_log": read_session_log,
}


def execute_tool(name, arguments, data_dir, base_dir=None, model=None):
    """Execute a tool by name with the given arguments."""
    if name not in TOOL_FUNCTIONS:
        return f"Unknown tool: {name}"

    fn = TOOL_FUNCTIONS[name]

    if name == "read_session_log":
        return fn(base_dir=base_dir, **arguments)
    elif name == "search_by_date":
        return fn(data_dir=data_dir, base_dir=base_dir, **arguments)
    elif name == "get_patterns":
        return fn(data_dir=data_dir, model=model, **arguments)
    else:
        return fn(data_dir=data_dir, **arguments)
