import sys
import os
from dotenv import load_dotenv
import requests
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from io import BytesIO

load_dotenv()
API_KEY = os.getenv("STATIC_MAPS_API_KEY")

ZOOM = 10
MIN_ZOOM = 1
MAX_ZOOM = 17


def get_move_step(zoom):
    return 180 / (2 ** zoom)


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yandex Maps Viewer")
        self.setGeometry(100, 100, 600, 550)

        self.coords = [37.6173, 55.7558]  # Москва (долгота, широта)
        self.zoom = ZOOM
        self.map_type = 'light'

        # Настроим интерфейс
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.toggle_button = QPushButton("Сменить тему", self)
        self.toggle_button.clicked.connect(self.toggle_map_theme)

        self.coord_input = QLineEdit(self)
        self.coord_input.setPlaceholderText("Введите координаты (долгота, широта)")
        self.coord_input.returnPressed.connect(self.set_coordinates)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.coord_input)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_map()

    def update_map(self):
        map_data = self.get_map(self.coords, self.zoom)
        if map_data:
            pixmap = QPixmap()
            pixmap.loadFromData(map_data)
            self.label.setPixmap(pixmap)

    def get_map(self, coords, zoom):
        url = "https://static-maps.yandex.ru/1.x/"
        params = {
            "ll": f"{coords[0]},{coords[1]}",
            "z": zoom,
            "size": "600,450",
            "l": "map",
            "theme": self.get_map_type(),
            "apikey": API_KEY
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return BytesIO(response.content).read()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка загрузки карты: {e}")
            return None

    def keyPressEvent(self, event):
        move_step = get_move_step(self.zoom)
        if event.key() == Qt.Key.Key_PageUp and self.zoom < MAX_ZOOM:
            self.zoom += 1
        elif event.key() == Qt.Key.Key_PageDown and self.zoom > MIN_ZOOM:
            self.zoom -= 1
        elif event.key() == Qt.Key.Key_Up:
            self.coords[1] = min(self.coords[1] + move_step, 85.0)
        elif event.key() == Qt.Key.Key_Down:
            self.coords[1] = max(self.coords[1] - move_step, -85.0)
        elif event.key() == Qt.Key.Key_Left:
            self.coords[0] = max(self.coords[0] - move_step, -180.0)
        elif event.key() == Qt.Key.Key_Right:
            self.coords[0] = min(self.coords[0] + move_step, 180.0)
        self.update_map()

    def toggle_map_theme(self):
        current_type = self.get_map_type()
        new_type = "dark" if current_type == "light" else "light"
        self.set_map_type(new_type)
        self.update_map()

    def get_map_type(self):
        return self.map_type

    def set_map_type(self, map_type):
        self.map_type = map_type

    def set_coordinates(self):
        try:
            coords = self.coord_input.text().strip().split(",")
            if len(coords) == 2:
                lon, lat = float(coords[0]), float(coords[1])
                if -180.0 <= lon <= 180.0 and -85.0 <= lat <= 85.0:
                    self.coords = [lon, lat]
                    self.update_map()
                else:
                    print("Координаты вне допустимого диапазона!")
            else:
                print("Введите координаты в формате: долгота, широта")
        except ValueError:
            print("Некорректный формат координат!")
        QApplication.focusWidget().clearFocus()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())