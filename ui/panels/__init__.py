"""
UI Panels Package

Contains the modular UI panel components for the Radiology Reader application.
"""

from ui.panels.bottom_panel import BottomPanel
from ui.panels.center_panel import CenterPanel
from ui.panels.inak_esak_panel import INAKESAKPanel
from ui.panels.left_panel import LeftPanel
from ui.panels.right_panel import RightPanel

__all__ = [
    "LeftPanel",
    "CenterPanel",
    "RightPanel",
    "BottomPanel",
    "INAKESAKPanel",
]
