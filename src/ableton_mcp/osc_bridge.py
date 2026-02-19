"""
osc_bridge.py — OSC communication layer for AbletonOSC + ClyphX Pro.

AbletonOSC: sends on port 11000, receives responses on port 11001
ClyphX Pro: sends on port 7005 (one-way, no responses)
"""

import logging
import socket
import threading
import time
from typing import Any, Optional

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.udp_client import SimpleUDPClient

logger = logging.getLogger("ableton_mcp.osc_bridge")


class AbletonOSCBridge:
    """Bidirectional OSC bridge to AbletonOSC (port 11000 → 11001)."""

    def __init__(self, host: str = "127.0.0.1", send_port: int = 11000, recv_port: int = 11001):
        self.host = host
        self.send_port = send_port
        self.recv_port = recv_port
        self._client: Optional[SimpleUDPClient] = None
        self._server: Optional[ThreadingOSCUDPServer] = None
        self._handlers: dict[str, Any] = {}
        self._connected = False

    def connect(self) -> bool:
        """Start the OSC client and response listener."""
        try:
            self._client = SimpleUDPClient(self.host, self.send_port)

            # Set up response listener with port reuse
            dispatcher = Dispatcher()
            dispatcher.set_default_handler(self._on_message)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(("0.0.0.0", self.recv_port))

            self._server = ThreadingOSCUDPServer(
                ("0.0.0.0", self.recv_port), dispatcher, bind_and_activate=False
            )
            self._server.socket = sock
            self._server.server_activate()

            threading.Thread(target=self._server.serve_forever, daemon=True).start()
            self._connected = True
            logger.info(f"AbletonOSC bridge connected (send:{self.send_port} recv:{self.recv_port})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect AbletonOSC bridge: {e}")
            return False

    def disconnect(self):
        """Stop the response listener."""
        if self._server:
            self._server.shutdown()
            self._server = None
        self._connected = False
        logger.info("AbletonOSC bridge disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _on_message(self, address: str, *params):
        """Route incoming OSC messages to registered handlers."""
        if address in self._handlers:
            self._handlers[address](address, params)

    def send(self, address: str, params: tuple = ()):
        """Send a fire-and-forget OSC message to AbletonOSC."""
        if not self._client:
            raise ConnectionError("AbletonOSC bridge not connected")
        self._client.send_message(address, list(params))

    def query(self, address: str, params: tuple = (), timeout: float = 3.0) -> Optional[tuple]:
        """
        Send an OSC message and wait for a response.

        Returns the response params as a tuple, or None if timeout.
        """
        if not self._client:
            raise ConnectionError("AbletonOSC bridge not connected")

        result = None
        event = threading.Event()

        def callback(addr, p):
            nonlocal result
            result = p
            event.set()

        self._handlers[address] = callback
        self._client.send_message(address, list(params))
        event.wait(timeout)
        self._handlers.pop(address, None)

        if not event.is_set():
            logger.warning(f"Query timeout for {address}")
            return None
        return result

    def test_connection(self) -> bool:
        """Test if AbletonOSC is responding."""
        try:
            result = self.query("/live/song/get/tempo", timeout=2.0)
            return result is not None
        except Exception:
            return False


class ClyphXBridge:
    """One-way OSC bridge to ClyphX Pro (port 7005)."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7005):
        self.host = host
        self.port = port
        self._client: Optional[SimpleUDPClient] = None

    def connect(self) -> bool:
        """Create the OSC client for ClyphX Pro."""
        try:
            self._client = SimpleUDPClient(self.host, self.port)
            logger.info(f"ClyphX bridge connected (port:{self.port})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect ClyphX bridge: {e}")
            return False

    def disconnect(self):
        """No persistent connection to close for UDP."""
        self._client = None
        logger.info("ClyphX bridge disconnected")

    def action(self, action_string: str):
        """
        Send a ClyphX Pro action string.

        Examples:
            "1/LOADDEV \"Auto Filter\""
            "ADDAUDIO"
            "1/NAME \"Sub/Pad\" ; 1/COLOR 43"
        """
        if not self._client:
            raise ConnectionError("ClyphX bridge not connected")
        self._client.send_message("/clyphx/action", [action_string])
        logger.debug(f"ClyphX action: {action_string}")

    def action_with_delay(self, action_string: str, delay: float = 0.5):
        """Send a ClyphX action and wait for it to complete."""
        self.action(action_string)
        time.sleep(delay)
