from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp

from config import ACCENT_COLORS_RGBA, hex_to_kivy, COLORS

BG = hex_to_kivy(COLORS["bg_card"])
TEXT_MUTED = hex_to_kivy(COLORS["text_muted"])
TEXT_PRIMARY = hex_to_kivy(COLORS["text_primary"])


class _BarColumn(BoxLayout):
    def __init__(self, cid: int, name: str, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(2), **kwargs)
        self.cid = cid
        self._color = ACCENT_COLORS_RGBA[(cid - 1) % len(ACCENT_COLORS_RGBA)]
        self._fraction = 0.0
        self._votes = 0

        self._votes_lbl = Label(
            text="0",
            font_size="11sp",
            color=self._color,
            bold=True,
            size_hint_y=None,
            height=dp(18),
        )
        self.add_widget(self._votes_lbl)

        self._bar_widget = Widget()
        self._bar_widget.bind(size=self._redraw, pos=self._redraw)
        self.add_widget(self._bar_widget)

        short = name[:8] if len(name) > 8 else name
        self._name_lbl = Label(
            text=short,
            font_size="9sp",
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(18),
        )
        self.add_widget(self._name_lbl)

    def set_value(self, votes: int, fraction: float, name: str):
        self._votes = votes
        self._fraction = max(0.0, min(1.0, fraction))
        self._votes_lbl.text = str(votes)
        short = name[:8] if len(name) > 8 else name
        self._name_lbl.text = short
        self._redraw()

    def _redraw(self, *args):
        w = self._bar_widget
        w.canvas.clear()
        with w.canvas:
            Color(*BG)
            Rectangle(pos=w.pos, size=w.size)
            h = w.height * self._fraction
            if h < dp(3):
                h = dp(3)
            margin = w.width * 0.15
            Color(*self._color)
            RoundedRectangle(
                pos=(w.x + margin, w.y),
                size=(w.width - margin * 2, h),
                radius=[dp(4), dp(4), 0, 0],
            )


class BarChartWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._columns: dict[int, _BarColumn] = {}
        self._title = Label(
            text="Votes per Candidate",
            font_size="11sp",
            color=TEXT_MUTED,
            size_hint_y=None,
            height=dp(20),
        )
        self.add_widget(self._title)
        self._cols_row = BoxLayout(orientation="horizontal", spacing=dp(4))
        self.add_widget(self._cols_row)

    def update_data(self, candidate_map: dict, totals: dict):
        if not self._columns:
            for cid in sorted(candidate_map.keys()):
                col = _BarColumn(cid, candidate_map[cid])
                self._columns[cid] = col
                self._cols_row.add_widget(col)

        max_votes = max(totals.values(), default=0) if totals else 0

        for cid, col in self._columns.items():
            votes = totals.get(cid, 0)
            fraction = (votes / max_votes) if max_votes > 0 else 0.0
            col.set_value(votes, fraction, candidate_map.get(cid, f"C{cid}"))
