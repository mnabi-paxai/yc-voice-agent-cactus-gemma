"""Twin Mind — Agent CLI

Query, reflect on, and get insights from your knowledge base
using Gemma 4 tool-calling agents on Cactus.

Usage:
    python agent.py ask "What is GRPO?"
    python agent.py ask --voice                 # Ask via microphone
    python agent.py ask "What is GRPO?" --speak  # Read answer aloud
    python agent.py ask --voice --speak          # Full voice interaction
    python agent.py reflect --speak
    python agent.py companion --voice --speak
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import wave

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "python", "src"))

from cactus import cactus_init, cactus_destroy, cactus_transcribe
from agent_loop import run_agent
from tools import TOOL_DEFINITIONS

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

SAMPLE_RATE = 16000

ASK_TOOLS = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in (
    "search", "focus", "overview", "recognize", "reflect",
)]
REFLECT_TOOLS = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in (
    "overview", "focus", "search", "reflect",
)]
COMPANION_TOOLS = [t for t in TOOL_DEFINITIONS if t["function"]["name"] in (
    "replay", "overview", "focus", "search", "recognize", "reflect",
)]

SYSTEM_PROMPTS = {
    "ask": (
        "You are Twin Mind, a personal knowledge assistant. "
        "Answer the user's question using ONLY information from the knowledge base. "
        "To find information, first use the 'search' tool with relevant keywords, "
        "then use the 'focus' tool to read the full article. "
        "If the information is not in the knowledge base, say so honestly. "
        "Be concise and specific."
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


def record_voice(duration_sec=5):
    """Record audio from microphone and return path to wav file."""
    if not AUDIO_AVAILABLE:
        print("Error: sounddevice not installed. Run: pip install sounddevice")
        return None

    print(f"Listening for {duration_sec}s... speak now.\n")
    audio = sd.rec(int(duration_sec * SAMPLE_RATE),
                   samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()

    path = tempfile.mktemp(suffix=".wav")
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    return path


def voice_to_text(model, duration_sec=5):
    """Record from mic, transcribe with Gemma 4, return text."""
    audio_path = record_voice(duration_sec)
    if not audio_path:
        return None

    print("Transcribing...")
    prompt = "<|startoftranscript|><|en|><|transcribe|><|notimestamps|>"
    raw = cactus_transcribe(model, audio_path, prompt, None, None, None)
    transcript = json.loads(raw).get("response", "")
    os.unlink(audio_path)

    print(f"You said: {transcript}\n")
    return transcript


def speak(text):
    """Read text aloud using macOS text-to-speech."""
    clean = text.replace("<|tool_call>", "").strip()
    subprocess.run(["say", clean])


def _add_voice_flags(parser):
    parser.add_argument("--voice", action="store_true",
                        help="Use microphone for input instead of text")
    parser.add_argument("--speak", action="store_true",
                        help="Read the answer aloud")
    parser.add_argument("--listen-duration", type=int, default=5,
                        help="Seconds to listen for voice input (default: 5)")


def parse_args():
    parser = argparse.ArgumentParser(description="Twin Mind Agent — your second brain")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    ask_parser = subparsers.add_parser("ask", help="Ask a question about your knowledge")
    ask_parser.add_argument("question", nargs="?", default=None, help="Your question")
    _add_voice_flags(ask_parser)

    reflect_parser = subparsers.add_parser("reflect", help="Find patterns and gaps across all knowledge")
    _add_voice_flags(reflect_parser)

    companion_parser = subparsers.add_parser("companion", help="Get insights after a session")
    companion_parser.add_argument(
        "--session", default="latest",
        help="Session ID or 'latest' (default: latest)",
    )
    _add_voice_flags(companion_parser)

    return parser.parse_args()


def main():
    args = parse_args()

    weights_path = os.path.join(BASE_DIR, "weights", "gemma-4-e4b-it")
    data_dir = os.path.join(BASE_DIR, "data")

    print("Loading Gemma 4 on Cactus...\n")
    model = cactus_init(weights_path, None, False)

    system_prompt = SYSTEM_PROMPTS[args.mode]

    if args.mode == "ask":
        if args.voice:
            user_message = voice_to_text(model, args.listen_duration)
            if not user_message:
                cactus_destroy(model)
                return
        elif args.question:
            user_message = args.question
        else:
            print("Error: provide a question or use --voice")
            cactus_destroy(model)
            return
        print(f"Question: {user_message}\n")

    elif args.mode == "reflect":
        if args.voice:
            print("Voice input for reflect mode: speak your focus area.\n")
            focus = voice_to_text(model, args.listen_duration)
            user_message = (
                f"Analyze the knowledge base, focusing on: {focus}. "
                f"Identify patterns, gaps, contradictions, and connections."
            ) if focus else (
                "Analyze the entire knowledge base. "
                "Read through all articles and identify patterns, gaps, "
                "contradictions, and connections."
            )
        else:
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

    mode_tools = {"ask": ASK_TOOLS, "reflect": REFLECT_TOOLS, "companion": COMPANION_TOOLS}

    print("=" * 60)
    answer = run_agent(model, system_prompt, user_message, data_dir, BASE_DIR,
                       tools=mode_tools[args.mode])
    print("=" * 60)
    print(f"\n{answer}\n")

    if args.speak and answer:
        print("Speaking...\n")
        speak(answer)

    cactus_destroy(model)


if __name__ == "__main__":
    main()
