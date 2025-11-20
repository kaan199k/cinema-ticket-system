import random
import string
from typing import Dict, Tuple, Set

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QGridLayout,
    QTextEdit,
    QSizePolicy,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QPalette, QColor

from data import ROWS, NUM_COLUMNS
from themes import THEMES, apply_theme_to_palette, Theme
from storage import (
    init_db,
    save_booking,
    get_taken_seats,
    mark_seats_taken,
    get_stats_by_movie,
    get_all_movie_titles,
    get_halls_for_movie,
    get_show_times,
    get_movie_id_for_title,
    cancel_booking,
)
from i18n import get_translations
from ticket_pdf import generate_ticket_pdf
from admin_window import AdminWindow


SeatKey = str  # e.g. "A5"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # DB
        init_db()

        # език
        self.current_lang = "en"
        self.translations = get_translations(self.current_lang)

        # тема
        self.current_theme: Theme = THEMES["light"]
        self.current_theme_name: str = "light"

        # ticket types & prices
        self.ticket_prices: Dict[str, float] = {
            "Standard": 12.0,
            "Student": 9.0,
            "Child": 8.0,
            "VIP": 18.0,
        }

        # полета за етикети и бутони
        self.labels: Dict[str, QLabel] = {}
        self.seat_buttons: Dict[SeatKey, QPushButton] = {}
        self.selected_seats: Dict[SeatKey, bool] = {}
        self.taken_seats: Set[SeatKey] = set()

        # разумен размер на прозореца
        self.setMinimumSize(900, 600)
        self.resize(1200, 720)

        self._build_ui()
        self._apply_theme("light")
        self._update_texts()

    # ---------- helpers ----------

    def _t(self, key: str) -> str:
        return self.translations.get(key, key)

    # ---------- UI BUILD ----------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(18)
        central.setLayout(main_layout)

        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()

        main_layout.addWidget(left_panel, 0)
        main_layout.addWidget(right_panel, 1)

        # повече място за салона, особено при малък прозорец
        main_layout.setStretch(0, 2)   # форма
        main_layout.setStretch(1, 7)   # седалки

    def _build_left_panel(self) -> QGroupBox:
        self.reservation_group = QGroupBox(self._t("reservation_group"))
        self._apply_card_shadow(self.reservation_group)
        box = self.reservation_group
        layout = QVBoxLayout()
        layout.setSpacing(10)
        box.setLayout(layout)

        self.title_label = QLabel(self._t("app_title"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self._t("subtitle"))
        self.subtitle_label.setStyleSheet("font-size: 11px; color: #6b7280;")
        layout.addWidget(self.subtitle_label)

        # Movie
        self.movie_combo = QComboBox()
        self._load_movies()
        self.movie_combo.currentIndexChanged.connect(self._on_movie_changed)
        layout.addWidget(self._labeled_widget("movie_label", self.movie_combo))

        # Hall
        self.hall_combo = QComboBox()
        self.hall_combo.addItem("Select hall…")
        self.hall_combo.setEnabled(False)
        self.hall_combo.currentIndexChanged.connect(self._on_hall_changed)
        layout.addWidget(self._labeled_widget("hall_label", self.hall_combo))

        # Time
        self.time_combo = QComboBox()
        self.time_combo.addItem("Select time…")
        self.time_combo.setEnabled(False)
        self.time_combo.currentIndexChanged.connect(self._on_time_changed)
        layout.addWidget(self._labeled_widget("time_label", self.time_combo))

        # Client name
        self.client_name_edit = QLineEdit()
        self.client_name_edit.setPlaceholderText("Full name")
        self.client_name_edit.textChanged.connect(self._update_summary)
        layout.addWidget(self._labeled_widget("client_label", self.client_name_edit))

        # Ticket type
        self.ticket_type_combo = QComboBox()
        self.ticket_type_combo.addItems(list(self.ticket_prices.keys()))
        self.ticket_type_combo.currentIndexChanged.connect(self._update_price_display)
        layout.addWidget(self._plain_labeled_widget("Ticket type", self.ticket_type_combo))

        # Price info
        self.price_label = QLabel("Price per seat: —")
        self.total_label = QLabel("Total: —")
        layout.addWidget(self.price_label)
        layout.addWidget(self.total_label)

        # Language group
        self.lang_group = QGroupBox(self._t("lang_group"))
        lang_layout = QVBoxLayout()
        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)
        self.lang_en_btn = QPushButton(self._t("lang_en"))
        self.lang_bg_btn = QPushButton(self._t("lang_bg"))
        self.lang_en_btn.setCheckable(True)
        self.lang_bg_btn.setCheckable(True)
        self.lang_en_btn.clicked.connect(lambda checked: self._set_language("en"))
        self.lang_bg_btn.clicked.connect(lambda checked: self._set_language("bg"))
        lang_row.addWidget(self.lang_en_btn)
        lang_row.addWidget(self.lang_bg_btn)
        lang_layout.addLayout(lang_row)
        self.lang_group.setLayout(lang_layout)
        layout.addWidget(self.lang_group)

        # Theme group
        self.theme_group = QGroupBox(self._t("theme_group"))
        theme_box_layout = QVBoxLayout()
        theme_row = QHBoxLayout()
        theme_row.setSpacing(6)

        self.light_btn = QPushButton("Light")
        self.dark_btn = QPushButton("Dark")
        self.night_btn = QPushButton("Night")

        for btn, name in [
            (self.light_btn, "light"),
            (self.dark_btn, "dark"),
            (self.night_btn, "night"),
        ]:
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, n=name: self._apply_theme(n))
            theme_row.addWidget(btn)

        theme_box_layout.addLayout(theme_row)
        self.theme_group.setLayout(theme_box_layout)
        layout.addWidget(self.theme_group)

        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(130)
        layout.addWidget(self._labeled_widget("summary_label", self.summary_text))

        # Confirm button
        self.confirm_btn = QPushButton(self._t("confirm_button"))
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._handle_booking)
        self.confirm_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        layout.addWidget(self.confirm_btn)

        # Stats + Admin в един ред
        tools_row = QWidget()
        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(8)

        self.stats_btn = QPushButton(
            self._t("stats_button") if "stats_button" in self.translations else "Stats"
        )
        self.stats_btn.setObjectName("secondaryButton")
        self.stats_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.stats_btn.clicked.connect(self._open_stats_dialog)

        self.admin_btn = QPushButton("Admin")
        self.admin_btn.setObjectName("secondaryButton")
        self.admin_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.admin_btn.clicked.connect(self._open_admin_window)

        tools_layout.addWidget(self.stats_btn)
        tools_layout.addWidget(self.admin_btn)
        tools_row.setLayout(tools_layout)
        layout.addWidget(tools_row)

        # Cancel booking section
        cancel_group = QGroupBox("Cancel booking")
        self._apply_card_shadow(cancel_group)
        cg_layout = QVBoxLayout()
        self.cancel_code_edit = QLineEdit()
        self.cancel_code_edit.setPlaceholderText("Booking code")
        self.cancel_btn = QPushButton("Cancel reservation")
        self.cancel_btn.setObjectName("dangerButton")
        self.cancel_btn.clicked.connect(self._handle_cancel_booking)
        cg_layout.addWidget(self.cancel_code_edit)
        cg_layout.addWidget(self.cancel_btn)
        cancel_group.setLayout(cg_layout)
        layout.addWidget(cancel_group)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch(1)
        return box

    def _build_right_panel(self) -> QGroupBox:
        self.seat_group = QGroupBox(self._t("seat_group"))
        self._apply_card_shadow(self.seat_group)
        box = self.seat_group
        layout = QVBoxLayout()
        layout.setSpacing(8)
        box.setLayout(layout)

        self.seat_subtitle_label = QLabel(self._t("seat_subtitle"))
        self.seat_subtitle_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.seat_subtitle_label)

        self.seat_grid = QGridLayout()
        self.seat_grid.setContentsMargins(12, 8, 12, 12)
        self.seat_grid.setHorizontalSpacing(6)
        self.seat_grid.setVerticalSpacing(6)
        layout.addLayout(self.seat_grid)

        self._build_seat_buttons()

        layout.addStretch(1)
        return box

    def _build_seat_buttons(self) -> None:
        self.seat_buttons.clear()
        self.selected_seats.clear()

        # screen label
        screen_label = QLabel("S C R E E N")
        screen_label.setAlignment(Qt.AlignCenter)
        screen_label.setStyleSheet("font-size: 11px; letter-spacing: 3px;")
        self.seat_grid.addWidget(screen_label, 0, 0, 1, NUM_COLUMNS + 1)

        for row_index, row_label in enumerate(ROWS):
            row_label_widget = QLabel(row_label)
            row_label_widget.setAlignment(Qt.AlignCenter)
            self.seat_grid.addWidget(row_label_widget, row_index + 1, 0)

            for col in range(1, NUM_COLUMNS + 1):
                seat_id = f"{row_label}{col}"
                btn = QPushButton(str(col))
                btn.setProperty("seat_id", seat_id)
                btn.clicked.connect(self._on_seat_clicked)

                # по-скромни размери, да не се чупи при малък прозорец
                btn.setMinimumSize(30, 26)
                btn.setMaximumHeight(32)
                btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

                self._style_seat_button(btn, selected=False, taken=False)

                self.seat_grid.addWidget(btn, row_index + 1, col)
                self.seat_buttons[seat_id] = btn
                self.selected_seats[seat_id] = False

    # ---------- LABEL HELPERS ----------

    def _labeled_widget(self, label_key: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        lbl = QLabel(self._t(label_key))
        lbl.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl)
        layout.addWidget(widget)
        container.setLayout(layout)

        # запомняме етикета по ключ
        self.labels[label_key] = lbl
        return container

    def _plain_labeled_widget(self, label_text: str, widget: QWidget) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 11px;")
        layout.addWidget(lbl)
        layout.addWidget(widget)
        container.setLayout(layout)
        return container

    def _apply_card_shadow(self, widget: QWidget) -> None:
        """Лек shadow за групите (card feeling)."""
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(24)
        effect.setOffset(0, 10)
        effect.setColor(QColor(15, 23, 42, 110))
        widget.setGraphicsEffect(effect)

    def _style_seat_button(self, btn: QPushButton, selected: bool, taken: bool = False) -> None:
        """
        Седалките да са:
        - свободни: по-различни за light/dark
        - избрани: зелени
        - заети: сиви
        """
        theme_name = getattr(self, "current_theme_name", "light")

        if taken:
            if theme_name == "light":
                bg = "#e5e7eb"
                text = "#9ca3af"
                border = "#d1d5db"
            else:
                bg = "#4b5563"
                text = "#9ca3af"
                border = "#374151"
            btn.setEnabled(False)
        else:
            btn.setEnabled(True)
            if selected:
                bg = "#22c55e"
                text = "#ffffff"
                border = "#16a34a"
            else:
                if theme_name == "light":
                    bg = "#f3f4f6"
                    text = "#111827"
                    border = "#d1d5db"
                else:
                    bg = "#020617"
                    text = "#e5e7eb"
                    border = "#4b5563"

        btn.setStyleSheet(
            f"QPushButton {{"
            f"background-color: {bg};"
            f"color: {text};"
            f"border-radius: 8px;"
            f"border: 1px solid {border};"
            f"font-size: 11px;"
            f"padding: 4px 0;"
            f"}}"
        )

    def _generate_booking_code(self) -> str:
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # ---------- THEME & LANGUAGE ----------

    def _apply_theme(self, theme_name: str) -> None:
        theme = THEMES.get(theme_name, THEMES["light"])
        self.current_theme = theme
        self.current_theme_name = theme_name

        palette: QPalette = self.palette()
        apply_theme_to_palette(theme, palette)
        self.setPalette(palette)

        base_style = f"""
        QMainWindow {{
            background-color: {theme.panel_bg};
        }}

        QGroupBox {{
            border: 1px solid {theme.border};
            border-radius: 16px;
            margin-top: 10px;
            background-color: {theme.panel_bg};
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 6px;
            color: {theme.muted_text};
            font-size: 11px;
            letter-spacing: 0.6px;
        }}

        QLabel {{
            color: {theme.text};
        }}

        QLineEdit, QComboBox, QTextEdit {{
            background-color: {theme.panel_bg};
            color: {theme.text};
            border: 1px solid {theme.border};
            border-radius: 10px;
            padding: 6px 9px;
            selection-background-color: {theme.accent};
            selection-color: #ffffff;
        }}

        QTextEdit {{
            font-family: 'Consolas', 'Menlo', 'Courier New', monospace;
            font-size: 11px;
        }}

        QPushButton {{
            background-color: {theme.accent};
            color: white;
            border-radius: 999px;
            padding: 6px 14px;
            border: none;
            font-size: 11px;
        }}

        QPushButton:hover {{
            background-color: {theme.accent_soft};
        }}

        QPushButton:disabled {{
            background-color: {theme.accent_soft};
            color: {theme.muted_text};
        }}

        QPushButton#secondaryButton {{
            background-color: transparent;
            color: {theme.text};
            border: 1px solid {theme.border};
        }}

        QPushButton#secondaryButton:hover {{
            background-color: {theme.panel_bg};
        }}

        QPushButton#dangerButton {{
            background-color: #dc2626;
        }}

        QPushButton#dangerButton:hover {{
            background-color: #ef4444;
        }}
        """

        self.setStyleSheet(base_style)

        self.light_btn.setChecked(theme_name == "light")
        self.dark_btn.setChecked(theme_name == "dark")
        self.night_btn.setChecked(theme_name == "night")

        # update seat стилове според заети/избрани
        for seat_id, btn in self.seat_buttons.items():
            selected = self.selected_seats.get(seat_id, False)
            taken = seat_id in self.taken_seats
            self._style_seat_button(btn, selected=selected, taken=taken)

    def _set_language(self, lang_code: str) -> None:
        self.current_lang = lang_code
        self.translations = get_translations(lang_code)
        self._update_texts()

    def _update_texts(self) -> None:
        self.setWindowTitle(self._t("app_title"))
        self.reservation_group.setTitle(self._t("reservation_group"))
        self.seat_group.setTitle(self._t("seat_group"))
        self.theme_group.setTitle(self._t("theme_group"))
        self.lang_group.setTitle(self._t("lang_group"))

        self.title_label.setText(self._t("app_title"))
        self.subtitle_label.setText(self._t("subtitle"))
        self.seat_subtitle_label.setText(self._t("seat_subtitle"))

        for key, lbl in self.labels.items():
            lbl.setText(self._t(key))

        self.confirm_btn.setText(self._t("confirm_button"))
        if "stats_button" in self.translations:
            self.stats_btn.setText(self._t("stats_button"))
        self.lang_en_btn.setText(self._t("lang_en"))
        self.lang_bg_btn.setText(self._t("lang_bg"))

        self.lang_en_btn.setChecked(self.current_lang == "en")
        self.lang_bg_btn.setChecked(self.current_lang == "bg")

        self._update_summary()

    # ---------- MOVIES / SHOW HELPERS ----------

    def _load_movies(self) -> None:
        self.movie_combo.blockSignals(True)
        self.movie_combo.clear()
        self.movie_combo.addItem("Select movie…")
        for title in get_all_movie_titles():
            self.movie_combo.addItem(title)
        self.movie_combo.blockSignals(False)

    def _get_current_show_key(self) -> Tuple[str, str, str] | None:
        if (
            self.movie_combo.currentIndex() <= 0
            or self.hall_combo.currentIndex() <= 0
            or self.time_combo.currentIndex() <= 0
        ):
            return None

        movie_title = self.movie_combo.currentText()
        hall = self.hall_combo.currentText()
        time = self.time_combo.currentText()

        movie_id = get_movie_id_for_title(movie_title)
        if not movie_id:
            return None

        return movie_id, hall, time

    def _load_taken_seats_for_current_show(self) -> None:
        key = self._get_current_show_key()
        if key is None:
            self.taken_seats = set()
            # всичко е свободно
            for seat_id, btn in self.seat_buttons.items():
                selected = self.selected_seats.get(seat_id, False)
                self._style_seat_button(btn, selected=selected, taken=False)
            return

        movie_id, hall, time = key
        taken = get_taken_seats(movie_id, hall, time)
        self.taken_seats = taken

        for seat_id, btn in self.seat_buttons.items():
            selected = self.selected_seats.get(seat_id, False)
            is_taken = seat_id in self.taken_seats
            if is_taken:
                self.selected_seats[seat_id] = False
                selected = False
            self._style_seat_button(btn, selected=selected, taken=is_taken)

    # ---------- SIGNAL HANDLERS ----------

    def _on_movie_changed(self, index: int) -> None:
        self.hall_combo.blockSignals(True)
        self.time_combo.blockSignals(True)

        self.hall_combo.clear()
        self.time_combo.clear()
        self.hall_combo.addItem("Select hall…")
        self.time_combo.addItem("Select time…")
        self.hall_combo.setEnabled(False)
        self.time_combo.setEnabled(False)

        self.hall_combo.blockSignals(False)
        self.time_combo.blockSignals(False)

        # ресет места
        for seat in list(self.selected_seats.keys()):
            self.selected_seats[seat] = False
        self._load_taken_seats_for_current_show()
        self._update_price_display()

        if index <= 0:
            self._update_summary()
            self._update_confirm_state()
            return

        movie_title = self.movie_combo.currentText()
        halls = get_halls_for_movie(movie_title)

        self.hall_combo.blockSignals(True)
        for hall in halls:
            self.hall_combo.addItem(hall)
        self.hall_combo.blockSignals(False)
        self.hall_combo.setEnabled(True)

        self._update_summary()
        self._update_confirm_state()

    def _on_hall_changed(self, index: int) -> None:
        self.time_combo.blockSignals(True)
        self.time_combo.clear()
        self.time_combo.addItem("Select time…")
        self.time_combo.blockSignals(False)
        self.time_combo.setEnabled(False)

        if index <= 0:
            self._load_taken_seats_for_current_show()
            self._update_summary()
            self._update_confirm_state()
            return

        movie_title = self.movie_combo.currentText()
        hall_name = self.hall_combo.currentText()

        times = get_show_times(movie_title, hall_name)
        self.time_combo.blockSignals(True)
        for t in times:
            self.time_combo.addItem(t)
        self.time_combo.blockSignals(False)
        self.time_combo.setEnabled(True)

        self._load_taken_seats_for_current_show()
        self._update_summary()
        self._update_confirm_state()

    def _on_time_changed(self, index: int) -> None:
        self._load_taken_seats_for_current_show()
        self._update_summary()
        self._update_confirm_state()

    def _on_seat_clicked(self) -> None:
        btn: QPushButton = self.sender()  # type: ignore
        seat_id: SeatKey = btn.property("seat_id")

        if seat_id in self.taken_seats:
            # вече заето -> не пипаме
            return

        current = self.selected_seats.get(seat_id, False)
        new_state = not current
        self.selected_seats[seat_id] = new_state
        self._style_seat_button(btn, selected=new_state, taken=False)
        self._update_summary()
        self._update_confirm_state()
        self._update_price_display()

    # ---------- PRICE ----------

    def _collect_selected_seats(self) -> Tuple[SeatKey, ...]:
        return tuple(sorted([s for s, sel in self.selected_seats.items() if sel]))

    def _get_current_ticket_type(self) -> str:
        return self.ticket_type_combo.currentText() or "Standard"

    def _get_price_info(self) -> Tuple[float, float]:
        """Връща (price_per_seat, total_price)."""
        ticket_type = self._get_current_ticket_type()
        price_per_seat = self.ticket_prices.get(ticket_type, 0.0)
        seats_count = len(self._collect_selected_seats())
        total_price = price_per_seat * seats_count
        return price_per_seat, total_price

    def _update_price_display(self) -> None:
        price_per_seat, total_price = self._get_price_info()
        if price_per_seat == 0:
            self.price_label.setText("Price per seat: —")
        else:
            self.price_label.setText(f"Price per seat: {price_per_seat:.2f} лв.")

        if total_price == 0:
            self.total_label.setText("Total: —")
        else:
            self.total_label.setText(f"Total: {total_price:.2f} лв.")

    # ---------- SUMMARY & BOOKING ----------

    def _update_summary(self) -> None:
        movie_title = self.movie_combo.currentText() if self.movie_combo.currentIndex() > 0 else "—"
        hall = self.hall_combo.currentText() if self.hall_combo.currentIndex() > 0 else "—"
        time = self.time_combo.currentText() if self.time_combo.currentIndex() > 0 else "—"
        client_name = self.client_name_edit.text().strip() or "—"
        seats = self._collect_selected_seats()
        seats_str = ", ".join(seats) if seats else "—"
        ticket_type = self._get_current_ticket_type()

        text = (
            f"{self._t('movie_label')}: {movie_title}\n"
            f"{self._t('hall_label')}: {hall}\n"
            f"{self._t('time_label')}: {time}\n"
            f"{self._t('client_summary')}: {client_name}\n"
            f"{self._t('seats_summary')}: {seats_str}\n"
            f"Ticket type: {ticket_type}\n"
        )
        self.summary_text.setPlainText(text)

    def _update_confirm_state(self) -> None:
        has_movie = self.movie_combo.currentIndex() > 0
        has_hall = self.hall_combo.currentIndex() > 0
        has_time = self.time_combo.currentIndex() > 0
        has_name = bool(self.client_name_edit.text().strip())
        has_seats = len(self._collect_selected_seats()) > 0

        self.confirm_btn.setEnabled(
            has_movie and has_hall and has_time and has_name and has_seats
        )

    def _open_pdf(self, path: str) -> None:
        """Отваря PDF файла с default viewer-а на системата."""
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # Windows
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", path])  # macOS
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])  # Linux
        except Exception as e:
            current = self.status_label.text()
            self.status_label.setText(f"{current}\n(Could not open PDF: {e})")

    def _handle_booking(self) -> None:
        movie_title = self.movie_combo.currentText()
        hall = self.hall_combo.currentText()
        time = self.time_combo.currentText()
        client_name = self.client_name_edit.text().strip()
        seats = self._collect_selected_seats()

        if not client_name:
            self.status_label.setText(self._t("status_missing_name"))
            return
        if not seats:
            self.status_label.setText(self._t("status_missing_seats"))
            return

        movie_id = get_movie_id_for_title(movie_title)
        code = self._generate_booking_code()

        ticket_type = self._get_current_ticket_type()
        price_per_seat, total_price = self._get_price_info()

        # запис в база
        save_booking(
            movie_id=movie_id,
            movie_title=movie_title,
            hall=hall,
            show_time=time,
            client_name=client_name,
            seats=seats,
            booking_code=code,
            ticket_type=ticket_type,
            price_per_seat=price_per_seat,
            total_price=total_price,
        )

        # маркирай местата като заети
        mark_seats_taken(movie_id, hall, time, seats)
        self._load_taken_seats_for_current_show()

        # генерация на PDF билет
        pdf_path = generate_ticket_pdf(
            booking_code=code,
            movie_title=movie_title,
            hall=hall,
            show_time=time,
            client_name=client_name,
            seats=seats,
        )
        self._open_pdf(str(pdf_path))

        msg_template = self._t("status_booked")
        base_text = msg_template.format(
            movie=movie_title,
            hall=hall,
            time=time,
            client=client_name,
            seats=", ".join(seats),
            code=code,
        )

        extra_price = ""
        if price_per_seat > 0:
            extra_price = f"\nType: {ticket_type} · Price: {total_price:.2f} лв."

        self.status_label.setText(f"{base_text}{extra_price}\nPDF: {pdf_path}")

        # изчистваме селекцията
        for seat in seats:
            self.selected_seats[seat] = False

        self._update_summary()
        self._update_confirm_state()
        self._update_price_display()

    # ---------- CANCEL BOOKING ----------

    def _handle_cancel_booking(self) -> None:
        code = self.cancel_code_edit.text().strip()
        if not code:
            self.status_label.setText("Enter booking code to cancel.")
            return

        ok, reason = cancel_booking(code)
        if ok:
            self.status_label.setText(f"Booking {code} canceled.")
            self._load_taken_seats_for_current_show()
            self._update_price_display()
        else:
            if reason == "not_found":
                self.status_label.setText(f"No booking found with code {code}.")
            elif reason == "already_canceled":
                self.status_label.setText(f"Booking {code} is already canceled.")
            else:
                self.status_label.setText(f"Could not cancel booking {code}.")

    # ---------- STATS & ADMIN ----------

    def _open_stats_dialog(self) -> None:
        dlg = StatsDialog(self, lang=self.current_lang)
        dlg.exec_()

    def _open_admin_window(self) -> None:
        dlg = AdminWindow(self)
        dlg.exec_()
        # след затваряне на Admin презареждаме списъка с филми
        self._load_movies()
        self._update_summary()
        self._update_confirm_state()


class StatsDialog(QDialog):
    def __init__(self, parent=None, lang: str = "en"):
        super().__init__(parent)
        self.lang = lang
        self.translations = get_translations(lang)

        self.setWindowTitle(self.translations.get("stats_title", "Statistics"))
        self.resize(420, 320)

        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(
            [
                self.translations.get("stats_movie_column", "Movie"),
                self.translations.get("stats_tickets_column", "Tickets"),
            ]
        )
        layout.addWidget(self.table)
        self.setLayout(layout)

        self._load_data()

    def _load_data(self) -> None:
        rows = get_stats_by_movie()
        self.table.setRowCount(len(rows))

        for i, (title, count) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(title))
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))

        self.table.resizeColumnsToContents()
