#!/usr/bin/env python3
"""
run_session.py — Emotion-first circular breathing session

Design philosophy:
  - Start with EMOTION (handpan + guitar), not drums
  - Breathing enters AFTER 5 seconds (double inhale slow)
  - Holds have handpan with reverb texture (audible, not silent)
  - Seamless transitions: breathe → deep inhale → big exhale → rest → repeat
  - Both rounds identical

Pattern: Breathe 30s → Hold 20s → Breathe 30s → Hold 20s → Outro 10s
"""

import json
import time
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ableton_mcp.osc_bridge import AbletonOSCBridge

BPM = 90.0
BEAT_DUR = 60.0 / BPM

BREATH   = 6
DRUMS    = 7
PERC_MID = 8
PERC_HI  = 9
GUITAR   = 10
MELODY   = 11
ARPS     = 13
PADS     = 14

ALL_TRACKS = [BREATH, DRUMS, PERC_MID, PERC_HI, GUITAR, MELODY, ARPS, PADS]
RHYTHM_TRACKS = [DRUMS, PERC_MID, PERC_HI]

T0 = 0.0

def sleep_until(t):
    r = (T0 + t) - time.time()
    if r > 0: time.sleep(r)

def ramp(ab, path, args_fn, start, end, dur):
    def _r():
        steps = max(int(dur * 10), 1)
        dt = dur / steps
        for i in range(steps + 1):
            v = start + (end - start) * (i / steps)
            ab.send(path, args_fn(v))
            if i < steps: time.sleep(dt)
    threading.Thread(target=_r, daemon=True).start()

def vol(ab, track, start, end, dur):
    ramp(ab, "/live/track/set/volume", lambda v: (track, float(v)), start, end, dur)

def dev(ab, t, d, p, start, end, dur):
    ramp(ab, "/live/device/set/parameter/value", lambda v: (t, d, p, float(v)), start, end, dur)


class DM:
    def __init__(self, m): self.m = m
    def find(self, tn, df, pn):
        t = self.m["tracks"].get(tn)
        if not t: return None
        for dk, dd in t["devices"].items():
            if df.lower() in dd["device_name"].lower():
                if pn in dd["params"]:
                    p = dd["params"][pn]
                    return (t["track_index"], dd["device_index"], p["index"])
        return None


def fmt(s):
    return f"{int(s)//60}:{int(s)%60:02d}"


def breathe_round(ab, t0, melody_eq, melody_rack, pads_eq, drums_comp):
    """
    30-second breathe phase.
    Starts with EMOTION (handpan + guitar), then breathing + drums build.
    """

    # ── t+0: EMOTION FIRST — Handpan + guitar + pad ─────────────
    # The user feels the music before they breathe
    ab.send("/live/track/set/mute", (MELODY, 0))
    ab.send("/live/clip/fire", (MELODY, 8))  # hand pan melody 1
    vol(ab, MELODY, 0.0, 0.5, 4.0)

    ab.send("/live/track/set/mute", (GUITAR, 0))
    ab.send("/live/clip/fire", (GUITAR, 8))  # guitar acou strum 1
    vol(ab, GUITAR, 0.0, 0.35, 4.0)

    ab.send("/live/track/set/volume", (PADS, 0.25))

    # 🎛️ EQ starts open for clear handpan entry, no filter needed
    if melody_eq: ab.send("/live/device/set/parameter/value", (*melody_eq, 0.6))
    if melody_rack: ab.send("/live/device/set/parameter/value", (*melody_rack, 30.0))

    sleep_until(t0 + 5)

    # ── t+5: BREATHING ENTERS — double inhale slow ──────────────
    print(f"   [{fmt(t0+5)}] 🫁 Double inhale slow enters")
    ab.send("/live/track/set/mute", (BREATH, 0))
    ab.send("/live/clip/fire", (BREATH, 14))  # double inhale slow
    vol(ab, BREATH, 0.0, 0.6, 4.0)

    # Light kick underneath
    ab.send("/live/track/set/mute", (DRUMS, 0))
    ab.send("/live/clip/fire", (DRUMS, 8))  # kick solo — just heartbeat
    vol(ab, DRUMS, 0.0, 0.4, 3.0)

    sleep_until(t0 + 12)

    # ── t+12: GROOVE BUILDS — groove 3 + shaker ─────────────────
    print(f"   [{fmt(t0+12)}] 🥁 Groove + shaker")
    ab.send("/live/clip/fire", (DRUMS, 14))  # groove 3
    vol(ab, DRUMS, 0.4, 0.55, 3.0)

    ab.send("/live/track/set/mute", (PERC_HI, 0))
    ab.send("/live/clip/fire", (PERC_HI, 10))  # shaker groove
    ab.send("/live/track/set/volume", (PERC_HI, 0.3))

    # 🎛️ Slow compressor push over rest of breathe
    if drums_comp: dev(ab, *drums_comp, -10.0, -18.0, 16.0)

    sleep_until(t0 + 18)

    # ── t+18: LAYERING — taiko + hihat ──────────────────────────
    print(f"   [{fmt(t0+18)}] Taiko + hihat layer")
    ab.send("/live/track/set/mute", (PERC_MID, 0))
    ab.send("/live/clip/fire", (PERC_MID, 14))  # taiko 1
    vol(ab, PERC_MID, 0.0, 0.35, 3.0)

    ab.send("/live/clip/fire", (PERC_HI, 16))  # hihat perc
    ab.send("/live/track/set/volume", (PERC_HI, 0.35))

    ab.send("/live/track/set/volume", (MELODY, 0.5))
    ab.send("/live/track/set/volume", (BREATH, 0.65))

    sleep_until(t0 + 24)

    # ── t+24: FULL ENERGY — djembe, peak ────────────────────────
    print(f"   [{fmt(t0+24)}] 🔥 Full energy peak")
    ab.send("/live/clip/fire", (PERC_MID, 21))  # djembe strike
    ab.send("/live/track/set/volume", (PERC_MID, 0.4))
    ab.send("/live/track/set/volume", (DRUMS, 0.6))
    ab.send("/live/track/set/volume", (PADS, 0.3))

    sleep_until(t0 + 30)


def hold_round(ab, t0, melody_eq, melody_rack, pads_eq):
    """
    20-second hold phase.
    Seamless transition: cut rhythm → deep inhale → exhale → rest.
    Handpan continues with reverb texture (audible, emotional).
    """

    # ── t+0: CUT RHYTHM — deep inhale hold ──────────────────────
    for t in RHYTHM_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))
    ab.send("/live/track/set/mute", (GUITAR, 1))

    # Deep inhale hold breathing
    ab.send("/live/clip/fire", (BREATH, 21))  # deep inhale hold
    ab.send("/live/track/set/volume", (BREATH, 0.7))

    # HANDPAN STAYS — but quieter and reverbed
    # Rack macro pushes high = heavy reverb wash, making it sound distant/spacious
    ab.send("/live/track/set/volume", (MELODY, 0.3))
    if melody_eq: dev(ab, *melody_eq, 0.6, 0.3, 6.0)   # EQ closes — muffled, dreamy
    if melody_rack: dev(ab, *melody_rack, 30.0, 100.0, 6.0)  # full reverb wash

    # Atmo pluck for shimmer texture
    ab.send("/live/track/set/mute", (ARPS, 0))
    ab.send("/live/clip/fire", (ARPS, 22))  # atmo pluck
    vol(ab, ARPS, 0.0, 0.2, 3.0)

    # Pad stays warm
    ab.send("/live/track/set/volume", (PADS, 0.28))
    if pads_eq: dev(ab, *pads_eq, 0.45, 0.3, 8.0)

    sleep_until(t0 + 8)

    # ── t+8: BIG EXHALE ─────────────────────────────────────────
    print(f"   [{fmt(t0+8)}] Big exhale — release")
    ab.send("/live/clip/fire", (BREATH, 22))  # big exhale
    ab.send("/live/track/set/volume", (BREATH, 0.6))

    # Handpan fades slowly
    vol(ab, MELODY, 0.3, 0.15, 5.0)

    sleep_until(t0 + 14)

    # ── t+14: REST — space before next round ─────────────────────
    print(f"   [{fmt(t0+14)}] Rest — settling")

    # Gentle nasal exhale for resting breath
    ab.send("/live/clip/fire", (BREATH, 25))  # nasal inhale + relaxed exhale
    ab.send("/live/track/set/volume", (BREATH, 0.4))

    # Everything very quiet
    vol(ab, MELODY, 0.15, 0.0, 4.0)
    vol(ab, ARPS, 0.2, 0.0, 4.0)
    ab.send("/live/track/set/volume", (PADS, 0.22))

    sleep_until(t0 + 20)

    # Clean up for next round
    ab.send("/live/track/set/mute", (MELODY, 1))
    ab.send("/live/track/set/mute", (ARPS, 1))

    # Reset devices for identical next round
    if melody_eq: ab.send("/live/device/set/parameter/value", (*melody_eq, 0.6))
    if melody_rack: ab.send("/live/device/set/parameter/value", (*melody_rack, 30.0))
    if drums_comp_g: ab.send("/live/device/set/parameter/value", (*drums_comp_g, -10.0))


# Global ref for drums_comp (used in hold cleanup)
drums_comp_g = None


def main():
    global T0, drums_comp_g

    map_path = os.path.join(os.path.dirname(__file__), "session_param_map.json")
    if not os.path.exists(map_path):
        print("❌ Run build_template.py first!")
        sys.exit(1)
    with open(map_path) as f:
        dm = DM(json.load(f))

    melody_eq   = dm.find("MELODY", "EQ Eight", "1 Frequency A")
    melody_rack = dm.find("MELODY", "Audio Effect Rack", "Macro 1")
    pads_eq     = dm.find("PADS",   "EQ Eight", "1 Frequency A")
    drums_comp  = dm.find("DRUMS",  "Glue Compressor", "Threshold")
    drums_comp_g = drums_comp

    print("🌀 EMOTION-FIRST BREATHING SESSION")
    print(f"   BPM: {BPM}  |  Target: 1:50")
    print("   Start with handpan + guitar, breathing enters after 5s")
    print("   Double inhale slow  |  Both rounds identical")
    print()

    ab = AbletonOSCBridge()
    ab.connect()

    # Reset
    for t in ALL_TRACKS:
        ab.send("/live/track/set/mute", (t, 1))
        ab.send("/live/track/set/volume", (t, 0.0))
    if melody_eq:   ab.send("/live/device/set/parameter/value", (*melody_eq, 0.6))
    if melody_rack: ab.send("/live/device/set/parameter/value", (*melody_rack, 30.0))
    if pads_eq:     ab.send("/live/device/set/parameter/value", (*pads_eq, 0.25))
    if drums_comp:  ab.send("/live/device/set/parameter/value", (*drums_comp, -10.0))
    time.sleep(0.3)

    ab.send("/live/song/stop_playing", ())
    time.sleep(0.2)
    ab.send("/live/song/set/current_song_time", (0.0,))
    time.sleep(0.2)

    print("▶  Press RECORD in Ableton now!")
    print("=" * 50)

    ab.send("/live/song/start_playing", ())
    T0 = time.time()

    # Pad drone — always on
    ab.send("/live/track/set/mute", (PADS, 0))
    ab.send("/live/clip/fire", (PADS, 9))
    ab.send("/live/track/set/volume", (PADS, 0.22))

    # ═══════════════ ROUND 1 BREATHE (0:00 - 0:30) ══════════════
    print("🌀 [0:00] ROUND 1 — BREATHE (30s)")
    print("   [0:00] ✨ Handpan + guitar enter first")
    breathe_round(ab, 0, melody_eq, melody_rack, pads_eq, drums_comp)

    # ═══════════════ ROUND 1 HOLD (0:30 - 0:50) ═════════════════
    print()
    print("💫 [0:30] ROUND 1 — HOLD (20s)")
    print("   [0:30] Deep inhale... hold...")
    hold_round(ab, 30, melody_eq, melody_rack, pads_eq)

    # ═══════════════ ROUND 2 BREATHE (0:50 - 1:20) ══════════════
    print()
    print("🌀 [0:50] ROUND 2 — BREATHE (30s) [identical]")
    print("   [0:50] ✨ Handpan + guitar enter first")
    breathe_round(ab, 50, melody_eq, melody_rack, pads_eq, drums_comp)

    # ═══════════════ ROUND 2 HOLD (1:20 - 1:40) ═════════════════
    print()
    print("💫 [1:20] ROUND 2 — HOLD (20s) [identical]")
    print("   [1:20] Deep inhale... hold...")
    hold_round(ab, 80, melody_eq, melody_rack, pads_eq)

    # ═══════════════ OUTRO (1:40 - 1:50) ═════════════════════════
    print()
    print("🌊 [1:40] OUTRO — final settling")

    # Very gentle nasal exhale continues from hold
    ab.send("/live/track/set/volume", (BREATH, 0.35))

    vol(ab, PADS, 0.22, 0.0, 9.0)
    vol(ab, BREATH, 0.35, 0.0, 7.0)
    if pads_eq: dev(ab, *pads_eq, 0.3, 0.08, 8.0)

    sleep_until(110)

    ab.send("/live/song/stop_playing", ())
    elapsed = time.time() - T0

    print()
    print("=" * 50)
    print(f"✅ Done! Actual duration: {int(elapsed)//60}:{int(elapsed)%60:02d}")

    ab.disconnect()


if __name__ == "__main__":
    main()
