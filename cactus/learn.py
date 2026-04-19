"""Twin Mind — Learn Module

Extracts concepts from a session's transcript and visual observations,
generates structured wiki articles, and updates the knowledge index.

Embedding pipeline:
  - One embedding per markdown file (title + overview section)
  - Stored in cactus_index with filename as metadata

Retrieval + scoring:
  1. semantic_sim used as a threshold gate — trim candidates below threshold
  2. Remaining candidates ranked by engagement_score:
       engagement_score = sum(exp(-0.1 * days) for each session that accessed this file)
     More recently and frequently accessed = higher score
  3. Access log persisted in vector_index/access_log.json

File watcher:
  - Monitors Data/ directory for user opens/edits of .md files
  - Logs to access_log.json so engagement score reflects real user interest
"""

import json
import math
import os
import re
import threading
from datetime import datetime
from pathlib import Path

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _WATCHDOG_AVAILABLE = True
except ImportError:
    _WATCHDOG_AVAILABLE = False

_ATIME_POLL_INTERVAL = 5  # seconds between atime checks

from cactus import (
    cactus_complete,
    cactus_embed,
    cactus_index_init,
    cactus_index_add,
    cactus_index_query,
    cactus_index_get,
    cactus_index_compact,
)

SIM_THRESHOLD = 0.3   # minimum semantic similarity to be a candidate
ENGAGEMENT_DECAY = 0.1  # recency decay rate per day


# ---------------------------------------------------------------------------
# Embedding index
# ---------------------------------------------------------------------------

def init_index(model, data_dir):
    """Initialise the vector index, inferring embedding dim from a test embed."""
    dim = len(cactus_embed(model, "init", True))
    index_dir = os.path.join(data_dir, "vector_index")
    os.makedirs(index_dir, exist_ok=True)
    index = cactus_index_init(index_dir, dim)
    return index


def chunk_markdown(text):
    """Split a markdown file into sections on ## headers."""
    sections = re.split(r'\n(?=## )', text)
    return [s.strip() for s in sections if s.strip()]


def _parse_timestamp(text):
    """Extract session timestamp from article Source section."""
    match = re.search(r'Session:\s*(\S+)', text)
    return match.group(1) if match else "unknown"


def _indexed_log_path(data_dir):
    return os.path.join(data_dir, "vector_index", "indexed.json")


def _load_indexed(data_dir):
    path = _indexed_log_path(data_dir)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)  # {filename: doc_id_start}
    return {}


def _save_indexed(data_dir, indexed):
    with open(_indexed_log_path(data_dir), "w") as f:
        json.dump(indexed, f)


def build_wiki_index(model, index, data_dir):
    """Embed wiki articles by section. Skips already-indexed files."""
    indexed = _load_indexed(data_dir)
    doc_id = sum(indexed.values()) if indexed else 0

    new_count = 0
    for filepath in sorted(Path(data_dir).glob("*.md")):
        if filepath.name == "index.md" or filepath.name in indexed:
            continue
        text = filepath.read_text()
        start_id = doc_id
        for section in chunk_markdown(text):
            emb = cactus_embed(model, section, True)
            cactus_index_add(index, [doc_id], [section], [emb], [filepath.name])
            doc_id += 1
        indexed[filepath.name] = doc_id - start_id
        new_count += 1

    if new_count:
        cactus_index_compact(index)
        _save_indexed(data_dir, indexed)

    skipped = len(indexed) - new_count
    print(f"  Indexed {new_count} new articles ({skipped} already cached)")
    return doc_id


def add_article_to_index(model, index, doc_id, filepath, timestamp, data_dir):
    """Embed a newly written article by section and update the indexed log."""
    filename = os.path.basename(filepath)
    text = Path(filepath).read_text()
    start_id = doc_id
    for section in chunk_markdown(text):
        emb = cactus_embed(model, section, True)
        cactus_index_add(index, [doc_id], [section], [emb], [filename])
        doc_id += 1
    cactus_index_compact(index)
    indexed = _load_indexed(data_dir)
    indexed[filename] = doc_id - start_id
    _save_indexed(data_dir, indexed)
    return doc_id


# ---------------------------------------------------------------------------
# Engagement log (replaces separate cognitive + recency signals)
# ---------------------------------------------------------------------------

def _access_log_path(data_dir):
    return os.path.join(data_dir, "vector_index", "access_log.json")


def _load_access_log(data_dir):
    """Load {filename: [date_str, ...]} access history."""
    path = _access_log_path(data_dir)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def _save_access_log(data_dir, log):
    with open(_access_log_path(data_dir), "w") as f:
        json.dump(log, f)


def _log_access(data_dir, filenames, timestamp):
    """Record that these files were accessed in a session."""
    log = _load_access_log(data_dir)
    date_str = timestamp[:10]
    for filename in filenames:
        log.setdefault(filename, []).append(date_str)
    _save_access_log(data_dir, log)


def _engagement_score(access_dates, decay=ENGAGEMENT_DECAY):
    """
    Time-decayed access frequency:
      score = sum(exp(-decay * days_since_access)) for each session access
    More recent and more frequent access = higher score.
    Files never accessed score 0.
    """
    if not access_dates:
        return 0.0
    today = datetime.now()
    score = 0.0
    for date_str in access_dates:
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
            days = max(0, (today - d).days)
            score += math.exp(-decay * days)
        except Exception:
            pass
    return score


# ---------------------------------------------------------------------------
# File watcher — tracks direct user interaction with markdown files
# ---------------------------------------------------------------------------

class _AtimePoller(threading.Thread):
    """Polls st_atime of every .md file to detect reads (opens) and writes."""

    def __init__(self, data_dir):
        super().__init__(daemon=True)
        self._data_dir = data_dir
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._atimes = self._snapshot()

    def _snapshot(self):
        result = {}
        for f in Path(self._data_dir).glob("*.md"):
            if f.name == "index.md":
                continue
            try:
                result[f.name] = os.stat(f).st_atime
            except OSError:
                pass
        return result

    def run(self):
        while not self._stop.wait(_ATIME_POLL_INTERVAL):
            current = self._snapshot()
            today = datetime.now().strftime("%Y-%m-%d")
            accessed = [
                name for name, atime in current.items()
                if atime != self._atimes.get(name)
            ]
            if accessed:
                with self._lock:
                    _log_access(self._data_dir, accessed, today)
            self._atimes = current

    def stop(self):
        self._stop.set()
        self.join()


if _WATCHDOG_AVAILABLE:
    class _MarkdownWriteHandler(FileSystemEventHandler):
        """Catches saves/writes instantly via FSEvents (complements atime polling for reads)."""

        def __init__(self, data_dir, lock):
            self._data_dir = data_dir
            self._lock = lock

        def on_modified(self, event):
            if event.is_directory:
                return
            path = event.src_path
            if not path.endswith(".md") or os.path.basename(path) == "index.md":
                return
            filename = os.path.basename(path)
            today = datetime.now().strftime("%Y-%m-%d")
            with self._lock:
                _log_access(self._data_dir, [filename], today)


def start_file_watcher(data_dir):
    """
    Start two complementary watchers:
      - AtimePoller: detects reads (opens) by polling st_atime every 5 s
      - FSEvents observer (watchdog): detects writes instantly
    Returns (poller, observer) tuple; observer may be None if watchdog unavailable.
    """
    poller = _AtimePoller(data_dir)
    poller.start()

    observer = None
    if _WATCHDOG_AVAILABLE:
        lock = poller._lock
        handler = _MarkdownWriteHandler(data_dir, lock)
        observer = Observer()
        observer.schedule(handler, data_dir, recursive=False)
        observer.start()
        print("  File watcher started (reads via atime polling + writes via FSEvents)")
    else:
        print("  File watcher started (reads via atime polling; install watchdog for instant write detection)")

    return poller, observer


def stop_file_watcher(watcher):
    """Stop watchers returned by start_file_watcher."""
    if watcher is None:
        return
    poller, observer = watcher
    poller.stop()
    if observer is not None:
        observer.stop()
        observer.join()


# ---------------------------------------------------------------------------
# Retrieval + scoring
# ---------------------------------------------------------------------------

def retrieve_and_score(model, index, query_text, data_dir,
                       top_k=5, sim_threshold=SIM_THRESHOLD):
    """
    1. Embed query and retrieve candidate files from vector index
    2. Trim candidates below sim_threshold
    3. Rank remaining by engagement_score (time-decayed access frequency)
    4. Log accessed files for future scoring
    """
    query_emb = cactus_embed(model, query_text, True)
    raw = cactus_index_query(index, query_emb, json.dumps({"top_k": top_k * 3}))
    results = json.loads(raw)["results"]

    access_log = _load_access_log(data_dir)

    # collect best semantic_sim per file across all matching sections
    best_per_file = {}
    for r in results:
        if r["score"] < sim_threshold:
            continue
        doc_raw = json.loads(cactus_index_get(index, [r["id"]]))["results"][0]
        filename = doc_raw.get("metadata", "unknown")
        if filename not in best_per_file or r["score"] > best_per_file[filename]["semantic_sim"]:
            best_per_file[filename] = {
                "filename": filename,
                "text": doc_raw["document"],
                "semantic_sim": r["score"],
                "engagement": _engagement_score(access_log.get(filename, [])),
            }

    ranked = sorted(best_per_file.values(), key=lambda x: x["engagement"], reverse=True)[:top_k]

    # log this retrieval as an access event
    today = datetime.now().strftime("%Y-%m-%d")
    _log_access(data_dir, [r["filename"] for r in ranked], today)

    return ranked


# ---------------------------------------------------------------------------
# Knowledge extraction (unchanged logic, now index-aware)
# ---------------------------------------------------------------------------

def slugify(title):
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def read_existing_index(data_dir):
    index_path = os.path.join(data_dir, "index.md")
    if not os.path.exists(index_path):
        return "", []
    with open(index_path, "r") as f:
        content = f.read()
    articles = re.findall(r"\[([^\]]+)\]\(([^)]+\.md)\)", content)
    return content, articles


def extract_concepts(model, transcript, visual_summary, existing_articles):
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
    response = cactus_complete(model, json.dumps(messages), json.dumps({"max_tokens": 500}), None, None)
    raw = json.loads(response)["response"]
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        print(f"  [WARN] Could not parse concepts: {raw[:200]}")
        return []
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        print(f"  [WARN] Invalid JSON in concepts: {match.group()[:200]}")
        return []


def generate_article(model, concept, transcript, visual_summary, timestamp, existing_articles):
    related_names = concept.get("related", [])
    related_links = [
        f"- [{name}]({filename})"
        for name, filename in existing_articles
        if name in related_names
    ]
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
    response = cactus_complete(model, json.dumps(messages), json.dumps({"max_tokens": 800}), None, None)
    return json.loads(response)["response"]


def save_article(data_dir, concept, article_content):
    slug = slugify(concept["title"])
    filename = f"{slug}.md"
    filepath = os.path.join(data_dir, filename)
    with open(filepath, "w") as f:
        f.write(article_content)
    print(f"  Saved article: {filename}")
    return filename, slug


def update_index(data_dir, new_entries):
    index_path = os.path.join(data_dir, "index.md")
    content = open(index_path).read() if os.path.exists(index_path) else "# Concept Wiki Index\n\n"
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


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def learn_from_session(model, transcript, visual_summary, timestamp, data_dir,
                       index=None, doc_id=0):
    """
    Full learning pipeline: retrieve related context, extract concepts,
    generate articles, update index and vector store.

    Returns (new_entries, updated_doc_id).
    """
    print("\n=== LEARNING FROM SESSION ===\n")

    # Use scored retrieval from vector index if available
    if index and transcript:
        print("Retrieving related wiki articles...")
        scored = retrieve_and_score(model, index, transcript, data_dir)
        existing_articles = [(s["filename"].replace(".md", "").replace("-", " ").title(),
                              s["filename"]) for s in scored]
        for s in scored:
            print(f"  {s['filename']}  sim={s['semantic_sim']:.2f}  engagement={s['engagement']:.3f}")
        print()
    else:
        _, existing_articles = read_existing_index(data_dir)

    print("Extracting concepts...")
    concepts = extract_concepts(model, transcript, visual_summary, existing_articles)

    if not concepts:
        print("  No new concepts identified.")
        return [], doc_id

    print(f"  Found {len(concepts)} concepts: {', '.join(c['title'] for c in concepts)}\n")

    new_entries = []
    for concept in concepts:
        print(f"Generating article: {concept['title']}...")
        article = generate_article(model, concept, transcript, visual_summary, timestamp, existing_articles)
        filename, _ = save_article(data_dir, concept, article)
        new_entries.append((concept["title"], filename, concept.get("summary", "")))

        # add new article to vector index immediately
        if index:
            filepath = os.path.join(data_dir, filename)
            doc_id = add_article_to_index(model, index, doc_id, filepath, timestamp, data_dir)
            _log_access(data_dir, [filename], timestamp)

    if new_entries:
        update_index(data_dir, new_entries)

    print(f"\n=== LEARNED {len(new_entries)} NEW CONCEPTS ===\n")
    return new_entries, doc_id
