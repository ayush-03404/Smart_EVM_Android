from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

from config import COLORS, hex_to_kivy
from database import get_all_events

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_CARD = hex_to_kivy(COLORS["bg_card"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])
ACCENT_GREEN = hex_to_kivy(COLORS["accent_green"])
ACCENT_RED = hex_to_kivy(COLORS["accent_red"])


def _tab_btn(text, active=False):
    bg = ACCENT if active else hex_to_kivy(COLORS["bg_card"])
    fg = (0, 0, 0, 1) if active else TEXT_MUTED
    btn = Button(text=text, font_size="11sp", color=fg,
                 background_color=bg, background_normal="",
                 size_hint_y=None, height=dp(32))
    return btn


class LogRow(BoxLayout):
    def __init__(self, evt, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(38), spacing=dp(6), padding=[dp(4), dp(2)], **kwargs)
        is_vote = evt["event_type"] == "vote"
        color = ACCENT_GREEN if is_vote else ACCENT_RED

        with self.canvas.before:
            Color(*BG_CARD)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._u, size=self._u)

        for text, sx in [
            (str(evt["id"]), 0.06),
            (evt["timestamp"], 0.25),
            (str(evt["candidate_id"]), 0.07),
            (evt["candidate_name"], 0.30),
        ]:
            lbl = Label(text=text, font_size="10sp", color=TEXT_PRIMARY,
                        size_hint_x=sx, halign="center", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            self.add_widget(lbl)

        type_lbl = Label(text=evt["event_type"].upper(), font_size="10sp",
                         color=color, bold=True, size_hint_x=0.18,
                         halign="center", valign="middle")
        type_lbl.bind(size=type_lbl.setter("text_size"))
        self.add_widget(type_lbl)

    def _u(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


class LogsScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._filter = 0
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

        top.add_widget(Label(text="📋  Event Logs", font_size="16sp", color=TEXT_PRIMARY,
                             bold=True, size_hint_x=1, halign="left"))

        self._all_btn = _tab_btn("All", active=True)
        self._vote_btn = _tab_btn("Votes")
        self._err_btn = _tab_btn("Errors")
        self._all_btn.bind(on_press=lambda *a: self._set_filter(0))
        self._vote_btn.bind(on_press=lambda *a: self._set_filter(1))
        self._err_btn.bind(on_press=lambda *a: self._set_filter(2))
        for b in [self._all_btn, self._vote_btn, self._err_btn]:
            b.size_hint_x = None
            b.width = dp(70)
            top.add_widget(b)
        self.add_widget(top)

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32),
                           padding=[dp(4), 0], spacing=dp(6))
        with header.canvas.before:
            Color(*BG_SECONDARY)
            self._hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self._hbg, "pos", header.pos),
                    size=lambda *a: setattr(self._hbg, "size", header.size))
        for text, sx in [("ID", 0.06), ("Timestamp", 0.25), ("C.ID", 0.07),
                         ("Candidate", 0.30), ("Type", 0.18)]:
            lbl = Label(text=text, font_size="9sp", color=TEXT_MUTED,
                        size_hint_x=sx, halign="center")
            lbl.bind(size=lbl.setter("text_size"))
            header.add_widget(lbl)
        self.add_widget(header)

        sv = ScrollView()
        self._list = BoxLayout(orientation="vertical", spacing=dp(2),
                               size_hint_y=None, padding=[dp(4), dp(4)])
        self._list.bind(minimum_height=self._list.setter("height"))
        sv.add_widget(self._list)
        self.add_widget(sv)

        self._count_lbl = Label(text="", font_size="11sp", color=TEXT_MUTED,
                                size_hint_y=None, height=dp(26))
        self.add_widget(self._count_lbl)

        self.refresh()

    def _set_filter(self, idx):
        self._filter = idx
        for i, b in enumerate([self._all_btn, self._vote_btn, self._err_btn]):
            if i == idx:
                b.background_color = ACCENT
                b.color = (0, 0, 0, 1)
            else:
                b.background_color = BG_CARD
                b.color = TEXT_MUTED
        self.refresh()

    def refresh(self):
        self._list.clear_widgets()
        events = get_all_events()
        if self._filter == 1:
            events = [e for e in events if e["event_type"] == "vote"]
        elif self._filter == 2:
            events = [e for e in events if e["event_type"] != "vote"]

        for evt in events:
            self._list.add_widget(LogRow(evt))

        self._count_lbl.text = f"  Showing {len(events)} record(s)"
