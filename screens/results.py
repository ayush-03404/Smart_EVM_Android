from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock

from config import COLORS, ACCENT_COLORS_RGBA, hex_to_kivy
from database import get_vote_totals, get_total_votes

BG_PRIMARY = hex_to_kivy(COLORS["bg_primary"])
BG_CARD = hex_to_kivy(COLORS["bg_card"])
BG_SECONDARY = hex_to_kivy(COLORS["bg_secondary"])
BORDER = hex_to_kivy(COLORS["border"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
ACCENT = hex_to_kivy(COLORS["accent"])
ACCENT_GREEN = hex_to_kivy(COLORS["accent_green"])
ACCENT_RED = hex_to_kivy(COLORS["accent_red"])


def _h(text, size="11sp", color=None, bold=False, halign="center"):
    lbl = Label(text=text, font_size=size, color=color or TEXT_MUTED, bold=bold,
                halign=halign, valign="middle")
    lbl.bind(size=lbl.setter("text_size"))
    return lbl


class ResultRow(BoxLayout):
    def __init__(self, rank, cid, name, votes, share, is_leader=False, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(40),
                         spacing=dp(4), **kwargs)
        color = ACCENT_COLORS_RGBA[(cid - 1) % len(ACCENT_COLORS_RGBA)]
        text_color = color if is_leader else TEXT_PRIMARY

        with self.canvas.before:
            Color(*BG_CARD)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._upd, size=self._upd)

        for text, weight in [
            (str(rank), 0.08),
            (str(cid), 0.08),
            (name, 0.35),
            (str(votes), 0.15),
            (f"{share:.1f}%", 0.15),
        ]:
            lbl = Label(text=text, font_size="12sp", color=text_color,
                        bold=is_leader, size_hint_x=weight,
                        halign="center", valign="middle")
            lbl.bind(size=lbl.setter("text_size"))
            self.add_widget(lbl)

    def _upd(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


class ResultsScreen(BoxLayout):
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
                        padding=[dp(16), dp(8)], spacing=dp(12))
        with top.canvas.before:
            Color(*hex_to_kivy(COLORS["bg_secondary"]))
            self._top_bg = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda *a: setattr(self._top_bg, "pos", top.pos),
                 size=lambda *a: setattr(self._top_bg, "size", top.size))

        top.add_widget(Label(text="📊  Results", font_size="16sp", color=TEXT_PRIMARY,
                             bold=True, size_hint_x=1, halign="left", valign="middle",
                             text_size=(None, None)))

        self._total_lbl = Label(text="Total: 0 votes", font_size="12sp", color=ACCENT,
                                size_hint_x=None, width=dp(140), halign="right")
        self._total_lbl.bind(size=self._total_lbl.setter("text_size"))
        top.add_widget(self._total_lbl)
        self.add_widget(top)

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36),
                           padding=[dp(4), 0], spacing=dp(4))
        with header.canvas.before:
            Color(*BG_SECONDARY)
            self._hbg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self._hbg, "pos", header.pos),
                    size=lambda *a: setattr(self._hbg, "size", header.size))
        for text, weight in [("Rank", 0.08), ("ID", 0.08), ("Candidate", 0.35),
                              ("Votes", 0.15), ("Share %", 0.15)]:
            header.add_widget(_h(text, "10sp", TEXT_MUTED, True))
        self.add_widget(header)

        sv = ScrollView()
        self._list = BoxLayout(orientation="vertical", spacing=dp(2),
                               size_hint_y=None, padding=[dp(4), dp(4)])
        self._list.bind(minimum_height=self._list.setter("height"))
        sv.add_widget(self._list)
        self.add_widget(sv)

        self._footer = Label(text="", font_size="11sp", color=TEXT_MUTED,
                             size_hint_y=None, height=dp(28))
        self.add_widget(self._footer)

        self.refresh()

    def refresh(self):
        self._list.clear_widgets()
        totals = get_vote_totals()
        total = get_total_votes()
        self._total_lbl.text = f"Total: {total} votes"

        ranked = sorted(self._candidate_map.items(),
                        key=lambda x: totals.get(x[0], 0), reverse=True)
        max_v = max(totals.values(), default=0) if totals else 0

        for rank, (cid, name) in enumerate(ranked, start=1):
            votes = totals.get(cid, 0)
            share = (votes / total * 100) if total > 0 else 0.0
            is_leader = (votes == max_v and votes > 0)
            row = ResultRow(rank, cid, name, votes, share, is_leader,
                            size_hint_y=None, height=dp(40))
            self._list.add_widget(row)

        self._footer.text = f"Showing {len(ranked)} candidates — {total} total vote(s)"

    def update_candidate_names(self, candidate_map: dict):
        self._candidate_map = candidate_map
        self.refresh()
