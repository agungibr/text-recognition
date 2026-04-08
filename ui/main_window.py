import os
import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.data_matcher import DataMatcher
from core.dicom_handler import DicomHandler
from core.dose_calculator import DoseCalculator
from services.database_service import DatabaseService
from ui.panels.bottom_panel import BottomPanel
from ui.panels.center_panel import CenterPanel
from ui.panels.left_panel import LeftPanel
from ui.panels.right_panel import RightPanel
from ui.theme import COLORS, ThemeManager


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
    """Background thread for running inference."""

    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str)

    def __init__(self, yolo_model, ocr_reader, image_path, conf=0.25, parent=None):
        super().__init__(parent)
        self.yolo_model = yolo_model
        self.ocr_reader = ocr_reader
        self.image_path = image_path
        self.conf = conf

    def run(self):
        try:
            import cv2

            self.progress.emit(10, "Loading image...")

            image = DicomHandler.load_image(self.image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {self.image_path}")

            patient_info = DicomHandler.get_patient_info(self.image_path)
            self.progress.emit(20, "Extracting metadata...")

            temp_png = None
            if self.image_path.lower().endswith((".dcm", ".dicom")):
                temp_png = DicomHandler.dicom_to_temp_png(self.image_path)
                source = temp_png
            else:
                source = self.image_path

            self.progress.emit(30, "Running text detection...")
            results = self.yolo_model.predict(
                source=source, conf=self.conf, verbose=False
            )

            detections = []
            orig_img = None
            if results and len(results) > 0:
                result = results[0]
                orig_img = result.orig_img
                for i, box in enumerate(result.boxes):
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    xc, yc, w, h = box.xywh[0].tolist()
                    conf_val = float(box.conf[0])
                    detections.append(
                        {
                            "id": i,
                            "xyxy": [int(x1), int(y1), int(x2), int(y2)],
                            "xywh": [xc, yc, w, h],
                            "conf": conf_val,
                            "text": "",
                        }
                    )

            self.progress.emit(50, f"Found {len(detections)} text regions")

            for i, det in enumerate(detections):
                x1, y1, x2, y2 = det["xyxy"]
                h_img, w_img = (
                    orig_img.shape[:2] if orig_img is not None else image.shape[:2]
                )
                x1 = max(0, min(x1, w_img - 1))
                y1 = max(0, min(y1, h_img - 1))
                x2 = max(x1 + 1, min(x2, w_img))
                y2 = max(y1 + 1, min(y2, h_img))
                crop = (
                    orig_img[y1:y2, x1:x2]
                    if orig_img is not None
                    else image[y1:y2, x1:x2]
                )
                if crop.size > 0:
                    crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    ocr_texts = self.ocr_reader.readtext(crop_rgb, detail=0)
                    det["text"] = " ".join(ocr_texts)
                pct = 50 + int((i + 1) / len(detections) * 40) if detections else 70
                self.progress.emit(pct, f"Processing region {i + 1}/{len(detections)}")

            if temp_png:
                try:
                    os.unlink(temp_png)
                except OSError:
                    pass

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
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)

        self._yolo_model = None
        self._ocr_reader = None
        self._current_image_path = None
        self._current_result = None
        self._patient_csv_data = []
        self._data_matcher = DataMatcher()
        self._database_service = DatabaseService()
        self._theme_mgr = ThemeManager()

        self._build_ui()
        self._connect_signals()
        self._apply_styles()
        self.statusBar().showMessage("Ready to use")
        self._auto_load_models()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._topbar = self._create_topbar()
        root.addWidget(self._topbar)

        content = self._create_content_area()
        root.addWidget(content, 1)

        self._bottom_panel = BottomPanel()
        self._bottom_panel.setFixedHeight(180)
        root.addWidget(self._bottom_panel)

        self._status_bar = QStatusBar()
        self._status_bar.setFixedHeight(28)
        self.setStatusBar(self._status_bar)
        self._footer_label = QLabel("Size: -  |  Zoom: 100%")
        self._footer_label.setStyleSheet(
            f"color: {COLORS['text_muted']}; font-size: 11px;"
        )
        self._status_bar.addPermanentWidget(self._footer_label)

    def _create_topbar(self):
        from PySide6.QtWidgets import QToolBar

        toolbar = QToolBar()
        toolbar.setFixedHeight(50)
        toolbar.setMovable(False)

        title = QLabel("  Radiology Reader  ")
        title.setStyleSheet(
            f"color: {COLORS['accent']}; font-size: 16px; font-weight: bold;"
        )
        toolbar.addWidget(title)
        toolbar.addSeparator()

        self._btn_open_image = QPushButton("  Open Image")
        self._btn_open_image.setFixedHeight(34)
        self._btn_open_image.clicked.connect(self._on_open_image)
        toolbar.addWidget(self._btn_open_image)

        self._btn_patient_data = QPushButton("  Open Patient Data")
        self._btn_patient_data.setFixedHeight(34)
        self._btn_patient_data.clicked.connect(self._on_open_patient_data)
        toolbar.addWidget(self._btn_patient_data)

        self._btn_scan_text = QPushButton("  Scan Text")
        self._btn_scan_text.setFixedHeight(34)
        self._btn_scan_text.setObjectName("primary")
        self._btn_scan_text.setEnabled(False)
        self._btn_scan_text.clicked.connect(self._on_scan_text)
        toolbar.addWidget(self._btn_scan_text)

        self._btn_save_results = QPushButton("  Save Results")
        self._btn_save_results.setFixedHeight(34)
        self._btn_save_results.setEnabled(False)
        self._btn_save_results.clicked.connect(self._on_save_results)
        toolbar.addWidget(self._btn_save_results)

        self._btn_help = QPushButton("  Help")
        self._btn_help.setFixedHeight(34)
        self._btn_help.clicked.connect(self._on_help)
        toolbar.addWidget(self._btn_help)

        toolbar.addSeparator()

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(150)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        toolbar.addWidget(self._progress_bar)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        self._logos_widget = self._create_logos()
        toolbar.addWidget(self._logos_widget)

        return toolbar

    def _create_logos(self):
        logos = QWidget()
        logos.setFixedWidth(140)
        lay = QHBoxLayout(logos)
        lay.setContentsMargins(0, 5, 10, 5)
        lay.setSpacing(8)

        logo1 = QLabel()
        logo1.setFixedSize(60, 36)
        logo1.setStyleSheet(
            f"background: {COLORS['accent']}30; border: 1px solid {COLORS['accent']}60; border-radius: 4px; color: {COLORS['accent']}; font-size: 9px;"
        )
        logo1.setText("LOGO 1")
        logo1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo2 = QLabel()
        logo2.setFixedSize(60, 36)
        logo2.setStyleSheet(
            f"background: {COLORS['success']}30; border: 1px solid {COLORS['success']}60; border-radius: 4px; color: {COLORS['success']}; font-size: 9px;"
        )
        logo2.setText("LOGO 2")
        logo2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(logo1)
        lay.addWidget(logo2)
        return logos

    def _create_content_area(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        self._left_panel = LeftPanel()
        self._center_panel = CenterPanel()
        self._right_panel = RightPanel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.addWidget(self._left_panel)
        splitter.addWidget(self._center_panel)
        splitter.addWidget(self._right_panel)
        splitter.setSizes([260, 700, 260])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)

        layout.addWidget(splitter)
        return container

    def _apply_styles(self):
        self.setStyleSheet(f"""
            QMainWindow {{ background: {COLORS["bg"]}; }}
            QToolBar {{ background: {COLORS["surface"]}; border-bottom: 1px solid {COLORS["border"]}; padding: 4px 8px; }}
            QPushButton {{ background: {COLORS["surface2"]}; color: {COLORS["text_primary"]}; border: 1px solid {COLORS["border"]}; border-radius: 6px; padding: 6px 16px; font-size: 12px; }}
            QPushButton:hover {{ background: {COLORS["surface3"]}; }}
            QPushButton#primary {{ background: {COLORS["accent"]}; color: white; border: none; font-weight: 600; }}
            QPushButton#primary:hover {{ background: {COLORS["accent_hover"]}; }}
            QPushButton:disabled {{ background: {COLORS["surface2"]}; color: {COLORS["text_muted"]}; }}
            QProgressBar {{ background: {COLORS["surface2"]}; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {COLORS["accent"]}; border-radius: 3px; }}
            QSplitter::handle {{ background: {COLORS["border"]}; }}
        """)

    def _connect_signals(self):
        self._left_panel.calculateDose.connect(self._on_calculate_dose)
        self._center_panel.zoom_changed.connect(self._on_zoom_changed)
        self._bottom_panel.save_clicked.connect(self._on_save_results)
        self._bottom_panel.clear_clicked.connect(self._on_clear_results)

    def _auto_load_models(self):
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "models",
            "best.pt",
        )
        if os.path.exists(model_path):
            self._load_yolo_model(model_path)

    def _load_yolo_model(self, model_path):
        self._status_bar.showMessage("Loading YOLO model...")
        self._right_panel.info("Loading YOLO model...")

        self._yolo_loader = ModelLoaderThread("yolo", model_path)
        self._yolo_loader.progress.connect(
            lambda msg, val: self._status_bar.showMessage(msg)
        )
        self._yolo_loader.loaded.connect(self._on_yolo_loaded)
        self._yolo_loader.error.connect(self._on_model_error)
        self._yolo_loader.start()

    def _load_ocr_engine(self):
        self._status_bar.showMessage("Loading OCR engine...")
        self._right_panel.info("Loading OCR engine...")

        self._ocr_loader = ModelLoaderThread("ocr")
        self._ocr_loader.progress.connect(
            lambda msg, val: self._status_bar.showMessage(msg)
        )
        self._ocr_loader.loaded.connect(self._on_ocr_loaded)
        self._ocr_loader.error.connect(self._on_model_error)
        self._ocr_loader.start()

    @Slot(object, str)
    def _on_yolo_loaded(self, model, model_type):
        self._yolo_model = model
        self._right_panel.success("YOLO model loaded")
        self._status_bar.showMessage("YOLO model ready")
        self._load_ocr_engine()

    @Slot(object, str)
    def _on_ocr_loaded(self, reader, model_type):
        self._ocr_reader = reader
        self._right_panel.success("OCR engine loaded")
        self._status_bar.showMessage("Ready to use")
        if self._current_image_path:
            self._btn_scan_text.setEnabled(True)

    @Slot(str)
    def _on_model_error(self, error_msg):
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
        if self._center_panel.set_image(path):
            self._right_panel.success(f"Image loaded: {os.path.basename(path)}")
            self._status_bar.showMessage(f"Image loaded: {os.path.basename(path)}")
            patient_info = DicomHandler.get_patient_info(path)
            if patient_info.get("patient_id") or patient_info.get("name"):
                self._left_panel.set_from_image_data(patient_info)
                self._right_panel.info("Patient metadata extracted from DICOM")
            if self._patient_csv_data:
                self._try_match_patient(patient_info)
            if self._yolo_model and self._ocr_reader:
                self._btn_scan_text.setEnabled(True)
        else:
            self._right_panel.error(f"Failed to load: {path}")
            QMessageBox.warning(self, "Load Error", f"Could not load image:\n{path}")

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
            self._right_panel.success("Patient data matched!")
        else:
            self._left_panel.set_matched_data(None)
            self._right_panel.info("No matching patient data found")

    @Slot()
    def _on_scan_text(self):
        if not self._current_image_path:
            QMessageBox.warning(self, "No Image", "Please open an image first.")
            return
        if not self._yolo_model or not self._ocr_reader:
            QMessageBox.warning(
                self, "Models Not Ready", "Please wait for models to load."
            )
            return

        self._btn_scan_text.setEnabled(False)
        self._btn_save_results.setEnabled(False)
        self._progress_bar.setValue(0)
        self._right_panel.info("Starting text scan...")

        self._inference_thread = InferenceThread(
            self._yolo_model, self._ocr_reader, self._current_image_path, conf=0.25
        )
        self._inference_thread.progress.connect(self._on_inference_progress)
        self._inference_thread.result.connect(self._on_inference_complete)
        self._inference_thread.error.connect(self._on_inference_error)
        self._inference_thread.start()

    @Slot(int, str)
    def _on_inference_progress(self, value, message):
        self._progress_bar.setValue(value)
        self._status_bar.showMessage(message)

    @Slot(object)
    def _on_inference_complete(self, result):
        self._current_result = result
        self._progress_bar.setValue(100)
        self._center_panel.set_detections(result.detections)

        extracted_data = {
            "patient_name": result.patient_info.get("name", ""),
            "exam_type": result.patient_info.get("study_description", ""),
            "notes": result.combined_text[:500]
            if len(result.combined_text) > 500
            else result.combined_text,
            "full_text": result.combined_text,
        }
        self._bottom_panel.set_extracted_data(extracted_data)

        detection_count = len(result.detections)
        if detection_count > 0:
            self._right_panel.success(
                f"Text scan complete! Found {detection_count} text regions"
            )
            self._status_bar.showMessage(
                f"Text found! {detection_count} regions detected"
            )
        else:
            self._right_panel.warning("No text detected in image")
            self._status_bar.showMessage("No text found")

        self._btn_scan_text.setEnabled(True)
        self._btn_save_results.setEnabled(True)

    @Slot(str)
    def _on_inference_error(self, error_msg):
        self._right_panel.error(f"Scan error: {error_msg}")
        self._status_bar.showMessage(f"Error: {error_msg}")
        QMessageBox.critical(self, "Scan Error", error_msg)
        self._btn_scan_text.setEnabled(True)
        self._progress_bar.setValue(0)

    @Slot(float)
    def _on_calculate_dose(self, weight):
        data = self._left_panel._patient_id_label.text()
        age_str = self._left_panel._age_label.text()
        gender = self._left_panel._gender_label.text()
        try:
            age = int(age_str) if age_str and age_str != "-" else 30
        except ValueError:
            age = 30

        exam_type = self._bottom_panel.get_exam_type()
        if not exam_type:
            exam_type = "DEFAULT"

        result = DoseCalculator.estimate_dose(age, gender, weight, exam_type)
        dose = result["estimated_dose_msv"]
        comparison = DoseCalculator.get_dose_comparison(dose)
        comp_text = f"~ {comparison['equivalent_chest_xrays']} chest X-rays"
        self._left_panel.set_dose_result(dose, comp_text)
        self._right_panel.info(f"Estimated dose: {dose:.2f} mSv")

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
        if path:
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
        self._bottom_panel.clear()
        self._left_panel.clear_all()
        self._right_panel.info("Results cleared")

    @Slot(float)
    def _on_zoom_changed(self, zoom):
        percent = int(zoom * 100)
        self._footer_label.setText(f"Size: -  |  Zoom: {percent}%")

    @Slot()
    def _on_help(self):
        help_text = "<h2>Radiology Reader Help</h2><p><b>1. Open Image:</b> Load a DICOM or standard image file.</p><p><b>2. Open Patient Data:</b> Load a CSV file with patient records.</p><p><b>3. Scan Text:</b> Run text detection and OCR on the loaded image.</p><p><b>4. Save Results:</b> Export detected text to CSV format.</p><p><b>5. Dose Estimation:</b> Enter patient weight and calculate estimated radiation dose.</p>"
        QMessageBox.information(self, "Help", help_text)

    def closeEvent(self, event):
        self._database_service.close()
        event.accept()
