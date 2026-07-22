#!/usr/bin/env python3
"""Festival loop — fire-and-forget OSC only, no blocking queries."""
from pythonosc.udp_client import SimpleUDPClient
import time, random, struct

random.seed(7)

# Two clients: AbletonOSC on 11000, ClyphX on 7005
osc = SimpleUDPClient("127.0.0.1", 11000)
cx = SimpleUDPClient("127.0.0.1", 7005)

def note(track, clip, pitch, start, dur, vel):
    osc.send_message("/live/clip/add/notes", [track, clip, pitch, start, dur, vel, 0])

print("Stopping...")
osc.send_message("/live/song/stop_playing", [])
time.sleep(0.3)

print("Setting 128 BPM...")
osc.send_message("/live/song/set/tempo", [128.0])
time.sleep(0.2)

# Mute pad track, unmute others
osc.send_message("/live/track/set/mute", [0, 1])
osc.send_message("/live/track/set/mute", [1, 0])
osc.send_message("/live/track/set/mute", [2, 0])
osc.send_message("/live/track/set/mute", [3, 0])

# Mute all audio
for i in range(4, 27):
    osc.send_message("/live/track/set/mute", [i, 1])

# Volumes
osc.send_message("/live/track/set/volume", [0, 0.5])
osc.send_message("/live/track/set/volume", [1, 0.5])
osc.send_message("/live/track/set/volume", [2, 0.8])
osc.send_message("/live/track/set/volume", [3, 0.65])

# Delete existing clips and recreate
BARS = 8
CLIP_LEN = float(BARS * 4)

for t in range(4):
    try:
        osc.send_message("/live/clip_slot/delete_clip", [t, 0])
        time.sleep(0.15)
    except:
        pass
    osc.send_message("/live/clip_slot/create_clip", [t, 0, CLIP_LEN])
    time.sleep(0.15)

def h(beat, amt=0.015):
    return round(beat + random.uniform(-amt, amt), 4)

# ================================================================
# TRACK 2: DRUMS — kick, clap, hi-hats, rolls
# ================================================================
print("Writing drums...")
for bar in range(BARS):
    base = bar * 4
    intensity = 0.6 + (bar / BARS) * 0.4

    for beat in range(4):
        vel = int(115 * intensity) + random.randint(-3, 3)
        note(2, 0, 36, h(base + beat, 0.008), 0.2, min(127, vel))

    for beat in [1, 3]:
        vel = int(95 * intensity) + random.randint(-5, 5)
        note(2, 0, 39, h(base + beat, 0.01), 0.15, min(127, vel))

    for sixteenth in range(16):
        beat_pos = base + sixteenth * 0.25
        if sixteenth % 4 == 0:
            vel = int(85 * intensity)
        elif sixteenth % 2 == 0:
            vel = int(65 * intensity)
        else:
            vel = int(45 * intensity)
        vel += random.randint(-8, 8)
        pitch = 46 if sixteenth % 8 == 4 else 42
        dur = 0.2 if pitch == 46 else 0.1
        note(2, 0, pitch, h(beat_pos, 0.012), dur, max(30, min(120, vel)))

    if bar in [3, 7]:
        for i in range(8):
            pos = base + 3.5 + i * 0.0625
            vel = 60 + i * 8
            note(2, 0, 42, round(pos, 4), 0.05, min(127, vel))

    time.sleep(0.01)

osc.send_message("/live/clip/set/name", [2, 0, "Festival Drums"])

# ================================================================
# TRACK 3: BASS (Analog)
# ================================================================
print("Writing bass...")
bass_a = [(38,0.0,0.3,110),(38,1.0,0.2,95),(38,1.75,0.2,100),(38,2.5,0.3,105),(41,3.0,0.2,90),(41,3.5,0.2,95)]
bass_b = [(38,0.0,0.3,110),(50,0.75,0.15,85),(38,1.0,0.2,100),(36,1.75,0.2,95),(38,2.5,0.3,110),(43,3.0,0.2,90),(41,3.5,0.3,100)]

for bar in range(BARS):
    base = bar * 4
    pattern = bass_b if bar % 2 == 1 else bass_a
    for pitch, offset, dur, vel in pattern:
        vel_adj = vel + random.randint(-5, 5)
        if bar >= 4:
            vel_adj = min(127, vel_adj + 10)
        note(3, 0, pitch, h(base + offset), dur, vel_adj)
    time.sleep(0.01)

osc.send_message("/live/clip/set/name", [3, 0, "Driving Bass"])

# ================================================================
# TRACK 0: LEAD (Drift) — enters bar 3, full arp bars 5-8
# ================================================================
print("Writing lead...")
simple_lead = [
    (74,8.0,0.2,90),(77,8.5,0.15,82),(81,9.0,0.3,100),
    (77,10.0,0.2,85),(74,10.5,0.3,90),
    (74,12.0,0.2,88),(79,12.5,0.15,82),(81,13.0,0.25,95),
    (84,13.5,0.3,105),(81,14.5,0.5,90),
]
for p, s, d, v in simple_lead:
    note(0, 0, p, h(s), d, v)

arp_pitches = [62,65,69,74,77,81,77,74,69,65,62,65,69,74,77,81]
for bar in range(4, BARS):
    base = bar * 4
    for sixteenth in range(16):
        pos = base + sixteenth * 0.25
        pitch = arp_pitches[sixteenth % len(arp_pitches)]
        if sixteenth % 4 == 0: vel = 100
        elif sixteenth % 2 == 0: vel = 80
        else: vel = 65
        vel += random.randint(-5, 5)
        if bar >= 6: vel = min(127, vel + 10)
        note(0, 0, pitch, h(pos, 0.01), 0.2, vel)
    time.sleep(0.01)

osc.send_message("/live/clip/set/name", [0, 0, "Festival Lead"])

# ================================================================
# TRACK 1: PLUCKS (Collision) — offbeat stabs, bars 5-8
# ================================================================
print("Writing pluck stabs...")
for bar in range(4, BARS):
    base = bar * 4
    for beat in range(4):
        pos = base + beat + 0.5
        for pitch in [62, 65, 69]:
            vel = 85 + random.randint(-5, 10)
            if bar >= 6: vel = min(127, vel + 8)
            note(1, 0, pitch, h(pos, 0.01), 0.15, vel)
    time.sleep(0.01)

osc.send_message("/live/clip/set/name", [1, 0, "Offbeat Stabs"])

# ================================================================
# FIRE!
# ================================================================
print("FIRING...")
time.sleep(0.2)
for t in range(4):
    osc.send_message("/live/clip/fire", [t, 0])
    time.sleep(0.02)
osc.send_message("/live/song/start_playing", [])

print()
print("PLAYING @ 128 BPM:")
print("  Bars 1-2: Drums + Bass")
print("  Bars 3-4: + Lead motif")
print("  Bars 5-8: + 16th arp + offbeat stabs + rolls")
print("Done!")
