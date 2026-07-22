#!/usr/bin/env python3
"""Place a named locator at the start of every arrangement clip on track 3."""
import socket
import threading
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


VOICE_TRACK = 3


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


def main():
    osc = OSC()

    # 1. read clip start times on the voice track
    ct = osc.query("/live/track/get/arrangement_clips/start_time", (VOICE_TRACK,), timeout=3.0)
    starts = list(ct[1:]) if ct else []
    if not starts:
        print(f"no arrangement clips on track {VOICE_TRACK}")
        return
    print(f"→ found {len(starts)} clips on track {VOICE_TRACK}")

    # 2. ensure playback stopped (cleaner cue placement)
    osc.send("/live/song/stop_playing")
    time.sleep(0.2)

    # 3. read existing cues so we can skip any duplicates
    existing = osc.query("/live/song/get/cue_points", timeout=2.0)
    existing_times = set()
    if existing:
        d = list(existing)
        for i in range(0, len(d), 2):
            if i + 1 < len(d):
                existing_times.add(round(float(d[i + 1]), 1))
    if existing_times:
        print(f"   skipping {len(existing_times)} existing cue position(s)")

    # 4. place a cue at the start of each clip
    placed = []
    for i, t in enumerate(starts):
        beat = float(t)
        if round(beat, 1) in existing_times:
            print(f"   [{i:2}] beat {beat:.2f} already has cue — skipping")
            continue
        osc.send("/live/song/set/current_song_time", (beat,))
        time.sleep(0.30)
        osc.send("/live/song/set_or_delete_cue")
        time.sleep(0.40)
        placed.append((i, beat))
        print(f"   [{i:2}] cue placed @ beat {beat:.2f} (bar {beat/4 + 1:.1f})")

    # 5. read all cues and rename the new ones
    time.sleep(0.5)
    cues = osc.query("/live/song/get/cue_points", timeout=3.0)
    if not cues:
        print("no cues to rename")
        return
    pairs = list(cues)
    cue_list = []
    for i in range(0, len(pairs), 2):
        if i + 1 < len(pairs):
            cue_list.append((str(pairs[i]), float(pairs[i + 1])))
    cue_list.sort(key=lambda x: x[1])
    print(f"\n→ renaming {len(placed)} new cues (of {len(cue_list)} total)")
    for clip_idx, target_beat in placed:
        for cue_idx, (cur_name, cur_time) in enumerate(cue_list):
            if abs(cur_time - target_beat) < 0.5:
                new_name = f"Voice {clip_idx + 1:02d}"
                osc.send("/live/song/cue_point/set/name", (cue_idx, new_name))
                time.sleep(0.07)
                break

    # 6. transport home
    osc.send("/live/song/set/current_song_time", (0.0,))
    print(f"\n✅ DONE — {len(placed)} 'Voice NN' locators placed at clip-start positions on track {VOICE_TRACK}.")
    print("   Open Arrangement View — locators show as orange triangles in the timeline ruler.")
    print("   If any aren't actually voice, double-click the locator to rename or delete.")


if __name__ == "__main__":
    main()
