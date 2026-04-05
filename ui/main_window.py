import os
import sys
import zipfile
from datetime import datetime

from PyQt6.QtCore import QCoreApplication, Qt, QTimer
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.file_utils import collect_files_from_folder, collect_files_from_paths
from core.inference import InferenceWorker
from core.model_loader import ModelLoader
from ui.panel_center import CenterPanel
from ui.panel_left import LeftPanel
from ui.panel_log import LogPanel
from ui.panel_right import RightPanel
from ui.theme import COLORS, ThemeManager, build_palette, build_stylesheet
from ui.widgets import Badge


class MainWindow(QMainWindow):
    def __init__(self, theme_mgr: ThemeManager):
        super().__init__()
        self.setWindowTitle("Text Detection")
        self.resize(1280, 820)
        self.setMinimumSize(900, 600)

        self._theme_mgr = theme_mgr
        self._model: object = None
        self._reader: object = None
        self._files: list[dict] = []
        self._results: list[dict] = []
        self._output_dir: str | None = None
        self._is_loading: bool = False

        self._model_loader: ModelLoader | None = None
        self._ocr_loader: ModelLoader | None = None
        self._worker: InferenceWorker | None = None

        self._build_ui()
        self._connect_signals()
        self._update_run_state()

        # ── auto-load model if models/best.pt is pre-filled ────────────
        if self.left.model_path and os.path.isfile(self.left.model_path):
            QTimer.singleShot(300, self._load_model)

    # ═════════════════════════════════════════════════════════════════════
    #  BUILD UI
    # ═════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())

        vsplit = QSplitter(Qt.Orientation.Vertical)
        vsplit.setHandleWidth(1)
        vsplit.addWidget(self._build_body())
        vsplit.addWidget(self._build_log_wrap())
        vsplit.setSizes([620, 130])
        vsplit.setCollapsible(0, False)
        vsplit.setCollapsible(1, False)
        root.addWidget(vsplit)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _build_topbar(self) -> QWidget:
        self._topbar = QWidget()
        self._topbar.setFixedHeight(44)

        lay = QHBoxLayout(self._topbar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)

        self._title_lbl = QLabel("YOLO · OCR")
        lay.addWidget(self._title_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        lay.addWidget(sep)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(200)
        self._progress_bar.setFixedHeight(4)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setValue(0)
        lay.addWidget(self._progress_bar)

        self._progress_lbl = QLabel("")
        lay.addWidget(self._progress_lbl)

        lay.addStretch()

        self._model_badge = Badge("idle", "Model")
        self._ocr_badge = Badge("idle", "OCR")
        lay.addWidget(self._model_badge)
        lay.addSpacing(8)
        lay.addWidget(self._ocr_badge)

        lay.addSpacing(12)

        # ── Theme toggle button ──────────────────────────────────────
        self._theme_btn = QPushButton("☀" if self._theme_mgr.is_dark else "🌙")
        self._theme_btn.setObjectName("themeToggle")
        self._theme_btn.setToolTip("Toggle light / dark theme")
        self._theme_btn.setFixedSize(32, 32)
        self._theme_btn.clicked.connect(self._toggle_theme)
        lay.addWidget(self._theme_btn)

        self._apply_topbar_style()
        return self._topbar

    def _build_body(self) -> QSplitter:
        self.left = LeftPanel()
        self.center = CenterPanel()
        self.right = RightPanel()

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setHandleWidth(1)
        body.addWidget(self.left)
        body.addWidget(self.center)
        body.addWidget(self.right)
        body.setSizes([280, 580, 380])
        body.setCollapsible(0, False)
        body.setCollapsible(1, False)
        body.setCollapsible(2, False)

        return body

    def _build_log_wrap(self) -> QWidget:
        self._log_wrap = QWidget()
        lay = QVBoxLayout(self._log_wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.log_panel = LogPanel()
        lay.addWidget(self.log_panel)

        self._apply_log_wrap_style()
        return self._log_wrap

    # ── inline theme styles ──────────────────────────────────────────────

    def _apply_topbar_style(self) -> None:
        self._topbar.setStyleSheet(
            f"background:{COLORS['surface']};"
            f"border-bottom:1px solid {COLORS['border']};"
        )
        self._title_lbl.setStyleSheet(
            f"color:{COLORS['text_primary']};"
            f"font-size:13px;font-weight:700;"
            f"letter-spacing:1px;font-family:'Consolas',monospace;"
        )
        self._progress_lbl.setStyleSheet(
            f"color:{COLORS['text_muted']};"
            f"font-size:11px;font-family:'Consolas',monospace;"
            f"min-width:260px;"
        )

    def _apply_log_wrap_style(self) -> None:
        self._log_wrap.setStyleSheet(
            f"background:{COLORS['surface']};border-top:1px solid {COLORS['border']};"
        )

    # ═════════════════════════════════════════════════════════════════════
    #  SIGNALS
    # ═════════════════════════════════════════════════════════════════════

    def _connect_signals(self) -> None:
        L = self.left
        L.loadModelClicked.connect(self._load_model)
        L.loadOCRClicked.connect(self._load_ocr)
        L.addFilesClicked.connect(self._add_files)
        L.addFolderClicked.connect(self._add_folder)
        L.clearFilesClicked.connect(self._clear_files)
        L.runClicked.connect(self._run)
        L.exportClicked.connect(self._export)

        self.center.fileSelected.connect(self._on_file_selected)

    # ═════════════════════════════════════════════════════════════════════
    #  LOADING STATE MANAGEMENT
    # ═════════════════════════════════════════════════════════════════════

    def _set_loading_state(self, loading: bool) -> None:
        """Toggle the global loading-state UI (cursor, progress, buttons)."""
        if loading and not self._is_loading:
            self._is_loading = True
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._progress_bar.setRange(0, 0)  # indeterminate pulse
            self.left.setInteractable(False)
        elif not loading and self._is_loading:
            self._is_loading = False
            QApplication.restoreOverrideCursor()
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(0)
            self._progress_lbl.setText("")
            self.left.setInteractable(True)

    # ═════════════════════════════════════════════════════════════════════
    #  THEME TOGGLE
    # ═════════════════════════════════════════════════════════════════════

    def _toggle_theme(self) -> None:
        """Swap dark ↔ light and refresh every themed surface."""
        self._theme_mgr.toggle()
        app = QApplication.instance()
        self._theme_mgr.apply(app)

        # Update toggle icon
        self._theme_btn.setText("☀" if self._theme_mgr.is_dark else "🌙")

        # Cascade refresh to all inline-styled widgets
        self._apply_topbar_style()
        self._apply_log_wrap_style()
        self._model_badge.refresh_theme()
        self._ocr_badge.refresh_theme()

        self.left.refresh_theme()
        self.center.refresh_theme()
        self.right.refresh_theme()
        self.log_panel.refresh_theme()

    # ═════════════════════════════════════════════════════════════════════
    #  STATE HELPERS
    # ═════════════════════════════════════════════════════════════════════

    def _update_run_state(self) -> None:
        ready = bool(self._model and self._reader and self._files)
        self.left.setRunnable(ready)

        if ready:
            self.left.setRunHint("")
            return

        missing = []
        if not self._model:
            missing.append("① Load Model")
        if not self._reader:
            missing.append("② Load OCR")
        if not self._files:
            missing.append("③ Add files")
        self.left.setRunHint("  ·  ".join(missing))

    def _post_status(self, msg: str) -> None:
        self._status_bar.showMessage(msg)
        self.log_panel.append(msg)

    def _refresh_file_list(self) -> None:
        self.left.setFileCount(len(self._files))
        self.center.setFiles(self._files)
        self._update_run_state()

    # ═════════════════════════════════════════════════════════════════════
    #  MODEL / OCR LOADING
    # ═════════════════════════════════════════════════════════════════════

    def _load_model(self) -> None:
        path = self.left.model_path
        if not path or not os.path.isfile(path):
            QMessageBox.warning(
                self,
                "Model not found",
                f"File not found:\n{path or '(empty)'}",
            )
            return

        self._set_loading_state(True)
        self.left.model_badge.setState("busy", "Loading…")
        self._model_badge.setState("busy", "Model")
        self._progress_lbl.setText("⏳ Loading YOLO model…")
        self._post_status(f"Loading YOLO model — {os.path.basename(path)} …")

        self._model_loader = ModelLoader("yolo", model_path=path)
        self._model_loader.done.connect(self._on_loader_done)
        self._model_loader.error.connect(self._on_load_error)
        self._model_loader.start()

    def _load_ocr(self) -> None:
        self._set_loading_state(True)
        self.left.ocr_badge.setState("busy", "Loading…")
        self._ocr_badge.setState("busy", "OCR")
        self._progress_lbl.setText("⏳ Loading EasyOCR engine…")
        self._post_status("Loading EasyOCR reader …")

        self._ocr_loader = ModelLoader(
            "ocr",
            languages=self.left.languages,
            use_gpu=self.left.use_gpu,
        )
        self._ocr_loader.done.connect(self._on_loader_done)
        self._ocr_loader.error.connect(self._on_load_error)
        self._ocr_loader.start()

    def _on_loader_done(self, obj: object, kind: str) -> None:
        if kind == "yolo":
            self._model = obj
            self.left.model_badge.setState("ok", "Ready")
            self._model_badge.setState("ok", "Model")
            self._post_status("YOLO model loaded successfully.")

            # ── Auto-load OCR after model (requirement #4) ────────────
            if self._reader is None:
                self._load_ocr()  # stays in loading state
            else:
                self._set_loading_state(False)

        elif kind == "ocr":
            self._reader = obj
            self.left.ocr_badge.setState("ok", "Ready")
            self._ocr_badge.setState("ok", "OCR")
            self._post_status("EasyOCR reader loaded successfully.")
            self._set_loading_state(False)

        self._update_run_state()

    def _on_load_error(self, msg: str) -> None:
        self.left.model_badge.setState("error", "Error")
        self.left.ocr_badge.setState("error", "Error")
        self._model_badge.setState("error", "Model")
        self._ocr_badge.setState("error", "OCR")
        self._set_loading_state(False)
        self._post_status(f"Error: {msg}")
        QMessageBox.critical(self, "Load Error", msg)

    # ═════════════════════════════════════════════════════════════════════
    #  FILE MANAGEMENT
    # ═════════════════════════════════════════════════════════════════════

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select images",
            "",
            "Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.dcm)",
        )
        if not paths:
            return

        new_entries = collect_files_from_paths(paths)
        existing = {f["path"] for f in self._files if f.get("type") == "path"}
        added = [e for e in new_entries if e["path"] not in existing]

        self._files.extend(added)
        self._refresh_file_list()
        if added:
            self._post_status(f"Added {len(added)} file(s) to queue.")

    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select folder")
        if not folder:
            return

        new_entries = collect_files_from_folder(folder)
        existing = {f["path"] for f in self._files if f.get("type") == "path"}
        added = [e for e in new_entries if e["path"] not in existing]

        self._files.extend(added)
        self._refresh_file_list()
        self._post_status(
            f"Added {len(added)} file(s) from {os.path.basename(folder)}/"
        )

    def _clear_files(self) -> None:
        self._files.clear()
        self._results.clear()
        self.center.clearResults()
        self._refresh_file_list()
        self.right.clear()
        self.left.setExportable(False)
        self._post_status("File queue cleared.")

    def _on_file_selected(self, file_dict: dict) -> None:
        name = file_dict.get("name", "")
        for r in self._results:
            if r.get("filename") == name:
                self.right.showResult(r)
                return
        self.right.clear()

    # ═════════════════════════════════════════════════════════════════════
    #  INFERENCE
    # ═════════════════════════════════════════════════════════════════════

    def _run(self) -> None:
        if self._worker and self._worker.isRunning():
            return

        self.left.btn_run.setEnabled(False)
        self.left.setExportable(False)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_lbl.setText("")
        self._results = []
        self.right.clear()
        self._post_status("Starting detection …")

        self._worker = InferenceWorker(
            model=self._model,
            reader=self._reader,
            files=self._files,
            conf=self.left.conf,
            save_crops=self.left.save_crops,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.result.connect(self._on_result)
        self._worker.error.connect(self._on_inference_error)
        self._worker.log.connect(self.log_panel.append)
        self._worker.start()

    def _on_progress(self, pct: int, label: str) -> None:
        self._progress_bar.setValue(pct)
        self._progress_lbl.setText(label)

    def _on_result(self, results: list, output_dir: str) -> None:
        self._results = results
        self._output_dir = output_dir

        self._progress_bar.setValue(100)
        self._progress_lbl.setText("Done")

        self.left.btn_run.setEnabled(True)
        self.left.setExportable(True)

        for r in results:
            self.center.markProcessed(r["filename"], r)

        if results:
            self.right.showResult(results[0])

        self._post_status(f"Detection complete — {len(results)} image(s) processed.")
        self._update_run_state()

    def _on_inference_error(self, msg: str) -> None:
        self.left.btn_run.setEnabled(True)
        self._post_status(f"Error: {msg}")
        QMessageBox.critical(self, "Inference Error", msg)
        self._update_run_state()

    # ═════════════════════════════════════════════════════════════════════
    #  EXPORT
    # ═════════════════════════════════════════════════════════════════════

    def _export(self) -> None:
        if not self._output_dir or not os.path.isdir(self._output_dir):
            QMessageBox.warning(self, "Nothing to export", "No output directory found.")
            return

        default_name = f"detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export results",
            default_name,
            "ZIP archive (*.zip)",
        )
        if not save_path:
            return

        try:
            with zipfile.ZipFile(save_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for dirpath, _dirs, filenames in os.walk(self._output_dir):
                    for fname in filenames:
                        abs_path = os.path.join(dirpath, fname)
                        arc_name = os.path.relpath(abs_path, self._output_dir)
                        zf.write(abs_path, arc_name)
            self._post_status(f"Exported → {save_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))


# ═════════════════════════════════════════════════════════════════════════════
#  DPI SETUP
# ═════════════════════════════════════════════════════════════════════════════


def _setup_dpi() -> None:
    """Configure High-DPI scaling before QApplication is created."""
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")


# ═════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════


def launch() -> None:
    """Create the QApplication, apply theme, show the window, and run."""
    _setup_dpi()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set org/app name for QSettings persistence
    QCoreApplication.setOrganizationName("YOLOxOCR")
    QCoreApplication.setApplicationName("DetectionSuite")

    # ThemeManager reads QSettings and swaps COLORS in-place
    theme_mgr = ThemeManager()
    theme_mgr.apply(app)

    win = MainWindow(theme_mgr)
    win.show()
    sys.exit(app.exec())
