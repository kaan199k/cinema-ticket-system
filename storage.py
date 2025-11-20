# storage.py

from pathlib import Path
from typing import Iterable, Set, List, Tuple, Optional
import sqlite3

from data import MOVIES  # ползва се за първоначално пълнене

DB_PATH = Path(__file__).resolve().parent / "cinema.db"


def get_connection() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    """Създава таблиците и прави миграции, ако е нужно."""
    conn = get_connection()
    cur = conn.cursor()

    # Основна таблица за резервации
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
            ticket_type TEXT,
            price_per_seat REAL,
            total_price REAL,
            is_canceled INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            canceled_at TIMESTAMP
        )
        """
    )

    # Заети места по прожекция
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

    # Филми
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            movie_id TEXT PRIMARY KEY,
            title TEXT NOT NULL
        )
        """
    )

    # Прожекции (hall + hour)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id TEXT NOT NULL,
            hall TEXT NOT NULL,
            show_time TEXT NOT NULL
        )
        """
    )

    _ensure_booking_columns(cur)
    conn.commit()

    _seed_initial_movies_and_shows(conn)
    conn.close()


def _ensure_booking_columns(cur: sqlite3.Cursor) -> None:
    """Добавя липсващи колони в bookings (ако DB е по-стар)."""
    cur.execute("PRAGMA table_info(bookings)")
    cols = {row[1] for row in cur.fetchall()}

    def add_column_if_missing(name: str, ddl: str) -> None:
        if name not in cols:
            cur.execute(f"ALTER TABLE bookings ADD COLUMN {name} {ddl}")

    add_column_if_missing("ticket_type", "TEXT")
    add_column_if_missing("price_per_seat", "REAL")
    add_column_if_missing("total_price", "REAL")
    add_column_if_missing("is_canceled", "INTEGER NOT NULL DEFAULT 0")
    add_column_if_missing("canceled_at", "TIMESTAMP")


def _seed_initial_movies_and_shows(conn: sqlite3.Connection) -> None:
    """Пълни таблиците movies/shows от MOVIES, ако са празни."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM movies")
    count = cur.fetchone()[0]
    if count > 0:
        return

    for title, info in MOVIES.items():
        movie_id = info["id"]
        cur.execute(
            "INSERT OR IGNORE INTO movies (movie_id, title) VALUES (?, ?)",
            (movie_id, title),
        )
        for hall, times in info["halls"].items():
            for t in times:
                cur.execute(
                    "INSERT INTO shows (movie_id, hall, show_time) VALUES (?, ?, ?)",
                    (movie_id, hall, t),
                )

    conn.commit()


# ----------------- BOOKING / SEATS -----------------


def save_booking(
    movie_id: str,
    movie_title: str,
    hall: str,
    show_time: str,
    client_name: str,
    seats: Iterable[str],
    booking_code: str,
    ticket_type: str,
    price_per_seat: float,
    total_price: float,
) -> None:
    """Записва резервацията в bookings."""
    conn = get_connection()
    cur = conn.cursor()

    seats_str = ",".join(seats)

    cur.execute(
        """
        INSERT INTO bookings (
            booking_code, movie_id, movie_title,
            hall, show_time, client_name, seats,
            ticket_type, price_per_seat, total_price
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            booking_code,
            movie_id,
            movie_title,
            hall,
            show_time,
            client_name,
            seats_str,
            ticket_type,
            price_per_seat,
            total_price,
        ),
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
            (movie_id, hall, show_time, seat.strip()),
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


def cancel_booking(booking_code: str) -> Tuple[bool, str]:
    """
    Отказва резервация по код:
    - маха заетите места от taken_seats
    - маркира booking като canceled
    Връща (успех, причина).
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT movie_id, hall, show_time, seats, is_canceled
        FROM bookings
        WHERE booking_code = ?
        """,
        (booking_code,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "not_found"

    movie_id, hall, show_time, seats_str, is_canceled = row
    if is_canceled:
        conn.close()
        return False, "already_canceled"

    seats = [s.strip() for s in seats_str.split(",") if s.strip()]

    for seat in seats:
        cur.execute(
            """
            DELETE FROM taken_seats
            WHERE movie_id = ? AND hall = ? AND show_time = ? AND seat_id = ?
            """,
            (movie_id, hall, show_time, seat),
        )

    cur.execute(
        """
        UPDATE bookings
        SET is_canceled = 1,
            canceled_at = CURRENT_TIMESTAMP
        WHERE booking_code = ?
        """,
        (booking_code,),
    )

    conn.commit()
    conn.close()
    return True, "ok"


# ----------------- MOVIES / SHOWS -----------------


def get_all_movie_titles() -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title FROM movies ORDER BY title")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_movie_id_for_title(title: str) -> str:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT movie_id FROM movies WHERE title = ? LIMIT 1", (title,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""


def get_halls_for_movie(title: str) -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DISTINCT s.hall
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        WHERE m.title = ?
        ORDER BY s.hall
        """,
        (title,),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_show_times(title: str, hall: str) -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.show_time
        FROM shows s
        JOIN movies m ON s.movie_id = m.movie_id
        WHERE m.title = ? AND s.hall = ?
        ORDER BY s.show_time
        """,
        (title, hall),
    )
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def _make_slug(title: str) -> str:
    base = title.lower().strip().replace(" ", "_")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    cleaned = "".join(ch for ch in base if ch in allowed)
    return cleaned or "movie"


def add_movie(title: str) -> str:
    """Добавя нов филм. Връща movie_id (slug)."""
    movie_id = _make_slug(title)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO movies (movie_id, title) VALUES (?, ?)",
        (movie_id, title),
    )
    conn.commit()
    conn.close()
    return movie_id


def add_show(movie_id: str, hall: str, show_time: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO shows (movie_id, hall, show_time) VALUES (?, ?, ?)",
        (movie_id, hall, show_time),
    )
    conn.commit()
    conn.close()


def get_movies_with_show_counts() -> List[Tuple[str, int]]:
    """За Admin таблицата: (title, number_of_shows)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT m.title, COUNT(s.id) AS cnt
        FROM movies m
        LEFT JOIN shows s ON m.movie_id = s.movie_id
        GROUP BY m.movie_id, m.title
        ORDER BY m.title
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------- STATS -----------------


def get_stats_by_movie() -> List[Tuple[str, int]]:
    """
    Колко резервации има за всеки филм (без отменените).
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT movie_title, COUNT(*) as cnt
        FROM bookings
        WHERE is_canceled = 0
        GROUP BY movie_id, movie_title
        ORDER BY cnt DESC, movie_title ASC
        """
    )

    rows = cur.fetchall()
    conn.close()
    return rows
