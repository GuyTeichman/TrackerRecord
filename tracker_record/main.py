import importlib
import os
import sys

from tracker_record import gui


def run():
    app = gui.QtWidgets.QApplication(sys.argv)
    app.setOrganizationName("GuyTeichman")
    app.setOrganizationDomain("github.com/GuyTeichman")
    app.setApplicationName("Tracker Record")
    window = gui.MainWindow()
    app.setWindowIcon(window.style().standardIcon(gui.QtWidgets.QStyle.StandardPixmap.SP_MediaPlay))
    # close built-in splash screen in frozen app version of DoubleBlind
    if '_PYIBoot_SPLASH' in os.environ and importlib.util.find_spec("pyi_splash"):
        import pyi_splash
        pyi_splash.close()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
