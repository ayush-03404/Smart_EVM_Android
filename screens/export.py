import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock

from config import COLORS, hex_to_kivy
from database import get_total_votes
from excel_export import export as do_export

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_CARD = hex_to_kivy(COLORS["bg_card"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])
ACCENT_GREEN = hex_to_kivy(COLORS["accent_green"])
ACCENT_RED = hex_to_kivy(COLORS["accent_red"])


def _make_card():
    card = BoxLayout(orientation="vertical", spacing=dp(12),
                     padding=[dp(20), dp(16)], size_hint_y=None)
    card.bind(minimum_height=card.setter("height"))
    with card.canvas.before:
        Color(*BG_CARD)
        rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(10)])
    card.bind(pos=lambda *a: setattr(rect, "pos", card.pos),
              size=lambda *a: setattr(rect, "size", card.size))
    return card


def _btn(text, color_rgba, solid=False):
    if solid:
        b = Button(text=text, font_size="13sp", color=(0, 0, 0, 1),
                   background_color=color_rgba, background_normal="",
                   size_hint_y=None, height=dp(44))
    else:
        b = Button(text=text, font_size="12sp", color=color_rgba,
                   background_color=(0, 0, 0, 0), background_normal="",
                   size_hint_y=None, height=dp(36))
    return b


class ExportScreen(BoxLayout):
    def __init__(self, candidate_map: dict, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._candidate_map = candidate_map
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
        top.add_widget(Label(text="📤  Export", font_size="16sp", color=TEXT_PRIMARY,
                             bold=True, halign="left"))
        self.add_widget(top)

        sv = ScrollView()
        content = BoxLayout(orientation="vertical", spacing=dp(16),
                            padding=[dp(16), dp(16)], size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))

        card = _make_card()

        icon = Label(text="📊", font_size="40sp", size_hint_y=None, height=dp(60))
        card.add_widget(icon)

        title = Label(text="Export Results to Excel", font_size="15sp",
                      color=TEXT_PRIMARY, bold=True, size_hint_y=None, height=dp(30))
        card.add_widget(title)

        desc = Label(
            text="Generates a professional .xlsx report containing:\n"
                 "  •  Vote totals per candidate\n"
                 "  •  Bar chart and pie chart\n"
                 "  •  Full timestamped event log",
            font_size="12sp", color=TEXT_MUTED,
            size_hint_y=None, height=dp(80),
            halign="center", valign="middle",
        )
        desc.bind(size=desc.setter("text_size"))
        card.add_widget(desc)

        self._votes_lbl = Label(text="0 vote(s) will be exported",
                                font_size="12sp", color=ACCENT,
                                size_hint_y=None, height=dp(24))
        card.add_widget(self._votes_lbl)

        self._path_lbl = Label(text="Tap Export to generate file",
                               font_size="10sp", color=TEXT_MUTED,
                               size_hint_y=None, height=dp(40),
                               halign="center", valign="middle")
        self._path_lbl.bind(size=self._path_lbl.setter("text_size"))
        card.add_widget(self._path_lbl)

        self._progress = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        self._progress.opacity = 0
        card.add_widget(self._progress)

        self._export_btn = _btn("Export to Excel", ACCENT_GREEN, solid=True)
        self._export_btn.bind(on_press=self._do_export)
        card.add_widget(self._export_btn)

        content.add_widget(card)
        sv.add_widget(content)
        self.add_widget(sv)
        self._update_count()

    def _update_count(self):
        self._votes_lbl.text = f"{get_total_votes()} vote(s) will be exported"

    def _do_export(self, *a):
        self._update_count()
        self._export_btn.disabled = True
        self._progress.opacity = 1

        def _run():
            try:
                path = do_export(self._candidate_map)
                Clock.schedule_once(lambda dt: self._on_done(path), 0)
            except Exception as exc:
                Clock.schedule_once(lambda dt: self._on_fail(str(exc)), 0)

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, path: str):
        self._progress.opacity = 0
        self._export_btn.disabled = False
        self._path_lbl.text = f"Saved:\n{path}"
        self._path_lbl.color = ACCENT_GREEN

    def _on_fail(self, msg: str):
        self._progress.opacity = 0
        self._export_btn.disabled = False
        self._path_lbl.text = f"Export failed: {msg}"
        self._path_lbl.color = ACCENT_RED

    def update_candidate_names(self, candidate_map: dict):
        self._candidate_map = candidate_map
