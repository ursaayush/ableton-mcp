# Ableton MCP

MCP server for **full Ableton Live control** — wraps **AbletonOSC** + **ClyphX Pro** into 143 tools controllable from Claude, Cursor, or any MCP client.

## Prerequisites

- **Ableton Live** with [AbletonOSC](https://github.com/ideoforms/AbletonOSC) control surface (port 11000)
- **ClyphX Pro** control surface (port 7005) — for device loading and track creation
- **Python 3.10+** and [uv](https://astral.sh/uv)

## Setup

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ableton": {
      "command": "uv",
      "args": ["--directory", "/path/to/ableton-mcp", "run", "ableton-mcp"]
    }
  }
}
```

### Cursor

Go to **Settings > MCP** and add:

```
uv --directory "/path/to/ableton-mcp" run ableton-mcp
```

## Tool Groups (143 tools)

| Group | Tools | Examples |
|-------|-------|---------|
| **Song / Transport** | 40 | `set_tempo`, `trigger_session_record`, `start_playback`, `set_loop`, `capture_midi` |
| **Track** | 21 | `set_track_volume`, `set_track_mute`, `set_track_send`, `set_track_monitoring` |
| **Clip** | 24 | `fire_clip`, `stop_clip`, `set_clip_pitch`, `set_clip_warp_mode`, `add_clip_notes` |
| **Clip Slot** | 6 | `create_clip`, `delete_clip`, `duplicate_clip_to`, `fire_clip_slot` |
| **Scene** | 6 | `fire_scene`, `fire_selected_scene`, `set_scene_tempo` |
| **Device** | 9 | `set_device_parameter`, `get_device_parameter_range`, `find_parameter_by_name` |
| **View** | 6 | `get_selected_track`, `set_selected_scene`, `select_device` |
| **ClyphX Pro** | 17 | `load_device`, `clyphx_global`, `clyphx_clip_notes`, `clyphx_snap` |
| **Query** | 4 | `discover_all_tracks`, `discover_all_devices`, `test_connection` |
| **High-Level** | 7 | `ramp_volume`, `ramp_parameter`, `build_session_template` |

## Example Usage

> "Set tempo to 120 BPM, then fire clip at track 0 slot 0"

> "Load Auto Filter and Reverb onto track 1"

> "Ramp the volume of track 3 from 0 to 0.8 over 8 beats at 120 BPM"

> "Build a session template with 6 audio tracks, each with Auto Filter and EQ Eight"

## License

MIT
