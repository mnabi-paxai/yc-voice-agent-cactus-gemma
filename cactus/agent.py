"""Twin Mind — Agent CLI

Query, reflect on, and get insights from your knowledge base
using Gemma 4 tool-calling agents on Cactus.

Usage:
    python agent.py ask "What is GRPO?"
    python agent.py ask "When is Lily's recital?"
    python agent.py reflect
    python agent.py companion
    python agent.py companion --session 2026-04-18_223309
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "cactus", "python", "src"))

from cactus import cactus_init, cactus_destroy
from agent_loop import run_agent

SYSTEM_PROMPTS = {
    "ask": (
        "You are Twin Mind, a personal knowledge assistant. "
        "Answer the user's question using ONLY information from the knowledge base. "
        "Use the available tools to search and read articles before answering. "
        "If the information is not in the knowledge base, say so honestly. "
        "Be concise and specific — cite which article the information came from."
    ),
    "reflect": (
        "You are Twin Mind's reflection engine. "
        "Your job is to read across the entire knowledge base and produce a thoughtful analysis. "
        "Use the tools to list and read all articles systematically. "
        "Then identify:\n"
        "1. Patterns and recurring themes across articles\n"
        "2. Gaps — important topics that are missing or under-explored\n"
        "3. Contradictions — where articles disagree\n"
        "4. Unexpected connections between different concepts\n"
        "Be specific and reference article titles."
    ),
    "companion": (
        "You are Twin Mind's companion — a proactive learning partner. "
        "A new session just completed. Use the tools to read the latest session "
        "and compare it against existing knowledge. "
        "Then surface:\n"
        "1. What is genuinely new in this session\n"
        "2. What reinforces or deepens existing knowledge\n"
        "3. What contradicts something already known\n"
        "4. Suggested next topics or follow-ups worth exploring\n"
        "Be warm, concise, and actionable."
    ),
}


def parse_args():
    parser = argparse.ArgumentParser(description="Twin Mind Agent — your second brain")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    ask_parser = subparsers.add_parser("ask", help="Ask a question about your knowledge")
    ask_parser.add_argument("question", type=str, help="Your question")

    subparsers.add_parser("reflect", help="Find patterns and gaps across all knowledge")

    companion_parser = subparsers.add_parser("companion", help="Get insights after a session")
    companion_parser.add_argument(
        "--session", default="latest",
        help="Session ID or 'latest' (default: latest)",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    weights_path = os.path.join(BASE_DIR, "cactus", "weights", "gemma-4-e2b-it")
    data_dir = os.path.join(BASE_DIR, "Data")

    print("Loading Gemma 4 on Cactus...\n")
    model = cactus_init(weights_path, None, False)

    system_prompt = SYSTEM_PROMPTS[args.mode]

    if args.mode == "ask":
        user_message = args.question
        print(f"Question: {user_message}\n")

    elif args.mode == "reflect":
        user_message = (
            "Analyze the entire knowledge base. "
            "Read through all articles and identify patterns, gaps, "
            "contradictions, and connections."
        )
        print("Reflecting on your knowledge base...\n")

    elif args.mode == "companion":
        session_id = args.session
        user_message = (
            f"Read the session log for '{session_id}' and compare it "
            f"against the existing knowledge base. "
            f"What's new, what's reinforced, and what should I explore next?"
        )
        print(f"Analyzing session: {session_id}\n")

    print("=" * 60)
    answer = run_agent(model, system_prompt, user_message, data_dir, BASE_DIR)
    print("=" * 60)
    print(f"\n{answer}\n")

    cactus_destroy(model)


if __name__ == "__main__":
    main()
