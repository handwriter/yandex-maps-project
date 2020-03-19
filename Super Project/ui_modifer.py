from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtWidgets import QErrorMessage
from PyQt5.QtGui import QPixmap
from PIL.ImageQt import ImageQt
from PIL import Image
import requests
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt

import sys

sys.path.append('data\\ui-py\\')

from mainWindow import Ui_Form


class Widget(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.horizontalSlider.valueChanged.connect(self.changeZoom)
        self.pushButton.clicked.connect(self.query)
        self.pushButton_2.clicked.connect(self.editMoveMapMode)
        self.horizontalSlider.sliderReleased.connect(self.query)
        self.comboBox.currentIndexChanged.connect(self.query)
        self.w = 0.0
        self.h = 0.0
        self.move_map_mode = False
        self.zoom = 0
        self.error_msg = QErrorMessage()
        self.zoom_map = {0: 18,
                         1: 24,
                         2: 18,
                         3: 13,
                         4: 9,
                         5: 1.3,
                         6: 0.9,
                         7: 0.5,
                         8: 0.1,
                         9: 0.068,
                         10: 0.03,
                         11: 0.009,
                         12: 0.005,
                         13: 0.001,
                         14: 0.0006,
                         15: 0.0002,
                         16: 0.00008,
                         17: 0.000046}
        self.type_map = {0: 'map',
                         1: 'sat',
                         2: 'sat,skl'}
        print(dir(self.lineEdit))

    def keyReleaseEvent(self, a0: QKeyEvent) -> None:
        if self.lineEdit.text() != '' or self.lineEdit_2.text() != '':
            self.lineEdit_3.setEnabled(False)
        elif self.lineEdit_3.text() != '':
            self.lineEdit.setEnabled(False)
            self.lineEdit_2.setEnabled(False)
        else:
            self.lineEdit.setEnabled(True)
            self.lineEdit_2.setEnabled(True)
            self.lineEdit_3.setEnabled(True)

    def indexChanged(self):
        self.query()
        print(1)
        return 1

    def editMoveMapMode(self, value=False):
        self.lineEdit.setEnabled(value)
        self.lineEdit_2.setEnabled(value)
        self.lineEdit_3.setEnabled(value)
        self.horizontalSlider.setEnabled(value)
        self.pushButton.setEnabled(value)
        self.pushButton_2.setEnabled(value)
        self.comboBox.setEnabled(value)
        self.move_map_mode = not value

    def changeZoom(self, z):
        self.zoom = z
        self.label_2.setText(f'Масштаб: {z}')

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        if a0.key() == Qt.Key_PageUp:
            if self.zoom < 17:
                self.zoom += 1
                self.horizontalSlider.setValue(self.zoom)
                self.query()
        elif a0.key() == Qt.Key_PageDown:
            if self.zoom > 0:
                self.zoom -= 1
                self.horizontalSlider.setValue(self.zoom)
                self.query()
        elif a0.key() == Qt.Key_Escape:
            if self.move_map_mode:
                self.editMoveMapMode(True)
        else:
            if self.move_map_mode:
                if a0.key() == Qt.Key_Up:
                    self.h += self.zoom_map[self.zoom]
                    self.query()
                elif a0.key() == Qt.Key_Down:
                    self.h -= self.zoom_map[self.zoom]
                    self.query()
                elif a0.key() == Qt.Key_Left:
                    self.w -= self.zoom_map[self.zoom]
                    self.query()
                elif a0.key() == Qt.Key_Right:
                    self.w += self.zoom_map[self.zoom]
                    self.query()

    def query(self):
        if self.lineEdit.text() != '' or self.lineEdit_2.text() != '':
            map_request = {'l': self.type_map[self.comboBox.currentIndex()], 'z': str(self.zoom)}
            w, h = self.lineEdit.text(), self.lineEdit_2.text()
            if self.is_valid(w, h):
                if -180 <= self.w + float(w) <= 180 and -90 <= self.h + float(h) <= 90:
                    map_request['ll'] = f'{float(w) + self.w},{float(h) + self.h}'
                else:
                    return
            else:
                return
            url = 'http://static-maps.yandex.ru/1.x/'
            request = requests.get(url, params=map_request, stream=True).raw
            a = QPixmap.fromImage(ImageQt(Image.open(request).convert('RGBA')))
            self.label_3.setPixmap(a)
        elif self.lineEdit_3.text() != '':
            toponym_to_find = self.lineEdit_3.text()

            geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

            geocoder_params = {
                "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                "geocode": toponym_to_find,
                "format": "json"}

            response = requests.get(geocoder_api_server, params=geocoder_params)
            if not response:
                pass

            json_response = response.json()

            toponym = json_response["response"]["GeoObjectCollection"][
                "featureMember"][0]["GeoObject"]

            toponym_coodrinates = toponym["Point"]["pos"]
            toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
            if self.is_valid(toponym_longitude, toponym_lattitude, address=2, coords=[toponym_longitude, toponym_lattitude]):
                toponym_longitude = float(toponym_longitude)
                toponym_lattitude = float(toponym_lattitude)
            else:
                return
            if toponym_longitude + self.w > 180 or toponym_longitude + self.w < -180 or toponym_lattitude + self.h > 90 or toponym_lattitude + self.h < -90:
                return
            print(1)
            map_params = {
                "ll": ",".join([str(toponym_longitude + self.w), str(toponym_lattitude + self.h)]),
                "l": "map",
                "z": self.zoom,
                'pt': ','.join(toponym_coodrinates.split()) + ',pmwtm'
            }

            map_api_server = "http://static-maps.yandex.ru/1.x/"
            response = requests.get(map_api_server, params=map_params, stream=True).raw
            a = QPixmap.fromImage(ImageQt(Image.open(response).convert('RGBA')))
            self.label_3.setPixmap(a)

    def is_valid(self, w, h, show_error=True, debag=False, address=1, coords=None):
        print(w, h)
        if debag:
            print('перевод долготы в float')
        try:
            if address == 1:
                w = float(self.lineEdit.text())
            else:
                w = float(coords[0])
        except Exception:
            self.error('Неверная долгота (выражается вещественным числом, через точку)')
            return

        if debag:
            print('проверка ограничения долготы (-180 - 180)')
        if w >= 180 or w <= -180:
            self.error('Неверная долгота (от -180 до 180)')
            return

        if debag:
            print('перевод широта в float')
        try:
            if address == 1:
                h = float(self.lineEdit.text())
            else:
                h = float(coords[1])
        except Exception:
            self.error('Неверная широта (выражается вещественным числом, через точку)')
            return

        if debag:
            print('проверка ограничения долготы (-90 - 90)')
        if h >= 90 or h <= -90:
            print(2)
            self.error('Неверная широта (от -90 до 90)')
            return

        return str(w), str(h)

    def error(self, msg):
        self.error_msg.showMessage(msg)