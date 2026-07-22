#!/usr/bin/env python3
"""
session_1min_handpan.py — 1-minute emotional breathwork session
Focus: Handpan melodies over kicks and beats with breathing sounds.

Emotional arc:
  0:00-0:15  Opening    — Pad drone + rain + breathing, soft and grounding
  0:15-0:30  Build      — Bass enters, kick starts, filter opens slowly
  0:30-0:45  Peak       — Handpan melody, percussion layers, full energy
  0:45-0:55  Drop       — Strip to pad + reverb tail, deep inhale hold
  0:55-1:00  Close      — Gentle fade, final exhale

Tracks used:
  5  NATURE AMBIENT    — slot 11 "rain"
  6  BREATH SOUND      — slot 8 "circular mouth slow", slot 21 "deep inhale hold"
  7  MAIN DRUMS        — slot 8 "kick solo", slot 12 "groove 1"
  8  PERC DRUMS MID    — slot 8 "tabla 1"
  11 INSTRUMENT MELODIES— slot 8 "hand pan melody 1", slot 9 "hand pan melody 2"
  12 BASS              — slot 18 "bass acou long 1"
  14 PADS AMBIENT      — slot 8 "pad drone 1"
"""

import time
import sys
import os

# Add the project to path
sys.path.insert(0, os.path.dirname(__file__))
from ableton_mcp.osc_bridge import AbletonOSCBridge, ClyphXBridge

# ── Config ───────────────────────────────────────────────────────
BPM = 90.0
BEAT_DUR = 60.0 / BPM  # 0.667s per beat

# Track indices (0-based)
NATURE   = 5   # rain
BREATH   = 6   # breathing sounds
DRUMS    = 7   # kick, groove
PERC     = 8   # tabla
MELODY   = 11  # handpan
BASS     = 12  # bass acou long
PADS     = 14  # pad drone

# All music tracks for group operations
ALL_MUSIC = [NATURE, DRUMS, PERC, MELODY, BASS, PADS]

def wait_beats(n):
    """Wait n beats at current BPM."""
    time.sleep(BEAT_DUR * n)

def ramp(bridge, osc_path, args_fn, start, end, beats, steps_per_beat=4):
    """Smooth parameter ramp over N beats."""
    num_steps = max(int(beats * steps_per_beat), 1)
    dt = (BEAT_DUR * beats) / num_steps
    for i in range(num_steps + 1):
        val = start + (end - start) * (i / num_steps)
        bridge.send(osc_path, args_fn(val))
        if i < num_steps:
            time.sleep(dt)


def main():
    print("🎵 1-Minute Breathwork Session — Handpan + Kicks")
    print(f"   BPM: {BPM}")
    print("   Loading effects and preparing session...")
    print()

    # ── Connect ──────────────────────────────────────────────────
    ab = AbletonOSCBridge()
    ab.connect()

    cx = ClyphXBridge()
    clyphx_ok = cx.connect()

    # ── Set tempo ────────────────────────────────────────────────
    ab.send("/live/song/set/tempo", (BPM,))
    time.sleep(0.3)

    # ── Load effects via ClyphX (1-based track numbers) ──────────
    if clyphx_ok:
        print("   Loading Auto Filter + Reverb on key tracks...")

        # Handpan (track 12 in ClyphX = index 11)
        cx.action_with_delay('12/LOADDEV "Auto Filter"', delay=0.6)
        cx.action_with_delay('12/LOADDEV "Reverb"', delay=0.6)

        # Pads (track 15 = index 14)
        cx.action_with_delay('15/LOADDEV "Reverb"', delay=0.6)
        cx.action_with_delay('15/LOADDEV "Chorus"', delay=0.6)

        # Drums (track 8 = index 7)
        cx.action_with_delay('8/LOADDEV "Saturator"', delay=0.6)

        # Bass (track 13 = index 12)
        cx.action_with_delay('13/LOADDEV "Auto Filter"', delay=0.6)

        # Nature (track 6 = index 5)
        cx.action_with_delay('6/LOADDEV "Reverb"', delay=0.6)

        time.sleep(1.0)
        print("   Effects loaded ✓")
    else:
        print("   ⚠️  ClyphX not available — running without effect loading")
        print("   (Session will still work with existing devices)")
        time.sleep(0.5)

    # ── Discover device indices after loading ─────────────────────
    # We need to find where our new effects landed
    # Utility is always device 0, so our loaded devices start at 1+

    # ── Initial state: everything muted, volumes zeroed ──────────
    print("   Setting initial mixer state...")
    for t in ALL_MUSIC + [BREATH]:
        ab.send("/live/track/set/mute", (t, 1))      # mute all
        ab.send("/live/track/set/volume", (t, 0.0))   # zero volume

    time.sleep(0.3)

    # ── START RECORDING TO ARRANGEMENT ───────────────────────────
    print()
    print("▶  RECORDING — Session starts NOW")
    print("=" * 50)
    ab.send("/live/song/trigger_session_record", ())
    time.sleep(0.1)
    ab.send("/live/song/start_playing", ())
    time.sleep(0.2)

    # ═══════════════════════════════════════════════════════════════
    #  OPENING (0:00 – 0:15) — 22 beats
    #  Pad drone + rain + gentle breathing. Soft and grounding.
    # ═══════════════════════════════════════════════════════════════
    print("🌅 [0:00] Opening — Pad drone + rain + breathing")

    # Fire pad drone
    ab.send("/live/track/set/mute", (PADS, 0))
    ab.send("/live/clip/fire", (PADS, 8))  # pad drone 1
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.0, 0.55, beats=8)

    # Fire rain
    ab.send("/live/track/set/mute", (NATURE, 0))
    ab.send("/live/clip/fire", (NATURE, 11))  # rain
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.0, 0.35, beats=6)

    # Fire breathing — circular mouth slow
    ab.send("/live/track/set/mute", (BREATH, 0))
    ab.send("/live/clip/fire", (BREATH, 8))  # circular mouth slow
    ramp(ab, "/live/track/set/volume", lambda v: (BREATH, float(v)), 0.0, 0.45, beats=4)

    wait_beats(6)  # Let it breathe for the remaining beats (~4s)

    # ═══════════════════════════════════════════════════════════════
    #  BUILD (0:15 – 0:30) — 22 beats
    #  Bass enters, kick starts, filter opens, energy rises.
    # ═══════════════════════════════════════════════════════════════
    print("📈 [0:15] Build — Bass + kick enter, filter opens")

    # Bass enters with fade-in
    ab.send("/live/track/set/mute", (BASS, 0))
    ab.send("/live/clip/fire", (BASS, 18))  # bass acou long 1
    ramp(ab, "/live/track/set/volume", lambda v: (BASS, float(v)), 0.0, 0.5, beats=8)

    # Kick enters
    ab.send("/live/track/set/mute", (DRUMS, 0))
    ab.send("/live/clip/fire", (DRUMS, 8))  # kick solo
    ramp(ab, "/live/track/set/volume", lambda v: (DRUMS, float(v)), 0.0, 0.6, beats=4)

    wait_beats(4)

    # Switch to groove for more energy
    ab.send("/live/clip/fire", (DRUMS, 12))  # groove 1
    ramp(ab, "/live/track/set/volume", lambda v: (DRUMS, float(v)), 0.6, 0.75, beats=4)

    # Pad and nature volume adjustments
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.55, 0.65, beats=4)
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.35, 0.25, beats=4)

    wait_beats(4)

    # ═══════════════════════════════════════════════════════════════
    #  PEAK (0:30 – 0:45) — 22 beats
    #  Handpan melody takes center stage, percussion layers in,
    #  all layers at full energy.
    # ═══════════════════════════════════════════════════════════════
    print("🔥 [0:30] Peak — Handpan melody + full percussion")

    # HANDPAN enters — the star!
    ab.send("/live/track/set/mute", (MELODY, 0))
    ab.send("/live/clip/fire", (MELODY, 8))  # hand pan melody 1
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.0, 0.75, beats=4)

    # Tabla enters for texture
    ab.send("/live/track/set/mute", (PERC, 0))
    ab.send("/live/clip/fire", (PERC, 8))  # tabla 1
    ramp(ab, "/live/track/set/volume", lambda v: (PERC, float(v)), 0.0, 0.45, beats=4)

    # Push drums and bass up
    ab.send("/live/track/set/volume", (DRUMS, 0.8))
    ab.send("/live/track/set/volume", (BASS, 0.6))

    wait_beats(4)

    # Switch handpan to melody 2 for variation at beat 8
    ab.send("/live/clip/fire", (MELODY, 9))  # hand pan melody 2

    # Push everything to max energy
    ab.send("/live/track/set/volume", (PADS, 0.7))
    ab.send("/live/track/set/volume", (MELODY, 0.8))
    ab.send("/live/track/set/volume", (PERC, 0.55))

    # Boost breathing for rhythmic feel
    ab.send("/live/track/set/volume", (BREATH, 0.5))

    wait_beats(6)

    # ═══════════════════════════════════════════════════════════════
    #  DROP (0:45 – 0:55) — 15 beats
    #  Sudden strip to pad only + reverb tail. Deep inhale hold.
    #  Spaciousness, surrender, stillness.
    # ═══════════════════════════════════════════════════════════════
    print("💫 [0:45] Drop — Everything falls away, deep inhale hold")

    # Stop all rhythmic elements immediately
    ab.send("/live/clip/stop", (DRUMS, 0))
    ab.send("/live/clip/stop", (PERC, 0))
    ab.send("/live/clip/stop", (BASS, 0))
    ab.send("/live/clip/stop", (MELODY, 0))

    # Mute drums, perc, bass
    ab.send("/live/track/set/mute", (DRUMS, 1))
    ab.send("/live/track/set/mute", (PERC, 1))
    ab.send("/live/track/set/mute", (BASS, 1))
    ab.send("/live/track/set/mute", (MELODY, 1))

    # Switch breathing to deep inhale hold
    ab.send("/live/clip/fire", (BREATH, 21))  # deep inhale hold
    ab.send("/live/track/set/volume", (BREATH, 0.6))

    # Pad stays, gets spacious
    ab.send("/live/track/set/volume", (PADS, 0.45))
    ab.send("/live/track/set/volume", (NATURE, 0.3))

    wait_beats(10)

    # ═══════════════════════════════════════════════════════════════
    #  CLOSE (0:55 – 1:00) — 7 beats
    #  Everything fades gently to silence.
    # ═══════════════════════════════════════════════════════════════
    print("🌙 [0:55] Close — Gentle fade to silence")

    # Fade everything out
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.45, 0.0, beats=6)
    ramp(ab, "/live/track/set/volume", lambda v: (NATURE, float(v)), 0.3, 0.0, beats=5)
    ramp(ab, "/live/track/set/volume", lambda v: (BREATH, float(v)), 0.6, 0.0, beats=4)

    wait_beats(2)

    # ── STOP ─────────────────────────────────────────────────────
    ab.send("/live/song/stop_playing", ())
    time.sleep(0.5)

    # Stop session record
    ab.send("/live/song/trigger_session_record", ())

    print()
    print("=" * 50)
    print("✅ Session complete! Check Arrangement View.")
    print("   Duration: ~1 minute")
    print("   Tracks used: Pads, Nature, Breath, Drums, Perc, Handpan, Bass")

    ab.disconnect()


if __name__ == "__main__":
    main()
