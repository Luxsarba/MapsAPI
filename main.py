import sys
import os
from dotenv import load_dotenv
import requests
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from io import BytesIO

load_dotenv()
API_KEY = os.getenv("STATIC_MAPS_API_KEY")

COORDS = [37.6173, 55.7558]  # Москва (долгота, широта)
ZOOM = 10
MIN_ZOOM = 1
MAX_ZOOM = 17
MOVE_STEP = 0.1


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yandex Maps Viewer")
        self.setGeometry(100, 100, 600, 450)

        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 600, 450)

        self.update_map()

    def update_map(self):
        map_data = self.get_map(COORDS, ZOOM)
        pixmap = QPixmap()
        pixmap.loadFromData(map_data)
        self.label.setPixmap(pixmap)

    def get_map(self, coords, zoom):
        url = f"https://static-maps.yandex.ru/1.x/?ll={coords[0]},{coords[1]}&z={zoom}&size=600,450&l=map&apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content).read()
        else:
            print("Ошибка загрузки карты")
            sys.exit(1)

    def keyPressEvent(self, event):
        global ZOOM, COORDS
        if event.key() == Qt.Key.Key_PageUp and ZOOM < MAX_ZOOM:
            ZOOM += 1
        elif event.key() == Qt.Key.Key_PageDown and ZOOM > MIN_ZOOM:
            ZOOM -= 1
        elif event.key() == Qt.Key.Key_Up:
            COORDS[1] = min(COORDS[1] + MOVE_STEP, 85.0)
        elif event.key() == Qt.Key.Key_Down:
            COORDS[1] = max(COORDS[1] - MOVE_STEP, -85.0)
        elif event.key() == Qt.Key.Key_Left:
            COORDS[0] = max(COORDS[0] - MOVE_STEP, -180.0)
        elif event.key() == Qt.Key.Key_Right:
            COORDS[0] = min(COORDS[0] + MOVE_STEP, 180.0)
        self.update_map()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())