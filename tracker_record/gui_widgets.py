from pathlib import Path

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QSpinBox, QWidget


class SliderBoxWidget(QtWidgets.QWidget):
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, min_val=1, max_val=20):
        super().__init__(parent)
        self.layout = QtWidgets.QHBoxLayout(self)

        self.spinbox = QSpinBox()
        self.spinbox.setRange(min_val, max_val)
        self.spinbox.setValue(max_val)
        self.spinbox.valueChanged.connect(self.update_slider)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(max_val)
        self.slider.setSizePolicy(QtWidgets.QSizePolicy.Policy.Maximum, QtWidgets.QSizePolicy.Policy.Maximum)
        self.slider.valueChanged.connect(self.update_spinbox)

        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.spinbox)

    def update_slider(self, value: int):
        self.slider.setValue(value)
        self.valueChanged.emit(value)

    def update_spinbox(self, value: int):
        self.spinbox.setValue(value)
        self.valueChanged.emit(value)

    def value(self):
        return self.spinbox.value()


class StartStopWidget(QWidget):
    def __init__(self, start_callback, stop_callback):
        super().__init__()
        self.start_callback = start_callback
        self.stop_callback = stop_callback

        self.start_button = QtWidgets.QPushButton("Start Recording")
        self.start_button.setCheckable(True)
        self.start_button.clicked.connect(self.on_start)

        self.stop_button = QtWidgets.QPushButton("Stop Recording")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.on_stop)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)

    def on_start(self):
        if self.start_button.isChecked():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.start_callback()

    def on_stop(self):
        self.start_button.setEnabled(True)
        self.start_button.setChecked(False)
        self.stop_button.setEnabled(False)
        self.stop_callback()


class PathLineEdit(QtWidgets.QWidget):
    textChanged = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.file_path = QtWidgets.QLineEdit('', self)
        self.open_button = QtWidgets.QPushButton('Choose save path', self)
        self._is_legal = False

        self.layout = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout)
        self.layout.addWidget(self.open_button, 1, 0)
        self.layout.addWidget(self.file_path, 1, 1)

        self.file_path.textChanged.connect(self._check_legality)
        self.open_button.clicked.connect(self.choose_file)
        contents = 'No path chosen'
        self.file_path.setText(contents)

    def clear(self):
        self.file_path.clear()

    @property
    def is_legal(self):
        return self._is_legal

    def _check_legality(self):
        current_path = self.file_path.text()
        if Path(current_path).parent.exists():
            self._is_legal = True
        else:
            self._is_legal = False
        self.set_file_path_bg_color()
        self.textChanged.emit(self.is_legal)

    def set_file_path_bg_color(self):
        if self.is_legal:
            self.file_path.setStyleSheet("QLineEdit{border: 1.5px solid #57C4AD;}")
        else:
            self.file_path.setStyleSheet("QLineEdit{border: 1.5px solid #DB4325;}")

    def disable_bg_color(self):
        self.file_path.setStyleSheet("QLineEdit{}")

    def setEnabled(self, to_enable: bool):
        self.setDisabled(not to_enable)

    def setDisabled(self, to_disable: bool):
        if to_disable:
            self.disable_bg_color()
        else:
            self.set_file_path_bg_color()
        super().setDisabled(to_disable)

    def choose_file(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Choose a save path", filter="AVI file (*.avi)")
        if filename:
            self.file_path.setText(filename)

    def text(self):
        return self.file_path.text()

    def setText(self, text: str):
        return self.file_path.setText(text)

    def path(self):
        return Path(self.text())
