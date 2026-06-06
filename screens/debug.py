from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from config import COLORS, hex_to_kivy

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_CARD = hex_to_kivy(COLORS["bg_card"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])

LEVEL_COLORS = {
    "DEBUG":    (0.431, 0.463, 0.506, 1),
    "INFO":     (0.345, 0.651, 1.000, 1),
    "WARNING":  (0.824, 0.600, 0.133, 1),
    "ERROR":    (0.973, 0.318, 0.286, 1),
    "CRITICAL": (1.000, 0.431, 0.431, 1),
}


class DebugScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._entries = []
        self._auto_scroll = True
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(*BG_PRIMARY)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                        padding=[dp(12), dp(8)], spacing=dp(8))
        with top.canvas.before:
            Color(*BG_SECONDARY)
            self._top_bg = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda *a: setattr(self._top_bg, "pos", top.pos),
                 size=lambda *a: setattr(self._top_bg, "size", top.size))

        top.add_widget(Label(text="🔧  Debugging Log", font_size="16sp",
                             color=TEXT_PRIMARY, bold=True, size_hint_x=1, halign="left"))

        as_btn = Button(text="Auto-scroll: ON", font_size="10sp",
                        color=ACCENT, background_color=(0, 0, 0, 0),
                        background_normal="", size_hint_x=None, width=dp(120))
        as_btn.bind(on_press=lambda *a: self._toggle_autoscroll(as_btn))
        top.add_widget(as_btn)
        self._as_btn = as_btn

        clear_btn = Button(text="Clear", font_size="11sp",
                           color=TEXT_MUTED, background_color=BG_CARD,
                           background_normal="", size_hint_x=None, width=dp(60),
                           size_hint_y=None, height=dp(32))
        clear_btn.bind(on_press=self._clear)
        top.add_widget(clear_btn)
        self.add_widget(top)

        legend = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24),
                           padding=[dp(12), 0], spacing=dp(16))
        with legend.canvas.before:
            Color(*BG_CARD)
            self._leg_bg = Rectangle(pos=legend.pos, size=legend.size)
        legend.bind(pos=lambda *a: setattr(self._leg_bg, "pos", legend.pos),
                    size=lambda *a: setattr(self._leg_bg, "size", legend.size))
        for lvl, c in LEVEL_COLORS.items():
            lbl = Label(text=f"● {lvl}", font_size="9sp", color=c,
                        size_hint_x=None, width=dp(70))
            legend.add_widget(lbl)
        self.add_widget(legend)

        self._sv = ScrollView()
        self._log_box = BoxLayout(orientation="vertical", spacing=dp(1),
                                  padding=[dp(10), dp(6)], size_hint_y=None)
        self._log_box.bind(minimum_height=self._log_box.setter("height"))
        self._sv.add_widget(self._log_box)
        self.add_widget(self._sv)

        self._status = Label(text="0 messages", font_size="10sp", color=TEXT_MUTED,
                             size_hint_y=None, height=dp(22))
        self.add_widget(self._status)

    def _toggle_autoscroll(self, btn):
        self._auto_scroll = not self._auto_scroll
        btn.text = f"Auto-scroll: {'ON' if self._auto_scroll else 'OFF'}"

    def _clear(self, *a):
        self._log_box.clear_widgets()
        self._entries.clear()
        self._status.text = "0 messages"

    def append_entry(self, level: str, line: str):
        color = LEVEL_COLORS.get(level, TEXT_MUTED)
        lbl = Label(text=line, font_size="10sp", color=color,
                    size_hint_y=None, halign="left", valign="top")
        lbl.bind(width=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
        lbl.bind(texture_size=lambda *a: setattr(lbl, "height", lbl.texture_size[1] + dp(4)))
        self._log_box.add_widget(lbl)
        self._entries.append(lbl)

        if len(self._entries) > 500:
            old = self._entries.pop(0)
            self._log_box.remove_widget(old)

        self._status.text = f"{len(self._entries)} messages"
        if self._auto_scroll:
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self._sv, "scroll_y", 0), 0.05)
