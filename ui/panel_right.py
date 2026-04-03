"""
ui/panel_right.py
─────────────────
Right panel — detection results, metrics, and crop thumbnails.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QScrollArea, QStackedWidget, QHeaderView,
    QAbstractItemView, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.theme import COLORS
from ui.widgets import MetricCard, Divider, ImageViewer


class RightPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(300)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_placeholder())
        self.stack.addWidget(self._build_results_view())

        root.addWidget(self.stack)

    def _build_placeholder(self) -> QWidget:
        self._placeholder = QWidget()

        lay = QVBoxLayout(self._placeholder)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._placeholder_lbl = QLabel(
            "No results yet.\nRun detection to see output here."
        )
        self._placeholder_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._placeholder_lbl)

        self._apply_placeholder_style()
        return self._placeholder

    def _build_results_view(self) -> QWidget:
        self._results_widget = QWidget()

        lay = QVBoxLayout(self._results_widget)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(10)

        hdr = QHBoxLayout()
        self._det_hdr_lbl = QLabel("DETECTIONS")
        self._det_count_lbl = QLabel("0 objects")
        hdr.addWidget(self._det_hdr_lbl)
        hdr.addStretch()
        hdr.addWidget(self._det_count_lbl)
        lay.addLayout(hdr)

        metrics_row = QHBoxLayout()
        self._card_total = MetricCard("Total", "0")
        self._card_conf = MetricCard("Avg Conf", "—")
        metrics_row.addWidget(self._card_total)
        metrics_row.addWidget(self._card_conf)
        lay.addLayout(metrics_row)

        lay.addWidget(Divider())

        self._table = self._build_table()
        lay.addWidget(self._table)

        lay.addWidget(Divider())

        self._crops_hdr_lbl = QLabel("CROPS")
        lay.addWidget(self._crops_hdr_lbl)

        self._crops_scroll = QScrollArea()
        self._crops_scroll.setWidgetResizable(True)
        self._crops_scroll.setFixedHeight(160)

        self._crops_container = QWidget()
        self._crops_layout = QHBoxLayout(self._crops_container)
        self._crops_layout.setContentsMargins(4, 4, 4, 4)
        self._crops_layout.setSpacing(6)
        self._crops_layout.addStretch()

        self._crops_scroll.setWidget(self._crops_container)
        lay.addWidget(self._crops_scroll)

        self._apply_results_style()
        return self._results_widget

    def _build_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "TEXT", "CONF", "SIZE"])

        hh = table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(0, 44)
        table.setColumnWidth(2, 60)
        table.setColumnWidth(3, 90)

        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setAlternatingRowColors(False)

        return table

    # ── inline theme styles ──────────────────────────────────────────────

    def _apply_placeholder_style(self) -> None:
        self._placeholder.setStyleSheet(
            f"background:{COLORS['surface']};"
        )
        self._placeholder_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};font-size:12px;line-height:1.6;"
        )

    def _apply_results_style(self) -> None:
        self._results_widget.setStyleSheet(f"background:{COLORS['bg']};")

        _muted = (
            f"color:{COLORS['text_muted']};"
            f"font-size:10px;font-weight:700;letter-spacing:2px;"
        )
        self._det_hdr_lbl.setStyleSheet(_muted)
        self._crops_hdr_lbl.setStyleSheet(_muted)

        self._det_count_lbl.setStyleSheet(
            f"color:{COLORS['accent']};"
            f"font-size:11px;font-family:'Consolas',monospace;"
        )

    # ── public API ───────────────────────────────────────────────────────

    def showResult(self, result: dict) -> None:
        dets: list[dict] = result.get("detections", [])
        n = len(dets)

        plural = "object" if n == 1 else "objects"
        self._det_count_lbl.setText(f"{n} {plural}")
        self._card_total.setValue(str(n))

        if dets:
            avg_conf = sum(d["conf"] for d in dets) / n
            self._card_conf.setValue(f"{avg_conf:.2f}")
        else:
            self._card_conf.setValue("—")

        self._table.setRowCount(0)
        for det in dets:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(
                row, 0,
                self._cell(f"{det['id']:02d}", Qt.AlignmentFlag.AlignCenter),
            )
            self._table.setItem(row, 1, self._cell(det["text"] or "—"))

            conf_item = self._cell(
                f"{det['conf']:.2f}", Qt.AlignmentFlag.AlignCenter
            )
            conf_item.setForeground(self._conf_color(det["conf"]))
            self._table.setItem(row, 2, conf_item)

            self._table.setItem(
                row, 3,
                self._cell(
                    f"{det['w']:.0f}×{det['h']:.0f}",
                    Qt.AlignmentFlag.AlignCenter,
                ),
            )
            self._table.setRowHeight(row, 34)

        self._clear_crops()
        for det in dets:
            arr = det.get("crop_arr")
            if arr is not None:
                thumb = ImageViewer()
                thumb.setFixedSize(120, 120)
                thumb.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                thumb.setImage(arr)
                thumb.setToolTip(det.get("text", ""))
                self._crops_layout.insertWidget(
                    self._crops_layout.count() - 1, thumb
                )

        self.stack.setCurrentIndex(1)

    def clear(self) -> None:
        self._table.setRowCount(0)
        self._det_count_lbl.setText("0 objects")
        self._card_total.setValue("0")
        self._card_conf.setValue("—")
        self._clear_crops()
        self.stack.setCurrentIndex(0)

    def refresh_theme(self) -> None:
        """Re-apply inline theme styles after a theme toggle."""
        self._apply_placeholder_style()
        self._apply_results_style()
        self._card_total.refresh_theme()
        self._card_conf.refresh_theme()

    @staticmethod
    def _cell(
        text: str,
        align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
        return item

    @staticmethod
    def _conf_color(conf: float) -> QColor:
        if conf >= 0.7:
            return QColor(COLORS["success"])
        if conf >= 0.4:
            return QColor(COLORS["warning"])
        return QColor(COLORS["error"])

    def _clear_crops(self) -> None:
        while self._crops_layout.count() > 1:
            item = self._crops_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
