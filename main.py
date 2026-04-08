"""Radiology Reader - Main Entry Point

A PySide6-based radiology image text recognition application.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import ThemeManager


def setup_high_dpi():
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")


def launch():
    setup_high_dpi()
    app = QApplication(sys.argv)
    app.setApplicationName("Radiology Reader")
    app.setOrganizationName("RadiologyApp")

    theme_mgr = ThemeManager()
    theme_mgr.apply(app)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch()
