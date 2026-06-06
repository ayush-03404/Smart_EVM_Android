APP_NAME = "SMART EVM"
APP_VERSION = "1.0.0"

WS_HOST = "0.0.0.0"
WS_PORT = 8765

DEFAULT_CANDIDATES = {
    1: "Physics",
    2: "Chemistry",
    3: "Mathematics",
    4: "Biology",
    5: "English",
}

CANDIDATE_COUNT = 5

COLORS = {
    "bg_primary":    "#0d1117",
    "bg_secondary":  "#161b22",
    "bg_card":       "#1c2128",
    "bg_sidebar":    "#010409",
    "accent":        "#58a6ff",
    "accent_green":  "#3fb950",
    "accent_red":    "#f85149",
    "accent_orange": "#d29922",
    "text_primary":  "#e6edf3",
    "text_muted":    "#8b949e",
    "border":        "#30363d",
}

ACCENT_COLORS_HEX = [
    "#58a6ff",
    "#3fb950",
    "#d29922",
    "#f85149",
    "#bc8cff",
]

ACCENT_COLORS_RGBA = [
    (0.345, 0.651, 1.000, 1),
    (0.247, 0.729, 0.314, 1),
    (0.824, 0.600, 0.133, 1),
    (0.973, 0.318, 0.286, 1),
    (0.737, 0.549, 1.000, 1),
]

def hex_to_kivy(h: str):
    h = h.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r / 255, g / 255, b / 255, 1)
