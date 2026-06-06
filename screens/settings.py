import json
import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.utils import platform

from config import COLORS, CANDIDATE_COUNT, WS_PORT, ACCENT_COLORS_HEX, hex_to_kivy
from database import clear_all

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_CARD = hex_to_kivy(COLORS["bg_card"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])
ACCENT_GREEN = hex_to_kivy(COLORS["accent_green"])
ACCENT_RED = hex_to_kivy(COLORS["accent_red"])
ACCENT_ORANGE = hex_to_kivy(COLORS["accent_orange"])


def _card(border_color=None):
    bc = border_color or BG_SECONDARY
    card = BoxLayout(orientation="vertical", spacing=dp(10),
                     padding=[dp(16), dp(14)], size_hint_y=None)
    card.bind(minimum_height=card.setter("height"))
    with card.canvas.before:
        Color(*BG_CARD)
        rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(8)])
        Color(*bc)
        from kivy.graphics import Line
    card.bind(pos=lambda *a: setattr(rect, "pos", card.pos),
              size=lambda *a: setattr(rect, "size", card.size))
    return card


def _section_title(text, color=None):
    lbl = Label(text=text, font_size="13sp", color=color or TEXT_PRIMARY,
                bold=True, size_hint_y=None, height=dp(28), halign="left")
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def _sub(text):
    lbl = Label(text=text, font_size="11sp", color=TEXT_MUTED,
                size_hint_y=None, height=dp(22), halign="left")
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


def _action_btn(text, color_rgba):
    b = Button(text=text, font_size="12sp", color=color_rgba,
               background_color=(color_rgba[0], color_rgba[1], color_rgba[2], 0.15),
               background_normal="", size_hint_y=None, height=dp(38))
    return b


def _settings_path() -> str:
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app:
            return os.path.join(app.user_data_dir, "settings.json")
    except Exception:
        pass
    return "evm_settings.json"


def load_settings() -> dict:
    try:
        path = _settings_path()
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {"orientation": "landscape"}


def save_settings(data: dict):
    try:
        path = _settings_path()
        with open(path, "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def apply_orientation(landscape: bool):
    if platform == "android":
        try:
            from jnius import autoclass
            ActivityInfo = autoclass("android.content.pm.ActivityInfo")
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            if landscape:
                activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE)
            else:
                activity.setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT)
        except Exception:
            pass
    else:
        from kivy.core.window import Window
        if landscape:
            Window.size = (1280, 720)
        else:
            Window.size = (720, 1280)


class SettingsScreen(BoxLayout):
    def __init__(self, candidate_map: dict, on_names_changed=None,
                 on_session_cleared=None, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._candidate_map = dict(candidate_map)
        self._inputs: dict[int, TextInput] = {}
        self._on_names_changed = on_names_changed
        self._on_session_cleared = on_session_cleared
        self._settings = load_settings()
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(*BG_PRIMARY)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                        padding=[dp(16), dp(8)])
        with top.canvas.before:
            Color(*BG_SECONDARY)
            self._top_bg = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda *a: setattr(self._top_bg, "pos", top.pos),
                 size=lambda *a: setattr(self._top_bg, "size", top.size))
        top.add_widget(Label(text="⚙️  Settings", font_size="16sp", color=TEXT_PRIMARY,
                             bold=True, halign="left"))
        self.add_widget(top)

        sv = ScrollView()
        content = BoxLayout(orientation="vertical", spacing=dp(14),
                            padding=[dp(14), dp(14)], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        # Candidate names card
        cand = _card()
        cand.add_widget(_section_title("Candidate Names"))
        cand.add_widget(_sub("Edit the names mapped to each hardware button (1–5)."))

        for cid in range(1, CANDIDATE_COUNT + 1):
            row = BoxLayout(orientation="horizontal", size_hint_y=None,
                            height=dp(40), spacing=dp(8))
            badge_color = hex_to_kivy(ACCENT_COLORS_HEX[(cid - 1) % len(ACCENT_COLORS_HEX)])
            badge = Label(text=str(cid), font_size="12sp", color=(0, 0, 0, 1),
                          bold=True, size_hint_x=None, width=dp(32))
            with badge.canvas.before:
                Color(*badge_color)
                r = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(4)])
            badge.bind(pos=lambda *a, _r=r, _b=badge: setattr(_r, "pos", _b.pos),
                       size=lambda *a, _r=r, _b=badge: setattr(_r, "size", _b.size))
            row.add_widget(badge)

            ti = TextInput(
                text=self._candidate_map.get(cid, f"Candidate {cid}"),
                font_size="13sp",
                foreground_color=TEXT_PRIMARY,
                background_color=hex_to_kivy(COLORS["bg_secondary"]),
                cursor_color=ACCENT,
                multiline=False,
                size_hint_y=None, height=dp(36),
            )
            self._inputs[cid] = ti
            row.add_widget(ti)
            cand.add_widget(row)

        save_btn = _action_btn("Save Names", ACCENT)
        save_btn.bind(on_press=self._save_names)
        cand.add_widget(save_btn)
        content.add_widget(cand)

        # Orientation card
        orient = _card()
        orient.add_widget(_section_title("Screen Orientation"))
        orient.add_widget(_sub("Switch between landscape and portrait mode."))
        is_land = self._settings.get("orientation", "landscape") == "landscape"

        orient_row = BoxLayout(orientation="horizontal", size_hint_y=None,
                               height=dp(42), spacing=dp(10))
        self._land_btn = _action_btn("⇔ Landscape", ACCENT_GREEN if is_land else TEXT_MUTED)
        self._port_btn = _action_btn("⇕ Portrait", ACCENT_GREEN if not is_land else TEXT_MUTED)
        self._land_btn.bind(on_press=lambda *a: self._set_orientation("landscape"))
        self._port_btn.bind(on_press=lambda *a: self._set_orientation("portrait"))
        orient_row.add_widget(self._land_btn)
        orient_row.add_widget(self._port_btn)
        orient.add_widget(orient_row)
        content.add_widget(orient)

        # Network info card
        net = _card()
        net.add_widget(_section_title("Network Configuration"))
        for label, value in [
            ("WebSocket Port", str(WS_PORT)),
            ("ESP8266 SSID", "SMART_EVM"),
            ("ESP8266 Password", "12345678"),
            ("ESP8266 IP", "192.168.4.1"),
            ("Phone IP (assigned)", "192.168.4.2"),
        ]:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28))
            k = Label(text=label + ":", font_size="11sp", color=TEXT_MUTED,
                      size_hint_x=0.5, halign="left")
            k.bind(size=k.setter("text_size"))
            v = Label(text=value, font_size="11sp", color=TEXT_PRIMARY,
                      bold=True, size_hint_x=0.5, halign="left")
            v.bind(size=v.setter("text_size"))
            row.add_widget(k)
            row.add_widget(v)
            net.add_widget(row)
        content.add_widget(net)

        # Danger zone card
        danger = _card()
        danger.add_widget(_section_title("Danger Zone", ACCENT_RED))
        danger.add_widget(_sub("Delete all vote records and start a fresh election session."))
        clear_btn = _action_btn("🗑  Clear All Data", ACCENT_RED)
        clear_btn.bind(on_press=self._confirm_clear)
        danger.add_widget(clear_btn)
        content.add_widget(danger)

        sv.add_widget(content)
        self.add_widget(sv)

    def _save_names(self, *a):
        for cid, ti in self._inputs.items():
            name = ti.text.strip() or f"Candidate {cid}"
            self._candidate_map[cid] = name
        if self._on_names_changed:
            self._on_names_changed(dict(self._candidate_map))
        self._show_toast("Candidate names saved.")

    def _set_orientation(self, mode: str):
        self._settings["orientation"] = mode
        save_settings(self._settings)
        apply_orientation(mode == "landscape")
        is_land = (mode == "landscape")
        self._land_btn.color = ACCENT_GREEN if is_land else TEXT_MUTED
        self._port_btn.color = ACCENT_GREEN if not is_land else TEXT_MUTED

    def _confirm_clear(self, *a):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label as KLabel
        from kivy.uix.boxlayout import BoxLayout as KBox

        content = KBox(orientation="vertical", padding=dp(16), spacing=dp(12))
        content.add_widget(KLabel(
            text="This will permanently delete ALL vote records.\nAre you sure?",
            font_size="13sp", color=TEXT_PRIMARY, halign="center",
        ))
        btn_row = KBox(orientation="horizontal", size_hint_y=None, height=dp(42), spacing=dp(10))
        yes = Button(text="Yes, Clear All", font_size="12sp",
                     background_color=ACCENT_RED, background_normal="", color=(1, 1, 1, 1))
        no = Button(text="Cancel", font_size="12sp",
                    background_color=BG_SECONDARY, background_normal="", color=TEXT_PRIMARY)
        btn_row.add_widget(yes)
        btn_row.add_widget(no)
        content.add_widget(btn_row)

        popup = Popup(title="Clear All Data", content=content,
                      size_hint=(0.7, 0.4))

        def _do_clear(*a):
            clear_all()
            popup.dismiss()
            if self._on_session_cleared:
                self._on_session_cleared()
            self._show_toast("All data cleared. New session started.")

        yes.bind(on_press=_do_clear)
        no.bind(on_press=popup.dismiss)
        popup.open()

    def _show_toast(self, msg: str):
        from kivy.uix.popup import Popup
        from kivy.uix.label import Label as KLabel
        p = Popup(title="", content=KLabel(text=msg, color=TEXT_PRIMARY,
                                           halign="center"),
                  size_hint=(0.6, 0.25))
        p.open()
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: p.dismiss(), 1.5)

    def update_candidate_names(self, candidate_map: dict):
        self._candidate_map = candidate_map
        for cid, ti in self._inputs.items():
            ti.text = candidate_map.get(cid, f"Candidate {cid}")
