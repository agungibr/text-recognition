"""
INAK / ESAK Calculation Panel

A dedicated tab panel for computing:
    y    = a × kVp^b          (Dose Output, mGy)
    INAK = y × (mAs / 1000)   (Incident Air Kerma, mGy)
    ESAK = INAK × BSF         (Entrance Surface Air Kerma, mGy)

Supports two modes:
    1. Auto-fill from DICOM metadata (kVp, mA, exposure time)
    2. Manual entry when DICOM tags are not available

Also provides a calibration sub-panel for fitting custom
power regression coefficients from measured data.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QAbstractItemView,
)

from ui.theme import COLORS


def _header(text: str) -> QLabel:
    """Create a styled section header."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: 700;"
        f" padding: 2px 0; background: transparent;"
    )
    return lbl


def _sub_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color: {COLORS['text_muted']}; font-size: 10px;"
        f" background: transparent;"
    )
    return lbl


def _result_value(initial: str = "—") -> QLabel:
    lbl = QLabel(initial)
    lbl.setStyleSheet(
        f"color: {COLORS['text_primary']}; font-size: 22px; font-weight: 700;"
        f' font-family: "Consolas", "SF Mono", monospace; background: transparent;'
    )
    return lbl


def _result_card() -> QFrame:
    card = QFrame()
    card.setStyleSheet(f"""
        QFrame {{
            background: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
        }}
    """)
    return card


class INAKESAKPanel(QWidget):
    """Panel for INAK/ESAK dose calculations with DICOM auto-fill."""

    # Emitted when calculate is pressed: (kvp, ma, exposure_time_s, bsf, coeff_a, coeff_b)
    calculateRequested = Signal(float, float, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self._build_ui()

    # -----------------------------------------------------------------
    #  UI construction
    # -----------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        content = QWidget()
        content.setStyleSheet(f"background: {COLORS['bg']};")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # ── Section 1: Input Parameters ──
        layout.addWidget(self._build_input_section())

        # ── Section 2: Calibration Coefficients ──
        layout.addWidget(self._build_coefficients_section())

        # ── Calculate button ──
        self._btn_calculate = QPushButton("  ⚡  Hitung  y / INAK / ESAK  ")
        self._btn_calculate.setObjectName("primary")
        self._btn_calculate.setFixedHeight(38)
        self._btn_calculate.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_calculate.clicked.connect(self._on_calculate)
        layout.addWidget(self._btn_calculate)

        # ── Section 3: Results ──
        layout.addWidget(self._build_results_section())

        # ── Section 4: Calibration table ──
        layout.addWidget(self._build_calibration_section())

        layout.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # -- input fields -------------------------------------------------------
    def _build_input_section(self) -> QFrame:
        card = _result_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        lay.addWidget(_header("Parameter Eksposur"))
        lay.addWidget(_sub_label("Otomatis dari DICOM atau isi manual"))

        # kVp
        row_kvp = QHBoxLayout()
        lbl = QLabel("kVp")
        lbl.setFixedWidth(90)
        lbl.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_kvp = QDoubleSpinBox()
        self._spin_kvp.setRange(20.0, 200.0)
        self._spin_kvp.setDecimals(1)
        self._spin_kvp.setValue(80.0)
        self._spin_kvp.setSuffix(" kV")
        self._spin_kvp.setToolTip("DICOM tag (0018,0060)")
        self._apply_spin_style(self._spin_kvp)
        self._kvp_source = QLabel("")
        self._kvp_source.setStyleSheet(f"color: {COLORS['success']}; font-size: 9px; background: transparent;")
        row_kvp.addWidget(lbl)
        row_kvp.addWidget(self._spin_kvp, 1)
        row_kvp.addWidget(self._kvp_source)
        lay.addLayout(row_kvp)

        # mA
        row_ma = QHBoxLayout()
        lbl2 = QLabel("mA")
        lbl2.setFixedWidth(90)
        lbl2.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_ma = QDoubleSpinBox()
        self._spin_ma.setRange(0.1, 2000.0)
        self._spin_ma.setDecimals(2)
        self._spin_ma.setValue(200.0)
        self._spin_ma.setSuffix(" mA")
        self._spin_ma.setToolTip("DICOM tag (0018,1151)")
        self._apply_spin_style(self._spin_ma)
        self._ma_source = QLabel("")
        self._ma_source.setStyleSheet(f"color: {COLORS['success']}; font-size: 9px; background: transparent;")
        row_ma.addWidget(lbl2)
        row_ma.addWidget(self._spin_ma, 1)
        row_ma.addWidget(self._ma_source)
        lay.addLayout(row_ma)

        # Exposure time (s)
        row_t = QHBoxLayout()
        lbl3 = QLabel("Waktu (s)")
        lbl3.setFixedWidth(90)
        lbl3.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_time = QDoubleSpinBox()
        self._spin_time.setRange(0.001, 60.0)
        self._spin_time.setDecimals(4)
        self._spin_time.setValue(0.1)
        self._spin_time.setSuffix(" s")
        self._spin_time.setToolTip("DICOM tag (0018,1150) / 1000")
        self._apply_spin_style(self._spin_time)
        self._time_source = QLabel("")
        self._time_source.setStyleSheet(f"color: {COLORS['success']}; font-size: 9px; background: transparent;")
        row_t.addWidget(lbl3)
        row_t.addWidget(self._spin_time, 1)
        row_t.addWidget(self._time_source)
        lay.addLayout(row_t)

        # BSF
        row_bsf = QHBoxLayout()
        lbl4 = QLabel("BSF")
        lbl4.setFixedWidth(90)
        lbl4.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_bsf = QDoubleSpinBox()
        self._spin_bsf.setRange(1.0, 2.0)
        self._spin_bsf.setDecimals(2)
        self._spin_bsf.setValue(1.35)
        self._spin_bsf.setToolTip("Backscatter Factor (default 1.35)")
        self._apply_spin_style(self._spin_bsf)
        row_bsf.addWidget(lbl4)
        row_bsf.addWidget(self._spin_bsf, 1)
        lay.addLayout(row_bsf)

        return card

    # -- coefficients -------------------------------------------------------
    def _build_coefficients_section(self) -> QFrame:
        card = _result_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        lay.addWidget(_header("Koefisien Regresi Power"))
        lay.addWidget(_sub_label("y = a × kVp^b"))

        row_a = QHBoxLayout()
        lbl_a = QLabel("a (koefisien)")
        lbl_a.setFixedWidth(90)
        lbl_a.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_a = QDoubleSpinBox()
        self._spin_a.setRange(0.000001, 10.0)
        self._spin_a.setDecimals(6)
        self._spin_a.setValue(0.0004)
        self._apply_spin_style(self._spin_a)
        row_a.addWidget(lbl_a)
        row_a.addWidget(self._spin_a, 1)
        lay.addLayout(row_a)

        row_b = QHBoxLayout()
        lbl_b = QLabel("b (eksponen)")
        lbl_b.setFixedWidth(90)
        lbl_b.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._spin_b = QDoubleSpinBox()
        self._spin_b.setRange(0.01, 10.0)
        self._spin_b.setDecimals(4)
        self._spin_b.setValue(2.5917)
        self._apply_spin_style(self._spin_b)
        row_b.addWidget(lbl_b)
        row_b.addWidget(self._spin_b, 1)
        lay.addLayout(row_b)

        # Reset button
        btn_reset = QPushButton("Reset Default")
        btn_reset.setObjectName("secondary")
        btn_reset.setFixedHeight(26)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self._reset_coefficients)
        lay.addWidget(btn_reset)

        return card

    # -- results display ----------------------------------------------------
    def _build_results_section(self) -> QFrame:
        card = _result_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        lay.addWidget(_header("Hasil Perhitungan"))

        # mAs row
        row_mas = QHBoxLayout()
        lbl_mas = QLabel("mAs")
        lbl_mas.setFixedWidth(50)
        lbl_mas.setStyleSheet(f"color: {COLORS['text_label']}; font-size: 11px; font-weight: 600; background: transparent;")
        self._result_mas = QLabel("—")
        self._result_mas.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 13px;"
            f' font-family: "Consolas", monospace; background: transparent;'
        )
        row_mas.addWidget(lbl_mas)
        row_mas.addWidget(self._result_mas, 1)
        lay.addLayout(row_mas)

        # Separator
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {COLORS['border']};")
        lay.addWidget(sep1)

        # y (dose output)
        lay.addWidget(_sub_label("Dosis Output (y)"))
        self._result_y = _result_value()
        lay.addWidget(self._result_y)

        # Separator
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {COLORS['border']};")
        lay.addWidget(sep2)

        # INAK
        lay.addWidget(_sub_label("INAK (Incident Air Kerma)"))
        self._result_inak = _result_value()
        lay.addWidget(self._result_inak)

        # Separator
        sep3 = QFrame()
        sep3.setFixedHeight(1)
        sep3.setStyleSheet(f"background: {COLORS['border']};")
        lay.addWidget(sep3)

        # ESAK
        lay.addWidget(_sub_label("ESAK (Entrance Surface Air Kerma)"))
        self._result_esak = _result_value()
        self._result_esak.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 24px; font-weight: 700;"
            f' font-family: "Consolas", monospace; background: transparent;'
        )
        lay.addWidget(self._result_esak)

        # Formula display
        self._formula_lbl = QLabel("")
        self._formula_lbl.setWordWrap(True)
        self._formula_lbl.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 10px;"
            f" padding: 6px 0 0 0; background: transparent;"
        )
        lay.addWidget(self._formula_lbl)

        return card

    # -- calibration data table ---------------------------------------------
    def _build_calibration_section(self) -> QFrame:
        card = _result_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        lay.addWidget(_header("Data Kalibrasi (Opsional)"))
        lay.addWidget(_sub_label("Masukkan pasangan kVp — mGy untuk regresi ulang"))

        # Table for calibration points
        self._cal_table = QTableWidget()
        self._cal_table.setColumnCount(2)
        self._cal_table.setHorizontalHeaderLabels(["kVp", "mGy"])
        self._cal_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._cal_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._cal_table.setMinimumHeight(150)
        self._cal_table.setMaximumHeight(220)
        self._cal_table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS['surface2']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 4px;
                color: {COLORS['text_primary']};
            }}
            QHeaderView::section {{
                background: {COLORS['surface3']};
                color: {COLORS['text_primary']};
                padding: 4px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                font-weight: bold;
                font-size: 10px;
            }}
        """)
        lay.addWidget(self._cal_table)

        # Default calibration data
        default_data = [
            (50, 0.19), (60, 0.33), (70, 0.50),
            (80, 0.69), (90, 0.91), (100, 1.16),
        ]
        self._cal_table.setRowCount(len(default_data))
        for i, (kvp, mgy) in enumerate(default_data):
            self._cal_table.setItem(i, 0, QTableWidgetItem(str(kvp)))
            self._cal_table.setItem(i, 1, QTableWidgetItem(str(mgy)))

        # Buttons
        btn_row = QHBoxLayout()

        btn_add = QPushButton("+ Baris")
        btn_add.setObjectName("secondary")
        btn_add.setFixedHeight(26)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._add_calibration_row)
        btn_row.addWidget(btn_add)

        btn_del = QPushButton("- Baris")
        btn_del.setObjectName("secondary")
        btn_del.setFixedHeight(26)
        btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_del.clicked.connect(self._remove_calibration_row)
        btn_row.addWidget(btn_del)

        self._btn_fit = QPushButton("Fit Regresi")
        self._btn_fit.setObjectName("primary")
        self._btn_fit.setFixedHeight(26)
        self._btn_fit.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_fit.clicked.connect(self._on_fit_regression)
        btn_row.addWidget(self._btn_fit)

        lay.addLayout(btn_row)

        # R² result
        self._r2_label = QLabel("")
        self._r2_label.setStyleSheet(
            f"color: {COLORS['success']}; font-size: 11px;"
            f" font-weight: 600; background: transparent;"
        )
        lay.addWidget(self._r2_label)

        return card

    # -----------------------------------------------------------------
    #  Style helper
    # -----------------------------------------------------------------
    def _apply_spin_style(self, spin):
        spin.setStyleSheet(f"""
            QDoubleSpinBox, QSpinBox {{
                background: {COLORS['surface2']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QDoubleSpinBox:focus, QSpinBox:focus {{
                border-color: {COLORS['accent']};
            }}
        """)

    # -----------------------------------------------------------------
    #  Public API — auto-fill from DICOM
    # -----------------------------------------------------------------
    def set_dicom_params(self, params: dict):
        """
        Auto-fill input fields from DICOM exposure parameters.

        Args:
            params: dict with keys kvp, ma, exposure_time_s, mas
        """
        if params.get("kvp") is not None:
            self._spin_kvp.setValue(float(params["kvp"]))
            self._kvp_source.setText("DICOM")
        else:
            self._kvp_source.setText("Manual")

        if params.get("ma") is not None:
            self._spin_ma.setValue(float(params["ma"]))
            self._ma_source.setText("DICOM")
        else:
            self._ma_source.setText("Manual")

        if params.get("exposure_time_s") is not None:
            self._spin_time.setValue(float(params["exposure_time_s"]))
            self._time_source.setText("DICOM")
        elif params.get("mas") is not None and params.get("ma") is not None:
            # Derive time from mAs and mA
            ma = float(params["ma"])
            if ma > 0:
                t = float(params["mas"]) / ma
                self._spin_time.setValue(t)
                self._time_source.setText("DICOM (mAs/mA)")
        else:
            self._time_source.setText("Manual")

    def set_result(self, result):
        """
        Display INAKESAKResult on the panel.
        """
        self._result_mas.setText(f"{result.mas:.4f} mAs")
        self._result_y.setText(f"{result.y_mgy:.4f} mGy")
        self._result_inak.setText(f"{result.inak_mgy:.6f} mGy")
        self._result_esak.setText(f"{result.esak_mgy:.6f} mGy")

        self._formula_lbl.setText(
            f"y = {result.coeff_a} × {result.kvp:.1f}^{result.coeff_b}\n"
            f"INAK = {result.y_mgy:.4f} × ({result.mas:.4f}/1000)\n"
            f"ESAK = {result.inak_mgy:.6f} × {result.bsf}"
        )

    def clear_results(self):
        """Reset all result labels."""
        self._result_mas.setText("—")
        self._result_y.setText("—")
        self._result_inak.setText("—")
        self._result_esak.setText("—")
        self._formula_lbl.setText("")

    # -----------------------------------------------------------------
    #  Slots
    # -----------------------------------------------------------------
    def _on_calculate(self):
        kvp = self._spin_kvp.value()
        ma = self._spin_ma.value()
        t = self._spin_time.value()
        bsf = self._spin_bsf.value()
        a = self._spin_a.value()
        b = self._spin_b.value()
        self.calculateRequested.emit(kvp, ma, t, bsf, a, b)

    def _reset_coefficients(self):
        self._spin_a.setValue(0.0004)
        self._spin_b.setValue(2.5917)
        self._r2_label.setText("")

    def _add_calibration_row(self):
        row = self._cal_table.rowCount()
        self._cal_table.insertRow(row)
        self._cal_table.setItem(row, 0, QTableWidgetItem(""))
        self._cal_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_calibration_row(self):
        rows = self._cal_table.selectionModel().selectedRows()
        if rows:
            for idx in sorted(rows, reverse=True):
                self._cal_table.removeRow(idx.row())
        elif self._cal_table.rowCount() > 0:
            self._cal_table.removeRow(self._cal_table.rowCount() - 1)

    def _on_fit_regression(self):
        """Collect table data and run power regression."""
        from core.inak_esak_calculator import (
            CalibrationPoint,
            INAKESAKCalculator,
        )

        points = []
        for row in range(self._cal_table.rowCount()):
            kvp_item = self._cal_table.item(row, 0)
            mgy_item = self._cal_table.item(row, 1)
            if kvp_item and mgy_item:
                try:
                    kvp = float(kvp_item.text().replace(",", "."))
                    mgy = float(mgy_item.text().replace(",", "."))
                    if kvp > 0 and mgy > 0:
                        points.append(CalibrationPoint(kvp=kvp, mgy=mgy))
                except ValueError:
                    continue

        if len(points) < 2:
            QMessageBox.warning(
                self,
                "Data Kurang",
                "Minimal 2 titik kalibrasi valid diperlukan untuk regresi.",
            )
            return

        try:
            result = INAKESAKCalculator.fit_power_regression(points)
            self._spin_a.setValue(result.a)
            self._spin_b.setValue(result.b)
            self._r2_label.setText(
                f"R² = {result.r_squared:.6f}  ({result.points_used} titik)"
            )
            if result.r_squared < 0.95:
                self._r2_label.setStyleSheet(
                    f"color: {COLORS['warning']}; font-size: 11px;"
                    f" font-weight: 600; background: transparent;"
                )
            else:
                self._r2_label.setStyleSheet(
                    f"color: {COLORS['success']}; font-size: 11px;"
                    f" font-weight: 600; background: transparent;"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error Regresi", str(e))
