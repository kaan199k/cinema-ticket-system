# admin_window.py

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
)

from storage import (
    get_all_movie_titles,
    add_movie,
    add_show,
    get_movies_with_show_counts,
    get_movie_id_for_title,
)


class AdminWindow(QDialog):
    """
    Прост Admin прозорец:
    - Добавяне на нов филм
    - Добавяне на прожекция (movie + hall + time)
    - Таблица с филми и брой прожекции
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Admin · Movies & Shows")
        self.resize(520, 380)

        main_layout = QVBoxLayout()

        top_row = QHBoxLayout()

        # ---- Add movie ----
        movie_group = QGroupBox("Add movie")
        mg_layout = QVBoxLayout()

        self.movie_title_edit = QLineEdit()
        self.movie_title_edit.setPlaceholderText("Movie title (e.g. True Romance)")
        self.movie_add_btn = QPushButton("Add movie")
        self.movie_add_btn.clicked.connect(self._handle_add_movie)

        mg_layout.addWidget(QLabel("Title"))
        mg_layout.addWidget(self.movie_title_edit)
        mg_layout.addWidget(self.movie_add_btn)
        movie_group.setLayout(mg_layout)

        # ---- Add showtime ----
        show_group = QGroupBox("Add showtime")
        sg_layout = QVBoxLayout()

        self.show_movie_combo = QComboBox()
        self._reload_movie_combo()

        self.hall_edit = QLineEdit()
        self.hall_edit.setPlaceholderText("Hall (e.g. Hall 1, VIP Hall)")

        self.time_edit = QLineEdit()
        self.time_edit.setPlaceholderText("Time (e.g. 19:00)")

        self.show_add_btn = QPushButton("Add showtime")
        self.show_add_btn.clicked.connect(self._handle_add_show)

        sg_layout.addWidget(QLabel("Movie"))
        sg_layout.addWidget(self.show_movie_combo)
        sg_layout.addWidget(QLabel("Hall"))
        sg_layout.addWidget(self.hall_edit)
        sg_layout.addWidget(QLabel("Time"))
        sg_layout.addWidget(self.time_edit)
        sg_layout.addWidget(self.show_add_btn)
        show_group.setLayout(sg_layout)

        top_row.addWidget(movie_group)
        top_row.addWidget(show_group)

        main_layout.addLayout(top_row)

        # ---- Movies table ----
        table_group = QGroupBox("Movies & showtimes")
        tg_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Movie", "Showtimes"])
        tg_layout.addWidget(self.table)
        table_group.setLayout(tg_layout)

        main_layout.addWidget(table_group)

        # status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

        self._reload_table()

    def _reload_movie_combo(self) -> None:
        self.show_movie_combo.clear()
        titles = get_all_movie_titles()
        self.show_movie_combo.addItems(titles)

    def _reload_table(self) -> None:
        rows = get_movies_with_show_counts()
        self.table.setRowCount(len(rows))
        for i, (title, cnt) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(title))
            self.table.setItem(i, 1, QTableWidgetItem(str(cnt)))
        self.table.resizeColumnsToContents()

    def _handle_add_movie(self) -> None:
        title = self.movie_title_edit.text().strip()
        if not title:
            self.status_label.setText("Enter movie title.")
            return

        movie_id = add_movie(title)
        self.status_label.setText(f"Movie added: {title} (id: {movie_id})")

        self.movie_title_edit.clear()
        self._reload_movie_combo()
        self._reload_table()

    def _handle_add_show(self) -> None:
        title = self.show_movie_combo.currentText().strip()
        hall = self.hall_edit.text().strip()
        time = self.time_edit.text().strip()

        if not title:
            self.status_label.setText("Select a movie.")
            return
        if not hall or not time:
            self.status_label.setText("Hall and time are required.")
            return

        movie_id = get_movie_id_for_title(title)
        if not movie_id:
            self.status_label.setText("Movie not found in DB.")
            return

        add_show(movie_id, hall, time)
        self.status_label.setText(f"Showtime added: {title} · {hall} · {time}")

        self.hall_edit.clear()
        self.time_edit.clear()
        self._reload_table()
