#!/usr/bin/env python3
"""
Arrangement-Record demo: ride three parameters in parallel while looping
bars 21-37, baking three drawn-automation envelopes into the arrangement.

Rides (over 16 bars at 122 BPM ≈ 31.5s):
  • track 13 MELODIES ORGANIC   volume   0.85 → 0.40 → 0.85   (V-duck)
  • track  8 perc high          pan       0  → -0.5 → +0.5 → 0  (sweep)
  • track 19 BREATHING SOUNDS   volume   0.80 → 0.30          (linear fade)

After it runs, right-click each track header → Show Volume/Pan Automation
to see the envelopes that were just drawn.
"""
import socket
import threading
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


BPM = 122.0
BEAT = 60.0 / BPM
LOOP_START_BEAT = 80.0     # bar 21
LOOP_BARS = 16
TOTAL_BEATS = LOOP_BARS * 4
STEPS_PER_BAR = 8
TOTAL_STEPS = LOOP_BARS * STEPS_PER_BAR


class OSC:
    def __init__(self):
        self.client = SimpleUDPClient("127.0.0.1", 11000)
        self._reply = {}
        d = Dispatcher()
        d.set_default_handler(self._on)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", 11001))
        self.srv = ThreadingOSCUDPServer(("0.0.0.0", 11001), d, bind_and_activate=False)
        self.srv.socket = sock
        self.srv.server_activate()
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def _on(self, addr, *p):
        self._reply[addr] = p

    def send(self, addr, p=()):
        self.client.send_message(addr, list(p) if p else [])

    def query(self, addr, params=(), timeout=2.0):
        self._reply.pop(addr, None)
        self.send(addr, params)
        end = time.time() + timeout
        while time.time() < end:
            if addr in self._reply:
                return self._reply[addr]
            time.sleep(0.02)
        return None


def lerp(a, b, t):
    return a + (b - a) * t


def main():
    osc = OSC()

    # ── cache current state ────────────────────────────────────────────
    print("→ caching current state")
    cache = {
        "vol_13": osc.query("/live/track/get/volume", (13,))[1] if osc.query("/live/track/get/volume", (13,)) else 0.85,
        "pan_8":  osc.query("/live/track/get/panning", (8,))[1] if osc.query("/live/track/get/panning", (8,)) else 0.0,
        "vol_19": osc.query("/live/track/get/volume", (19,))[1] if osc.query("/live/track/get/volume", (19,)) else 0.85,
        "loop_start": osc.query("/live/song/get/loop_start")[0] if osc.query("/live/song/get/loop_start") else 0.0,
        "loop_length": osc.query("/live/song/get/loop_length")[0] if osc.query("/live/song/get/loop_length") else 4.0,
        "loop_enabled": osc.query("/live/song/get/loop")[0] if osc.query("/live/song/get/loop") else 0,
        "record_mode": osc.query("/live/song/get/record_mode")[0] if osc.query("/live/song/get/record_mode") else 0,
    }
    print(f"   cached: {cache}")

    # ── set up arrangement loop & playhead ─────────────────────────────
    print(f"→ loop bars 21-37 (beats {LOOP_START_BEAT}–{LOOP_START_BEAT+TOTAL_BEATS})")
    osc.send("/live/song/set/loop_start", (LOOP_START_BEAT,))
    osc.send("/live/song/set/loop_length", (float(TOTAL_BEATS),))
    osc.send("/live/song/set/loop", (1,))
    time.sleep(0.2)

    print(f"→ playhead → beat {LOOP_START_BEAT}")
    osc.send("/live/song/set/current_song_time", (LOOP_START_BEAT,))
    time.sleep(0.2)

    # ── arm arrangement record ────────────────────────────────────────
    print("→ arming Arrangement Record")
    osc.send("/live/song/set/record_mode", (1,))
    time.sleep(0.3)

    # ── start playback ────────────────────────────────────────────────
    print("→ START playback")
    osc.send("/live/song/start_playing")
    time.sleep(0.5)  # let transport settle

    # ── ride parameters over 16 bars ──────────────────────────────────
    dt = (TOTAL_BEATS * BEAT) / TOTAL_STEPS
    print(f"→ riding 3 params for {LOOP_BARS} bars ({TOTAL_BEATS*BEAT:.1f}s, {TOTAL_STEPS} steps, {dt*1000:.0f}ms each)")

    for step in range(TOTAL_STEPS + 1):
        t = step / TOTAL_STEPS  # 0..1

        # MELODIES ORGANIC volume V-duck (0.85 → 0.40 → 0.85)
        if t <= 0.5:
            vol_13 = lerp(0.85, 0.40, t * 2)
        else:
            vol_13 = lerp(0.40, 0.85, (t - 0.5) * 2)
        osc.send("/live/track/set/volume", (13, float(vol_13)))

        # perc high pan: 0 → -0.5 (4 bars) → +0.5 (8 bars) → 0 (4 bars)
        if t <= 0.25:
            pan_8 = lerp(0.0, -0.5, t * 4)
        elif t <= 0.75:
            pan_8 = lerp(-0.5, 0.5, (t - 0.25) * 2)
        else:
            pan_8 = lerp(0.5, 0.0, (t - 0.75) * 4)
        osc.send("/live/track/set/panning", (8, float(pan_8)))

        # BREATHING SOUNDS volume linear fade 0.80 → 0.30
        vol_19 = lerp(0.80, 0.30, t)
        osc.send("/live/track/set/volume", (19, float(vol_19)))

        if step % (STEPS_PER_BAR * 4) == 0:  # every 4 bars
            print(f"   bar {LOOP_START_BEAT/4 + 1 + (t*LOOP_BARS):.0f} | vol13={vol_13:.2f} pan8={pan_8:+.2f} vol19={vol_19:.2f}")

        if step < TOTAL_STEPS:
            time.sleep(dt)

    # ── stop & disarm ────────────────────────────────────────────────
    print("→ STOP playback")
    osc.send("/live/song/stop_playing")
    time.sleep(0.3)

    print("→ disarming Arrangement Record")
    osc.send("/live/song/set/record_mode", (int(cache["record_mode"]),))
    time.sleep(0.2)

    # ── restore live overrides ────────────────────────────────────────
    print("→ restoring live state (recorded automation stays in arrangement)")
    osc.send("/live/track/set/volume", (13, float(cache["vol_13"])))
    osc.send("/live/track/set/panning", (8, float(cache["pan_8"])))
    osc.send("/live/track/set/volume", (19, float(cache["vol_19"])))
    osc.send("/live/song/set/loop_start", (cache["loop_start"],))
    osc.send("/live/song/set/loop_length", (cache["loop_length"],))
    osc.send("/live/song/set/loop", (int(cache["loop_enabled"]),))
    osc.send("/live/song/set/current_song_time", (0.0,))
    time.sleep(0.3)

    print("\n✅ DONE")
    print("Right-click these track headers → 'Show Volume/Pan Automation' to see the envelopes:")
    print("  • track 13 (MELODIES ORGANIC) → Volume   — V-shaped duck, bars 21-37")
    print("  • track  8 (perc high)        → Panning  — L-R sweep, bars 21-37")
    print("  • track 19 (BREATHING SOUNDS) → Volume   — linear fade, bars 21-37")
    print("Don't like it? Cmd+Z removes the recording.")


if __name__ == "__main__":
    main()
