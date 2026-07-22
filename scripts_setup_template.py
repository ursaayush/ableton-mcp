#!/usr/bin/env python3
"""Wim Hof template build — pure AbletonOSC, idempotent-ish."""
import socket
import threading
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient


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

    # ── 1. tempo
    print("→ tempo 90")
    osc.send("/live/song/set/tempo", (90.0,))
    time.sleep(0.2)

    # ── 2. audio tracks (8) — pure AbletonOSC
    audio_track_names = [
        "BREATH IN/OUT", "BREATH HOLD CUES",
        "DRUMS", "BASS", "MELODY", "PAD",
        "NATURE", "DRONE",
    ]
    n_before = osc.query("/live/song/get/num_tracks", timeout=2.0)
    base = n_before[0] if n_before else 4
    print(f"→ creating {len(audio_track_names)} audio tracks (existing main: {base})")
    for _ in audio_track_names:
        osc.send("/live/song/create_audio_track", (-1,))
        time.sleep(0.25)

    # ── 3. return tracks (2)
    print("→ creating 2 return tracks")
    osc.send("/live/song/create_return_track")
    time.sleep(0.4)
    osc.send("/live/song/create_return_track")
    time.sleep(0.4)

    # ── 4. rename audio tracks
    print("→ renaming audio tracks")
    for i, name in enumerate(audio_track_names):
        osc.send("/live/track/set/name", (base + i, name))
        time.sleep(0.05)

    # ── 5. rename return tracks
    print("→ renaming return tracks")
    osc.send("/live/return_track/set/name", (0, "Hall Reverb"))
    time.sleep(0.05)
    osc.send("/live/return_track/set/name", (1, "Tape Delay"))
    time.sleep(0.05)

    # ── 6. locators
    locators = [
        ("INTRO",         1),
        ("R1 BREATH-IN",  9),
        ("R1 BREATHS",    21),
        ("R1 RETENTION",  69),
        ("R1 RECOVERY",   105),
        ("R2 BREATH-IN",  111),
        ("R2 BREATHS",    123),
        ("R2 RETENTION",  171),
        ("R2 RECOVERY",   207),
        ("R3 BREATH-IN",  213),
        ("R3 BREATHS",    225),
        ("R3 RETENTION",  273),
        ("R3 RECOVERY",   309),
        ("OUTRO",         315),
    ]
    print(f"→ placing {len(locators)} locators")
    for _, bar in locators:
        beat = (bar - 1) * 4
        osc.send("/live/song/set/current_song_time", (float(beat),))
        time.sleep(0.25)
        osc.send("/live/song/set_or_delete_cue")
        time.sleep(0.35)

    # ── 7. rename locators (correct path: /live/song/cue_point/set/name)
    time.sleep(0.5)
    print("→ renaming locators")
    cues = osc.query("/live/song/get/cue_points", timeout=3.0)
    if cues:
        existing = []
        data = list(cues)
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                existing.append((str(data[i]), float(data[i + 1])))
        existing.sort(key=lambda x: x[1])
        print(f"   {len(existing)} cues found")
        for new_name, target_bar in locators:
            target_beat = (target_bar - 1) * 4.0
            for cue_idx, (_cur, cur_time) in enumerate(existing):
                if abs(cur_time - target_beat) < 0.5:
                    osc.send("/live/song/cue_point/set/name", (cue_idx, new_name))
                    time.sleep(0.06)
                    break
    else:
        print("   no cues to rename")

    # ── 8. transport home
    osc.send("/live/song/set/current_song_time", (0.0,))
    time.sleep(0.2)
    print("\n✅ DONE")
    print("Manual remaining (≈30s): ")
    print("  • Drag 'Reverb' onto 'Hall Reverb' return")
    print("  • Drag 'Delay' onto 'Tape Delay' return")
    print("  • Optional: select [BREATH groups] → Cmd+G to fold")


if __name__ == "__main__":
    main()
