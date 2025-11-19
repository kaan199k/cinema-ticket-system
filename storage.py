# storage.py

import sqlite3
from pathlib import Path
from typing import Iterable, Set

DB_PATH = Path(__file__).resolve().parent / "cinema.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Създава таблиците, ако не съществуват."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_code TEXT NOT NULL,
            movie_id TEXT NOT NULL,
            movie_title TEXT NOT NULL,
            hall TEXT NOT NULL,
            show_time TEXT NOT NULL,
            client_name TEXT NOT NULL,
            seats TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS taken_seats (
            movie_id TEXT NOT NULL,
            hall TEXT NOT NULL,
            show_time TEXT NOT NULL,
            seat_id TEXT NOT NULL,
            PRIMARY KEY (movie_id, hall, show_time, seat_id)
        )
        """
    )

    conn.commit()
    conn.close()


def save_booking(
    movie_id: str,
    movie_title: str,
    hall: str,
    show_time: str,
    client_name: str,
    seats: Iterable[str],
    booking_code: str,
) -> None:
    """Записва резервацията в bookings."""
    conn = get_connection()
    cur = conn.cursor()

    seats_str = ",".join(seats)

    cur.execute(
        """
        INSERT INTO bookings (
            booking_code, movie_id, movie_title, hall, show_time, client_name, seats
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (booking_code, movie_id, movie_title, hall, show_time, client_name, seats_str),
    )

    conn.commit()
    conn.close()


def mark_seats_taken(
    movie_id: str,
    hall: str,
    show_time: str,
    seats: Iterable[str],
) -> None:
    """Маркира местата като заети за дадена прожекция."""
    conn = get_connection()
    cur = conn.cursor()

    for seat in seats:
        cur.execute(
            """
            INSERT OR IGNORE INTO taken_seats (movie_id, hall, show_time, seat_id)
            VALUES (?, ?, ?, ?)
            """,
            (movie_id, hall, show_time, seat),
        )

    conn.commit()
    conn.close()


def get_taken_seats(movie_id: str, hall: str, show_time: str) -> Set[str]:
    """Връща всички заети места за дадена прожекция."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT seat_id FROM taken_seats
        WHERE movie_id = ? AND hall = ? AND show_time = ?
        """,
        (movie_id, hall, show_time),
    )

    rows = cur.fetchall()
    conn.close()

    return {row[0] for row in rows}
