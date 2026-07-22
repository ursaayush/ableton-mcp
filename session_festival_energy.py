#!/usr/bin/env python3
"""
session_festival_energy.py — 1-minute ENERGETIC festival breathwork session

Vibe: Festival stage, tribal drums, driving grooves, soaring handpan, raw energy.
Think Burning Man sunrise ceremony meets ecstatic dance.

Emotional arc:
  0:00-0:10  Ignition     — 4-on-floor kick + shaker hit immediately, bass groove enters
  0:10-0:20  Tribal Build  — Taiko + djembe layer in, bass melody drives, energy surges
  0:20-0:35  Full Fire     — Handpan melody soars, tribal percussion stacks, groove 6/7
  0:35-0:45  Peak Frenzy   — All layers maxed, breath of fire fast, epic pluck accent
  0:45-0:53  The Drop      — Everything cuts — just pad drone + deep inhale hold
  0:53-1:00  Exhale Out    — Gentle fade, big exhale, silence

Tracks used:
  5  NATURE AMBIENT      — slot 8 "sea" (subtle background texture)
  6  BREATH SOUND        — slot 18 "breath of fire fast", slot 21 "deep inhale hold", slot 22 "big exhale"
  7  MAIN DRUMS          — slot 22 "4 on the floor 1", slot 14 "groove 3", slot 17 "groove 6"
  8  PERC DRUMS MID      — slot 14 "taiko 1", slot 21 "djembe strike", slot 17 "drum break"
  9  PERC DRUMS HIGH     — slot 10 "shaker groove", slot 16 "4 on the floor hihat perc"
  10 GUITAR ACOU CHORDS  — slot 8 "guitar acou strum 1"
  11 INSTRUMENT MELODIES — slot 8 "hand pan melody 1", slot 10 "hand pan melody 3"
  12 BASS                — slot 8 "bass melody 1", slot 9 "bass melody 2"
  13 ARPS & MELODIES     — slot 18 "epic pluck"
  14 PADS AMBIENT        — slot 9 "pad drone 2"
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ableton_mcp.osc_bridge import AbletonOSCBridge, ClyphXBridge

# ── Config ───────────────────────────────────────────────────────
BPM = 90.0
BEAT_DUR = 60.0 / BPM

# Track indices (0-based)
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
    print("🔥 ENERGETIC FESTIVAL SESSION — 1 Minute")
    print(f"   BPM: {BPM}")
    print()

    ab = AbletonOSCBridge()
    ab.connect()
    cx = ClyphXBridge()
    clyphx_ok = cx.connect()

    # ── Set tempo ────────────────────────────────────────────────
    ab.send("/live/song/set/tempo", (BPM,))
    time.sleep(0.3)

    # ── Load effects ─────────────────────────────────────────────
    if clyphx_ok:
        print("   Loading effects...")
        cx.action_with_delay('8/LOADDEV "Saturator"', delay=0.6)    # Drums — warm punch
        cx.action_with_delay('12/LOADDEV "Auto Filter"', delay=0.6) # Handpan — filter sweep
        cx.action_with_delay('12/LOADDEV "Reverb"', delay=0.6)      # Handpan — space
        cx.action_with_delay('13/LOADDEV "Auto Filter"', delay=0.6) # Bass — filter
        cx.action_with_delay('15/LOADDEV "Reverb"', delay=0.6)      # Pads — depth
        cx.action_with_delay('9/LOADDEV "Saturator"', delay=0.6)    # Perc mid — drive
        cx.action_with_delay('14/LOADDEV "Reverb"', delay=0.6)      # Arps — shimmer
        time.sleep(0.5)
        print("   Effects loaded ✓")
    else:
        print("   ⚠️  ClyphX not available, skipping effects")

    # ── Reset: mute everything, zero volumes ─────────────────────
    print("   Resetting mixer...")
    for t in ALL_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))
        ab.send("/live/track/set/volume", (t, 0.0))
    time.sleep(0.3)

    # ── Ensure Ableton is stopped & at start ─────────────────────
    ab.send("/live/song/stop_playing", ())
    time.sleep(0.3)
    ab.send("/live/song/set/current_song_time", (0.0,))
    time.sleep(0.3)

    # ── START ────────────────────────────────────────────────────
    print()
    print("▶  STARTING — Recording to Arrangement")
    print("=" * 55)

    # Trigger session record FIRST, then wait, then play
    ab.send("/live/song/trigger_session_record", ())
    time.sleep(0.5)
    ab.send("/live/song/start_playing", ())
    time.sleep(0.3)

    # ═══════════════════════════════════════════════════════════════
    #  IGNITION (0:00 – 0:10) — 15 beats
    #  BAM. 4-on-floor kick hits immediately. Festival energy.
    #  Shaker groove rides on top. Bass groove enters.
    # ═══════════════════════════════════════════════════════════════
    print("⚡ [0:00] IGNITION — 4-on-floor kick + shaker + bass groove")

    # KICK — immediate hit at festival volume
    ab.send("/live/track/set/mute", (DRUMS, 0))
    ab.send("/live/track/set/volume", (DRUMS, 0.7))
    ab.send("/live/clip/fire", (DRUMS, 22))  # "4 on the floor 1"

    # SHAKER — rhythmic texture on top
    ab.send("/live/track/set/mute", (PERC_HI, 0))
    ab.send("/live/track/set/volume", (PERC_HI, 0.4))
    ab.send("/live/clip/fire", (PERC_HI, 10))  # "shaker groove"

    # PAD (subtle) — foundation underneath
    ab.send("/live/track/set/mute", (PADS, 0))
    ab.send("/live/clip/fire", (PADS, 9))  # "pad drone 2"
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.0, 0.3, beats=4)

    wait_beats(4)

    # BASS enters — melodic groove
    ab.send("/live/track/set/mute", (BASS, 0))
    ab.send("/live/clip/fire", (BASS, 8))  # "bass melody 1"
    ramp(ab, "/live/track/set/volume", lambda v: (BASS, float(v)), 0.0, 0.6, beats=4)

    # Breath of fire — fast rhythmic breathing, festival energy
    ab.send("/live/track/set/mute", (BREATH, 0))
    ab.send("/live/clip/fire", (BREATH, 18))  # "breath of fire fast"
    ab.send("/live/track/set/volume", (BREATH, 0.35))

    wait_beats(6)

    # ═══════════════════════════════════════════════════════════════
    #  TRIBAL BUILD (0:10 – 0:20) — 15 beats
    #  Taiko + djembe smash in. Drums switch to groove. Intensity ↑↑
    # ═══════════════════════════════════════════════════════════════
    print("🥁 [0:10] TRIBAL BUILD — Taiko + djembe + groove switch")

    # Switch drums to a groove
    ab.send("/live/clip/fire", (DRUMS, 14))  # "groove 3"
    ab.send("/live/track/set/volume", (DRUMS, 0.75))

    # TAIKO — power hits
    ab.send("/live/track/set/mute", (PERC_MID, 0))
    ab.send("/live/clip/fire", (PERC_MID, 14))  # "taiko 1"
    ramp(ab, "/live/track/set/volume", lambda v: (PERC_MID, float(v)), 0.0, 0.55, beats=4)

    wait_beats(4)

    # Add hihat perc for festival drive
    ab.send("/live/clip/fire", (PERC_HI, 16))  # "4 on the floor hihat perc"
    ab.send("/live/track/set/volume", (PERC_HI, 0.5))

    # Bass switches to melody 2 for variation
    ab.send("/live/clip/fire", (BASS, 9))  # "bass melody 2"
    ab.send("/live/track/set/volume", (BASS, 0.65))

    # Sea ambience for depth (quiet)
    ab.send("/live/track/set/mute", (NATURE, 0))
    ab.send("/live/clip/fire", (NATURE, 8))  # "sea"
    ab.send("/live/track/set/volume", (NATURE, 0.15))

    wait_beats(7)

    # ═══════════════════════════════════════════════════════════════
    #  FULL FIRE (0:20 – 0:35) — 22 beats
    #  Handpan melody SOARS over everything. Guitar strums.
    #  Percussion stacks high. This is the moment.
    # ═══════════════════════════════════════════════════════════════
    print("🔥 [0:20] FULL FIRE — Handpan soars, percussion stacks")

    # HANDPAN enters triumphantly
    ab.send("/live/track/set/mute", (MELODY, 0))
    ab.send("/live/clip/fire", (MELODY, 8))  # "hand pan melody 1"
    ramp(ab, "/live/track/set/volume", lambda v: (MELODY, float(v)), 0.0, 0.8, beats=4)

    # Guitar strum for harmonic richness
    ab.send("/live/track/set/mute", (GUITAR, 0))
    ab.send("/live/clip/fire", (GUITAR, 8))  # "guitar acou strum 1"
    ramp(ab, "/live/track/set/volume", lambda v: (GUITAR, float(v)), 0.0, 0.4, beats=4)

    # Switch perc to djembe
    ab.send("/live/clip/fire", (PERC_MID, 21))  # "djembe strike"
    ab.send("/live/track/set/volume", (PERC_MID, 0.6))

    # Drums to groove 6 — heavier
    ab.send("/live/clip/fire", (DRUMS, 17))  # "groove 6"
    ab.send("/live/track/set/volume", (DRUMS, 0.8))

    wait_beats(8)

    # Switch handpan to melody 3 for emotional lift
    ab.send("/live/clip/fire", (MELODY, 10))  # "hand pan melody 3"

    # Add drum break for intensity
    ab.send("/live/clip/fire", (PERC_MID, 17))  # "drum break"
    ab.send("/live/track/set/volume", (PERC_MID, 0.65))

    # Push everything up
    ab.send("/live/track/set/volume", (BASS, 0.7))
    ab.send("/live/track/set/volume", (PADS, 0.4))
    ab.send("/live/track/set/volume", (BREATH, 0.4))

    wait_beats(6)

    # ═══════════════════════════════════════════════════════════════
    #  PEAK FRENZY (0:35 – 0:45) — 15 beats
    #  EVERYTHING at max. Epic pluck accent. Groove 7. Tribal.
    #  This is the ecstatic moment.
    # ═══════════════════════════════════════════════════════════════
    print("💥 [0:35] PEAK FRENZY — All layers maxed, ecstatic climax")

    # EPIC PLUCK — accent layer
    ab.send("/live/track/set/mute", (ARPS, 0))
    ab.send("/live/clip/fire", (ARPS, 18))  # "epic pluck"
    ramp(ab, "/live/track/set/volume", lambda v: (ARPS, float(v)), 0.0, 0.55, beats=3)

    # Groove 7 — heaviest
    ab.send("/live/clip/fire", (DRUMS, 18))  # "groove 7"
    ab.send("/live/track/set/volume", (DRUMS, 0.85))

    # Tribal percussion switch
    ab.send("/live/clip/fire", (PERC_MID, 9))  # "tribal 1"
    ab.send("/live/track/set/volume", (PERC_MID, 0.65))

    # Max out shaker
    ab.send("/live/track/set/volume", (PERC_HI, 0.55))

    # Push handpan to full
    ab.send("/live/track/set/volume", (MELODY, 0.85))

    # Guitar and bass at peak
    ab.send("/live/track/set/volume", (GUITAR, 0.5))
    ab.send("/live/track/set/volume", (BASS, 0.75))

    wait_beats(12)

    # ═══════════════════════════════════════════════════════════════
    #  THE DROP (0:45 – 0:53) — 12 beats
    #  Everything CUTS. Just pad drone + deep inhale hold.
    #  Dramatic silence after the storm.
    # ═══════════════════════════════════════════════════════════════
    print("💫 [0:45] THE DROP — Silence after the storm")

    # Stop everything abruptly
    for t in [DRUMS, PERC_MID, PERC_HI, BASS, MELODY, GUITAR, ARPS, NATURE]:
        ab.send("/live/track/set/mute", (t, 1))

    # Switch breathing to deep inhale hold
    ab.send("/live/clip/fire", (BREATH, 21))  # "deep inhale hold"
    ab.send("/live/track/set/volume", (BREATH, 0.55))

    # Pad stays — spacious
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.4, 0.35, beats=4)

    wait_beats(10)

    # ═══════════════════════════════════════════════════════════════
    #  EXHALE OUT (0:53 – 1:00) — 10 beats
    #  Big exhale. Everything fades to silence.
    # ═══════════════════════════════════════════════════════════════
    print("🌊 [0:53] EXHALE OUT — Big exhale, fade to silence")

    # Big exhale
    ab.send("/live/clip/fire", (BREATH, 22))  # "big exhale"
    ab.send("/live/track/set/volume", (BREATH, 0.6))

    # Fade pad + breath to nothing
    ramp(ab, "/live/track/set/volume", lambda v: (PADS, float(v)), 0.35, 0.0, beats=8)
    ramp(ab, "/live/track/set/volume", lambda v: (BREATH, float(v)), 0.6, 0.0, beats=6)

    wait_beats(3)

    # ── STOP ─────────────────────────────────────────────────────
    ab.send("/live/song/stop_playing", ())
    time.sleep(0.5)
    ab.send("/live/song/trigger_session_record", ())  # toggle off

    print()
    print("=" * 55)
    print("✅ Session complete!")
    print("   Check Arrangement View for the recorded session.")
    print("   Tracks: Kick, Groove, Taiko, Djembe, Shaker, Handpan,")
    print("           Bass, Guitar, Epic Pluck, Pad, Breath of Fire")

    ab.disconnect()


if __name__ == "__main__":
    main()
