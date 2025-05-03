import sys
import os
from dotenv import load_dotenv
import requests
from PyQt6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton, QLineEdit,
    QVBoxLayout, QWidget, QHBoxLayout, QCheckBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from io import BytesIO

load_dotenv()
STATIC_MAPS_API_KEY = os.getenv("STATIC_MAPS_API_KEY")
GEOCODER_API_KEY = os.getenv("GEOCODER_API_KEY")

ZOOM = 10
MIN_ZOOM = 1
MAX_ZOOM = 17


def get_move_step(zoom):
    return 180 / (2 ** zoom)


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yandex Maps Viewer")
        self.setGeometry(100, 100, 600, 680)

        self.coords = [37.6173, 55.7558]
        self.zoom = ZOOM
        self.map_type = 'light'
        self.point = None
        self.last_geo_data = None

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setScaledContents(False)
        self.label.mousePressEvent = self.handle_map_click

        self.toggle_button = QPushButton("Сменить тему", self)
        self.toggle_button.clicked.connect(self.toggle_map_theme)

        self.coord_input = QLineEdit(self)
        self.coord_input.setPlaceholderText("Введите координаты (долгота, широта)")
        self.coord_input.returnPressed.connect(self.set_coordinates)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введите адрес или объект")
        self.search_input.returnPressed.connect(self.search_location)

        self.search_button = QPushButton("Искать", self)
        self.search_button.clicked.connect(self.search_location)

        self.reset_button = QPushButton("Сброс поискового результата", self)
        self.reset_button.clicked.connect(self.reset_search_point)

        self.address_output = QLineEdit(self)
        self.address_output.setReadOnly(True)
        self.address_output.setPlaceholderText("Адрес найденного объекта")

        self.index_checkbox = QCheckBox("Показывать почтовый индекс")
        self.index_checkbox.setChecked(True)
        self.index_checkbox.stateChanged.connect(self.update_address_display)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(search_layout)
        layout.addWidget(self.address_output)
        layout.addWidget(self.index_checkbox)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.coord_input)
        layout.addWidget(self.reset_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.update_map()

    def handle_map_click(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            img_width, img_height = 600, 450

            label_width = self.label.width()
            label_height = self.label.height()

            scale_x = label_width / img_width
            scale_y = label_height / img_height

            if scale_x * img_height <= label_height:
                scale = scale_x
                offset_x = 0
                offset_y = (label_height - img_height * scale) / 2
            else:
                scale = scale_y
                offset_x = (label_width - img_width * scale) / 2
                offset_y = 0

            click_x = (event.pos().x() - offset_x) / scale
            click_y = (event.pos().y() - offset_y) / scale

            if 0 <= click_x <= img_width and 0 <= click_y <= img_height:
                norm_x = (click_x / img_width) - 0.5
                norm_y = 0.5 - (click_y / img_height)

                move_step = get_move_step(self.zoom)
                lon = self.coords[0] + norm_x * 360 / (2 ** (self.zoom - 1))
                lat = self.coords[1] + norm_y * 180 / (2 ** (self.zoom - 1))

                lon = max(-180.0, min(180.0, lon))
                lat = max(-85.0, min(85.0, lat))

                self.reverse_geocode(lon, lat)

    def reverse_geocode(self, lon, lat):
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": GEOCODER_API_KEY,
            "geocode": f"{lon},{lat}",
            "format": "json"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            json_data = response.json()
            feature = json_data["response"]["GeoObjectCollection"]["featureMember"]
            if not feature:
                print("Ничего не найдено.")
                return

            geo_obj = feature[0]["GeoObject"]
            self.last_geo_data = geo_obj["metaDataProperty"]["GeocoderMetaData"]
            self.point = [lon, lat]
            self.update_address_display()
            self.update_map()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при обратном геокодинге: {e}")

    def update_map(self):
        map_data = self.get_map(self.coords, self.zoom, self.point)
        if map_data:
            pixmap = QPixmap()
            pixmap.loadFromData(map_data)
            self.label.setPixmap(pixmap)

    def get_map(self, coords, zoom, point=None):
        url = "https://static-maps.yandex.ru/1.x/"
        params = {
            "ll": f"{coords[0]},{coords[1]}",
            "z": zoom,
            "size": "600,450",
            "l": "map",
            "theme": self.get_map_type(),
            "apikey": STATIC_MAPS_API_KEY
        }
        if point:
            params["pt"] = f"{point[0]},{point[1]},pm2rdm"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return BytesIO(response.content).read()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка загрузки карты: {e}")
            return None

    def keyPressEvent(self, event):
        move_step = get_move_step(self.zoom)
        key = event.key()

        if key == Qt.Key.Key_Escape:
            QApplication.focusWidget().clearFocus()
            return

        if key == Qt.Key.Key_PageUp and self.zoom < MAX_ZOOM:
            self.zoom += 1
        elif key == Qt.Key.Key_PageDown and self.zoom > MIN_ZOOM:
            self.zoom -= 1
        elif key == Qt.Key.Key_Up:
            self.coords[1] = min(self.coords[1] + move_step, 85.0)
        elif key == Qt.Key.Key_Down:
            self.coords[1] = max(self.coords[1] - move_step, -85.0)
        elif key == Qt.Key.Key_Left:
            self.coords[0] = max(self.coords[0] - move_step, -180.0)
        elif key == Qt.Key.Key_Right:
            self.coords[0] = min(self.coords[0] + move_step, 180.0)
        self.update_map()

    def toggle_map_theme(self):
        self.map_type = "dark" if self.map_type == "light" else "light"
        self.update_map()

    def get_map_type(self):
        return self.map_type

    def set_coordinates(self):
        try:
            coords = self.coord_input.text().strip().split(",")
            if len(coords) == 2:
                lon, lat = float(coords[0]), float(coords[1])
                if -180.0 <= lon <= 180.0 and -85.0 <= lat <= 85.0:
                    self.coords = [lon, lat]
                    self.point = None
                    self.last_geo_data = None
                    self.address_output.clear()
                    self.update_map()
                else:
                    print("Координаты вне допустимого диапазона!")
            else:
                print("Введите координаты в формате: долгота, широта")
        except ValueError:
            print("Некорректный формат координат!")
        QApplication.focusWidget().clearFocus()

    def search_location(self):
        query = self.search_input.text().strip()
        if not query:
            return

        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": GEOCODER_API_KEY,
            "geocode": query,
            "format": "json"
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            json_data = response.json()
            feature = json_data["response"]["GeoObjectCollection"]["featureMember"]
            if not feature:
                print("Ничего не найдено.")
                return

            geo_obj = feature[0]["GeoObject"]
            self.last_geo_data = geo_obj["metaDataProperty"]["GeocoderMetaData"]
            point_str = geo_obj["Point"]["pos"]
            lon, lat = map(float, point_str.split())

            self.coords = [lon, lat]
            self.point = [lon, lat]
            self.update_address_display()
            self.update_map()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при поиске: {e}")
        QApplication.focusWidget().clearFocus()

    def update_address_display(self):
        if not self.last_geo_data:
            return
        base_text = self.last_geo_data.get("text", "")
        postal_code = self.last_geo_data.get("Address", {}).get("postal_code", "")
        if self.index_checkbox.isChecked() and postal_code:
            self.address_output.setText(f"{base_text}, {postal_code}")
        else:
            self.address_output.setText(base_text)

    def reset_search_point(self):
        self.point = None
        self.search_input.clear()
        self.address_output.clear()
        self.last_geo_data = None
        self.update_map()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())