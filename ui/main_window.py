import os
import re

from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QMenu,
    QToolBar,
    QStyle,
    QDialog,
    QFrame,
)
from PySide6.QtGui import QIcon, QAction, QFont

from core.data_matcher import DataMatcher
from core.dicom_handler import DicomHandler
from core.dose_calculator import DoseCalculator
from core.inak_esak_calculator import INAKESAKCalculator
from services.database_service import DatabaseService
from ui.panels.center_panel import CenterPanel
from ui.panels.left_panel import LeftPanel
from ui.panels.right_panel import RightPanel
from ui.theme import COLORS, ThemeManager


class LoadingSplashScreen(QDialog):
    """Professional loading screen while models are initializing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 200)
        
        # Center on parent
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.left() + (parent_rect.width() - 400) // 2
            y = parent_rect.top() + (parent_rect.height() - 200) // 2
            self.move(x, y)
        
        # Main content widget with background
        main_frame = QFrame()
        main_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(main_frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Initializing OCR Engine")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)
        
        # Message
        self.message = QLabel("Loading machine learning models...")
        self.message.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.message.setWordWrap(True)
        layout.addWidget(self.message)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                background: {COLORS['surface2']};
                height: 8px;
            }}
            QProgressBar::chunk {{
                background: {COLORS['accent']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self.progress)
        
        # Detail label
        self.detail = QLabel("Downloading and initializing...")
        self.detail.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
        layout.addWidget(self.detail)
        
        layout.addStretch()
        
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(main_frame)
        
    def set_message(self, text):
        self.message.setText(text)
        
    def set_detail(self, text):
        self.detail.setText(text)
        
    def set_progress(self, value):
        self.progress.setValue(min(100, max(0, value)))


class ModelLoaderThread(QThread):
    """Background thread for loading AI models."""

    progress = Signal(str, int)
    loaded = Signal(object, str)
    error = Signal(str)

    def __init__(self, model_type, model_path=None, languages=None, parent=None):
        super().__init__(parent)
        self.model_type = model_type
        self.model_path = model_path
        self.languages = languages or ["en", "id"]

    def run(self):
        try:
            if self.model_type == "yolo":
                self.progress.emit("Loading YOLO model...", 0)
                from ultralytics import YOLO

                model = YOLO(self.model_path)
                self.progress.emit("YOLO model ready", 100)
                self.loaded.emit(model, "yolo")
            elif self.model_type == "ocr":
                self.progress.emit("Loading OCR engine...", 0)
                import easyocr

                reader = easyocr.Reader(self.languages, gpu=False)
                self.progress.emit("OCR engine ready", 100)
                self.loaded.emit(reader, "ocr")
        except Exception as e:
            self.error.emit(str(e))


class InferenceThread(QThread):
    """Background thread for EasyOCR inference."""

    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str)

    def __init__(self, ocr_reader, image_path, conf=0.1, parent=None):
        super().__init__(parent)
        self.ocr_reader = ocr_reader
        self.image_path = image_path
        self.conf = conf

    def run(self):
        try:
            import cv2
            import numpy as np

            self.progress.emit(10, "Loading image...")
            image = DicomHandler.load_image(self.image_path, include_overlay=True)
            if image is None:
                raise ValueError(f"Failed to load image: {self.image_path}")

            # Patient identity comes from DICOM metadata, not OCR.
            patient_info = DicomHandler.get_patient_info(self.image_path)
            self.progress.emit(20, "Reading DICOM metadata...")

            # Use easyocr for text detection and recognition
            self.progress.emit(30, "Running text detection and recognition...")
            
            # Convert BGR to RGB for easyocr
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Use easyocr with detail=1 to get bounding boxes
            ocr_results = self.ocr_reader.readtext(image_rgb, detail=1)
            
            detections = []
            if ocr_results:
                for i, result in enumerate(ocr_results):
                    # result format: (bbox, text, confidence)
                    bbox = result[0]  # List of 4 corner points
                    text = result[1]
                    conf = result[2]
                    
                    # Convert corner points to xyxy format
                    bbox_array = np.array(bbox, dtype=np.float32)
                    x_coords = bbox_array[:, 0]
                    y_coords = bbox_array[:, 1]
                    x1, y1 = int(np.min(x_coords)), int(np.min(y_coords))
                    x2, y2 = int(np.max(x_coords)), int(np.max(y_coords))
                    
                    detections.append({
                        "id": i,
                        "xyxy": [x1, y1, x2, y2],
                        "xywh": [x1, y1, x2 - x1, y2 - y1],
                        "conf": float(conf),
                        "text": text,
                    })
            
            self.progress.emit(60, f"Found {len(detections)} text regions")

            combined_text = " ".join(d["text"] for d in detections if d.get("text"))
            self.progress.emit(100, "Complete")

            class Result:
                pass

            result_obj = Result()
            result_obj.image_path = self.image_path
            result_obj.image = image
            result_obj.detections = detections
            result_obj.combined_text = combined_text
            result_obj.patient_info = patient_info
            self.result.emit(result_obj)

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window for Radiology Reader."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radiology Reader")
        self.resize(1500, 940)
        self.setMinimumSize(1180, 760)

        self._yolo_model = None
        self._ocr_reader = None
        self._ocr_loaded = False
        self._current_image_path = None
        self._current_result = None
        self._patient_csv_data = []
        self._data_matcher = DataMatcher()
        self._database_service = DatabaseService()
        self._inak_calculator = INAKESAKCalculator()
        self._theme_mgr = ThemeManager()
        self._splash_screen = None
        self._ocr_loader = None

        self._build_ui()
        self._connect_signals()
        self._apply_styles()
        self.statusBar().showMessage("Ready")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Create menu bar
        self._create_menubar()

        # Create toolbar
        self._create_toolbar()

        # Main content area with panels
        root.addWidget(self._create_content_area(), 1)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setFixedHeight(28)
        self.setStatusBar(self._status_bar)
        
        # Add progress bar to status bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(140)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._status_bar.addWidget(self._progress_bar)
        
        self._footer_label = QLabel("Size: — | Zoom: 100%")
        self._footer_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px; padding-right: 6px;"
        )
        self._status_bar.addPermanentWidget(self._footer_label)

    def _create_menubar(self):
        """Create professional menu bar matching the wireframe."""
        menubar = self.menuBar()
        menubar.setStyleSheet(
            f"""
            QMenuBar {{
                background: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 0px;
                margin: 0px;
            }}
            QMenuBar::item:selected {{
                background: {COLORS['surface2']};
            }}
            QMenu {{
                background: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background: {COLORS['accent_bg']};
            }}
            """
        )

        # File Menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open Image").triggered.connect(self._on_open_image)
        file_menu.addAction("Open Patient Data").triggered.connect(self._on_open_patient_data)
        file_menu.addSeparator()
        file_menu.addAction("Exit").triggered.connect(self.close)

        # Local Database Menu
        db_menu = menubar.addMenu("Local Database")
        db_menu.addAction("Import Data")
        db_menu.addAction("Export Data")

        # View Menu
        view_menu = menubar.addMenu("View")
        view_menu.addAction("Zoom In")
        view_menu.addAction("Zoom Out")
        view_menu.addAction("Fit to Window")

        # Image Menu
        image_menu = menubar.addMenu("Image")
        image_menu.addAction("Scan Embedded Text").triggered.connect(self._on_scan_text)
        image_menu.addAction("Save Results").triggered.connect(self._on_save_results)

        # Options Menu
        options_menu = menubar.addMenu("Options")
        options_menu.addAction("Preferences")
        options_menu.addAction("Settings")

        # Help Menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("About").triggered.connect(lambda: QMessageBox.about(
            self, "About", "Radiology Reader v1.0\n\nAdvanced DICOM Viewer with OCR"
        ))

    def _create_toolbar(self):
        """Create toolbar with navigation and action icons only."""
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.setStyleSheet(
            f"""
            QToolBar {{
                background: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 4px 8px;
                spacing: 2px;
            }}
            QToolButton {{
                color: {COLORS['text_primary']};
                background: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 4px;
                margin: 0px;
                width: 28px;
                height: 28px;
            }}
            QToolButton:hover {{
                background: {COLORS['surface2']};
                border: 1px solid {COLORS['border']};
            }}
            QToolButton:pressed {{
                background: {COLORS['accent_bg']};
            }}
            """
        )

        # File operations
        open_action = toolbar.addAction("📁")  # Folder icon
        open_action.setToolTip("Open File")
        open_action.triggered.connect(self._on_open_image)
        
        self._toolbar_save_action = toolbar.addAction("💾")  # Save icon
        self._toolbar_save_action.setToolTip("Save Results")
        self._toolbar_save_action.setEnabled(False)
        self._toolbar_save_action.triggered.connect(self._on_save_results)
        
        toolbar.addSeparator()

        # Navigation controls
        prev_action = toolbar.addAction("⬅")  # Left arrow
        prev_action.setToolTip("Previous Image")
        prev_action.triggered.connect(lambda: None)
        
        next_action = toolbar.addAction("➡")  # Right arrow
        next_action.setToolTip("Next Image")
        next_action.triggered.connect(lambda: None)
        
        toolbar.addSeparator()

        # OCR/Scan
        self._toolbar_ocr_action = toolbar.addAction("▶️")  # Play button for OCR
        self._toolbar_ocr_action.setToolTip("Run OCR Scan")
        self._toolbar_ocr_action.setEnabled(False)
        self._toolbar_ocr_action.triggered.connect(self._on_scan_text)
        
        toolbar.addSeparator()

        # View controls
        zoom_in_action = toolbar.addAction("🔎")  # Magnifying glass with plus
        zoom_in_action.setToolTip("Zoom In")
        zoom_in_action.triggered.connect(lambda: None)
        
        zoom_out_action = toolbar.addAction("🔍")  # Magnifying glass
        zoom_out_action.setToolTip("Zoom Out")
        zoom_out_action.triggered.connect(lambda: None)
        
        toolbar.addSeparator()

        # Help
        help_action = toolbar.addAction("❓")  # Question mark
        help_action.setToolTip("Help")
        help_action.triggered.connect(self._on_help)

    def _create_topbar(self) -> QWidget:
        topbar = QWidget()
        topbar.setObjectName("topbar")
        layout = QHBoxLayout(topbar)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        brand = QLabel("Radiology Reader")
        brand.setObjectName("topbarTitle")
        layout.addWidget(brand)

        subtitle = QLabel("Clinical Imaging Workflow")
        subtitle.setObjectName("topbarSubtitle")
        layout.addWidget(subtitle)
        layout.addSpacing(16)

        self._btn_open_image = QPushButton("Open Image")
        self._btn_open_image.setFixedHeight(30)
        self._btn_open_image.clicked.connect(self._on_open_image)
        layout.addWidget(self._btn_open_image)

        self._btn_patient_data = QPushButton("Open Patient Data")
        self._btn_patient_data.setFixedHeight(30)
        self._btn_patient_data.clicked.connect(self._on_open_patient_data)
        layout.addWidget(self._btn_patient_data)

        self._btn_scan_text = QPushButton("Scan Embedded Text")
        self._btn_scan_text.setObjectName("primary")
        self._btn_scan_text.setFixedHeight(30)
        self._btn_scan_text.setEnabled(False)
        self._btn_scan_text.clicked.connect(self._on_scan_text)
        layout.addWidget(self._btn_scan_text)

        self._btn_save_results = QPushButton("Save Results")
        self._btn_save_results.setFixedHeight(30)
        self._btn_save_results.setEnabled(False)
        self._btn_save_results.clicked.connect(self._on_save_results)
        layout.addWidget(self._btn_save_results)

        self._btn_help = QPushButton("Help")
        self._btn_help.setObjectName("secondary")
        self._btn_help.setFixedHeight(30)
        self._btn_help.clicked.connect(self._on_help)
        layout.addWidget(self._btn_help)

        layout.addSpacing(12)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(140)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(spacer)

        layout.addWidget(self._create_logos())
        return topbar

    def _create_logo_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setFixedSize(56, 28)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"""
            background: {COLORS['surface2']};
            color: {COLORS['text_secondary']};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
            font-size: 9px;
            font-weight: 600;
            """
        )
        return label

    def _create_logos(self) -> QWidget:
        logos = QWidget()
        logos_layout = QHBoxLayout(logos)
        logos_layout.setContentsMargins(0, 0, 0, 0)
        logos_layout.setSpacing(6)
        logos_layout.addWidget(self._create_logo_label("LOGO 1"))
        logos_layout.addWidget(self._create_logo_label("LOGO 2"))
        return logos

    def _create_content_area(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)

        self._left_panel = LeftPanel()
        self._center_panel = CenterPanel()
        self._right_panel = RightPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.addWidget(self._left_panel)
        splitter.addWidget(self._center_panel)
        splitter.addWidget(self._right_panel)
        splitter.setSizes([300, 860, 300])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)

        layout.addWidget(splitter)
        return container

    def _apply_styles(self):
        self.setStyleSheet(
            f"""
            QMainWindow {{ 
                background: {COLORS['bg']}; 
            }}
            QStatusBar {{
                background: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
                color: {COLORS['text_muted']};
            }}
            QSplitter::handle {{
                background: {COLORS['border']};
            }}
            """
        )

    def _connect_signals(self):
        self._right_panel.calculateDose.connect(self._on_calculate_dose)
        self._right_panel.calculateINAKESAK.connect(self._on_calculate_inak_esak)
        self._center_panel.zoom_changed.connect(self._on_zoom_changed)

    @Slot(str, int)
    def _on_ocr_load_progress(self, msg, val):
        """Update splash screen during OCR loading."""
        if self._splash_screen:
            self._splash_screen.set_detail(msg)
            self._splash_screen.set_progress(10 + (val * 0.9))  # Progress from 10-100
        self._status_bar.showMessage(msg)

    @Slot(str)
    def _on_model_error(self, error_msg):
        # Close splash screen on error
        if self._splash_screen:
            self._splash_screen.close()
            self._splash_screen = None
        
        self._right_panel.error(f"Model error: {error_msg}")
        self._status_bar.showMessage(f"Error: {error_msg}")
        QMessageBox.critical(self, "Model Loading Error", error_msg)

    @Slot()
    def _on_open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "All Files (*.*);;DICOM Files (*.dcm *.dicom);;Images (*.jpg *.jpeg *.png *.bmp *.tiff *.tif)",
        )
        if path:
            self._load_image(path)

    def _load_image(self, path):
        self._current_image_path = path
        self._right_panel.info(f"Loading image: {os.path.basename(path)}")
        if not self._center_panel.set_image(path):
            self._right_panel.error(f"Failed to load: {path}")
            QMessageBox.warning(self, "Load Error", f"Could not load image:\n{path}")
            return

        self._right_panel.success(f"Image loaded: {os.path.basename(path)}")
        self._status_bar.showMessage(f"Image loaded: {os.path.basename(path)}")

        patient_info = DicomHandler.get_patient_info(path)
        self._left_panel.set_from_image_data(patient_info)
        self._right_panel.set_dicom_tags(patient_info, path)
        if patient_info.get("patient_id") or patient_info.get("name"):
            self._right_panel.info("Patient data loaded from DICOM metadata")
        else:
            self._right_panel.warning("No DICOM patient metadata found")

        if self._patient_csv_data:
            self._try_match_patient(patient_info)

        # Auto-fill INAK/ESAK exposure parameters from DICOM
        exposure_params = INAKESAKCalculator.extract_exposure_params_from_path(path)
        self._right_panel._inak_panel.set_dicom_params(exposure_params)
        
        # Enable OCR scan button when image is loaded (OCR will lazy-load on first scan)
        self._toolbar_ocr_action.setEnabled(True)
        if hasattr(self._right_panel, '_btn_scan_text'):
            self._right_panel._btn_scan_text.setEnabled(True)

    @Slot()
    def _on_open_patient_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Patient Data CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self._load_patient_data(path)

    def _load_patient_data(self, path):
        try:
            import pandas as pd

            df = pd.read_csv(path)
            self._patient_csv_data = df.to_dict("records")
            self._data_matcher.load_patient_data(self._patient_csv_data)
            self._right_panel.success(
                f"Loaded {len(self._patient_csv_data)} patient records"
            )
            self._status_bar.showMessage("Patient data loaded")
            if self._current_image_path:
                patient_info = DicomHandler.get_patient_info(self._current_image_path)
                self._try_match_patient(patient_info)
        except Exception as e:
            self._right_panel.error(f"Failed to load CSV: {str(e)}")
            QMessageBox.critical(self, "Load Error", f"Could not load CSV:\n{str(e)}")

    def _try_match_patient(self, patient_info):
        if not self._patient_csv_data:
            return

        extracted = {
            "patient_id": patient_info.get("patient_id", ""),
            "name": patient_info.get("name", ""),
            "age": patient_info.get("age", ""),
            "gender": patient_info.get("gender", ""),
        }
        matched = self._data_matcher.match_patient(extracted)
        if matched:
            self._left_panel.set_matched_data(matched)
            self._right_panel.success("Patient data matched")
        else:
            self._left_panel.set_matched_data(None)
            self._right_panel.info("No matching patient data found")

    @Slot()
    def _on_scan_text(self):
        if not self._current_image_path:
            QMessageBox.warning(self, "No Image", "Please open an image first.")
            return
        
        # Load OCR on first scan if not already loaded
        if not self._ocr_reader:
            if not self._ocr_loaded:
                self._ocr_loaded = True
                self._toolbar_ocr_action.setEnabled(False)
                
                # Show splash screen
                self._splash_screen = LoadingSplashScreen(self)
                self._splash_screen.show()
                self._splash_screen.set_message("Initializing OCR Engine")
                self._splash_screen.set_detail("Downloading and setting up... (first time only)")
                self._splash_screen.set_progress(10)
                
                # Load OCR and then scan
                self._ocr_loader = ModelLoaderThread("ocr")
                self._ocr_loader.progress.connect(self._on_ocr_load_progress)
                self._ocr_loader.loaded.connect(lambda reader, _: self._on_ocr_loaded_then_scan(reader))
                self._ocr_loader.error.connect(self._on_model_error)
                self._ocr_loader.start()
            else:
                QMessageBox.warning(
                    self, "Loading OCR", "OCR engine is initializing...\nPlease wait 1-2 minutes."
                )
            return
        
        # OCR ready, proceed with scan
        self._perform_ocr_scan()

    def _on_ocr_loaded_then_scan(self, reader):
        """Called when OCR loads on-demand, then starts the scan."""
        self._ocr_reader = reader
        self._toolbar_ocr_action.setEnabled(True)
        self._right_panel.success("OCR ready! Scanning image...")
        
        # Close splash and perform scan
        if self._splash_screen:
            self._splash_screen.close()
            self._splash_screen = None
        
        # Perform the scan
        QTimer.singleShot(100, self._perform_ocr_scan)

    def _perform_ocr_scan(self):
        """Perform the actual OCR scan."""
        self._toolbar_ocr_action.setEnabled(False)
        self._toolbar_save_action.setEnabled(False)
        self._progress_bar.setValue(0)
        self._right_panel.info("Scanning image for embedded text...")

        # Create progress dialog
        self._ocr_progress = QProgressDialog(
            "Running OCR scan...", None, 0, 100, self
        )
        self._ocr_progress.setWindowModality(Qt.WindowModality.WindowModal)
        self._ocr_progress.setRange(0, 100)
        self._ocr_progress.setValue(0)
        self._ocr_progress.show()

        self._inference_thread = InferenceThread(
            self._ocr_reader, self._current_image_path, conf=0.1
        )
        self._inference_thread.progress.connect(self._on_inference_progress)
        self._inference_thread.result.connect(self._on_inference_complete)
        self._inference_thread.error.connect(self._on_inference_error)
        self._inference_thread.start()

    @Slot(int, str)
    def _on_inference_progress(self, value, message):
        self._progress_bar.setValue(value)
        self._status_bar.showMessage(message)
        if hasattr(self, '_ocr_progress') and self._ocr_progress:
            self._ocr_progress.setValue(value)
            self._ocr_progress.setLabelText(message)

    @Slot(object)
    def _on_inference_complete(self, result):
        # Close progress dialog
        if hasattr(self, '_ocr_progress') and self._ocr_progress:
            self._ocr_progress.close()
        
        self._current_result = result
        self._progress_bar.setValue(100)
        self._center_panel.set_detections(result.detections)

        exam_type = result.patient_info.get("study_description", "") or result.patient_info.get(
            "modality", ""
        )
        extracted_data = {
            "patient_name": result.patient_info.get("name", ""),
            "exam_type": exam_type,
            "notes": result.combined_text[:500]
            if len(result.combined_text) > 500
            else result.combined_text,
            "full_text": result.combined_text,
        }
        # Extracted data can be accessed from result object directly

        detection_count = len(result.detections)
        if detection_count > 0:
            self._right_panel.success(
                f"OCR complete: {detection_count} text region(s) detected"
            )
            self._status_bar.showMessage(
                f"Text detected in {detection_count} region(s)"
            )
        else:
            self._right_panel.warning("No embedded text detected")
            self._status_bar.showMessage("No text found")

        self._toolbar_ocr_action.setEnabled(True)
        self._toolbar_save_action.setEnabled(True)

    @Slot(str)
    def _on_inference_error(self, error_msg):
        # Close progress dialog
        if hasattr(self, '_ocr_progress') and self._ocr_progress:
            self._ocr_progress.close()
        
        self._right_panel.error(f"Scan error: {error_msg}")
        self._status_bar.showMessage(f"Error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", error_msg)
        self._toolbar_ocr_action.setEnabled(True)
        self._progress_bar.setValue(0)

    def _parse_age(self, age_text: str) -> int:
        match = re.search(r"\d+", age_text or "")
        return int(match.group()) if match else 30

    def _normalize_exam_type(self, exam_type: str) -> str:
        normalized = (exam_type or "DEFAULT").strip().upper()
        normalized = re.sub(r"[^A-Z0-9]+", "_", normalized).strip("_")
        return normalized or "DEFAULT"

    @Slot(float)
    def _on_calculate_dose(self, weight):
        age = self._parse_age(self._left_panel._age_label.text())
        gender_label = (self._left_panel._gender_label.text() or "").strip().upper()
        if gender_label.startswith("F"):
            gender = "F"
        elif gender_label.startswith("M"):
            gender = "M"
        else:
            gender = "O"

        # Get exam type from current result or patient info
        exam_type = ""
        if self._current_result:
            exam_type = self._current_result.patient_info.get("study_description", "") or self._current_result.patient_info.get("modality", "")
        exam_type = self._normalize_exam_type(exam_type)
        result = DoseCalculator.estimate_dose(age, gender, weight, exam_type)
        dose = result["estimated_dose_mSv"]
        comparison = DoseCalculator.get_dose_comparison(dose)
        comp_text = f"~ {comparison['equivalent_chest_xrays']} chest X-rays"

        self._left_panel.set_dose_result(dose, comp_text)
        self._right_panel.info(f"Estimated dose: {dose:.2f} mSv")

    @Slot(float, float, float, float, float, float)
    def _on_calculate_inak_esak(self, kvp, ma, exposure_time_s, bsf, coeff_a, coeff_b):
        """Handle INAK/ESAK calculation from the panel."""
        try:
            self._inak_calculator.coeff_a = coeff_a
            self._inak_calculator.coeff_b = coeff_b

            result = self._inak_calculator.calculate_all(
                kvp=kvp,
                ma=ma,
                exposure_time_s=exposure_time_s,
                bsf=bsf,
            )
            self._right_panel._inak_panel.set_result(result)
            self._right_panel.info(
                f"ESAK = {result.esak_mgy:.6f} mGy | INAK = {result.inak_mgy:.6f} mGy"
            )
            self._status_bar.showMessage(
                f"y={result.y_mgy:.4f} mGy  |  INAK={result.inak_mgy:.6f} mGy  |  ESAK={result.esak_mgy:.6f} mGy"
            )
        except Exception as e:
            self._right_panel.error(f"Calculation error: {str(e)}")
            QMessageBox.critical(self, "Calculation Error", str(e))

    @Slot()
    def _on_save_results(self):
        if not self._current_result:
            QMessageBox.warning(
                self, "No Results", "No results to save. Run text scan first."
            )
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Results",
            f"results_{os.path.basename(self._current_image_path)}.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        try:
            import csv

            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Detection ID", "Text", "Confidence", "X1", "Y1", "X2", "Y2"]
                )
                for det in self._current_result.detections:
                    writer.writerow(
                        [det.get("id", 0), det.get("text", ""), det.get("conf", 0)]
                        + det.get("xyxy", [0, 0, 0, 0])
                    )
            self._right_panel.success(f"Results saved to {os.path.basename(path)}")
            self._status_bar.showMessage("Results saved")
        except Exception as e:
            self._right_panel.error(f"Save error: {str(e)}")
            QMessageBox.critical(self, "Save Error", str(e))

    @Slot()
    def _on_clear_results(self):
        self._current_result = None
        self._center_panel.clear()
        self._left_panel.clear_all()
        self._right_panel.info("Results cleared")

    @Slot(float)
    def _on_zoom_changed(self, zoom):
        percent = int(zoom * 100)
        self._footer_label.setText(f"Size: — | Zoom: {percent}%")

    @Slot()
    def _on_help(self):
        help_text = (
            "<h2>Radiology Reader</h2>"
            "<p><b>1. Open Image</b>: Load a DICOM or standard image.</p>"
            "<p><b>2. DICOM Metadata</b>: Patient identity is read from DICOM tags.</p>"
            "<p><b>3. Scan Embedded Text</b>: OCR is used only for text rendered inside the image.</p>"
            "<p><b>4. Open Patient Data</b>: Load CSV for matching.</p>"
            "<p><b>5. Save Results</b>: Export detections to CSV.</p>"
        )
        QMessageBox.information(self, "Help", help_text)

    def closeEvent(self, event):
        self._database_service.close()
        event.accept()
