#!/usr/bin/env python3
"""
web_server.py — Lightweight web server that wraps Ableton MCP tools as HTTP endpoints.

Start:  uv run python web_server.py
Open:   http://localhost:8765
"""

import json
import inspect
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Import all MCP tools
from ableton_mcp.server import mcp


# Collect all tools and their signatures
TOOLS = {}
for name, tool in mcp._tool_manager._tools.items():
    sig = inspect.signature(tool.fn)
    params = []
    for pname, param in sig.parameters.items():
        ptype = "string"
        default = None
        if param.annotation != inspect.Parameter.empty:
            if param.annotation in (int, float):
                ptype = "number"
            elif param.annotation == bool:
                ptype = "boolean"
            elif param.annotation in (list, dict):
                ptype = "json"
        if param.default != inspect.Parameter.empty:
            default = param.default
        params.append({"name": pname, "type": ptype, "default": default})
    TOOLS[name] = {"fn": tool.fn, "params": params, "doc": tool.fn.__doc__ or ""}


class AbletonHandler(SimpleHTTPRequestHandler):
    """Handle API calls and serve static files."""

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            html_path = Path(__file__).parent / "panel.html"
            self.wfile.write(html_path.read_bytes())
        elif self.path == "/api/tools":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            tool_info = {}
            for name, t in TOOLS.items():
                tool_info[name] = {"params": t["params"], "doc": t["doc"]}
            self.wfile.write(json.dumps(tool_info).encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/call":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            tool_name = body.get("tool", "")
            args = body.get("args", {})

            if tool_name not in TOOLS:
                self._json_response({"error": f"Unknown tool: {tool_name}"}, 400)
                return

            try:
                # Convert args to proper types
                tool = TOOLS[tool_name]
                typed_args = {}
                for param in tool["params"]:
                    if param["name"] in args:
                        val = args[param["name"]]
                        if param["type"] == "number" and isinstance(val, str):
                            val = float(val) if "." in val else int(val)
                        elif param["type"] == "boolean" and isinstance(val, str):
                            val = val.lower() in ("true", "1", "yes")
                        elif param["type"] == "json" and isinstance(val, str):
                            val = json.loads(val)
                        typed_args[param["name"]] = val

                result = tool["fn"](**typed_args)
                self._json_response({"result": result})
            except Exception as e:
                self._json_response({"error": str(e)}, 500)
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Suppress default logging for cleaner output."""
        pass


def main():
    port = 8765
    server = HTTPServer(("0.0.0.0", port), AbletonHandler)
    print(f"🎛️  Ableton MCP Command Panel")
    print(f"   http://localhost:{port}")
    print(f"   {len(TOOLS)} tools available")
    print(f"   Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped")
        server.server_close()


if __name__ == "__main__":
    main()
