"""Twin Mind — Cognitive Tools

Seven cognitive tools modeled after how human memory works,
powered by Gemma 4 function calling on-device.

    overview  — Scan all knowledge — what do I know?
    focus     — Focus on a specific concept in detail
    search    — Search for a keyword or idea
    recognize — Who is this person? What do I know about them?
    rewind    — What happened on a specific day?
    reflect   — What patterns do I see about a topic?
    replay    — What did I see and hear in a session?
"""

import json
import os
import re

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "overview",
            "description": "Scan all knowledge — what do I know?",
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
            "name": "focus",
            "description": "Focus on a specific concept in detail",
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
            "name": "search",
            "description": "Search for a keyword or idea",
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
            "name": "recognize",
            "description": "Who is this person? What do I know about them?",
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
            "name": "rewind",
            "description": "What happened on a specific day?",
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
            "name": "reflect",
            "description": "What patterns do I see about a topic?",
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
            "name": "replay",
            "description": "What did I see and hear in a session?",
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


def overview(data_dir, **kwargs):
    index_path = os.path.join(data_dir, "index.md")
    if not os.path.exists(index_path):
        return "No memories found. The knowledge base is empty."
    with open(index_path, "r") as f:
        return f.read()[:MAX_RESULT_CHARS]


def focus(data_dir, filename, **kwargs):
    path = os.path.join(data_dir, filename)
    if not os.path.exists(path):
        return f"Memory '{filename}' not found."
    with open(path, "r") as f:
        return f.read()[:MAX_RESULT_CHARS]


def search(data_dir, query, **kwargs):
    results = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, query)
        if matches:
            excerpts = "\n---\n".join(matches[:3])
            results.append(f"## {filename}\n{excerpts}")
    if not results:
        return f"No results found for '{query}'."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def recognize(data_dir, name, **kwargs):
    results = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, name, context=3)
        if matches:
            excerpts = "\n---\n".join(matches[:3])
            results.append(f"## {filename}\n{excerpts}")
    if not results:
        return f"No memories of '{name}' found."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def rewind(data_dir, date, base_dir=None, **kwargs):
    results = []

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

    for filename, content in _read_all_articles(data_dir):
        if date in content:
            matches = _extract_context_lines(content, date)
            if matches:
                results.append(f"## {filename}\n" + "\n".join(matches[:2]))

    if not results:
        return f"No memories found for date '{date}'."
    return "\n\n".join(results)[:MAX_RESULT_CHARS]


def reflect(data_dir, subject, model=None, **kwargs):
    """Collect all mentions of a subject, then use Gemma 4 to identify patterns."""
    all_mentions = []
    for filename, content in _read_all_articles(data_dir):
        matches = _extract_context_lines(content, subject, context=3)
        if matches:
            for m in matches[:2]:
                all_mentions.append(f"[{filename}] {m}")

    if not all_mentions:
        return f"No memories of '{subject}' found to analyze patterns."

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

    return f"Memories of '{subject}':\n\n{mentions_text}"


def replay(base_dir, session_id, **kwargs):
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
    "overview": overview,
    "focus": focus,
    "search": search,
    "recognize": recognize,
    "rewind": rewind,
    "reflect": reflect,
    "replay": replay,
}


def execute_tool(name, arguments, data_dir, base_dir=None, model=None):
    """Execute a cognitive tool by name."""
    if name not in TOOL_FUNCTIONS:
        return f"Unknown tool: {name}"

    fn = TOOL_FUNCTIONS[name]

    if name == "replay":
        return fn(base_dir=base_dir, **arguments)
    elif name == "rewind":
        return fn(data_dir=data_dir, base_dir=base_dir, **arguments)
    elif name == "reflect":
        return fn(data_dir=data_dir, model=model, **arguments)
    else:
        return fn(data_dir=data_dir, **arguments)
