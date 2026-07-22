#!/usr/bin/env python3
"""
session_circular_breath.py — 1.5-minute circular breathing session with 2 rounds

Breathwork pattern:
  Round 1: Breathe 30s (circular mouth fast) → Hold 20s (deep inhale hold)
  Round 2: Breathe 30s (circular mouth fast) → Hold 20s (deep inhale hold)
  Outro:   Slow exhale + fade (10s)

Total: ~110 seconds ≈ 1:50

Music maps to breath:
  BREATHE = energy, festival grooves, layers build
  HOLD    = strip to drone, spaciousness, reverb tails

Vibe: Festival groovy — driving kicks, tribal percussion, handpan melodies.
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ableton_mcp.osc_bridge import AbletonOSCBridge, ClyphXBridge

BPM = 90.0
BEAT_DUR = 60.0 / BPM

# Track indices
NATURE   = 5
BREATH   = 6
DRUMS    = 7
PERC_MID = 8
PERC_HI  = 9
GUITAR   = 10
MELODY   = 11
BASS     = 12
ARPS     = 13
PADS     = 14

ALL_TRACKS = [NATURE, BREATH, DRUMS, PERC_MID, PERC_HI, GUITAR, MELODY, BASS, ARPS, PADS]

# Rhythmic tracks (muted during holds)
RHYTHM_TRACKS = [DRUMS, PERC_MID, PERC_HI, BASS, GUITAR, ARPS]


def wait_beats(n):
    time.sleep(BEAT_DUR * n)

def ramp(bridge, path, args_fn, start, end, beats, steps_per_beat=6):
    num_steps = max(int(beats * steps_per_beat), 1)
    dt = (BEAT_DUR * beats) / num_steps
    for i in range(num_steps + 1):
        val = start + (end - start) * (i / num_steps)
        bridge.send(path, args_fn(val))
        if i < num_steps:
            time.sleep(dt)


def main():
    print("🌀 CIRCULAR BREATHING SESSION — 2 Rounds, 1.5 Minutes")
    print(f"   BPM: {BPM}")
    print("   Pattern: Breathe 30s → Hold 20s → Breathe 30s → Hold 20s → End")
    print()

    ab = AbletonOSCBridge()
    ab.connect()
    cx = ClyphXBridge()
    clyphx_ok = cx.connect()

    ab.send("/live/song/set/tempo", (BPM,))
    time.sleep(0.3)

    # ── Load effects ─────────────────────────────────────────────
    if clyphx_ok:
        print("   Loading effects...")
        cx.action_with_delay('8/LOADDEV "Saturator"', delay=0.6)
        cx.action_with_delay('12/LOADDEV "Auto Filter"', delay=0.6)
        cx.action_with_delay('12/LOADDEV "Reverb"', delay=0.6)
        cx.action_with_delay('13/LOADDEV "Auto Filter"', delay=0.6)
        cx.action_with_delay('15/LOADDEV "Reverb"', delay=0.6)
        cx.action_with_delay('15/LOADDEV "Chorus"', delay=0.6)
        cx.action_with_delay('9/LOADDEV "Saturator"', delay=0.6)
        cx.action_with_delay('14/LOADDEV "Reverb"', delay=0.6)
        time.sleep(0.5)
        print("   Effects loaded ✓")

    # ── Reset ────────────────────────────────────────────────────
    print("   Resetting mixer...")
    for t in ALL_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))
        ab.send("/live/track/set/volume", (t, 0.0))
    time.sleep(0.3)

    ab.send("/live/song/stop_playing", ())
    time.sleep(0.3)
    ab.send("/live/song/set/current_song_time", (0.0,))
    time.sleep(0.3)

    # ── Recording: use set property instead of toggle ────────────
    # set session_record directly rather than toggling
    ab.send("/live/song/set/session_record", (1,))
    time.sleep(0.5)

    print()
    print("▶  STARTING SESSION")
    print("=" * 60)

    ab.send("/live/song/start_playing", ())
    time.sleep(0.3)

    # Pad drone always present — foundation
    ab.send("/live/track/set/mute", (PADS, 0))
    ab.send("/live/clip/fire", (PADS, 9))  # pad drone 2
    ab.send("/live/track/set/volume", (PADS, 0.35))

    # ═══════════════════════════════════════════════════════════════
    #  ROUND 1 — BREATHE (0:00 – 0:30) — 45 beats
    #  Circular mouth fast breathing. Energy builds progressively.
    # ═══════════════════════════════════════════════════════════════
    print("🌀 [0:00] ROUND 1 BREATHE — Circular mouth fast (30 seconds)")

    # Breathing starts immediately
    ab.send("/live/track/set/mute", (BREATH, 0))
    ab.send("/live/clip/fire", (BREATH, 9))  # "circular mouth fast"
    ab.send("/live/track/set/volume", (BREATH, 0.45))

    # 0:00 — Kick enters immediately (festival energy)
    ab.send("/live/track/set/mute", (DRUMS, 0))
    ab.send("/live/clip/fire", (DRUMS, 22))  # "4 on the floor 1"
    ramp(ab, "/live/track/set/volume", lambda v: (DRUMS, float(v)), 0.0, 0.7, beats=4)

    # Shaker groove
    ab.send("/live/track/set/mute", (PERC_HI, 0))
    ab.send("/live/clip/fire", (PERC_HI, 10))  # "shaker groove"
    ab.send("/live/track/set/volume", (PERC_HI, 0.4))

    wait_beats(8)

    # 0:05 — Bass melody enters
    print("   [0:05] Bass groove enters")
    ab.send("/live/track/set/mute", (BASS, 0))
    ab.send("/live/clip/fire", (BASS, 8))  # "bass melody 1"
    ramp(ab, "/live/track/set/volume", lambda v: (BASS, float(v)), 0.0, 0.6, beats=4)

    wait_beats(6)

    # 0:10 — Switch to groove pattern + taiko
    print("   [0:10] Groove + taiko layer in")
    ab.send("/live/clip/fire", (DRUMS, 14))  # "groove 3"
    ab.send("/live/track/set/volume", (DRUMS, 0.75))

    ab.send("/live/track/set/mute", (PERC_MID, 0))
    ab.send("/live/clip/fire", (PERC_MID, 14))  # "taiko 1"
    ramp(ab, "/live/track/set/volume", lambda v: (PERC_MID, float(v)), 0.0, 0.5, beats=4)

    wait_beats(8)

    # 0:15 — Handpan enters
    print("   [0:15] Handpan melody soars")
    ab.send("/live/track/set/mute", (MELODY, 0))
    ab.send("/live/clip/fire", (MELODY, 8))  # "hand pan melody 1"
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.0, 0.75, beats=4)

    # Hihat perc for drive
    ab.send("/live/clip/fire", (PERC_HI, 16))  # "4 on the floor hihat perc"
    ab.send("/live/track/set/volume", (PERC_HI, 0.5))

    wait_beats(8)

    # 0:20 — Full energy, switch grooves
    print("   [0:20] Full energy build — groove 6, djembe")
    ab.send("/live/clip/fire", (DRUMS, 17))  # "groove 6"
    ab.send("/live/track/set/volume", (DRUMS, 0.8))

    ab.send("/live/clip/fire", (PERC_MID, 21))  # "djembe strike"
    ab.send("/live/track/set/volume", (PERC_MID, 0.6))

    ab.send("/live/track/set/volume", (BASS, 0.65))
    ab.send("/live/track/set/volume", (MELODY, 0.8))
    ab.send("/live/track/set/volume", (PADS, 0.4))

    wait_beats(8)

    # 0:25 — Peak of Round 1, guitar and epic pluck
    print("   [0:25] Round 1 peak — guitar + epic pluck")
    ab.send("/live/track/set/mute", (GUITAR, 0))
    ab.send("/live/clip/fire", (GUITAR, 8))  # "guitar acou strum 1"
    ramp(ab, "/live/track/set/volume", lambda v: (GUITAR, float(v)), 0.0, 0.4, beats=3)

    ab.send("/live/track/set/mute", (ARPS, 0))
    ab.send("/live/clip/fire", (ARPS, 18))  # "epic pluck"
    ramp(ab, "/live/track/set/volume", lambda v: (ARPS, float(v)), 0.0, 0.45, beats=3)

    ab.send("/live/track/set/volume", (DRUMS, 0.85))

    wait_beats(7)

    # ═══════════════════════════════════════════════════════════════
    #  ROUND 1 — HOLD (0:30 – 0:50) — 30 beats
    #  Everything drops. Deep inhale hold. Spaciousness.
    # ═══════════════════════════════════════════════════════════════
    print()
    print("💫 [0:30] ROUND 1 HOLD — Deep inhale hold (20 seconds)")

    # Mute all rhythm tracks
    for t in RHYTHM_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))

    # Melody fades over 4 beats then mutes
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.8, 0.0, beats=4)
    ab.send("/live/track/set/mute", (MELODY, 1))

    # Switch breathing to deep inhale hold
    ab.send("/live/clip/fire", (BREATH, 21))  # "deep inhale hold"
    ab.send("/live/track/set/volume", (BREATH, 0.55))

    # Pad expands
    ab.send("/live/track/set/volume", (PADS, 0.4))

    # Nature — sea sound for spaciousness
    ab.send("/live/track/set/mute", (NATURE, 0))
    ab.send("/live/clip/fire", (NATURE, 8))  # "sea"
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.0, 0.25, beats=6)

    wait_beats(27)

    # ═══════════════════════════════════════════════════════════════
    #  ROUND 2 — BREATHE (0:50 – 1:20) — 45 beats
    #  Circular mouth fast again. Comes back HARDER.
    #  Different clips for variation.
    # ═══════════════════════════════════════════════════════════════
    print()
    print("🌀 [0:50] ROUND 2 BREATHE — Circular mouth fast (30 seconds)")
    print("   Coming back HARDER")

    # Breathing resumes
    ab.send("/live/clip/fire", (BREATH, 9))  # "circular mouth fast"
    ab.send("/live/track/set/volume", (BREATH, 0.45))

    # Immediate kick — BAM (different groove this time)
    ab.send("/live/track/set/mute", (DRUMS, 0))
    ab.send("/live/clip/fire", (DRUMS, 15))  # "groove 4"
    ramp(ab, "/live/track/set/volume", lambda v: (DRUMS, float(v)), 0.0, 0.75, beats=3)

    # Bongo groove for different texture
    ab.send("/live/track/set/mute", (PERC_MID, 0))
    ab.send("/live/clip/fire", (PERC_MID, 10))  # "bongo 1"
    ramp(ab, "/live/track/set/volume", lambda v: (PERC_MID, float(v)), 0.0, 0.5, beats=4)

    # Shaker back
    ab.send("/live/track/set/mute", (PERC_HI, 0))
    ab.send("/live/clip/fire", (PERC_HI, 12))  # "shaker groove" (v2)
    ab.send("/live/track/set/volume", (PERC_HI, 0.45))

    # Fade out sea
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.25, 0.1, beats=4)

    wait_beats(6)

    # 0:55 — Bass melody 2 + handpan melody 3
    print("   [0:55] Bass + handpan re-enter")
    ab.send("/live/track/set/mute", (BASS, 0))
    ab.send("/live/clip/fire", (BASS, 9))  # "bass melody 2"
    ramp(ab, "/live/track/set/volume", lambda v: (BASS, float(v)), 0.0, 0.65, beats=4)

    ab.send("/live/track/set/mute", (MELODY, 0))
    ab.send("/live/clip/fire", (MELODY, 10))  # "hand pan melody 3"
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.0, 0.7, beats=4)

    wait_beats(6)

    # 1:00 — Switch to heavy groove
    print("   [1:00] Heavy groove — groove 7, tribal perc")
    ab.send("/live/clip/fire", (DRUMS, 18))  # "groove 7"
    ab.send("/live/track/set/volume", (DRUMS, 0.85))

    ab.send("/live/clip/fire", (PERC_MID, 9))  # "tribal 1"
    ab.send("/live/track/set/volume", (PERC_MID, 0.6))

    ab.send("/live/clip/fire", (PERC_HI, 16))  # "4 on the floor hihat perc"
    ab.send("/live/track/set/volume", (PERC_HI, 0.55))

    wait_beats(8)

    # 1:05 — Handpan melody 5 for new emotion
    print("   [1:05] Handpan melody 5 — emotional peak")
    ab.send("/live/clip/fire", (MELODY, 12))  # "hand pan melody 5"
    ab.send("/live/track/set/volume", (MELODY, 0.85))

    # Guitar strum
    ab.send("/live/track/set/mute", (GUITAR, 0))
    ab.send("/live/clip/fire", (GUITAR, 9))  # "guitar acou strum 2"
    ramp(ab, "/live/track/set/volume", lambda v: (GUITAR, float(v)), 0.0, 0.45, beats=3)

    wait_beats(8)

    # 1:10 — Absolute peak, everything at max
    print("   [1:10] ABSOLUTE PEAK — all layers screaming")
    ab.send("/live/track/set/mute", (ARPS, 0))
    ab.send("/live/clip/fire", (ARPS, 18))  # "epic pluck"
    ab.send("/live/track/set/volume", (ARPS, 0.5))

    ab.send("/live/track/set/volume", (DRUMS, 0.9))
    ab.send("/live/track/set/volume", (BASS, 0.7))
    ab.send("/live/track/set/volume", (PADS, 0.45))
    ab.send("/live/track/set/volume", (BREATH, 0.5))
    ab.send("/live/track/set/volume", (MELODY, 0.85))

    # Frame drum for maximum tribal energy
    ab.send("/live/clip/fire", (PERC_MID, 19))  # "frame drum"
    ab.send("/live/track/set/volume", (PERC_MID, 0.65))

    wait_beats(10)

    # ═══════════════════════════════════════════════════════════════
    #  ROUND 2 — HOLD (1:20 – 1:40) — 30 beats
    #  Everything drops again. Deeper surrender.
    # ═══════════════════════════════════════════════════════════════
    print()
    print("💫 [1:20] ROUND 2 HOLD — Deep inhale hold (20 seconds)")

    # Mute all rhythm
    for t in RHYTHM_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))

    # Handpan fades beautifully
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.85, 0.0, beats=6)
    ab.send("/live/track/set/mute", (MELODY, 1))

    # Deep inhale hold
    ab.send("/live/clip/fire", (BREATH, 21))  # "deep inhale hold"
    ab.send("/live/track/set/volume", (BREATH, 0.5))

    # Pad stays spacious
    ab.send("/live/track/set/volume", (PADS, 0.35))

    # Nature returns
    ab.send("/live/clip/fire", (NATURE, 10))  # "cave stream" — different from round 1
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.1, 0.2, beats=4)

    wait_beats(25)

    # ═══════════════════════════════════════════════════════════════
    #  OUTRO (1:40 – 1:50) — 15 beats
    #  Big exhale. Slow gentle fade to silence.
    # ═══════════════════════════════════════════════════════════════
    print()
    print("🌊 [1:40] OUTRO — Big exhale, slow fade to silence")

    # Big exhale
    ab.send("/live/clip/fire", (BREATH, 22))  # "big exhale"
    ab.send("/live/track/set/volume", (BREATH, 0.55))

    wait_beats(4)

    # Slow fade everything
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.35, 0.0, beats=10)
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.2, 0.0, beats=8)
    ramp(ab, "/live/track/set/volume", lambda v: (BREATH, float(v)), 0.55, 0.0, beats=6)

    wait_beats(4)

    # ── STOP ─────────────────────────────────────────────────────
    ab.send("/live/song/stop_playing", ())
    time.sleep(0.5)
    ab.send("/live/song/set/session_record", (0,))

    print()
    print("=" * 60)
    print("✅ Session complete!")
    print("   Duration: ~1:50")
    print("   Pattern: Breathe 30s → Hold 20s → Breathe 30s → Hold 20s → End")
    print("   Breathing: Circular mouth fast + deep inhale hold")

    ab.disconnect()


if __name__ == "__main__":
    main()
