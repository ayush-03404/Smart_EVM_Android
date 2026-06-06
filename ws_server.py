import asyncio
import json
import threading
from typing import Callable, Optional

import websockets
from kivy.clock import Clock

from config import WS_HOST, WS_PORT
from evm_logger import get_logger

log = get_logger("smart_evm.ws")


class WebSocketServer:
    def __init__(self):
        self.on_vote: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_hold_start: Optional[Callable] = None
        self.on_hold_cancel: Optional[Callable] = None
        self.on_client_connected: Optional[Callable] = None
        self.on_client_disconnected: Optional[Callable] = None
        self.on_server_started: Optional[Callable] = None
        self.on_server_stopped: Optional[Callable] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def _emit(self, cb, *args):
        if cb is not None:
            Clock.schedule_once(lambda dt: cb(*args), 0)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ws-server")
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as exc:
            log.error("WebSocket loop error: %s", exc)
        finally:
            self._loop.close()
            self._emit(self.on_server_stopped)

    async def _serve(self):
        log.info("Starting WebSocket server on %s:%s", WS_HOST, WS_PORT)
        async with websockets.serve(self._handler, WS_HOST, WS_PORT):
            self._emit(self.on_server_started, WS_PORT)
            await asyncio.Future()

    async def _handler(self, websocket):
        addr = websocket.remote_address
        remote = f"{addr[0]}:{addr[1]}" if addr else "unknown"
        log.info("ESP connected from %s", remote)
        self._emit(self.on_client_connected, remote)
        try:
            async for raw in websocket:
                self._process(raw)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            log.info("ESP disconnected: %s", remote)
            self._emit(self.on_client_disconnected, remote)

    def _process(self, raw: str):
        try:
            pkt = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Malformed packet: %s", raw)
            return

        pkt_type = pkt.get("type")
        if pkt_type == "vote":
            cid = pkt.get("candidate_id")
            if isinstance(cid, int) and 1 <= cid <= 5:
                log.info("Vote received → candidate %d", cid)
                self._emit(self.on_vote, cid)
            else:
                log.warning("Invalid candidate_id: %s", pkt)

        elif pkt_type == "error":
            reason = pkt.get("reason", "unknown")
            log.warning("ESP error → %s", reason)
            self._emit(self.on_error, reason)

        elif pkt_type == "hold_start":
            cid = pkt.get("candidate_id")
            if isinstance(cid, int) and 1 <= cid <= 5:
                log.info("Hold started → candidate %d", cid)
                self._emit(self.on_hold_start, cid)

        elif pkt_type == "hold_cancel":
            cid = pkt.get("candidate_id")
            if isinstance(cid, int) and 1 <= cid <= 5:
                log.info("Hold cancelled → candidate %d", cid)
                self._emit(self.on_hold_cancel, cid)

        else:
            log.warning("Unknown packet type: %s", pkt_type)
