from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar
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
ACCENT_ORANGE = hex_to_kivy(COLORS["accent_orange"])


def _set_bg(widget, color):
    with widget.canvas.before:
        c = Color(*color)
        r = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(pos=lambda *a: setattr(r, "pos", widget.pos),
                size=lambda *a: setattr(r, "size", widget.size))
    return r


class VoteCard(BoxLayout):
    ACCENT_COLORS = ACCENT_COLORS_RGBA

    def __init__(self, cid: int, name: str, **kwargs):
        super().__init__(orientation="vertical", padding=[dp(8), dp(6)],
                         spacing=dp(2), **kwargs)
        self.cid = cid
        self._color = self.ACCENT_COLORS[(cid - 1) % len(self.ACCENT_COLORS)]

        with self.canvas.before:
            Color(*BG_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*self._color)
            self._topbar = Rectangle(pos=self.pos, size=(self.width, dp(3)))
        self.bind(pos=self._redraw, size=self._redraw)

        self._name_lbl = Label(text=name.upper(), font_size="9sp", color=TEXT_MUTED,
                               bold=True, size_hint_y=None, height=dp(16),
                               halign="left")
        self._name_lbl.bind(size=self._name_lbl.setter("text_size"))
        self.add_widget(self._name_lbl)

        self._count_lbl = Label(text="0", font_size="24sp", color=self._color,
                                bold=True, size_hint_y=1, halign="center",
                                valign="middle")
        self._count_lbl.bind(size=self._count_lbl.setter("text_size"))
        self.add_widget(self._count_lbl)

        votes_lbl = Label(text="votes", font_size="9sp", color=TEXT_MUTED,
                          size_hint_y=None, height=dp(14), halign="center")
        votes_lbl.bind(size=votes_lbl.setter("text_size"))
        self.add_widget(votes_lbl)

    def _redraw(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._topbar.pos = (self.x, self.y + self.height - dp(3))
        self._topbar.size = (self.width, dp(3))

    def set_count(self, n: int):
        self._count_lbl.text = str(n)

    def set_name(self, name: str):
        self._name_lbl.text = name.upper()


class HoldBar(BoxLayout):
    HOLD_SECS = 2.0

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46),
                         padding=[dp(12), dp(6)], spacing=dp(10), **kwargs)
        with self.canvas.before:
            Color(*BG_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        self._icon = Label(text="⏳", font_size="16sp", size_hint_x=None, width=dp(28))
        self.add_widget(self._icon)

        mid = BoxLayout(orientation="vertical", spacing=dp(3))
        self._label = Label(text="Hold to vote…", font_size="12sp", color=TEXT_PRIMARY,
                            bold=True, halign="left", size_hint_y=None, height=dp(18))
        self._label.bind(size=self._label.setter("text_size"))
        self._pb = ProgressBar(max=100, value=0, size_hint_y=None, height=dp(6))
        mid.add_widget(self._label)
        mid.add_widget(self._pb)
        self.add_widget(mid)

        self._pct_lbl = Label(text="0%", font_size="13sp", color=ACCENT,
                              bold=True, size_hint_x=None, width=dp(44))
        self.add_widget(self._pct_lbl)

        self._elapsed = 0.0
        self._tick_ev = None
        self.opacity = 0
        self._candidate_id = -1

    def start(self, candidate_id: int, name: str):
        self._candidate_id = candidate_id
        self._elapsed = 0.0
        self._label.text = f"Holding for  {name.upper()}…"
        self._pb.value = 0
        self._pct_lbl.text = "0%"
        self.opacity = 1
        if self._tick_ev:
            self._tick_ev.cancel()
        self._tick_ev = Clock.schedule_interval(self._tick, 0.04)

    def cancel(self):
        if self._tick_ev:
            self._tick_ev.cancel()
        self.opacity = 0

    def complete(self):
        if self._tick_ev:
            self._tick_ev.cancel()
        self._pb.value = 100
        self._pct_lbl.text = "100%"
        self._label.text = "✅  Vote confirmed!"
        Clock.schedule_once(lambda dt: setattr(self, "opacity", 0), 0.8)

    def _tick(self, dt):
        self._elapsed += dt
        frac = min(self._elapsed / self.HOLD_SECS, 1.0)
        self._pb.value = frac * 100
        self._pct_lbl.text = f"{int(frac * 100)}%"
        if self._elapsed >= self.HOLD_SECS:
            if self._tick_ev:
                self._tick_ev.cancel()


class LockoutBanner(BoxLayout):
    LOCKOUT_SECS = 10.0

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=dp(46),
                         padding=[dp(12), dp(6)], spacing=dp(10), **kwargs)
        with self.canvas.before:
            Color(*BG_CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        self._icon = Label(text="🔒", font_size="16sp", size_hint_x=None, width=dp(28))
        self.add_widget(self._icon)

        mid = BoxLayout(orientation="vertical", spacing=dp(3))
        self._label = Label(text="Lockout active — no votes accepted",
                            font_size="12sp", color=TEXT_PRIMARY, bold=True,
                            halign="left", size_hint_y=None, height=dp(18))
        self._label.bind(size=self._label.setter("text_size"))
        self._pb = ProgressBar(max=100, value=100, size_hint_y=None, height=dp(6))
        mid.add_widget(self._label)
        mid.add_widget(self._pb)
        self.add_widget(mid)

        self._cd_lbl = Label(text="10s", font_size="16sp", color=ACCENT_RED,
                             bold=True, size_hint_x=None, width=dp(44))
        self.add_widget(self._cd_lbl)

        self._elapsed = 0.0
        self._tick_ev = None
        self.opacity = 0

    def start_lockout(self):
        self._elapsed = 0.0
        self._pb.value = 100
        self._cd_lbl.text = "10s"
        self._cd_lbl.color = ACCENT_RED
        self._icon.text = "🔒"
        self._label.text = "Lockout active — no votes accepted"
        self.opacity = 1
        if self._tick_ev:
            self._tick_ev.cancel()
        self._tick_ev = Clock.schedule_interval(self._tick, 0.1)

    def _tick(self, dt):
        self._elapsed += dt
        remaining = max(0.0, self.LOCKOUT_SECS - self._elapsed)
        self._pb.value = (remaining / self.LOCKOUT_SECS) * 100
        secs_left = int(remaining) + (1 if remaining % 1 > 0 else 0)
        self._cd_lbl.text = f"{secs_left}s"

        if remaining <= 3.0:
            self._cd_lbl.color = ACCENT_ORANGE

        if self._elapsed >= self.LOCKOUT_SECS:
            if self._tick_ev:
                self._tick_ev.cancel()
            self._icon.text = "✅"
            self._label.text = "Ready — lockout cleared"
            self._cd_lbl.text = "0s"
            self._cd_lbl.color = ACCENT_GREEN
            self._pb.value = 0
            Clock.schedule_once(lambda dt: setattr(self, "opacity", 0), 1.2)


class DashboardScreen(BoxLayout):
    def __init__(self, candidate_map: dict, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._candidate_map = candidate_map
        self._vote_cards: dict[int, VoteCard] = {}
        self._live_log_entries = []
        self._build_ui()
        self._refresh_timer = Clock.schedule_interval(lambda dt: self.refresh(), 2.0)

    def _build_ui(self):
        with self.canvas.before:
            Color(*BG_PRIMARY)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *a: setattr(self._bg, "pos", self.pos),
                  size=lambda *a: setattr(self._bg, "size", self.size))

        top = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48),
                        padding=[dp(16), dp(8)], spacing=dp(12))
        with top.canvas.before:
            Color(*BG_SECONDARY)
            self._top_bg = Rectangle(pos=top.pos, size=top.size)
        top.bind(pos=lambda *a: setattr(self._top_bg, "pos", top.pos),
                 size=lambda *a: setattr(self._top_bg, "size", top.size))
        top.add_widget(Label(text="🏠  Dashboard", font_size="16sp", color=TEXT_PRIMARY,
                             bold=True, size_hint_x=1, halign="left"))
        self._total_lbl = Label(text="Total Votes: 0", font_size="12sp", color=ACCENT,
                                size_hint_x=None, width=dp(160), halign="right")
        self._total_lbl.bind(size=self._total_lbl.setter("text_size"))
        top.add_widget(self._total_lbl)

        self._status_lbl = Label(text="⬤ Starting…", font_size="11sp", color=ACCENT_ORANGE,
                                 size_hint_x=None, width=dp(200), halign="right")
        top.add_widget(self._status_lbl)
        self.add_widget(top)

        main = BoxLayout(orientation="horizontal", spacing=dp(8), padding=[dp(8), dp(6)])

        left = BoxLayout(orientation="vertical", spacing=dp(6), size_hint_x=0.72)

        self._hold_bar = HoldBar()
        left.add_widget(self._hold_bar)
        self._lockout_banner = LockoutBanner()
        left.add_widget(self._lockout_banner)

        cards_row = BoxLayout(orientation="horizontal", spacing=dp(6),
                              size_hint_y=None, height=dp(110))
        for cid in sorted(self._candidate_map.keys()):
            card = VoteCard(cid, self._candidate_map[cid])
            self._vote_cards[cid] = card
            cards_row.add_widget(card)
        left.add_widget(cards_row)

        from bar_chart import BarChartWidget
        self._bar_chart = BarChartWidget()
        left.add_widget(self._bar_chart)

        left.add_widget(Label(
            text="Made by — Ayush Raj,  8C ICSE",
            font_size="9sp", color=TEXT_MUTED,
            size_hint_y=None, height=dp(18),
            halign="right",
        ))

        main.add_widget(left)

        right = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_x=0.28)
        log_title = Label(text="Live Events", font_size="12sp", color=TEXT_PRIMARY,
                          bold=True, size_hint_y=None, height=dp(24), halign="left")
        log_title.bind(size=log_title.setter("text_size"))
        right.add_widget(log_title)

        sv = ScrollView()
        self._log_box = BoxLayout(orientation="vertical", spacing=dp(2),
                                  size_hint_y=None, padding=[dp(2), dp(2)])
        self._log_box.bind(minimum_height=self._log_box.setter("height"))
        sv.add_widget(self._log_box)
        right.add_widget(sv)
        main.add_widget(right)

        self.add_widget(main)
        self.refresh()

    def refresh(self):
        totals = get_vote_totals()
        for cid, card in self._vote_cards.items():
            card.set_count(totals.get(cid, 0))
            card.set_name(self._candidate_map.get(cid, f"C{cid}"))
        self._total_lbl.text = f"Total Votes: {get_total_votes()}"
        self._bar_chart.update_data(self._candidate_map, totals)

    def update_candidate_names(self, candidate_map: dict):
        self._candidate_map = candidate_map
        for cid, card in self._vote_cards.items():
            card.set_name(candidate_map.get(cid, f"C{cid}"))
        self.refresh()

    def start_hold(self, candidate_id: int):
        name = self._candidate_map.get(candidate_id, f"Candidate {candidate_id}")
        self._hold_bar.start(candidate_id, name)

    def cancel_hold(self, candidate_id: int):
        self._hold_bar.cancel()

    def complete_hold(self):
        self._hold_bar.complete()

    def start_lockout(self):
        self._lockout_banner.start_lockout()

    def append_log(self, level: str, line: str):
        if "error" in line.lower() or "ERROR" in level:
            color = ACCENT_RED
        elif "vote" in line.lower() or "INFO" in level:
            color = ACCENT_GREEN
        else:
            color = TEXT_MUTED

        lbl = Label(text=line, font_size="9sp", color=color,
                    size_hint_y=None, halign="left", valign="top")
        lbl.bind(width=lambda *a: setattr(lbl, "text_size", (lbl.width, None)))
        lbl.bind(texture_size=lambda *a: setattr(lbl, "height", lbl.texture_size[1] + dp(2)))
        self._log_box.add_widget(lbl, index=len(self._log_box.children))
        self._live_log_entries.append(lbl)

        if len(self._live_log_entries) > 100:
            old = self._live_log_entries.pop(0)
            self._log_box.remove_widget(old)

    def set_status(self, text: str, color):
        self._status_lbl.text = text
        self._status_lbl.color = color
