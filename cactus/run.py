"""Twin Mind — Main Pipeline

Captures video + audio, transcribes and analyzes the session using Gemma 4
on Cactus (on-device), then extracts concepts and generates structured wiki
articles to build a living knowledge base.

Usage:
    python run.py                   # Record live from webcam + mic (10s)
    python run.py --duration 30     # Record for 30 seconds
    python run.py video.mp4         # Process an existing video file
"""

import argparse
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "python", "src"))

from cactus import cactus_init, cactus_destroy
from capture import create_session_dir, record_live, extract_from_video
from analyze import transcribe_audio, analyze_frames, summarize_session
from learn import learn_from_session


def parse_args():
    parser = argparse.ArgumentParser(description="Twin Mind — on-device learning pipeline")
    parser.add_argument("video", nargs="?", default=None,
                        help="Path to a video file to process (omit for live recording)")
    parser.add_argument("--duration", type=int, default=10,
                        help="Recording duration in seconds (default: 10)")
    return parser.parse_args()


def main():
    args = parse_args()

    weights_path = os.path.join(BASE_DIR, "weights", "gemma-4-e2b-it")
    data_dir = os.path.join(BASE_DIR, "data")

    print("Loading Gemma 4 on Cactus...\n")
    model = cactus_init(weights_path, None, False)

    session_dir, frames_dir = create_session_dir(BASE_DIR)
    timestamp = os.path.basename(session_dir)
    print(f"Session: {timestamp}\n")

    # 1. Capture
    if args.video:
        frame_paths, audio_path = extract_from_video(args.video, session_dir, frames_dir)
    else:
        frame_paths, audio_path = record_live(args.duration, session_dir, frames_dir)

    if not frame_paths:
        print("No frames captured. Exiting.")
        cactus_destroy(model)
        return

    # 2. Transcribe
    transcript = transcribe_audio(model, audio_path)

    # 3. Analyze frames
    observations = analyze_frames(model, frame_paths, transcript)

    # 4. Summarize
    session = summarize_session(transcript, observations)

    print("\n=== SESSION SUMMARY ===")
    if transcript:
        print(f"Transcript: {transcript}\n")
    for obs in observations:
        print(f"  Frame {obs['frame']}: {obs['observation']}")

    # 5. Learn — extract concepts and generate wiki articles
    new_articles = learn_from_session(
        model, transcript, session["visual_summary"], timestamp, data_dir
    )

    if new_articles:
        print("New articles added to knowledge base:")
        for title, filename, summary in new_articles:
            print(f"  - {title} ({filename})")

    cactus_destroy(model)
    print("\nDone.")


if __name__ == "__main__":
    main()
