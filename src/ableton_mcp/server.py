"""
server.py — Ableton MCP Server

Comprehensive MCP server wrapping AbletonOSC + ClyphX Pro for full
Ableton Live control. Exposes 140+ tools organized by API group.

Tool groups:
  1. Song / Transport    — tempo, playback, session record, metronome
  2. Track               — volume, mute, solo, pan, send, arm, name, color
  3. Clip                — fire, stop, gain, pitch, mute, name, color, notes
  4. Clip Slot           — create/delete clips
  5. Scene               — fire, name, color, tempo
  6. Device / Parameter  — get/set device parameters, enable/disable
  7. ClyphX Pro          — create tracks, load devices, routing
  8. Query / Discovery   — session info, track data, device discovery
  9. High-Level Tools    — ramps, sweeps, drops, build effects chain
"""

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Optional, Union

from mcp.server.fastmcp import FastMCP, Context

from .osc_bridge import AbletonOSCBridge, ClyphXBridge

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ableton_mcp")

# ── Global bridges ───────────────────────────────────────────────
_ableton: Optional[AbletonOSCBridge] = None
_clyphx: Optional[ClyphXBridge] = None


def get_ableton() -> AbletonOSCBridge:
    """Get or create the AbletonOSC bridge."""
    global _ableton
    if _ableton is None or not _ableton.is_connected:
        _ableton = AbletonOSCBridge()
        if not _ableton.connect():
            raise ConnectionError("Failed to connect to AbletonOSC on port 11000")
    return _ableton


def get_clyphx() -> ClyphXBridge:
    """Get or create the ClyphX Pro bridge."""
    global _clyphx
    if _clyphx is None:
        _clyphx = ClyphXBridge()
        if not _clyphx.connect():
            raise ConnectionError("Failed to connect to ClyphX Pro on port 7005")
    return _clyphx


# ── MCP Server ───────────────────────────────────────────────────
mcp = FastMCP(
    "Ableton",
    instructions="Full Ableton Live control via AbletonOSC + ClyphX Pro. Use ClyphX tools (1-based track numbers) for loading devices and creating tracks. Use AbletonOSC tools (0-based track indices) for parameter automation, mixer control, and clip operations.",
)


# ═══════════════════════════════════════════════════════════════════
# 1. SONG / TRANSPORT TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_tempo() -> str:
    """Get the current tempo (BPM) of the Ableton session."""
    ableton = get_ableton()
    result = ableton.query("/live/song/get/tempo")
    if result:
        return f"Current tempo: {result[0]} BPM"
    return "Error: Could not get tempo"


@mcp.tool()
def set_tempo(bpm: float) -> str:
    """
    Set the tempo of the Ableton session.

    Parameters:
    - bpm: Tempo in beats per minute (e.g., 90.0, 122.0)
    """
    ableton = get_ableton()
    ableton.send("/live/song/set/tempo", (float(bpm),))
    return f"Set tempo to {bpm} BPM"


@mcp.tool()
def start_playback() -> str:
    """Start playing the Ableton session."""
    ableton = get_ableton()
    ableton.send("/live/song/start_playing")
    return "Started playback"


@mcp.tool()
def stop_playback() -> str:
    """Stop playing the Ableton session."""
    ableton = get_ableton()
    ableton.send("/live/song/stop_playing")
    return "Stopped playback"


@mcp.tool()
def continue_playback() -> str:
    """Continue playing the Ableton session from the current position."""
    ableton = get_ableton()
    ableton.send("/live/song/continue_playing")
    return "Continued playback"


@mcp.tool()
def trigger_session_record() -> str:
    """
    Start Session Record mode — records all Session View clip launches
    and parameter changes into Arrangement View. This is the key method
    for capturing real-time performances.
    """
    ableton = get_ableton()
    ableton.send("/live/song/trigger_session_record")
    return "Session Record triggered — all actions now recording to Arrangement View"


@mcp.tool()
def set_song_time(time_in_beats: float) -> str:
    """
    Jump to a specific position in the song.

    Parameters:
    - time_in_beats: Position in beats from the start
    """
    ableton = get_ableton()
    ableton.send("/live/song/set/current_song_time", (float(time_in_beats),))
    return f"Jumped to beat {time_in_beats}"


@mcp.tool()
def set_metronome(enabled: bool) -> str:
    """
    Enable or disable the metronome.

    Parameters:
    - enabled: True to turn on, False to turn off
    """
    ableton = get_ableton()
    ableton.send("/live/song/set/metronome", (int(enabled),))
    return f"Metronome {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_time_signature(numerator: int, denominator: int) -> str:
    """
    Set the time signature.

    Parameters:
    - numerator: Top number (e.g., 4 for 4/4)
    - denominator: Bottom number (e.g., 4 for 4/4)
    """
    ableton = get_ableton()
    ableton.send("/live/song/set/signature_numerator", (numerator,))
    ableton.send("/live/song/set/signature_denominator", (denominator,))
    return f"Set time signature to {numerator}/{denominator}"


@mcp.tool()
def undo() -> str:
    """Undo the last action in Ableton."""
    ableton = get_ableton()
    ableton.send("/live/song/undo")
    return "Undone"


@mcp.tool()
def redo() -> str:
    """Redo the last undone action in Ableton."""
    ableton = get_ableton()
    ableton.send("/live/song/redo")
    return "Redone"


@mcp.tool()
def create_audio_track(index: int = -1) -> str:
    """
    Create a new audio track.

    Parameters:
    - index: Position to insert (-1 = end)
    """
    ableton = get_ableton()
    ableton.send("/live/song/create_audio_track", (index,))
    return f"Created audio track at index {index}"


@mcp.tool()
def create_midi_track(index: int = -1) -> str:
    """
    Create a new MIDI track.

    Parameters:
    - index: Position to insert (-1 = end)
    """
    ableton = get_ableton()
    ableton.send("/live/song/create_midi_track", (index,))
    return f"Created MIDI track at index {index}"


@mcp.tool()
def create_return_track() -> str:
    """Create a new return track (e.g., for reverb or delay sends)."""
    ableton = get_ableton()
    ableton.send("/live/song/create_return_track")
    return "Created return track"


@mcp.tool()
def create_scene(index: int = -1) -> str:
    """
    Create a new scene.

    Parameters:
    - index: Position to insert (-1 = end)
    """
    ableton = get_ableton()
    ableton.send("/live/song/create_scene", (index,))
    return f"Created scene at index {index}"


@mcp.tool()
def get_session_info() -> str:
    """Get comprehensive info about the current Ableton session — tempo, track count, etc."""
    ableton = get_ableton()
    tempo = ableton.query("/live/song/get/tempo")
    num = ableton.query("/live/song/get/signature_numerator")
    den = ableton.query("/live/song/get/signature_denominator")
    is_playing = ableton.query("/live/song/get/is_playing")

    info = {
        "tempo": tempo[0] if tempo else None,
        "signature": f"{num[0] if num else '?'}/{den[0] if den else '?'}",
        "is_playing": bool(is_playing[0]) if is_playing else None,
    }

    # Count tracks
    track_idx = 0
    while True:
        r = ableton.query("/live/track/get/name", (track_idx,), timeout=0.5)
        if r is None:
            break
        track_idx += 1
    info["track_count"] = track_idx

    return json.dumps(info, indent=2)


@mcp.tool()
def get_track_data(start_track: int, end_track: int, properties: str) -> str:
    """
    Query bulk data about multiple tracks and clips.

    Parameters:
    - start_track: First track index (inclusive)
    - end_track: Last track index (exclusive)
    - properties: Space-separated list of properties, e.g., "track.name clip.name clip.length"
                  Prefix with track., clip., or clip_slot.
    """
    ableton = get_ableton()
    props = properties.split()
    params = (start_track, end_track) + tuple(props)
    result = ableton.query("/live/song/get/track_data", params, timeout=5.0)
    if result:
        return json.dumps(list(result), indent=2)
    return "Error: No track data returned"


# ═══════════════════════════════════════════════════════════════════
# 2. TRACK TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_track_info(track_index: int) -> str:
    """
    Get detailed info about a specific track — name, volume, mute, solo, devices, etc.

    Parameters:
    - track_index: The track index (0-based)
    """
    ableton = get_ableton()
    name = ableton.query("/live/track/get/name", (track_index,), timeout=1.0)
    volume = ableton.query("/live/track/get/volume", (track_index,), timeout=1.0)
    mute = ableton.query("/live/track/get/mute", (track_index,), timeout=1.0)
    solo = ableton.query("/live/track/get/solo", (track_index,), timeout=1.0)
    pan = ableton.query("/live/track/get/panning", (track_index,), timeout=1.0)
    arm = ableton.query("/live/track/get/arm", (track_index,), timeout=1.0)
    color = ableton.query("/live/track/get/color", (track_index,), timeout=1.0)

    # Get device names
    devices = ableton.query("/live/track/get/devices/name", (track_index,), timeout=1.0)

    info = {
        "index": track_index,
        "name": name[1] if name and len(name) > 1 else None,
        "volume": volume[1] if volume and len(volume) > 1 else None,
        "mute": bool(mute[1]) if mute and len(mute) > 1 else None,
        "solo": bool(solo[1]) if solo and len(solo) > 1 else None,
        "panning": pan[1] if pan and len(pan) > 1 else None,
        "arm": bool(arm[1]) if arm and len(arm) > 1 else None,
        "color": color[1] if color and len(color) > 1 else None,
        "devices": list(devices[1:]) if devices and len(devices) > 1 else [],
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def set_track_volume(track_index: int, volume: float) -> str:
    """
    Set track volume.

    Parameters:
    - track_index: The track index (0-based)
    - volume: Volume level (0.0 = silence, 0.85 = 0dB, 1.0 = max)
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/volume", (track_index, float(volume)))
    return f"Set track {track_index} volume to {volume}"


@mcp.tool()
def set_track_mute(track_index: int, muted: bool) -> str:
    """
    Mute or unmute a track.

    Parameters:
    - track_index: The track index (0-based)
    - muted: True to mute, False to unmute
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/mute", (track_index, int(muted)))
    return f"Track {track_index} {'muted' if muted else 'unmuted'}"


@mcp.tool()
def set_track_solo(track_index: int, soloed: bool) -> str:
    """
    Solo or unsolo a track.

    Parameters:
    - track_index: The track index (0-based)
    - soloed: True to solo, False to unsolo
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/solo", (track_index, int(soloed)))
    return f"Track {track_index} {'soloed' if soloed else 'unsoloed'}"


@mcp.tool()
def set_track_pan(track_index: int, pan: float) -> str:
    """
    Set track panning position.

    Parameters:
    - track_index: The track index (0-based)
    - pan: Pan position (-1.0 = hard left, 0.0 = center, 1.0 = hard right)
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/panning", (track_index, float(pan)))
    return f"Set track {track_index} pan to {pan}"


@mcp.tool()
def set_track_send(track_index: int, send_index: int, value: float) -> str:
    """
    Set a track's send level (e.g., reverb or delay send).

    Parameters:
    - track_index: The track index (0-based)
    - send_index: Send index (0 = Send A, 1 = Send B, etc.)
    - value: Send level (0.0 to 1.0)
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/send", (track_index, send_index, float(value)))
    return f"Set track {track_index} send {send_index} to {value}"


@mcp.tool()
def set_track_arm(track_index: int, armed: bool) -> str:
    """
    Arm or disarm a track for recording.

    Parameters:
    - track_index: The track index (0-based)
    - armed: True to arm, False to disarm
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/arm", (track_index, int(armed)))
    return f"Track {track_index} {'armed' if armed else 'disarmed'}"


@mcp.tool()
def set_track_name(track_index: int, name: str) -> str:
    """
    Rename a track.

    Parameters:
    - track_index: The track index (0-based)
    - name: New name for the track
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/name", (track_index, name))
    return f"Renamed track {track_index} to '{name}'"


@mcp.tool()
def set_track_color(track_index: int, color: int) -> str:
    """
    Set track color.

    Parameters:
    - track_index: The track index (0-based)
    - color: Color index (Ableton color palette, 0-69)
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/color", (track_index, color))
    return f"Set track {track_index} color to {color}"


# ═══════════════════════════════════════════════════════════════════
# 3. CLIP TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def fire_clip(track_index: int, clip_index: int) -> str:
    """
    Fire (start playing) a clip in Session View.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    ableton.send("/live/clip/fire", (track_index, clip_index))
    return f"Fired clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def stop_clip(track_index: int, clip_index: int) -> str:
    """
    Stop a playing clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    ableton.send("/live/clip/stop", (track_index, clip_index))
    return f"Stopped clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def get_clip_info(track_index: int, clip_index: int) -> str:
    """
    Get detailed info about a clip — name, length, playing state, gain, pitch, etc.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    name = ableton.query("/live/clip/get/name", (track_index, clip_index), timeout=1.0)
    length = ableton.query("/live/clip/get/length", (track_index, clip_index), timeout=1.0)
    gain = ableton.query("/live/clip/get/gain", (track_index, clip_index), timeout=1.0)
    pitch = ableton.query("/live/clip/get/pitch_coarse", (track_index, clip_index), timeout=1.0)
    is_playing = ableton.query("/live/clip/get/is_playing", (track_index, clip_index), timeout=1.0)
    muted = ableton.query("/live/clip/get/muted", (track_index, clip_index), timeout=1.0)
    color = ableton.query("/live/clip/get/color", (track_index, clip_index), timeout=1.0)

    info = {
        "track": track_index,
        "slot": clip_index,
        "name": name[2] if name and len(name) > 2 else None,
        "length": length[2] if length and len(length) > 2 else None,
        "gain": gain[2] if gain and len(gain) > 2 else None,
        "pitch_coarse": pitch[2] if pitch and len(pitch) > 2 else None,
        "is_playing": bool(is_playing[2]) if is_playing and len(is_playing) > 2 else None,
        "muted": bool(muted[2]) if muted and len(muted) > 2 else None,
        "color": color[2] if color and len(color) > 2 else None,
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def set_clip_name(track_index: int, clip_index: int, name: str) -> str:
    """
    Set the name of a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - name: New clip name
    """
    ableton = get_ableton()
    ableton.send("/live/clip/set/name", (track_index, clip_index, name))
    return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"


@mcp.tool()
def set_clip_gain(track_index: int, clip_index: int, gain: float) -> str:
    """
    Set the gain of a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - gain: Gain value (0.0 to 1.0)
    """
    ableton = get_ableton()
    ableton.send("/live/clip/set/gain", (track_index, clip_index, float(gain)))
    return f"Set clip gain at track {track_index}, slot {clip_index} to {gain}"


@mcp.tool()
def set_clip_pitch(track_index: int, clip_index: int, semitones: int) -> str:
    """
    Set the pitch transposition of a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - semitones: Pitch shift in semitones (e.g., -2, 0, 3)
    """
    ableton = get_ableton()
    ableton.send("/live/clip/set/pitch_coarse", (track_index, clip_index, semitones))
    return f"Set clip pitch at track {track_index}, slot {clip_index} to {semitones} semitones"


@mcp.tool()
def set_clip_muted(track_index: int, clip_index: int, muted: bool) -> str:
    """
    Mute or unmute a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - muted: True to mute, False to unmute
    """
    ableton = get_ableton()
    ableton.send("/live/clip/set/muted", (track_index, clip_index, int(muted)))
    return f"Clip at track {track_index}, slot {clip_index} {'muted' if muted else 'unmuted'}"


@mcp.tool()
def set_clip_color(track_index: int, clip_index: int, color: int) -> str:
    """
    Set the color of a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - color: Color index (Ableton color palette)
    """
    ableton = get_ableton()
    ableton.send("/live/clip/set/color", (track_index, clip_index, color))
    return f"Set clip color at track {track_index}, slot {clip_index} to {color}"


@mcp.tool()
def get_clip_notes(track_index: int, clip_index: int) -> str:
    """
    Get all MIDI notes in a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    result = ableton.query("/live/clip/get/notes", (track_index, clip_index), timeout=3.0)
    if result:
        # Notes come as flat list: pitch, start, dur, vel, mute, pitch, start, ...
        notes = []
        data = list(result)[2:]  # skip track_id, clip_id prefix
        for i in range(0, len(data), 5):
            if i + 4 < len(data):
                notes.append({
                    "pitch": data[i],
                    "start_time": data[i + 1],
                    "duration": data[i + 2],
                    "velocity": data[i + 3],
                    "mute": bool(data[i + 4]),
                })
        return json.dumps(notes, indent=2)
    return "No notes found or clip is not a MIDI clip"


@mcp.tool()
def set_clip_notes(track_index: int, clip_index: int, notes: list[dict]) -> str:
    """
    Set MIDI notes in a clip (replaces existing notes).

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - notes: List of note dicts with keys: pitch, start_time, duration, velocity, mute
             Example: [{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100, "mute": false}]
    """
    ableton = get_ableton()
    # Flatten notes into OSC params
    params = [track_index, clip_index]
    for note in notes:
        params.extend([
            int(note.get("pitch", 60)),
            float(note.get("start_time", 0.0)),
            float(note.get("duration", 0.25)),
            int(note.get("velocity", 100)),
            int(note.get("mute", False)),
        ])
    ableton.send("/live/clip/set/notes", tuple(params))
    return f"Set {len(notes)} notes in clip at track {track_index}, slot {clip_index}"


# ═══════════════════════════════════════════════════════════════════
# 4. CLIP SLOT TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def create_clip(track_index: int, clip_index: int, length: float = 4.0) -> str:
    """
    Create a new empty MIDI clip in a clip slot.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    - length: Clip length in beats (default 4.0 = 1 bar in 4/4)
    """
    ableton = get_ableton()
    ableton.send("/live/clip_slot/create_clip", (track_index, clip_index, float(length)))
    return f"Created {length}-beat clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def delete_clip(track_index: int, clip_index: int) -> str:
    """
    Delete a clip from a clip slot.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    ableton.send("/live/clip_slot/delete_clip", (track_index, clip_index))
    return f"Deleted clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def has_clip(track_index: int, clip_index: int) -> str:
    """
    Check if a clip slot contains a clip.

    Parameters:
    - track_index: The track index (0-based)
    - clip_index: The clip slot index (0-based)
    """
    ableton = get_ableton()
    result = ableton.query("/live/clip_slot/get/has_clip", (track_index, clip_index), timeout=1.0)
    if result and len(result) > 2:
        has = bool(result[2])
        return f"Track {track_index}, slot {clip_index}: {'has clip' if has else 'empty'}"
    return f"Could not determine clip status for track {track_index}, slot {clip_index}"


# ═══════════════════════════════════════════════════════════════════
# 5. SCENE TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def fire_scene(scene_index: int) -> str:
    """
    Fire (trigger) a scene — launches all clips in the scene's row.

    Parameters:
    - scene_index: The scene index (0-based)
    """
    ableton = get_ableton()
    ableton.send("/live/scene/fire", (scene_index,))
    return f"Fired scene {scene_index}"


@mcp.tool()
def set_scene_name(scene_index: int, name: str) -> str:
    """
    Set the name of a scene.

    Parameters:
    - scene_index: The scene index (0-based)
    - name: New scene name
    """
    ableton = get_ableton()
    ableton.send("/live/scene/set/name", (scene_index, name))
    return f"Renamed scene {scene_index} to '{name}'"


@mcp.tool()
def set_scene_color(scene_index: int, color: int) -> str:
    """
    Set the color of a scene.

    Parameters:
    - scene_index: The scene index (0-based)
    - color: Color index (Ableton color palette)
    """
    ableton = get_ableton()
    ableton.send("/live/scene/set/color", (scene_index, color))
    return f"Set scene {scene_index} color to {color}"


@mcp.tool()
def set_scene_tempo(scene_index: int, bpm: float) -> str:
    """
    Set the tempo for a specific scene (scene-based tempo changes).

    Parameters:
    - scene_index: The scene index (0-based)
    - bpm: Scene tempo in BPM (0 = no tempo change)
    """
    ableton = get_ableton()
    ableton.send("/live/scene/set/tempo", (scene_index, float(bpm)))
    return f"Set scene {scene_index} tempo to {bpm} BPM"


# ═══════════════════════════════════════════════════════════════════
# 6. DEVICE / PARAMETER TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_device_list(track_index: int) -> str:
    """
    List all devices (effects/instruments) on a track.

    Parameters:
    - track_index: The track index (0-based)

    Returns device names and their indices for use with parameter tools.
    """
    ableton = get_ableton()
    result = ableton.query("/live/track/get/devices/name", (track_index,), timeout=2.0)
    if result:
        names = list(result[1:])  # skip track_id prefix
        devices = [{"index": i, "name": str(n)} for i, n in enumerate(names)]
        return json.dumps(devices, indent=2)
    return f"No devices found on track {track_index}"


@mcp.tool()
def get_device_parameters(track_index: int, device_index: int) -> str:
    """
    List all parameters of a device with their indices and current values.
    Use this to discover parameter indices for set_device_parameter.

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based) from get_device_list
    """
    ableton = get_ableton()
    names = ableton.query(
        "/live/device/get/parameters/name", (track_index, device_index), timeout=3.0
    )
    values = ableton.query(
        "/live/device/get/parameters/value", (track_index, device_index), timeout=3.0
    )

    if not names:
        return f"No parameters found for device {device_index} on track {track_index}"

    param_names = [str(p) for p in names[2:]]  # skip track_id, device_id
    param_values = [float(v) for v in values[2:]] if values else [None] * len(param_names)

    params = []
    for i, (n, v) in enumerate(zip(param_names, param_values)):
        params.append({"index": i, "name": n, "value": v})

    return json.dumps(params, indent=2)


@mcp.tool()
def get_device_parameter_value(track_index: int, device_index: int, parameter_index: int) -> str:
    """
    Get the current value of a specific device parameter.

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based)
    - parameter_index: The parameter index (0-based) from get_device_parameters
    """
    ableton = get_ableton()
    result = ableton.query(
        "/live/device/get/parameter/value",
        (track_index, device_index, parameter_index),
        timeout=1.0,
    )
    if result and len(result) > 3:
        return f"Parameter {parameter_index} on device {device_index}, track {track_index} = {result[3]}"
    return "Could not get parameter value"


@mcp.tool()
def set_device_parameter(track_index: int, device_index: int, parameter_index: int, value: float) -> str:
    """
    Set a device parameter value. This is the core automation primitive —
    controls filter frequency, reverb dry/wet, compressor threshold, etc.

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based)
    - parameter_index: The parameter index (0-based) from get_device_parameters
    - value: New parameter value (typically 0.0–1.0 for most params)
    """
    ableton = get_ableton()
    ableton.send(
        "/live/device/set/parameter/value",
        (track_index, device_index, parameter_index, float(value)),
    )
    return f"Set param {parameter_index} on device {device_index}, track {track_index} to {value}"


@mcp.tool()
def set_device_enabled(track_index: int, device_index: int, enabled: bool) -> str:
    """
    Enable or disable a device (bypass).

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based)
    - enabled: True to enable, False to bypass
    """
    ableton = get_ableton()
    ableton.send(
        "/live/device/set/is_enabled",
        (track_index, device_index, int(enabled)),
    )
    return f"Device {device_index} on track {track_index} {'enabled' if enabled else 'bypassed'}"


@mcp.tool()
def find_parameter_by_name(track_index: int, device_index: int, name_substring: str) -> str:
    """
    Find a device parameter index by searching for a substring in the parameter name.
    Useful for discovering parameter indices without manually inspecting all params.

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based)
    - name_substring: Part of the parameter name to search for (case-insensitive), e.g., "Frequency", "Dry/Wet"
    """
    ableton = get_ableton()
    names = ableton.query(
        "/live/device/get/parameters/name", (track_index, device_index), timeout=3.0
    )
    if not names:
        return f"No parameters found for device {device_index} on track {track_index}"

    param_names = [str(p) for p in names[2:]]
    matches = []
    for i, n in enumerate(param_names):
        if name_substring.lower() in n.lower():
            matches.append({"index": i, "name": n})

    if matches:
        return json.dumps(matches, indent=2)
    return f"No parameter matching '{name_substring}' found on device {device_index}, track {track_index}"


# ═══════════════════════════════════════════════════════════════════
# 7. CLYPHX PRO TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def clyphx_action(action_string: str) -> str:
    """
    Send a raw ClyphX Pro action string. Use this for any ClyphX command
    not covered by the specific ClyphX tools below.

    Parameters:
    - action_string: The ClyphX action string, e.g., '1/LOADDEV "Auto Filter"'
                     Multiple actions can be chained with semicolons:
                     '1/LOADDEV "Auto Filter" ; 1/LOADDEV "Reverb"'

    Common actions:
      ADDAUDIO / ADDMIDI / ADDRETURN — create tracks
      {track}/LOADDEV "{name}" — load a device
      {track}/NAME "{name}" — rename track
      {track}/COLOR {n} — set track color
      {track}/VOL {n} — set volume (0-127)
      {track}/PAN {n} — set pan (0-127, 64=center)
      {track}/MUTE ON/OFF — mute/unmute
      {track}/SEND {letter} {n} — set send level
      {track}/IN "{name}" / OUT "{name}" — set routing
      BPM {n} — set tempo
      SIG {n}/{n} — set time signature
      METRO ON/OFF — metronome
      SREC — toggle session record
    """
    clyphx = get_clyphx()
    clyphx.action(action_string)
    return f"Executed ClyphX action: {action_string}"


@mcp.tool()
def load_device(track_number: int, device_name: str) -> str:
    """
    Load an Ableton device (effect/instrument) onto a track using ClyphX Pro.
    This is the KEY capability that AbletonOSC alone cannot do.

    Parameters:
    - track_number: Track number (1-based, as ClyphX uses 1-based indexing)
    - device_name: Name of the Ableton device, e.g., "Auto Filter", "Reverb",
                   "Chorus", "Saturator", "Glue Compressor", "EQ Eight",
                   "Delay", "Compressor", "Utility"
    """
    clyphx = get_clyphx()
    clyphx.action_with_delay(f'{track_number}/LOADDEV "{device_name}"', delay=0.5)
    return f"Loaded '{device_name}' onto track {track_number}"


@mcp.tool()
def clyphx_create_audio_track() -> str:
    """Create a new audio track using ClyphX Pro."""
    clyphx = get_clyphx()
    clyphx.action_with_delay("ADDAUDIO", delay=0.3)
    return "Created audio track via ClyphX"


@mcp.tool()
def clyphx_create_midi_track() -> str:
    """Create a new MIDI track using ClyphX Pro."""
    clyphx = get_clyphx()
    clyphx.action_with_delay("ADDMIDI", delay=0.3)
    return "Created MIDI track via ClyphX"


@mcp.tool()
def clyphx_create_return_track() -> str:
    """Create a new return track using ClyphX Pro."""
    clyphx = get_clyphx()
    clyphx.action_with_delay("ADDRETURN", delay=0.3)
    return "Created return track via ClyphX"


@mcp.tool()
def set_track_routing(
    track_number: int,
    input_source: str = "",
    output_dest: str = "",
    input_sub: str = "",
    output_sub: str = "",
) -> str:
    """
    Set track routing using ClyphX Pro.

    Parameters:
    - track_number: Track number (1-based)
    - input_source: Input routing source, e.g., "Ext. In"
    - output_dest: Output routing destination, e.g., "Master"
    - input_sub: Input sub-routing, e.g., "Post FX"
    - output_sub: Output sub-routing, e.g., "Post FX"
    """
    clyphx = get_clyphx()
    actions = []
    if input_source:
        actions.append(f'{track_number}/IN "{input_source}"')
    if output_dest:
        actions.append(f'{track_number}/OUT "{output_dest}"')
    if input_sub:
        actions.append(f'{track_number}/INSUB "{input_sub}"')
    if output_sub:
        actions.append(f'{track_number}/OUTSUB "{output_sub}"')

    if actions:
        clyphx.action(" ; ".join(actions))
        return f"Set routing for track {track_number}: {', '.join(actions)}"
    return "No routing changes specified"


@mcp.tool()
def setup_track(
    track_number: int,
    name: str = "",
    color: int = -1,
    volume: int = -1,
    pan: int = -1,
    mute: str = "",
    arm: str = "",
) -> str:
    """
    Set multiple track properties at once using ClyphX Pro.

    Parameters:
    - track_number: Track number (1-based)
    - name: Track name (empty = skip)
    - color: Color index 0-69 (-1 = skip)
    - volume: Volume 0-127 (-1 = skip)
    - pan: Pan 0-127, 64=center (-1 = skip)
    - mute: "ON" or "OFF" (empty = skip)
    - arm: "ON" or "OFF" (empty = skip)
    """
    clyphx = get_clyphx()
    actions = []
    if name:
        actions.append(f'{track_number}/NAME "{name}"')
    if color >= 0:
        actions.append(f"{track_number}/COLOR {color}")
    if volume >= 0:
        actions.append(f"{track_number}/VOL {volume}")
    if pan >= 0:
        actions.append(f"{track_number}/PAN {pan}")
    if mute:
        actions.append(f"{track_number}/MUTE {mute}")
    if arm:
        actions.append(f"{track_number}/ARM {arm}")

    if actions:
        clyphx.action(" ; ".join(actions))
        return f"Set up track {track_number}: {', '.join(actions)}"
    return "No properties specified"


# ═══════════════════════════════════════════════════════════════════
# 8. QUERY / DISCOVERY TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def discover_all_tracks() -> str:
    """
    List all tracks with their names and indices. Useful for building
    a mental model of the current session layout.
    """
    ableton = get_ableton()
    tracks = []
    track_idx = 0
    while True:
        name = ableton.query("/live/track/get/name", (track_idx,), timeout=0.5)
        if name is None:
            break
        tracks.append({"index": track_idx, "name": str(name[1]) if len(name) > 1 else "?"})
        track_idx += 1
    return json.dumps(tracks, indent=2)


@mcp.tool()
def discover_all_clips(track_index: int, max_slots: int = 20) -> str:
    """
    List all clips in a track's Session View slots.

    Parameters:
    - track_index: The track index (0-based)
    - max_slots: Maximum number of slots to check (default 20)
    """
    ableton = get_ableton()
    clips = []
    for slot in range(max_slots):
        result = ableton.query("/live/clip_slot/get/has_clip", (track_index, slot), timeout=0.5)
        if result is None:
            break
        has = bool(result[2]) if len(result) > 2 else False
        if has:
            name = ableton.query("/live/clip/get/name", (track_index, slot), timeout=0.5)
            clip_name = str(name[2]) if name and len(name) > 2 else "?"
            clips.append({"slot": slot, "name": clip_name})
    return json.dumps(clips, indent=2)


@mcp.tool()
def discover_all_devices(track_index: int) -> str:
    """
    List all devices on a track with their parameters. Full device discovery
    for understanding what can be automated.

    Parameters:
    - track_index: The track index (0-based)
    """
    ableton = get_ableton()
    device_names = ableton.query("/live/track/get/devices/name", (track_index,), timeout=2.0)
    if not device_names:
        return f"No devices on track {track_index}"

    names = [str(n) for n in device_names[1:]]
    devices = []
    for dev_idx, dev_name in enumerate(names):
        params = ableton.query(
            "/live/device/get/parameters/name", (track_index, dev_idx), timeout=2.0
        )
        param_list = [str(p) for p in params[2:]] if params else []
        devices.append({
            "index": dev_idx,
            "name": dev_name,
            "parameters": [{"index": i, "name": n} for i, n in enumerate(param_list)],
        })

    return json.dumps(devices, indent=2)


@mcp.tool()
def test_connection() -> str:
    """
    Test connectivity to both AbletonOSC and ClyphX Pro.
    Verifies that both bridges are working.
    """
    results = {}

    # Test AbletonOSC
    try:
        ableton = get_ableton()
        if ableton.test_connection():
            tempo = ableton.query("/live/song/get/tempo")
            results["ableton_osc"] = {
                "status": "connected",
                "tempo": tempo[0] if tempo else None,
            }
        else:
            results["ableton_osc"] = {"status": "not responding"}
    except Exception as e:
        results["ableton_osc"] = {"status": "error", "message": str(e)}

    # Test ClyphX (can only verify the bridge exists, not that ClyphX is listening)
    try:
        clyphx = get_clyphx()
        results["clyphx_pro"] = {
            "status": "bridge ready",
            "note": "ClyphX Pro uses one-way UDP — cannot confirm it's listening. Send a test action to verify.",
        }
    except Exception as e:
        results["clyphx_pro"] = {"status": "error", "message": str(e)}

    return json.dumps(results, indent=2)


# ═══════════════════════════════════════════════════════════════════
# 9. HIGH-LEVEL TOOLS (Compound Operations)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def ramp_parameter(
    track_index: int,
    device_index: int,
    parameter_index: int,
    start_value: float,
    end_value: float,
    beats: float,
    bpm: float = 95.0,
    steps_per_beat: int = 6,
) -> str:
    """
    Smoothly ramp a device parameter from one value to another over a
    specified number of beats. This is used for filter sweeps, reverb
    builds, compression changes, etc.

    Parameters:
    - track_index: The track index (0-based)
    - device_index: The device index (0-based)
    - parameter_index: The parameter index (0-based)
    - start_value: Starting parameter value
    - end_value: Ending parameter value
    - beats: Duration in beats
    - bpm: Current tempo (default 95)
    - steps_per_beat: Resolution of the ramp (default 6 steps per beat)
    """
    ableton = get_ableton()
    beat_dur = 60.0 / bpm
    num_steps = max(int(beats * steps_per_beat), 1)
    dt = (beat_dur * beats) / num_steps

    for i in range(num_steps + 1):
        value = start_value + (end_value - start_value) * (i / num_steps)
        ableton.send(
            "/live/device/set/parameter/value",
            (track_index, device_index, parameter_index, float(value)),
        )
        if i < num_steps:
            time.sleep(dt)

    return (
        f"Ramped param {parameter_index} on device {device_index}, track {track_index} "
        f"from {start_value} to {end_value} over {beats} beats"
    )


@mcp.tool()
def ramp_volume(
    track_index: int,
    start_volume: float,
    end_volume: float,
    beats: float,
    bpm: float = 95.0,
    steps_per_beat: int = 6,
) -> str:
    """
    Smoothly ramp track volume over a specified number of beats.
    Used for fade-ins, fade-outs, and dynamic volume changes.

    Parameters:
    - track_index: The track index (0-based)
    - start_volume: Starting volume (0.0–1.0)
    - end_volume: Ending volume (0.0–1.0)
    - beats: Duration in beats
    - bpm: Current tempo (default 95)
    - steps_per_beat: Resolution of the ramp (default 6)
    """
    ableton = get_ableton()
    beat_dur = 60.0 / bpm
    num_steps = max(int(beats * steps_per_beat), 1)
    dt = (beat_dur * beats) / num_steps

    for i in range(num_steps + 1):
        vol = start_volume + (end_volume - start_volume) * (i / num_steps)
        ableton.send("/live/track/set/volume", (track_index, float(vol)))
        if i < num_steps:
            time.sleep(dt)

    return f"Ramped track {track_index} volume from {start_volume} to {end_volume} over {beats} beats"


@mcp.tool()
def ramp_send(
    track_index: int,
    send_index: int,
    start_value: float,
    end_value: float,
    beats: float,
    bpm: float = 95.0,
    steps_per_beat: int = 6,
) -> str:
    """
    Smoothly ramp a track's send level over a specified number of beats.
    Used for reverb/delay build-ups and decay.

    Parameters:
    - track_index: The track index (0-based)
    - send_index: Send index (0 = Send A, 1 = Send B, etc.)
    - start_value: Starting send level (0.0–1.0)
    - end_value: Ending send level (0.0–1.0)
    - beats: Duration in beats
    - bpm: Current tempo (default 95)
    - steps_per_beat: Resolution of the ramp (default 6)
    """
    ableton = get_ableton()
    beat_dur = 60.0 / bpm
    num_steps = max(int(beats * steps_per_beat), 1)
    dt = (beat_dur * beats) / num_steps

    for i in range(num_steps + 1):
        val = start_value + (end_value - start_value) * (i / num_steps)
        ableton.send("/live/track/set/send", (track_index, send_index, float(val)))
        if i < num_steps:
            time.sleep(dt)

    return f"Ramped track {track_index} send {send_index} from {start_value} to {end_value} over {beats} beats"


@mcp.tool()
def drop_all(
    track_indices: list[int],
    reverb_send_level: float = 0.95,
    delay_send_level: float = 0.80,
) -> str:
    """
    Execute a "drop" — spike send levels for a reverb/delay wash tail,
    then mute all specified tracks. A common production technique for
    creating dramatic transitions.

    Parameters:
    - track_indices: List of track indices to drop (0-based)
    - reverb_send_level: Reverb send level to spike to (default 0.95)
    - delay_send_level: Delay send level to spike to (default 0.80)
    """
    ableton = get_ableton()

    # Spike sends for wash tail
    for t in track_indices:
        ableton.send("/live/track/set/send", (t, 0, float(reverb_send_level)))
        ableton.send("/live/track/set/send", (t, 1, float(delay_send_level)))

    time.sleep(0.2)

    # Mute all
    for t in track_indices:
        ableton.send("/live/track/set/mute", (t, 1))

    return f"Dropped tracks {track_indices} — sends spiked, tracks muted"


@mcp.tool()
def build_effects_chain(track_number: int, effects: list[str], delay_between: float = 0.5) -> str:
    """
    Load multiple effects onto a track in sequence via ClyphX Pro.
    Each effect load requires a delay for Ableton to initialize it.

    Parameters:
    - track_number: Track number (1-based, ClyphX indexing)
    - effects: List of effect names, e.g., ["Auto Filter", "Reverb", "Chorus", "Saturator"]
    - delay_between: Seconds to wait between effect loads (default 0.5)
    """
    clyphx = get_clyphx()
    for effect in effects:
        clyphx.action_with_delay(f'{track_number}/LOADDEV "{effect}"', delay=delay_between)
    return f"Loaded effects chain on track {track_number}: {', '.join(effects)}"


@mcp.tool()
def build_session_template(
    track_configs: list[dict],
    bpm: float = 90.0,
    time_sig: str = "4/4",
) -> str:
    """
    Build a complete session template — creates tracks, loads effects,
    sets names/colors/volumes, and configures tempo. This is the
    the quickest way to set up a new session.

    Parameters:
    - track_configs: List of track config dicts, each with:
        - name: Track name
        - color: Color index (optional, default -1)
        - effects: List of effect names to load (optional)
        - volume: Initial volume 0-127 (optional, default 80)
        - send_a: Send A level 0-127 (optional, default 0)
    - bpm: Session tempo (default 90)
    - time_sig: Time signature as "num/denom" (default "4/4")

    Example track_config:
    {"name": "Sub/Pad", "color": 43, "effects": ["Auto Filter", "Reverb", "Chorus"], "volume": 80, "send_a": 40}
    """
    clyphx = get_clyphx()

    # Set tempo and time signature
    num, den = time_sig.split("/")
    clyphx.action_with_delay(f"BPM {int(bpm)} ; SIG {time_sig}", delay=0.3)

    results = []
    for i, config in enumerate(track_configs):
        track_num = i + 1  # ClyphX is 1-based

        # Create audio track
        clyphx.action_with_delay("ADDAUDIO", delay=0.3)

        # Set properties
        name = config.get("name", f"Track {track_num}")
        actions = [f'SEL/NAME "{name}"']

        color = config.get("color", -1)
        if color >= 0:
            actions.append(f"SEL/COLOR {color}")

        vol = config.get("volume", 80)
        actions.append(f"SEL/VOL {vol}")

        pan = config.get("pan", 64)
        actions.append(f"SEL/PAN {pan}")

        send_a = config.get("send_a", 0)
        if send_a > 0:
            actions.append(f"SEL/SEND A {send_a}")

        clyphx.action_with_delay(" ; ".join(actions), delay=0.3)

        # Load effects
        effects = config.get("effects", [])
        for effect in effects:
            clyphx.action_with_delay(f'SEL/LOADDEV "{effect}"', delay=0.5)

        results.append(f"Track {track_num}: {name} ({len(effects)} effects)")

    summary = "\n".join(results)
    return f"Built session template at {bpm} BPM ({time_sig}):\n{summary}"


@mcp.tool()
def wait_beats(beats: float, bpm: float = 95.0) -> str:
    """
    Wait for a specified number of beats. Useful for timing operations
    in a sequence of MCP tool calls.

    Parameters:
    - beats: Number of beats to wait
    - bpm: Current tempo (default 95)
    """
    beat_dur = 60.0 / bpm
    duration = beat_dur * beats
    time.sleep(duration)
    return f"Waited {beats} beats ({duration:.2f} seconds at {bpm} BPM)"


# ═══════════════════════════════════════════════════════════════════
# 10. MISSING SONG METHODS (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def delete_track(track_index: int) -> str:
    """Delete a track by index. Parameters: track_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/song/delete_track", (track_index,))
    return f"Deleted track {track_index}"


@mcp.tool()
def delete_scene(scene_index: int) -> str:
    """Delete a scene by index. Parameters: scene_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/song/delete_scene", (scene_index,))
    return f"Deleted scene {scene_index}"


@mcp.tool()
def duplicate_track(track_index: int) -> str:
    """Duplicate a track. Parameters: track_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/song/duplicate_track", (track_index,))
    return f"Duplicated track {track_index}"


@mcp.tool()
def duplicate_scene(scene_index: int) -> str:
    """Duplicate a scene. Parameters: scene_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/song/duplicate_scene", (scene_index,))
    return f"Duplicated scene {scene_index}"


@mcp.tool()
def stop_all_clips() -> str:
    """Stop all playing clips in the session."""
    ableton = get_ableton()
    ableton.send("/live/song/stop_all_clips")
    return "Stopped all clips"


@mcp.tool()
def capture_midi() -> str:
    """Capture recently played MIDI notes into a new clip (Live 10+ feature)."""
    ableton = get_ableton()
    ableton.send("/live/song/capture_midi")
    return "Captured MIDI"


@mcp.tool()
def tap_tempo() -> str:
    """Tap tempo — call repeatedly to set tempo by tap timing."""
    ableton = get_ableton()
    ableton.send("/live/song/tap_tempo")
    return "Tap tempo registered"


@mcp.tool()
def jump_to_prev_cue() -> str:
    """Jump to the previous cue point."""
    ableton = get_ableton()
    ableton.send("/live/song/jump_to_prev_cue")
    return "Jumped to previous cue"


@mcp.tool()
def jump_to_next_cue() -> str:
    """Jump to the next cue point."""
    ableton = get_ableton()
    ableton.send("/live/song/jump_to_next_cue")
    return "Jumped to next cue"


@mcp.tool()
def get_cue_points() -> str:
    """Get all cue points in the session (name + time pairs)."""
    ableton = get_ableton()
    result = ableton.query("/live/song/get/cue_points", timeout=2.0)
    if result:
        cues = []
        data = list(result)
        for i in range(0, len(data), 2):
            if i + 1 < len(data):
                cues.append({"name": str(data[i]), "time": float(data[i + 1])})
        return json.dumps(cues, indent=2)
    return "No cue points found"


@mcp.tool()
def jump_to_cue_point(name_or_index: str) -> str:
    """
    Jump to a cue point by name or index.
    Parameters: name_or_index — cue point name (string) or index (number)
    """
    ableton = get_ableton()
    try:
        idx = int(name_or_index)
        ableton.send("/live/song/cue_point/jump", (idx,))
    except ValueError:
        ableton.send("/live/song/cue_point/jump", (name_or_index,))
    return f"Jumped to cue point '{name_or_index}'"


@mcp.tool()
def set_or_delete_cue() -> str:
    """Set or delete a cue point at the current playback position."""
    ableton = get_ableton()
    ableton.send("/live/song/set_or_delete_cue")
    return "Set or deleted cue point at current position"


@mcp.tool()
def re_enable_automation() -> str:
    """Re-enable any automation that has been overridden by manual changes."""
    ableton = get_ableton()
    ableton.send("/live/song/re_enable_automation")
    return "Re-enabled automation"


@mcp.tool()
def set_loop(enabled: bool) -> str:
    """Enable or disable the arrangement loop. Parameters: enabled (bool)."""
    ableton = get_ableton()
    ableton.send("/live/song/set/loop", (int(enabled),))
    return f"Arrangement loop {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_loop_start(start_beats: float) -> str:
    """Set the arrangement loop start position in beats."""
    ableton = get_ableton()
    ableton.send("/live/song/set/loop_start", (float(start_beats),))
    return f"Set loop start to beat {start_beats}"


@mcp.tool()
def set_loop_length(length_beats: float) -> str:
    """Set the arrangement loop length in beats."""
    ableton = get_ableton()
    ableton.send("/live/song/set/loop_length", (float(length_beats),))
    return f"Set loop length to {length_beats} beats"


@mcp.tool()
def set_arrangement_overdub(enabled: bool) -> str:
    """Enable or disable arrangement overdub."""
    ableton = get_ableton()
    ableton.send("/live/song/set/arrangement_overdub", (int(enabled),))
    return f"Arrangement overdub {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_groove_amount(amount: float) -> str:
    """Set the global groove amount (0.0 to 1.0)."""
    ableton = get_ableton()
    ableton.send("/live/song/set/groove_amount", (float(amount),))
    return f"Set groove amount to {amount}"


@mcp.tool()
def set_punch_in(enabled: bool) -> str:
    """Enable or disable punch in."""
    ableton = get_ableton()
    ableton.send("/live/song/set/punch_in", (int(enabled),))
    return f"Punch in {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_punch_out(enabled: bool) -> str:
    """Enable or disable punch out."""
    ableton = get_ableton()
    ableton.send("/live/song/set/punch_out", (int(enabled),))
    return f"Punch out {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_record_mode(enabled: bool) -> str:
    """Toggle arrangement record mode."""
    ableton = get_ableton()
    ableton.send("/live/song/set/record_mode", (int(enabled),))
    return f"Arrangement record {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def set_session_record(enabled: bool) -> str:
    """Set session record state directly (vs trigger_session_record which toggles)."""
    ableton = get_ableton()
    ableton.send("/live/song/set/session_record", (int(enabled),))
    return f"Session record {'enabled' if enabled else 'disabled'}"


@mcp.tool()
def get_num_tracks() -> str:
    """Get the total number of tracks."""
    ableton = get_ableton()
    result = ableton.query("/live/song/get/num_tracks")
    if result:
        return f"Number of tracks: {result[0]}"
    return "Error getting track count"


@mcp.tool()
def get_num_scenes() -> str:
    """Get the total number of scenes."""
    ableton = get_ableton()
    result = ableton.query("/live/song/get/num_scenes")
    if result:
        return f"Number of scenes: {result[0]}"
    return "Error getting scene count"


@mcp.tool()
def get_track_names(start: int = 0, end: int = -1) -> str:
    """Get names of tracks in range. -1 for end means all tracks."""
    ableton = get_ableton()
    result = ableton.query("/live/song/get/track_names", (start, end), timeout=3.0)
    if result:
        return json.dumps(list(result), indent=2)
    return "Error getting track names"


@mcp.tool()
def export_song_structure() -> str:
    """Export full song structure (tracks, clips, devices, parameters) to a temp JSON file."""
    ableton = get_ableton()
    result = ableton.query("/live/song/export/structure", timeout=10.0)
    if result:
        import tempfile, os
        path = os.path.join(tempfile.gettempdir(), "abletonosc-song-structure.json")
        return f"Exported song structure to {path}"
    return "Error exporting song structure"


@mcp.tool()
def set_clip_trigger_quantization(value: int) -> str:
    """Set the clip trigger quantization. 0=None, 1=8bars, 2=4bars, 3=2bars, 4=1bar, etc."""
    ableton = get_ableton()
    ableton.send("/live/song/set/clip_trigger_quantization", (value,))
    return f"Set clip trigger quantization to {value}"


@mcp.tool()
def capture_and_insert_scene() -> str:
    """Capture the currently playing clips into a new scene."""
    ableton = get_ableton()
    ableton.send("/live/song/capture_and_insert_scene")
    return "Captured and inserted scene"


# ═══════════════════════════════════════════════════════════════════
# 11. MISSING TRACK METHODS (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def set_track_monitoring(track_index: int, state: int) -> str:
    """
    Set track monitoring state. 0=IN, 1=AUTO, 2=OFF.
    Parameters: track_index (0-based), state (0/1/2)
    """
    ableton = get_ableton()
    ableton.send("/live/track/set/current_monitoring_state", (track_index, state))
    states = {0: "IN", 1: "AUTO", 2: "OFF"}
    return f"Set track {track_index} monitoring to {states.get(state, state)}"


@mcp.tool()
def set_track_fold(track_index: int, folded: bool) -> str:
    """Fold or unfold a group track. Parameters: track_index (0-based), folded (bool)."""
    ableton = get_ableton()
    ableton.send("/live/track/set/fold_state", (track_index, int(folded)))
    return f"Track {track_index} {'folded' if folded else 'unfolded'}"


@mcp.tool()
def delete_device(track_index: int, device_index: int) -> str:
    """Delete a device from a track. Parameters: track_index, device_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/track/delete_device", (track_index, device_index))
    return f"Deleted device {device_index} from track {track_index}"


@mcp.tool()
def stop_track_clips(track_index: int) -> str:
    """Stop all clips on a specific track. Parameters: track_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/track/stop_all_clips", (track_index,))
    return f"Stopped all clips on track {track_index}"


@mcp.tool()
def get_track_output_meter(track_index: int) -> str:
    """Get the current output meter level of a track (for visual feedback)."""
    ableton = get_ableton()
    level = ableton.query("/live/track/get/output_meter_level", (track_index,), timeout=1.0)
    left = ableton.query("/live/track/get/output_meter_left", (track_index,), timeout=1.0)
    right = ableton.query("/live/track/get/output_meter_right", (track_index,), timeout=1.0)
    info = {
        "track": track_index,
        "level": level[1] if level and len(level) > 1 else None,
        "left": left[1] if left and len(left) > 1 else None,
        "right": right[1] if right and len(right) > 1 else None,
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def get_playing_slot(track_index: int) -> str:
    """Get the index of the currently playing clip slot on a track (-1 = none)."""
    ableton = get_ableton()
    result = ableton.query("/live/track/get/playing_slot_index", (track_index,), timeout=1.0)
    if result and len(result) > 1:
        return f"Track {track_index} playing slot: {result[1]}"
    return f"Could not get playing slot for track {track_index}"


@mcp.tool()
def get_track_routing_info(track_index: int) -> str:
    """Get complete input/output routing info for a track via AbletonOSC."""
    ableton = get_ableton()
    in_type = ableton.query("/live/track/get/input_routing_type", (track_index,), timeout=1.0)
    in_chan = ableton.query("/live/track/get/input_routing_channel", (track_index,), timeout=1.0)
    out_type = ableton.query("/live/track/get/output_routing_type", (track_index,), timeout=1.0)
    out_chan = ableton.query("/live/track/get/output_routing_channel", (track_index,), timeout=1.0)
    info = {
        "track": track_index,
        "input_type": in_type[1] if in_type and len(in_type) > 1 else None,
        "input_channel": in_chan[1] if in_chan and len(in_chan) > 1 else None,
        "output_type": out_type[1] if out_type and len(out_type) > 1 else None,
        "output_channel": out_chan[1] if out_chan and len(out_chan) > 1 else None,
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def set_track_output_routing(track_index: int, routing_type: str) -> str:
    """Set track output routing type (e.g., 'Master', 'Ext. Out'). Uses AbletonOSC directly."""
    ableton = get_ableton()
    ableton.send("/live/track/set/output_routing_type", (track_index, routing_type))
    return f"Set track {track_index} output routing to '{routing_type}'"


@mcp.tool()
def set_track_input_routing(track_index: int, routing_type: str) -> str:
    """Set track input routing type (e.g., 'Ext. In', 'No Input'). Uses AbletonOSC directly."""
    ableton = get_ableton()
    ableton.send("/live/track/set/input_routing_type", (track_index, routing_type))
    return f"Set track {track_index} input routing to '{routing_type}'"


@mcp.tool()
def get_available_routing(track_index: int) -> str:
    """Get all available input and output routing options for a track."""
    ableton = get_ableton()
    in_types = ableton.query("/live/track/get/available_input_routing_types", (track_index,), timeout=2.0)
    in_chans = ableton.query("/live/track/get/available_input_routing_channels", (track_index,), timeout=2.0)
    out_types = ableton.query("/live/track/get/available_output_routing_types", (track_index,), timeout=2.0)
    out_chans = ableton.query("/live/track/get/available_output_routing_channels", (track_index,), timeout=2.0)
    info = {
        "input_routing_types": list(in_types[1:]) if in_types else [],
        "input_routing_channels": list(in_chans[1:]) if in_chans else [],
        "output_routing_types": list(out_types[1:]) if out_types else [],
        "output_routing_channels": list(out_chans[1:]) if out_chans else [],
    }
    return json.dumps(info, indent=2)


@mcp.tool()
def get_arrangement_clips(track_index: int) -> str:
    """Get clips in Arrangement View for a track (name, length, start_time)."""
    ableton = get_ableton()
    names = ableton.query("/live/track/get/arrangement_clips/name", (track_index,), timeout=2.0)
    lengths = ableton.query("/live/track/get/arrangement_clips/length", (track_index,), timeout=2.0)
    starts = ableton.query("/live/track/get/arrangement_clips/start_time", (track_index,), timeout=2.0)
    name_list = list(names[1:]) if names and len(names) > 1 else []
    len_list = list(lengths[1:]) if lengths and len(lengths) > 1 else []
    start_list = list(starts[1:]) if starts and len(starts) > 1 else []
    clips = []
    for i in range(len(name_list)):
        clips.append({
            "name": str(name_list[i]) if i < len(name_list) else None,
            "length": float(len_list[i]) if i < len(len_list) else None,
            "start_time": float(start_list[i]) if i < len(start_list) else None,
        })
    return json.dumps(clips, indent=2)


# ═══════════════════════════════════════════════════════════════════
# 12. MISSING CLIP PROPERTIES (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def set_clip_pitch_fine(track_index: int, clip_index: int, cents: float) -> str:
    """Set fine pitch transposition of a clip in cents (-50.0 to 50.0)."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/pitch_fine", (track_index, clip_index, float(cents)))
    return f"Set clip fine pitch to {cents} cents"


@mcp.tool()
def set_clip_looping(track_index: int, clip_index: int, looping: bool) -> str:
    """Enable or disable clip looping."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/looping", (track_index, clip_index, int(looping)))
    return f"Clip looping {'enabled' if looping else 'disabled'}"


@mcp.tool()
def set_clip_loop_start(track_index: int, clip_index: int, position: float) -> str:
    """Set the clip loop start position in beats."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/loop_start", (track_index, clip_index, float(position)))
    return f"Set clip loop start to {position}"


@mcp.tool()
def set_clip_loop_end(track_index: int, clip_index: int, position: float) -> str:
    """Set the clip loop end position in beats."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/loop_end", (track_index, clip_index, float(position)))
    return f"Set clip loop end to {position}"


@mcp.tool()
def set_clip_warp_mode(track_index: int, clip_index: int, mode: int) -> str:
    """Set clip warp mode. 0=Beats, 1=Tones, 2=Texture, 3=Re-Pitch, 4=Complex, 6=Complex Pro."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/warp_mode", (track_index, clip_index, mode))
    modes = {0: "Beats", 1: "Tones", 2: "Texture", 3: "Re-Pitch", 4: "Complex", 6: "Complex Pro"}
    return f"Set clip warp mode to {modes.get(mode, mode)}"


@mcp.tool()
def set_clip_warping(track_index: int, clip_index: int, warping: bool) -> str:
    """Enable or disable warping on an audio clip."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/warping", (track_index, clip_index, int(warping)))
    return f"Clip warping {'enabled' if warping else 'disabled'}"


@mcp.tool()
def set_clip_launch_mode(track_index: int, clip_index: int, mode: int) -> str:
    """Set clip launch mode. 0=Trigger, 1=Gate, 2=Toggle, 3=Repeat."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/launch_mode", (track_index, clip_index, mode))
    modes = {0: "Trigger", 1: "Gate", 2: "Toggle", 3: "Repeat"}
    return f"Set clip launch mode to {modes.get(mode, mode)}"


@mcp.tool()
def set_clip_launch_quantization(track_index: int, clip_index: int, quantization: int) -> str:
    """Set clip launch quantization. 0=Global, 1=None, 2=8bars, ..., 6=1bar, 7=1/2, etc."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/launch_quantization", (track_index, clip_index, quantization))
    return f"Set clip launch quantization to {quantization}"


@mcp.tool()
def set_clip_position(track_index: int, clip_index: int, position: float) -> str:
    """Set the clip's playback position in beats."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/position", (track_index, clip_index, float(position)))
    return f"Set clip position to {position}"


@mcp.tool()
def set_clip_start_marker(track_index: int, clip_index: int, position: float) -> str:
    """Set the clip's start marker position."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/start_marker", (track_index, clip_index, float(position)))
    return f"Set clip start marker to {position}"


@mcp.tool()
def set_clip_end_marker(track_index: int, clip_index: int, position: float) -> str:
    """Set the clip's end marker position."""
    ableton = get_ableton()
    ableton.send("/live/clip/set/end_marker", (track_index, clip_index, float(position)))
    return f"Set clip end marker to {position}"


@mcp.tool()
def duplicate_clip_loop(track_index: int, clip_index: int) -> str:
    """Double the clip's loop length (duplicate loop content)."""
    ableton = get_ableton()
    ableton.send("/live/clip/duplicate_loop", (track_index, clip_index))
    return f"Duplicated loop in clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def add_clip_notes(track_index: int, clip_index: int, notes: list[dict]) -> str:
    """
    Add MIDI notes to a clip (does NOT delete existing notes, unlike set_clip_notes).
    Parameters: notes — list of dicts with pitch, start_time, duration, velocity, mute.
    """
    ableton = get_ableton()
    params = [track_index, clip_index]
    for note in notes:
        params.extend([
            int(note.get("pitch", 60)),
            float(note.get("start_time", 0.0)),
            float(note.get("duration", 0.25)),
            int(note.get("velocity", 100)),
            int(note.get("mute", False)),
        ])
    ableton.send("/live/clip/add/notes", tuple(params))
    return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"


@mcp.tool()
def remove_clip_notes(track_index: int, clip_index: int, pitch_start: int = 0, pitch_span: int = 127, time_start: float = -8192.0, time_span: float = 16384.0) -> str:
    """
    Remove MIDI notes from a clip within a pitch/time range.
    Default removes ALL notes. Specify ranges to target specific notes.
    """
    ableton = get_ableton()
    ableton.send("/live/clip/remove/notes", (track_index, clip_index, pitch_start, pitch_span, float(time_start), float(time_span)))
    return f"Removed notes from clip at track {track_index}, slot {clip_index}"


# ═══════════════════════════════════════════════════════════════════
# 13. MISSING CLIP SLOT METHODS (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def fire_clip_slot(track_index: int, clip_index: int) -> str:
    """Fire a clip slot (starts recording if empty and track is armed)."""
    ableton = get_ableton()
    ableton.send("/live/clip_slot/fire", (track_index, clip_index))
    return f"Fired clip slot at track {track_index}, slot {clip_index}"


@mcp.tool()
def stop_clip_slot(track_index: int, clip_index: int) -> str:
    """Stop a clip slot."""
    ableton = get_ableton()
    ableton.send("/live/clip_slot/stop", (track_index, clip_index))
    return f"Stopped clip slot at track {track_index}, slot {clip_index}"


@mcp.tool()
def duplicate_clip_to(src_track: int, src_slot: int, dst_track: int, dst_slot: int) -> str:
    """
    Duplicate a clip from one slot to another.
    Parameters: source track/slot and destination track/slot (all 0-based).
    """
    ableton = get_ableton()
    ableton.send("/live/clip_slot/duplicate_clip_to", (src_track, src_slot, dst_track, dst_slot))
    return f"Duplicated clip from track {src_track} slot {src_slot} to track {dst_track} slot {dst_slot}"


# ═══════════════════════════════════════════════════════════════════
# 14. MISSING SCENE METHODS (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def fire_scene_as_selected(scene_index: int) -> str:
    """Fire a scene as if it were the selected scene."""
    ableton = get_ableton()
    ableton.send("/live/scene/fire_as_selected", (scene_index,))
    return f"Fired scene {scene_index} as selected"


@mcp.tool()
def fire_selected_scene() -> str:
    """Fire the currently selected scene."""
    ableton = get_ableton()
    ableton.send("/live/scene/fire_selected")
    return "Fired selected scene"


# ═══════════════════════════════════════════════════════════════════
# 15. MISSING DEVICE METHODS (from AbletonOSC source audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_device_parameter_range(track_index: int, device_index: int) -> str:
    """
    Get all parameters with their min/max ranges and whether they're quantized.
    Essential for understanding valid value ranges for automation.
    """
    ableton = get_ableton()
    names = ableton.query("/live/device/get/parameters/name", (track_index, device_index), timeout=3.0)
    mins = ableton.query("/live/device/get/parameters/min", (track_index, device_index), timeout=3.0)
    maxs = ableton.query("/live/device/get/parameters/max", (track_index, device_index), timeout=3.0)
    quant = ableton.query("/live/device/get/parameters/is_quantized", (track_index, device_index), timeout=3.0)
    values = ableton.query("/live/device/get/parameters/value", (track_index, device_index), timeout=3.0)

    if not names:
        return f"No parameters found for device {device_index} on track {track_index}"

    param_names = [str(p) for p in names[2:]]
    param_mins = list(mins[2:]) if mins else [None] * len(param_names)
    param_maxs = list(maxs[2:]) if maxs else [None] * len(param_names)
    param_quant = list(quant[2:]) if quant else [None] * len(param_names)
    param_vals = list(values[2:]) if values else [None] * len(param_names)

    params = []
    for i in range(len(param_names)):
        params.append({
            "index": i,
            "name": param_names[i],
            "value": param_vals[i] if i < len(param_vals) else None,
            "min": param_mins[i] if i < len(param_mins) else None,
            "max": param_maxs[i] if i < len(param_maxs) else None,
            "is_quantized": bool(param_quant[i]) if i < len(param_quant) else None,
        })
    return json.dumps(params, indent=2)


@mcp.tool()
def get_device_parameter_display(track_index: int, device_index: int, parameter_index: int) -> str:
    """Get the human-readable display string for a parameter value (e.g., '2500 Hz', '-6.0 dB')."""
    ableton = get_ableton()
    result = ableton.query(
        "/live/device/get/parameter/value_string",
        (track_index, device_index, parameter_index),
        timeout=1.0,
    )
    if result and len(result) > 3:
        return f"Parameter {parameter_index}: {result[3]}"
    return "Could not get parameter display string"


@mcp.tool()
def set_all_device_parameters(track_index: int, device_index: int, values: list[float]) -> str:
    """Set all device parameters at once. Values must match parameter count in order."""
    ableton = get_ableton()
    params = (track_index, device_index) + tuple(float(v) for v in values)
    ableton.send("/live/device/set/parameters/value", params)
    return f"Set {len(values)} parameters on device {device_index}, track {track_index}"


# ═══════════════════════════════════════════════════════════════════
# 16. VIEW API (from AbletonOSC source audit — entirely missing)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def get_selected_track() -> str:
    """Get the index of the currently selected track."""
    ableton = get_ableton()
    result = ableton.query("/live/view/get/selected_track", timeout=1.0)
    if result:
        return f"Selected track index: {result[0]}"
    return "Could not get selected track"


@mcp.tool()
def set_selected_track(track_index: int) -> str:
    """Select a track by index (brings it into view). Parameters: track_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/view/set/selected_track", (track_index,))
    return f"Selected track {track_index}"


@mcp.tool()
def get_selected_scene() -> str:
    """Get the index of the currently selected scene."""
    ableton = get_ableton()
    result = ableton.query("/live/view/get/selected_scene", timeout=1.0)
    if result:
        return f"Selected scene index: {result[0]}"
    return "Could not get selected scene"


@mcp.tool()
def set_selected_scene(scene_index: int) -> str:
    """Select a scene by index. Parameters: scene_index (0-based)."""
    ableton = get_ableton()
    ableton.send("/live/view/set/selected_scene", (scene_index,))
    return f"Selected scene {scene_index}"


@mcp.tool()
def set_selected_clip(track_index: int, scene_index: int) -> str:
    """Select a clip slot by track and scene index."""
    ableton = get_ableton()
    ableton.send("/live/view/set/selected_clip", (track_index, scene_index))
    return f"Selected clip at track {track_index}, scene {scene_index}"


@mcp.tool()
def select_device(track_index: int, device_index: int) -> str:
    """Select a device on a track (brings it into view for editing)."""
    ableton = get_ableton()
    ableton.send("/live/view/set/selected_device", (track_index, device_index))
    return f"Selected device {device_index} on track {track_index}"


# ═══════════════════════════════════════════════════════════════════
# 17. EXTENDED CLYPHX PRO GLOBAL ACTIONS (from manual audit)
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def clyphx_global(action: str) -> str:
    """
    Execute a ClyphX Pro global action. Common actions include:
    - B2A — Back to Arrangement
    - CAP — Trigger Capture MIDI
    - DRAW / DRAW ON / OFF — toggle Draw Mode
    - FOLLOW / FOLLOW ON / OFF — toggle Follow
    - GQ x — Global Quantization (NONE, 8 BARS, 4 BARS, etc.)
    - GRV x — Global Groove Amount (0-131)
    - LOOP START x — Set arrangement loop start (Bars.Beats.Sixteenths)
    - LOOP RESET — Reset loop to 1.1.1
    - METRO / METRO ON / OFF — toggle Metronome
    - MSG x — Show message in Live's Status Bar
    - OVER / OVER ON / OFF — Arrangement Overdub
    - PIN / POUT — Punch In/Out
    - REC / REC ON / OFF — Arrangement Record
    - RESTART — Restart to 1.1.1
    - RQ x — Record Quantization
    - SATM / SATMR — session automation arm / re-enable
    - SETJUMP x — Jump to position (Bars.Beats.Sixteenths)
    - SHOWCLIP or SHOWDEV — show Clip or Device view
    - SIG x/y — Time Signature
    - SREC — toggle Session Record
    - SRECFIX x — Fixed-length Session Record (x bars)
    - STOPALL — Stop all clips
    - TAPBPM — Tap tempo
    - WAIT x — Wait x tenths of a second
    - WAITS x — Wait x beats (use B suffix for bars)
    """
    clyphx = get_clyphx()
    clyphx.action(action)
    return f"Executed global action: {action}"


@mcp.tool()
def clyphx_scene(action: str) -> str:
    """
    Execute a ClyphX Pro scene action. Syntax: SCENE_NUMBER/ACTION
    Common actions:
    - x/PLAY — Launch scene x
    - x/NAME "name" — Rename scene
    - x/COLOR n — Set scene color
    """
    clyphx = get_clyphx()
    clyphx.action(action)
    return f"Executed scene action: {action}"


@mcp.tool()
def clyphx_clip(track: int, action: str) -> str:
    """
    Execute a ClyphX Pro clip action on the playing/selected clip of a track.
    Common actions:
    - CLIP CENT x — Set clip cents
    - CLIP CHOP — Chop clip into equal slices
    - CLIP COLOR x — Set clip color
    - CLIP DEL — Delete clip
    - CLIP DUPE — Duplicate clip
    - CLIP END x — Set end position
    - CLIP EXTEND — Double loop length
    - CLIP GAIN x — Adjust audio clip gain
    - CLIP GRID x — Set fixed grid
    - CLIP LEGATO — Toggle legato
    - CLIP LMODE x — Set launch mode (TRIGGER, GATE, TOGGLE, REPEAT)
    - CLIP LQ x — Set launch quantization
    - CLIP MUTE — Toggle clip mute
    - CLIP NAME "x" — Rename clip
    - CLIP QNTZ x — Quantize notes/warps
    - CLIP SEMI x — Transpose semitones
    - CLIP SIG x/y — Set clip time signature
    - CLIP SPLIT x — Split clip at position
    - CLIP START x — Set start position
    - CLIP TOARR — Copy clip to Arrangement
    - CLIP TODR — Convert to Drum Rack
    - CLIP TOMIDI x — Convert audio to MIDI
    - CLIP TOSIMP — Convert to Simpler
    - CLIP WARP — Toggle warping
    - CLIP WARPMODE x — Set warp mode
    - CLIP VELOCITY x — Set velocity
    """
    clyphx = get_clyphx()
    clyphx.action(f"{track}/{action}")
    return f"Executed clip action on track {track}: {action}"


@mcp.tool()
def clyphx_clip_loop(track: int, action: str) -> str:
    """
    Execute a ClyphX Pro clip loop action on a track's playing/selected clip.
    Common: CLIP LOOP, CLIP LOOP END x, CLIP LOOP START x, CLIP LOOP RESET
    """
    clyphx = get_clyphx()
    clyphx.action(f"{track}/{action}")
    return f"Executed clip loop action on track {track}: {action}"


@mcp.tool()
def clyphx_clip_notes(track: int, action: str) -> str:
    """
    Execute a ClyphX Pro clip note manipulation action.
    Common actions:
    - CLIP NOTES — Toggle mute
    - CLIP NOTES CMB — Combine consecutive notes
    - CLIP NOTES COMP — Compress note durations
    - CLIP NOTES DEL — Delete notes
    - CLIP NOTES EXP — Expand note durations
    - CLIP NOTES INV — Invert pitches
    - CLIP NOTES NUDGE < or > — Nudge notes
    - CLIP NOTES REV — Reverse positions
    - CLIP NOTES SCRP — Scramble positions
    - CLIP NOTES SEMI <x or >x — Transpose
    - CLIP NOTES SPLIT — Split notes
    - CLIP NOTES VELO x — Set velocity
    - CLIP NOTES VELO << or >> — Crescendo/Decrescendo
    - CLIP NOTES VELO RND — Randomize velocity
    Pitch filter: CLIP NOTES(C3) REV, CLIP NOTES(F4-F#5) VELO <<
    """
    clyphx = get_clyphx()
    clyphx.action(f"{track}/{action}")
    return f"Executed clip notes action on track {track}: {action}"


@mcp.tool()
def clyphx_device_action(track: int, action: str) -> str:
    """
    Execute a ClyphX Pro device action on a track.
    Common actions:
    - DEV / DEV ON / DEV OFF — Toggle device on/off
    - DEV "Param Name" x — Set parameter by name
    - DEV B1 P1 x — Set bank 1 param 1
    - DEV CS x — Chain Selector
    - DEV CSEL x — Select chain
    - DEV DEL — Delete device
    - DEV FOLD / FOLD ON / OFF — Fold/unfold
    - DEV PRESET > or < — Navigate presets
    - DEV RESET — Reset all parameters
    - DEV RND — Randomize parameters
    - DEV SEL — Select device
    """
    clyphx = get_clyphx()
    clyphx.action(f"{track}/{action}")
    return f"Executed device action on track {track}: {action}"


@mcp.tool()
def clyphx_snap(action: str) -> str:
    """
    Execute a ClyphX Pro snap (snapshot) action.
    Common actions:
    - SNAP name STORE — Store a snapshot
    - SNAP name RECALL — Recall a snapshot
    - SNAP name DEL — Delete a snapshot
    - SNAP name RECALL MIX — Recall only mixer settings
    - SNAP name RECALL DEV — Recall only device settings
    """
    clyphx = get_clyphx()
    clyphx.action(action)
    return f"Executed snap action: {action}"


@mcp.tool()
def clyphx_midi(channel: int, msg_type: str, data1: int, data2: int = 0) -> str:
    """
    Send a MIDI message via ClyphX Pro.
    Parameters:
    - channel: MIDI channel (1-16)
    - msg_type: "NOTE" or "CC"
    - data1: Note number or CC number
    - data2: Velocity or CC value
    """
    clyphx = get_clyphx()
    clyphx.action(f"MIDI {channel} {msg_type} {data1} {data2}")
    return f"Sent MIDI {msg_type} CH{channel} {data1} {data2}"


@mcp.tool()
def clyphx_browser_load(track: int, item_type: str, name: str) -> str:
    """
    Load an item from Live's browser onto a track via ClyphX.
    Parameters:
    - track: Track number (1-based)
    - item_type: "DEV" (device), "SAMPLE" (audio sample), or "CLIP" (clip)
    - name: Name or path of the item to load
    """
    clyphx = get_clyphx()
    if item_type.upper() == "DEV":
        clyphx.action_with_delay(f'{track}/LOADDEV "{name}"', delay=0.5)
    elif item_type.upper() == "SAMPLE":
        clyphx.action_with_delay(f'{track}/LOADSAMPLE "{name}"', delay=0.5)
    elif item_type.upper() == "CLIP":
        clyphx.action_with_delay(f'{track}/LOADCLIP "{name}"', delay=0.5)
    else:
        return f"Unknown item type: {item_type}"
    return f"Loaded {item_type} '{name}' onto track {track}"


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    """Run the Ableton MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()

