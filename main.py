import os
import sys

from kivy.config import Config
Config.set("graphics", "orientation", "landscape")
Config.set("kivy", "keyboard_mode", "system")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock

from config import APP_NAME, APP_VERSION, DEFAULT_CANDIDATES, COLORS, hex_to_kivy
from database import init_db, record_vote
from ws_server import WebSocketServer
from evm_logger import get_logger, add_log_callback
from screens.settings import load_settings, apply_orientation

log = get_logger("smart_evm.main")

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
BG_SIDEBAR = hex_to_kivy(COLORS["bg_sidebar"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])
ACCENT_GREEN = hex_to_kivy(COLORS["accent_green"])
ACCENT_RED = hex_to_kivy(COLORS["accent_red"])
ACCENT_ORANGE = hex_to_kivy(COLORS["accent_orange"])

NAV_ITEMS = [
    ("dashboard", "🏠", "Dashboard"),
    ("results",   "📊", "Results"),
    ("logs",      "📋", "Logs"),
    ("settings",  "⚙️",  "Settings"),
    ("export",    "📤", "Export"),
    ("debug",     "🔧", "Debug"),
]


class NavButton(Button):
    def __init__(self, name, icon, label, **kwargs):
        super().__init__(
            text=f"{icon}\n{label}",
            font_size="9sp",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=TEXT_MUTED,
            **kwargs
        )
        self.screen_name = name
        self._active = False
        self.bind(size=self.setter("text_size"))

    def set_active(self, active: bool):
        self._active = active
        self.color = ACCENT if active else TEXT_MUTED


class EvmApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.candidate_map = dict(DEFAULT_CANDIDATES)
        self._ws_server = None
        self._dashboard = None
        self._results = None
        self._logs = None
        self._settings_screen = None
        self._export = None
        self._debug = None
        self._nav_buttons: dict[str, NavButton] = {}
        self._sm: ScreenManager = None
        self._current_tab = "dashboard"

    def build(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*BG_PRIMARY)
            self._root_bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self._root_bg, "pos", root.pos),
                  size=lambda *a: setattr(self._root_bg, "size", root.size))

        self._sm = ScreenManager(transition=NoTransition())
        self._build_screens()
        root.add_widget(self._sm)

        nav = self._build_nav()
        root.add_widget(nav)

        return root

    def _build_screens(self):
        from screens.dashboard import DashboardScreen
        from screens.results import ResultsScreen
        from screens.logs import LogsScreen
        from screens.settings import SettingsScreen
        from screens.export import ExportScreen
        from screens.debug import DebugScreen

        self._dashboard = DashboardScreen(self.candidate_map)
        self._results = ResultsScreen(self.candidate_map)
        self._logs = LogsScreen()
        self._settings_screen = SettingsScreen(
            self.candidate_map,
            on_names_changed=self._on_names_changed,
            on_session_cleared=self._on_session_cleared,
        )
        self._export = ExportScreen(self.candidate_map)
        self._debug = DebugScreen()

        screens_data = [
            ("dashboard", self._dashboard),
            ("results",   self._results),
            ("logs",      self._logs),
            ("settings",  self._settings_screen),
            ("export",    self._export),
            ("debug",     self._debug),
        ]
        for name, widget in screens_data:
            s = Screen(name=name)
            s.add_widget(widget)
            self._sm.add_widget(s)

    def _build_nav(self) -> BoxLayout:
        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56),
                        spacing=0)
        with nav.canvas.before:
            Color(*BG_SIDEBAR)
            self._nav_bg = Rectangle(pos=nav.pos, size=nav.size)
        nav.bind(pos=lambda *a: setattr(self._nav_bg, "pos", nav.pos),
                 size=lambda *a: setattr(self._nav_bg, "size", nav.size))

        for name, icon, label in NAV_ITEMS:
            btn = NavButton(name, icon, label)
            btn.bind(on_press=lambda b, n=name: self._navigate(n))
            self._nav_buttons[name] = btn
            nav.add_widget(btn)

        self._nav_buttons["dashboard"].set_active(True)
        return nav

    def _navigate(self, name: str):
        self._current_tab = name
        self._sm.current = name
        for n, btn in self._nav_buttons.items():
            btn.set_active(n == name)
        if name == "results":
            self._results.refresh()
        elif name == "logs":
            self._logs.refresh()

    def on_start(self):
        init_db()
        add_log_callback(self._on_log)
        settings = load_settings()
        apply_orientation(settings.get("orientation", "landscape") == "landscape")
        Clock.schedule_once(self._start_ws_server, 0.5)

    def on_stop(self):
        if self._ws_server:
            self._ws_server.stop()

    def _start_ws_server(self, dt=None):
        self._ws_server = WebSocketServer()
        self._ws_server.on_vote = self._on_vote
        self._ws_server.on_error = self._on_error
        self._ws_server.on_hold_start = self._on_hold_start
        self._ws_server.on_hold_cancel = self._on_hold_cancel
        self._ws_server.on_client_connected = self._on_esp_connected
        self._ws_server.on_client_disconnected = self._on_esp_disconnected
        self._ws_server.on_server_started = self._on_server_started
        self._ws_server.on_server_stopped = self._on_server_stopped
        self._ws_server.start()

    def _on_server_started(self, port: int):
        if self._dashboard:
            self._dashboard.set_status(f"⬤ Listening :{port}", ACCENT_GREEN)
        log.info("WebSocket server ready on port %d", port)

    def _on_server_stopped(self):
        if self._dashboard:
            self._dashboard.set_status("⬤ Server offline", ACCENT_RED)

    def _on_esp_connected(self, addr: str):
        if self._dashboard:
            self._dashboard.set_status(f"⬤ ESP {addr}", ACCENT_GREEN)
        log.info("ESP8266 connected from %s", addr)

    def _on_esp_disconnected(self, addr: str):
        if self._dashboard:
            self._dashboard.set_status("⬤ ESP disconnected", ACCENT_ORANGE)
        log.warning("ESP8266 disconnected: %s", addr)

    def _on_vote(self, candidate_id: int):
        name = self.candidate_map.get(candidate_id, f"Candidate {candidate_id}")
        record_vote(candidate_id, name, "vote")
        log.info("Vote Accepted → %s (ID %d)", name, candidate_id)
        if self._dashboard:
            self._dashboard.complete_hold()
            self._dashboard.start_lockout()
            self._dashboard.refresh()

    def _on_error(self, reason: str):
        record_vote(0, "N/A", f"error:{reason}")
        log.warning("Error → %s", reason)

    def _on_hold_start(self, candidate_id: int):
        if self._dashboard:
            self._dashboard.start_hold(candidate_id)

    def _on_hold_cancel(self, candidate_id: int):
        if self._dashboard:
            self._dashboard.cancel_hold(candidate_id)

    def _on_names_changed(self, candidate_map: dict):
        self.candidate_map = candidate_map
        if self._dashboard:
            self._dashboard.update_candidate_names(candidate_map)
        if self._results:
            self._results.update_candidate_names(candidate_map)
        if self._export:
            self._export.update_candidate_names(candidate_map)
        log.info("Candidate names updated")

    def _on_session_cleared(self):
        if self._dashboard:
            self._dashboard.refresh()
        if self._results:
            self._results.refresh()
        if self._logs:
            self._logs.refresh()
        log.info("Session cleared — new election started")

    def _on_log(self, level: str, line: str):
        if self._debug:
            self._debug.append_entry(level, line)
        if self._dashboard:
            self._dashboard.append_log(level, line)


def main():
    EvmApp().run()


if __name__ == "__main__":
    main()
