#!/usr/bin/env python3
"""
build_template.py — Phase 4A: Template Builder

Discovers devices, sets EQ curves for frequency separation,
sets initial values, saves parameter map JSON.

EQ Frequency Separation:
  DRUMS:    low end owner (60-200Hz), cut mids 500Hz
  PERC_MID: low-mid to mid (200-2000Hz), cut low end
  PERC_HI:  high end (4-10kHz), cut everything below
  MELODY:   mid presence (400-1500Hz), cut below 300Hz
  GUITAR:   upper mid (2-5kHz), cut below 200Hz — sits above handpan
  PADS:     sub/low warmth only (40-400Hz), cut mids to avoid handpan clash
  BREATH:   natural range, slight high boost for clarity
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from ableton_mcp.osc_bridge import AbletonOSCBridge

TRACKS = {
    "NATURE":   5,
    "BREATH":   6,
    "DRUMS":    7,
    "PERC_MID": 8,
    "PERC_HI":  9,
    "GUITAR":   10,
    "MELODY":   11,
    "BASS":     12,
    "ARPS":     13,
    "PADS":     14,
}


def discover_devices(ab, track_index):
    dev_names = ab.query("/live/track/get/devices/name", (track_index,), timeout=3.0)
    if not dev_names:
        return []
    devices = []
    for dev_idx, dev_name in enumerate(str(n) for n in dev_names[1:]):
        names = ab.query("/live/device/get/parameters/name", (track_index, dev_idx), timeout=3.0)
        values = ab.query("/live/device/get/parameters/value", (track_index, dev_idx), timeout=3.0)
        mins = ab.query("/live/device/get/parameters/min", (track_index, dev_idx), timeout=3.0)
        maxs = ab.query("/live/device/get/parameters/max", (track_index, dev_idx), timeout=3.0)
        if not names:
            continue
        param_names = [str(p) for p in names[2:]]
        param_values = list(values[2:]) if values else []
        param_mins = list(mins[2:]) if mins else []
        param_maxs = list(maxs[2:]) if maxs else []
        params = {}
        for i, pname in enumerate(param_names):
            params[pname] = {
                "index": i,
                "value": param_values[i] if i < len(param_values) else None,
                "min": param_mins[i] if i < len(param_mins) else None,
                "max": param_maxs[i] if i < len(param_maxs) else None,
            }
        devices.append({"device_index": dev_idx, "device_name": dev_name, "params": params})
    return devices


def set_eq_param(ab, track_idx, dev_idx, params, param_name, value):
    """Set an EQ Eight parameter by name."""
    if param_name in params:
        ab.send("/live/device/set/parameter/value",
                (track_idx, dev_idx, params[param_name]["index"], float(value)))


def main():
    print("🔧 TEMPLATE BUILDER — Phase 4A")
    print("=" * 55)
    print()

    ab = AbletonOSCBridge()
    ab.connect()

    ab.send("/live/song/set/tempo", (90.0,))
    print("Step 1: Tempo → 90 BPM")
    print()

    # ── Discover devices ─────────────────────────────────────────
    print("Step 2: Discovering devices...")
    param_map = {"bpm": 90.0, "tracks": {}}

    for track_name, track_idx in TRACKS.items():
        devices = discover_devices(ab, track_idx)
        device_map = {}
        for dev in devices:
            dev_key = f"{dev['device_index']}_{dev['device_name']}"
            device_map[dev_key] = dev
            print(f"   {track_name:10s} → [{dev['device_index']}] {dev['device_name']}")
        param_map["tracks"][track_name] = {"track_index": track_idx, "devices": device_map}
    print()

    # ── EQ Frequency Separation ──────────────────────────────────
    print("Step 3: Setting EQ curves for frequency separation...")

    def get_eq(track_name):
        """Find EQ Eight device on a track."""
        track = param_map["tracks"].get(track_name, {})
        for dk, dd in track.get("devices", {}).items():
            if "EQ Eight" in dd["device_name"]:
                return track["track_index"], dd["device_index"], dd["params"]
        return None, None, None

    # DRUMS — owns the low end. High-pass off, low shelf boost at ~100Hz
    t, d, p = get_eq("DRUMS")
    if p:
        # Band 1: low shelf boost at low freq (kick body)
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Filter Type A", 2.0)  # low shelf
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.25)    # ~100Hz
        set_eq_param(ab, t, d, p, "1 Gain A", 2.0)          # slight boost
        # Band 3: cut mids to make room for handpan (500Hz area)
        set_eq_param(ab, t, d, p, "3 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "3 Frequency A", 0.42)    # ~500Hz
        set_eq_param(ab, t, d, p, "3 Gain A", -2.0)         # cut
        print("   DRUMS: low boost, mid cut (room for handpan)")

    # PERC_MID — mid focus. Cut lows, presence around 800-2k
    t, d, p = get_eq("PERC_MID")
    if p:
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Filter Type A", 5.0)   # high-pass
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.2)     # ~80Hz cut
        set_eq_param(ab, t, d, p, "1 Gain A", 0.0)
        set_eq_param(ab, t, d, p, "3 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "3 Frequency A", 0.55)    # ~1kHz
        set_eq_param(ab, t, d, p, "3 Gain A", 1.5)          # slight boost
        print("   PERC_MID: high-pass 80Hz, mid presence boost")

    # PERC_HI — high end sparkle. Cut everything below 2kHz
    t, d, p = get_eq("PERC_HI")
    if p:
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Filter Type A", 5.0)   # high-pass
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.35)    # ~250Hz
        set_eq_param(ab, t, d, p, "1 Gain A", 0.0)
        set_eq_param(ab, t, d, p, "4 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "4 Frequency A", 0.72)    # ~5kHz
        set_eq_param(ab, t, d, p, "4 Gain A", 2.0)          # high sparkle
        print("   PERC_HI: high-pass 250Hz, high sparkle boost")

    # MELODY (handpan) — mid presence 400-1500Hz. Cut sub, gentle high roll-off
    t, d, p = get_eq("MELODY")
    if p:
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Filter Type A", 5.0)   # high-pass
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.3)     # ~200Hz cut
        set_eq_param(ab, t, d, p, "1 Gain A", 0.0)
        set_eq_param(ab, t, d, p, "3 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "3 Frequency A", 0.5)     # ~800Hz
        set_eq_param(ab, t, d, p, "3 Gain A", 1.5)          # presence
        print("   MELODY: high-pass 200Hz, 800Hz presence (handpan sweet spot)")

    # GUITAR — upper mids 2-5kHz. Cut below 200Hz to avoid drum/pad clash
    t, d, p = get_eq("GUITAR")
    if p:
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Filter Type A", 5.0)   # high-pass
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.27)    # ~150Hz cut
        set_eq_param(ab, t, d, p, "1 Gain A", 0.0)
        set_eq_param(ab, t, d, p, "4 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "4 Frequency A", 0.62)    # ~2.5kHz
        set_eq_param(ab, t, d, p, "4 Gain A", 1.5)          # strum clarity above handpan
        print("   GUITAR: high-pass 150Hz, 2.5kHz clarity (above handpan)")

    # PADS — sub/low warmth ONLY. Aggressive mid cut so it doesn't fight handpan
    t, d, p = get_eq("PADS")
    if p:
        set_eq_param(ab, t, d, p, "1 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "1 Frequency A", 0.18)    # ~60Hz
        set_eq_param(ab, t, d, p, "1 Gain A", 1.5)          # sub warmth
        set_eq_param(ab, t, d, p, "3 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "3 Frequency A", 0.48)    # ~600Hz
        set_eq_param(ab, t, d, p, "3 Gain A", -3.0)         # aggressive mid cut
        set_eq_param(ab, t, d, p, "5 Filter On A", 1.0)
        set_eq_param(ab, t, d, p, "5 Filter Type A", 6.0)   # low-pass
        set_eq_param(ab, t, d, p, "5 Frequency A", 0.55)    # ~1kHz roll-off
        set_eq_param(ab, t, d, p, "5 Gain A", 0.0)
        print("   PADS: sub warmth, aggressive mid cut, low-pass 1kHz (bed only)")

    time.sleep(0.3)
    print()

    # ── Initial device values ────────────────────────────────────
    print("Step 4: Setting initial device values...")
    def find_set(track_name, dev_frag, param_name, value):
        track = param_map["tracks"].get(track_name, {})
        for dk, dd in track.get("devices", {}).items():
            if dev_frag.lower() in dd["device_name"].lower():
                if param_name in dd["params"]:
                    ab.send("/live/device/set/parameter/value",
                            (track["track_index"], dd["device_index"],
                             dd["params"][param_name]["index"], float(value)))
                    print(f"   {track_name}/{dd['device_name']}/{param_name} = {value}")
                    return

    find_set("MELODY", "Audio Effect Rack", "Macro 1", 30.0)
    find_set("DRUMS", "Glue Compressor", "Threshold", -10.0)
    find_set("DRUMS", "Glue Compressor", "Dry/Wet", 0.6)
    print()

    # ── Mute everything ──────────────────────────────────────────
    print("Step 5: Resetting mixer...")
    for track_name, track_idx in TRACKS.items():
        ab.send("/live/track/set/mute", (track_idx, 1))
        ab.send("/live/track/set/volume", (track_idx, 0.0))
    print("   All muted, zeroed")
    print()

    # ── Save ─────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(__file__), "session_param_map.json")
    with open(output_path, "w") as f:
        json.dump(param_map, f, indent=2, default=str)

    print(f"Step 6: Saved → session_param_map.json")
    print()
    print("=" * 55)
    print("✅ Template ready! Run: uv run python run_session.py")

    ab.disconnect()


if __name__ == "__main__":
    main()
