import sys
import os
from dotenv import load_dotenv
import requests
from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow
from PyQt6.QtGui import QPixmap
from io import BytesIO

print("Загружаю .env:", os.path.exists("../YandexMapsAPI/.env"))
load_dotenv()

API_KEY = os.getenv("STATIC_MAPS_API_KEY")
COORDS = "37.6173,55.7558"  # Москва
ZOOM = "10"


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yandex Maps Viewer")
        self.setGeometry(100, 100, 600, 450)

        map_data = self.get_map(COORDS, ZOOM)

        label = QLabel(self)
        pixmap = QPixmap()
        pixmap.loadFromData(map_data)
        label.setPixmap(pixmap)
        label.setGeometry(0, 0, 600, 450)

    def get_map(self, coords, zoom):
        url = f"https://static-maps.yandex.ru/1.x/?ll={coords}&z={zoom}&size=600,450&l=map&apikey={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content).read()
        else:
            print("Ошибка загрузки карты")
            sys.exit(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MapApp()
    window.show()
    sys.exit(app.exec())
