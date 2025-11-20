from datetime import datetime
from pathlib import Path
from typing import Iterable
import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A6, landscape
from reportlab.pdfgen import canvas


def generate_ticket_pdf(
    booking_code: str,
    movie_title: str,
    hall: str,
    show_time: str,
    client_name: str,
    seats: Iterable[str],
) -> Path:
    """
    """

    tickets_dir = Path(__file__).resolve().parent / "tickets"
    tickets_dir.mkdir(exist_ok=True)

    file_path = tickets_dir / f"{booking_code}.pdf"

    # Size: A6 landscape
    page_size = landscape(A6)
    width, height = page_size

    c = canvas.Canvas(str(file_path), pagesize=page_size)

    # Цветове - светъл, чист дизайн
    bg_page = HexColor("#e5e7eb")      # светло сиво за фон
    card_bg = HexColor("#ffffff")      # бяла "карта" в средата
    border_color = HexColor("#d1d5db")
    accent = HexColor("#2563eb")       # син акцент
    accent_soft = HexColor("#dbeafe")
    text_main = HexColor("#111827")
    text_muted = HexColor("#6b7280")

    # Запълваме фон
    c.setFillColor(bg_page)
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # "карта" в центъра
    margin = 10
    card_x = margin
    card_y = margin
    card_width = width - margin * 2
    card_height = height - margin * 2

    c.setFillColor(card_bg)
    c.setStrokeColor(border_color)
    c.setLineWidth(1)
    c.roundRect(card_x, card_y, card_width, card_height, 10, fill=1, stroke=1)

    # Горна цветна лента
    header_height = 24
    c.setFillColor(accent_soft)
    c.setStrokeColor(accent_soft)
    c.roundRect(
        card_x,
        card_y + card_height - header_height,
        card_width,
        header_height,
        10,
        fill=1,
        stroke=0,
    )

    #  "CINEMA TICKET"
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(
        card_x + 14,
        card_y + card_height - header_height + 7,
        "CINEMA TICKET",
    )

    # Код вдясно, голям
    c.setFillColor(text_main)
    c.setFont("Helvetica-Bold", 16)
    c.drawRightString(
        card_x + card_width - 14,
        card_y + card_height - header_height + 8,
        booking_code,
    )

    # Basic informations
    content_left = card_x + 16
    content_right = card_x + card_width - 16
    y = card_y + card_height - header_height - 14

    seats_str = ", ".join(seats)
    issued_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Movie
    c.setFillColor(text_muted)
    c.setFont("Helvetica", 8)
    c.drawString(content_left, y, "Movie")
    y -= 13
    c.setFillColor(text_main)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(content_left, y, movie_title[:40])

    # Hall / Time
    y -= 18
    c.setFillColor(text_muted)
    c.setFont("Helvetica", 8)
    c.drawString(content_left, y, "Hall / Time")
    y -= 13
    c.setFillColor(text_main)
    c.setFont("Helvetica", 11)
    c.drawString(content_left, y, f"{hall}  ·  {show_time}")

    # Seats
    y -= 18
    c.setFillColor(text_muted)
    c.setFont("Helvetica", 8)
    c.drawString(content_left, y, "Seats")
    y -= 13
    c.setFillColor(text_main)
    c.setFont("Helvetica", 11)
    c.drawString(content_left, y, seats_str[:50])

    # Client
    y -= 18
    c.setFillColor(text_muted)
    c.setFont("Helvetica", 8)
    c.drawString(content_left, y, "Client")
    y -= 13
    c.setFillColor(text_main)
    c.setFont("Helvetica", 11)
    c.drawString(content_left, y, client_name[:40])

    # Долната лента: issued + system
    footer_y = card_y + 12
    c.setFillColor(text_muted)
    c.setFont("Helvetica", 7)
    c.drawString(content_left, footer_y, f"Issued: {issued_str}")
    c.drawRightString(content_right, footer_y, "Cinema Desktop System")

    c.showPage()
    c.save()

    # PDF automatically opens
    _open_pdf_with_default_viewer(file_path)

    return file_path


def _open_pdf_with_default_viewer(file_path: Path) -> None:
    """
   Opens PDF Fyle with default tool of system (Windows / macOS / Linux).
    """
    try:
        path_str = str(file_path)
        if sys.platform.startswith("win"):
            os.startfile(path_str)  # Windows
        elif sys.platform == "darwin":
            import subprocess
            subprocess.Popen(["open", path_str])  # macOS
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path_str])  # Linux
    except Exception as e:

        print(f"Could not open PDF automatically: {e}")
