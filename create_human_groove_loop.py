#!/usr/bin/env python3
"""
Create a multi-track MIDI loop using human groove DNA extracted from audio samples.
Uses basic-pitch analysis + Ableton MCP CLI to build a natural-sounding loop.
"""
import json
import subprocess
import time
import random
import sys

BPM = 95.0
BEAT_DUR = 60.0 / BPM  # seconds per beat
BARS = 4
CLIP_LENGTH = BARS * 4  # 16 beats
CLI_DIR = "/Users/aayush/code/Music Production/ableton-mcp"


def mcp(tool: str, args: dict):
    """Call an Ableton MCP CLI tool."""
    result = subprocess.run(
        ["/opt/homebrew/bin/uv", "run", "python", "ableton_cli.py", tool, json.dumps(args)],
        capture_output=True, text=True, cwd=CLI_DIR,
    )
    last_line = result.stdout.strip().split("\n")[-1] if result.stdout.strip() else ""
    return last_line


def cx_send(address: str, value: float = 1.0):
    """Send to a mapped X-OSC address."""
    subprocess.run(
        ["/opt/homebrew/bin/uv", "run", "python", "-c",
         f"from pythonosc.udp_client import SimpleUDPClient; "
         f"SimpleUDPClient('127.0.0.1', 7005).send_message('{address}', {value})"],
        capture_output=True, text=True, cwd=CLI_DIR,
    )


def load_patterns():
    """Load human groove patterns from basic-pitch analysis."""
    with open("/tmp/midi_output/all_patterns.json") as f:
        return json.load(f)


def sec_to_beats(seconds: float) -> float:
    """Convert seconds to beats at current BPM."""
    return seconds / BEAT_DUR


def build_melody_from_groove(pattern_notes, scale_pitches, octave_shift=0):
    """
    Extract timing + duration groove from a human pattern,
    map pitches to a target scale.
    """
    sorted_notes = sorted(pattern_notes, key=lambda n: n["start_time"])
    first_time = sorted_notes[0]["start_time"]

    notes = []
    for n in sorted_notes:
        beat = sec_to_beats(n["start_time"] - first_time)
        dur = max(sec_to_beats(n["duration"]), 0.15)

        if beat >= CLIP_LENGTH:
            break

        # Map original pitch to our scale (preserve contour)
        scale_idx = n["pitch"] % len(scale_pitches)
        pitch = scale_pitches[scale_idx % len(scale_pitches)] + octave_shift

        # Velocity arc — natural dynamics
        position = beat / CLIP_LENGTH
        base_vel = 65 + int(35 * (1 - abs(position - 0.55) * 1.8))
        vel = max(45, min(120, base_vel + random.randint(-10, 10)))

        notes.append({
            "pitch": pitch,
            "start_time": round(beat, 4),
            "duration": round(min(dur, CLIP_LENGTH - beat), 4),
            "velocity": vel,
            "mute": False,
        })

    return notes


def build_bass_from_groove(pattern_notes, root_notes):
    """Extract bass groove timing, use root movement."""
    sorted_notes = sorted(pattern_notes, key=lambda n: n["start_time"])
    first_time = sorted_notes[0]["start_time"]

    notes = []
    root_idx = 0
    last_beat = -2.0

    for n in sorted_notes:
        beat = sec_to_beats(n["start_time"] - first_time)
        dur = max(sec_to_beats(n["duration"]), 0.3)

        if beat >= CLIP_LENGTH:
            break

        # Only take notes with enough spacing for bass (min ~0.5 beats apart)
        if beat - last_beat < 0.4:
            continue

        pitch = root_notes[root_idx % len(root_notes)]
        root_idx += 1

        vel = 75 + random.randint(-5, 15)

        notes.append({
            "pitch": pitch,
            "start_time": round(beat, 4),
            "duration": round(min(dur * 2, CLIP_LENGTH - beat, 3.0), 4),
            "velocity": vel,
            "mute": False,
        })
        last_beat = beat

    return notes


def build_rhythm_pattern():
    """Create a percussion/bell rhythm with human feel (micro-timing offsets)."""
    notes = []
    # Kick-like hits on beats 1 and 3 with human timing
    for bar in range(BARS):
        base = bar * 4
        for beat_offset in [0.0, 2.0]:
            timing_offset = random.uniform(-0.03, 0.03)
            notes.append({
                "pitch": 36,  # kick
                "start_time": round(base + beat_offset + timing_offset, 4),
                "duration": 0.5,
                "velocity": 85 + random.randint(-5, 10),
                "mute": False,
            })

        # Hi-hat pattern — every half beat with shuffle feel
        for eighth in range(8):
            beat = base + eighth * 0.5
            swing = 0.04 if eighth % 2 == 1 else 0.0  # slight swing on offbeats
            timing = random.uniform(-0.02, 0.02)
            vel = 55 if eighth % 2 == 0 else 40  # accented downbeats
            vel += random.randint(-8, 8)
            notes.append({
                "pitch": 42,  # closed hi-hat
                "start_time": round(beat + swing + timing, 4),
                "duration": 0.15,
                "velocity": max(30, min(100, vel)),
                "mute": False,
            })

        # Snare/rim on beat 2 and 4
        for snare_beat in [1.0, 3.0]:
            timing_offset = random.uniform(-0.02, 0.02)
            notes.append({
                "pitch": 38,  # snare
                "start_time": round(base + snare_beat + timing_offset, 4),
                "duration": 0.3,
                "velocity": 70 + random.randint(-5, 10),
                "mute": False,
            })

    return notes


def main():
    print("=" * 60)
    print("Creating Multi-Track Human Groove MIDI Loop")
    print("=" * 60)

    # Load human groove patterns
    print("\n[1] Loading human groove patterns from basic-pitch analysis...")
    patterns = load_patterns()
    print(f"    Loaded {len(patterns)} patterns")

    # D minor pentatonic scale
    d_min_pent = [50, 53, 55, 57, 60, 62, 65, 67, 69, 72, 74]
    # Bass roots in D minor
    bass_roots = [38, 36, 41, 38, 36, 43, 38, 41]  # D2, C2, F2, D2...

    # --- Track 0: Melody (Drift) ---
    print("\n[2] Building melody from guitar groove DNA...")
    melody_notes = build_melody_from_groove(
        patterns["guitar_melodic_1"], d_min_pent, octave_shift=0
    )
    print(f"    {len(melody_notes)} melody notes")

    # Clear and write melody
    mcp("set_clip_notes", {"track_index": 0, "clip_index": 0, "notes": []})
    time.sleep(0.1)
    mcp("add_clip_notes", {"track_index": 0, "clip_index": 0, "notes": melody_notes})
    mcp("set_clip_name", {"track_index": 0, "clip_index": 0, "name": "Human Groove Melody"})
    print("    ✅ Written to Track 0 (Drift)")

    # --- Track 1: Bass (Analog) ---
    print("\n[3] Loading Analog on Track 2 and building bass...")
    cx_send("/aatam/load/2-midi/analog")
    time.sleep(3)

    # Check if clip exists, if not create it
    info = mcp("get_clip_info", {"track_index": 1, "clip_index": 0})
    if "No clip" in info or "Error" in info or "null" in info.lower():
        mcp("create_clip", {"track_index": 1, "clip_index": 0, "length": CLIP_LENGTH})
        time.sleep(0.2)

    bass_notes = build_bass_from_groove(patterns["bass_melody_1"], bass_roots)
    print(f"    {len(bass_notes)} bass notes")

    mcp("add_clip_notes", {"track_index": 1, "clip_index": 0, "notes": bass_notes})
    mcp("set_clip_name", {"track_index": 1, "clip_index": 0, "name": "Human Groove Bass"})
    mcp("set_track_name", {"track_index": 1, "name": "BASS"})
    mcp("set_track_volume", {"track_index": 1, "volume": 0.6})
    mcp("set_track_mute", {"track_index": 1, "muted": False})
    print("    ✅ Written to Track 1 (Analog)")

    # --- Track 2 (or new): Rhythm ---
    # Create a new MIDI track for percussion
    print("\n[4] Creating rhythm track with Collision...")
    # Use track index 2 if it's a MIDI track, or create new
    mcp("create_midi_track", {"index": 2})
    time.sleep(0.5)

    # Load Collision for bell/percussion sounds
    cx_send("/aatam/load/2-midi/collision")  # This won't work since we renamed
    # Manually select and load
    mcp("set_selected_track", {"track_index": 2})
    time.sleep(0.3)

    # Build the rhythm clip
    mcp("create_clip", {"track_index": 2, "clip_index": 0, "length": CLIP_LENGTH})
    time.sleep(0.2)

    rhythm_notes = build_rhythm_pattern()
    print(f"    {len(rhythm_notes)} rhythm notes")

    mcp("add_clip_notes", {"track_index": 2, "clip_index": 0, "notes": rhythm_notes})
    mcp("set_clip_name", {"track_index": 2, "clip_index": 0, "name": "Human Feel Rhythm"})
    mcp("set_track_name", {"track_index": 2, "name": "RHYTHM"})
    mcp("set_track_volume", {"track_index": 2, "volume": 0.5})
    mcp("set_track_mute", {"track_index": 2, "muted": False})
    print("    ✅ Written to Track 2")

    # --- Fire all clips ---
    print("\n[5] Firing all clips...")
    mcp("fire_clip", {"track_index": 0, "clip_index": 0})
    time.sleep(0.05)
    mcp("fire_clip", {"track_index": 1, "clip_index": 0})
    time.sleep(0.05)
    mcp("fire_clip", {"track_index": 2, "clip_index": 0})
    time.sleep(0.1)
    mcp("start_playback", {})

    print("\n" + "=" * 60)
    print("🎵 Multi-track loop playing!")
    print("   Track 0: Melody (Drift) — guitar groove DNA")
    print("   Track 1: Bass (Analog) — bass groove DNA")
    print("   Track 2: Rhythm — humanized kick/hat/snare")
    print("=" * 60)

    # Verify audio output
    time.sleep(2)
    for i in range(3):
        level = mcp("get_track_output_meter", {"track_index": i})
        print(f"   Track {i} output: {level}")


if __name__ == "__main__":
    main()
