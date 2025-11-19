# themes.py

from dataclasses import dataclass
from PyQt5.QtGui import QPalette, QColor


@dataclass
class Theme:
    name: str
    window_bg: str
    panel_bg: str
    text: str
    muted_text: str
    accent: str
    accent_soft: str
    border: str


LIGHT = Theme(
    name="light",
    window_bg="#f3f4f6",
    panel_bg="#ffffff",
    text="#111827",
    muted_text="#6b7280",
    accent="#2563eb",
    accent_soft="#dbeafe",
    border="#e5e7eb",
)

DARK = Theme(
    name="dark",
    window_bg="#020617",
    panel_bg="#030712",
    text="#e5e7eb",
    muted_text="#9ca3af",
    accent="#38bdf8",
    accent_soft="#0f172a",
    border="#1f2937",
)

NIGHT = Theme(
    name="night",
    window_bg="#000000",
    panel_bg="#020617",
    text="#e5e7eb",
    muted_text="#9ca3af",
    accent="#f97316",
    accent_soft="#111827",
    border="#4b5563",
)

THEMES = {
    "light": LIGHT,
    "dark": DARK,
    "night": NIGHT,
}


def apply_theme_to_palette(theme: Theme, palette: QPalette) -> None:
    """Set basic palette colors for the given theme."""
    window_color = QColor(theme.window_bg)
    panel_color = QColor(theme.panel_bg)
    text_color = QColor(theme.text)

    palette.setColor(QPalette.Window, window_color)
    palette.setColor(QPalette.Base, panel_color)
    palette.setColor(QPalette.AlternateBase, panel_color)
    palette.setColor(QPalette.Button, panel_color)
    palette.setColor(QPalette.Text, text_color)
    palette.setColor(QPalette.WindowText, text_color)
    palette.setColor(QPalette.ButtonText, text_color)
