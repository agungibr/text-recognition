from PyQt6.QtCore import QThread, pyqtSignal

class ModelLoader(QThread):
    done  = pyqtSignal(object, str)
    error = pyqtSignal(str)

    def __init__(
        self,
        kind: str,
        model_path: str | None = None,
        languages: list | None = None,
        use_gpu: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.kind       = kind
        self.model_path = model_path
        self.languages  = languages or ["id", "en"]
        self.use_gpu    = use_gpu

    def run(self) -> None:
        try:
            if self.kind == "yolo":
                self._load_yolo()
            elif self.kind == "ocr":
                self._load_ocr()
            else:
                raise ValueError(f"Unknown loader kind: {self.kind!r}")
        except Exception as exc:
            self.error.emit(str(exc))

    def _load_yolo(self) -> None:
        from ultralytics import YOLO

        if not self.model_path:
            raise ValueError("model_path must be set for kind='yolo'")

        model = YOLO(self.model_path)
        self.done.emit(model, "yolo")

    def _load_ocr(self) -> None:
        import easyocr

        try:
            reader = easyocr.Reader(self.languages, gpu=self.use_gpu)
        except Exception:
            reader = easyocr.Reader(self.languages, gpu=False)

        self.done.emit(reader, "ocr")
