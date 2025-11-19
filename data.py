# data.py

from typing import Dict, List

# Movies, halls, and showtimes.
MOVIES: Dict[str, Dict] = {
    "True Romance": {
        "id": "true_romance",
        "halls": {
            "Hall 1": ["12:00", "16:30", "21:00"],
            "Hall 2": ["14:15", "19:45"],
        },
    },
    "Indiana Jones and the Last Crusade": {
        "id": "indiana_jones_3",
        "halls": {
            "Hall 1": ["11:00", "15:00"],
            "Hall 3": ["18:30", "21:30"],
        },
    },
    "The Godfather": {
        "id": "godfather",
        "halls": {
            "Hall 2": ["13:00", "17:30"],
            "VIP Hall": ["20:30"],
        },
    },
    "Pulp Fiction": {
        "id": "pulp_fiction",
        "halls": {
            "Hall 3": ["12:30", "17:00", "22:15"],
        },
    },
    "Lost Highway": {
        "id": "lost_highway",
        "halls": {
            "Hall 4": ["19:00", "23:30"],
        },
    },
}

ROWS: List[str] = list("ABCDEFGH")  # A–H
NUM_COLUMNS: int = 12               # 1–12


def get_movie_titles() -> List[str]:
    return list(MOVIES.keys())


def get_movie_id(title: str) -> str:
    info = MOVIES.get(title)
    if not info:
        return ""
    return info["id"]
