# i18n.py

from typing import Dict

LANG_EN: Dict[str, str] = {
    "app_title": "Cinema Ticket System",
    "reservation_group": "Reservation",
    "seat_group": "Seat map",
    "theme_group": "Theme",
    "lang_group": "Language",

    "subtitle": "Cashier desktop · Select movie, hall, time, seats.",
    "seat_subtitle": "Click seats to select. Green = selected, gray = free.",

    "movie_label": "Movie",
    "hall_label": "Hall",
    "time_label": "Screening time",
    "client_label": "Client name",
    "summary_label": "Summary",
    "client_summary": "Client",
    "seats_summary": "Seats",

    "confirm_button": "Confirm booking",

    "lang_en": "EN",
    "lang_bg": "BG",

    "status_missing_name": "Client name is required.",
    "status_missing_seats": "Please select at least one seat.",

    "status_booked": (
        "Booking confirmed: {movie} · {hall} · {time}\n"
        "Client: {client} | Seats: {seats} | Code: {code}"
    ),
}

LANG_BG: Dict[str, str] = {
    "app_title": "Система за кино билети",
    "reservation_group": "Резервация",
    "seat_group": "Салон",
    "theme_group": "Тема",
    "lang_group": "Език",

    "subtitle": "Касиерски режим · Избери филм, зала, час и места.",
    "seat_subtitle": "Кликни върху местата за избор. Зелено = избрано, сиво = свободно.",

    "movie_label": "Филм",
    "hall_label": "Зала",
    "time_label": "Час на прожекция",
    "client_label": "Име на клиент",
    "summary_label": "Обобщение",
    "client_summary": "Клиент",
    "seats_summary": "Места",

    "confirm_button": "Потвърди",

    "lang_en": "EN",
    "lang_bg": "BG",

    "status_missing_name": "Въведи име на клиента.",
    "status_missing_seats": "Избери поне едно място.",

    "status_booked": (
        "Резервацията е потвърдена: {movie} · {hall} · {time}\n"
        "Клиент: {client} | Места: {seats} | Код: {code}"
    ),
}

LANGS = {
    "en": LANG_EN,
    "bg": LANG_BG,
}


def get_translations(lang_code: str) -> Dict[str, str]:
    return LANGS.get(lang_code, LANG_EN)
