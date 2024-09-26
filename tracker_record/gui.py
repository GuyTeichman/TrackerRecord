import os
import sys
from pathlib import Path

import numpy as np
from PyQt6 import QtWidgets, QtCore, QtGui, QtOpenGLWidgets
from PyQt6.QtWidgets import QMainWindow, QWidget

from tracker_record import record, gui_widgets, __version__

MAX_FPS = 20


class CameraFeed(QtOpenGLWidgets.QOpenGLWidget):
    timeElapsed = QtCore.pyqtSignal()

    def __init__(self, cti_path: Path):
        super().__init__()
        self.timer = QtCore.QTimer()
        self.frame_rate = 20  # Default frame rate
        self.n = 0
        self.recorder = record.TrackerRecorder([cti_path.as_posix()])
        self.current_writer = None
        self.duration = -1
        self.elapsed = -1
        self.image = None

    def start_recording(self, save_path: Path, duration_sec: int):
        self.current_writer = self.recorder.get_writer(save_path, self.frame_rate)
        self.duration = duration_sec * self.frame_rate
        self.elapsed = 0

    def stop_recording(self):
        self.current_writer.release()
        self.current_writer = None
        self.duration = -1
        self.elapsed = -1

    def set_frame_rate(self, fps):
        self.frame_rate = fps
        self.timer.start(1000 // self.frame_rate)

    def start_live_feed(self):
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1000 // self.frame_rate)

    def update_frame(self):
        frame = self.recorder.get_frame()
        height, width = frame.shape
        q_image = QtGui.QImage(frame.data, width, height, width, QtGui.QImage.Format.Format_Grayscale8)
        self.set_image(q_image)

        if self.elapsed < self.duration:
            self.record_frame(frame)
            self.elapsed += 1
        elif self.duration != -1:
            self.timeElapsed.emit()

    def record_frame(self, frame: np.ndarray):
        self.current_writer.write(frame)

    def set_image(self, image):
        self.image = image
        self.update()

    def paintEvent(self, event):
        if hasattr(self, 'image'):
            self.makeCurrent()  # Ensure the OpenGL context is current
            painter = QtGui.QPainter(self)

            # Get the widget dimensions
            widget_size = self.size()

            # Scale the image to fit the widget while maintaining the aspect ratio
            scaled_image = self.image.scaled(widget_size, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                             QtCore.Qt.TransformationMode.SmoothTransformation)

            # Draw the scaled image
            painter.drawImage((widget_size.width() - scaled_image.width()) // 2,
                              (widget_size.height() - scaled_image.height()) // 2,
                              scaled_image)

            if self.current_writer is not None:
                painter.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0), 2))  # Red pen, 2 pixels wide
            else:
                painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))  # black pen, 2 pixels wide
            painter.drawRect(1, 1, self.width() - 3, self.height() - 3)  # Adjust for border width

    def closeEvent(self, event):
        self.recorder.stop()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QtWidgets.QGridLayout(self.central_widget)
        self.setup_ui()

        self.settings = QtCore.QSettings()
        # Check if the CTI path is set in the settings
        self.cti_file_path = self.settings.value("CTIFilePath", type=str)
        while True:
            try:
                self.camera_feed = CameraFeed(Path(self.cti_file_path))
                break
            except ValueError as e:
                QtWidgets.QMessageBox.warning(self, "Error",
                                              "No device available. \n"
                                              "Please ensure your camera is connected, and choose a valid CTI file. "
                                              "(For example: \n"
                                              "'C:/Program Files/STEMMER IMAGING/Common Vision Blox/GenICam/"
                                              ".../GEVTL.cti')")
                self.prompt_for_cti_file()

        self.framerate_box = gui_widgets.SliderBoxWidget()
        self.framerate_box.valueChanged.connect(self.update_frame_rate)

        # Duration input
        self.duration_label = QtWidgets.QLabel("Duration (seconds):")
        self.duration_spinbox = QtWidgets.QSpinBox()
        self.duration_spinbox.setRange(1, 24 * 60 * 60)  # 24 hours in seconds
        self.duration_spinbox.setSuffix(" seconds")
        # Path input (assuming PathLineEdit is defined elsewhere)
        self.path_line_edit = gui_widgets.PathLineEdit()
        # Start/Stop widget
        self.start_stop_widget = gui_widgets.StartStopWidget(self.start_recording, self.stop_recording)
        self.camera_feed.timeElapsed.connect(self.start_stop_widget.on_stop)

        # Layout setup
        self.layout.addWidget(self.camera_feed, 0, 0, 1, 2)
        self.layout.addWidget(QtWidgets.QLabel("Frame Rate:"), 1, 0)
        self.layout.addWidget(self.framerate_box, 1, 1)
        self.layout.addWidget(self.duration_label, 2, 0)
        self.layout.addWidget(self.duration_spinbox, 2, 1)
        self.layout.addWidget(QtWidgets.QLabel("Save Path:"), 3, 0)
        self.layout.addWidget(self.path_line_edit, 3, 1)
        self.layout.addWidget(self.start_stop_widget, 4, 0, 1, 2)  # Span across two columns
        self.layout.setRowStretch(0, 2)

        self.camera_feed.start_live_feed()

    def setup_ui(self):
        self.setWindowTitle("Tracker Camera")
        self.setGeometry(100, 100, 800, 600)

    @staticmethod
    def is_cti_legal(file_path: str):
        return isinstance(file_path, str) and Path(file_path).exists() and Path(
            file_path).is_file() and file_path.lower().endswith(".cti")

    def prompt_for_cti_file(self):
        while True:
            # Create a file dialog to select the CTI file

            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select CTI File", "",
                                                                 "CTI Files (*.cti);;All Files (*)",
                                                                 options=QtWidgets.QFileDialog.Option.ReadOnly)

            if self.is_cti_legal(file_path):
                # Save the selected path in the settings
                self.settings.setValue("CTIFilePath", file_path)
                self.cti_file_path = file_path
                return
            elif not file_path:  # User canceled the dialog
                break
            else:
                QtWidgets.QMessageBox.critical(self, "Error", "You must select a CTI file to proceed.")
        sys.exit()

    def update_frame_rate(self, value):
        self.camera_feed.set_frame_rate(value)

    def start_recording(self):
        # Check if the directory of the provided path is valid
        save_path = self.path_line_edit.text()
        directory = os.path.dirname(save_path)

        if not os.path.isdir(directory) and directory:  # Check if directory exists
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid save path!")
            self.start_stop_widget.start_button.setChecked(False)
            return

        # Lock other inputs
        self.framerate_box.setEnabled(False)
        self.duration_spinbox.setEnabled(False)
        self.path_line_edit.setEnabled(False)

        self.camera_feed.start_recording(Path(save_path), self.duration_spinbox.value())
        print("Starting recording...")

    def stop_recording(self):
        # Unlock other inputs
        self.framerate_box.setEnabled(True)
        self.duration_spinbox.setEnabled(True)
        self.path_line_edit.setEnabled(True)

        self.camera_feed.stop_recording()
        print("Stop recording. ")


def splash_screen():
    img_path = str(Path(__file__).parent.joinpath('splash.png'))
    splash_pixmap = QtGui.QPixmap(img_path)
    splash_font = QtGui.QFont('Calibri', 16)
    splash = QtWidgets.QSplashScreen(splash_pixmap)
    splash.setFont(splash_font)
    splash.showMessage(f"<i>TrackerRecord</i> version {__version__}",
                       QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter)
    splash.show()
    return splash
