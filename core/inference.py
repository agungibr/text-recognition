import os
import tempfile

import cv2
import numpy as np
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.file_utils import load_dicom_as_bgr, dicom_to_temp_png


class InferenceWorker(QThread):
    progress = pyqtSignal(int, str)
    result   = pyqtSignal(list, str)
    log      = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(
        self,
        model,
        reader,
        files: list,
        conf: float = 0.25,
        save_crops: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.model      = model
        self.reader     = reader
        self.files      = files
        self.conf       = conf
        self.save_crops = save_crops

    def run(self) -> None:
        try:
            self._run_inference()
        except Exception as exc:
            self.error.emit(str(exc))

    def _run_inference(self) -> None:
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = tempfile.mkdtemp()
        final_out  = os.path.join(output_dir, f"detection_{timestamp}")
        os.makedirs(final_out, exist_ok=True)

        all_results: list[dict] = []
        total = len(self.files)

        for idx, file_dict in enumerate(self.files):
            name = file_dict["name"]
            self.progress.emit(
                int(idx / total * 100),
                f"[{idx + 1}/{total}]  {name}",
            )
            self.log.emit(f"Processing  →  {name}")

            result = self._process_file(file_dict, final_out)
            if result is not None:
                all_results.append(result)

        self.progress.emit(100, "Done")
        self.result.emit(all_results, final_out)

    def _process_file(self, file_dict: dict, output_root: str) -> dict | None:
        name = file_dict["name"]

        disk_path = self._resolve_to_disk(file_dict)
        if disk_path is None:
            self.log.emit(f"  ✕  Cannot resolve to disk path: {name}")
            return None

        ext = Path(disk_path).suffix.lower()
        owned_tmp: list[str] = []

        try:
            if ext == ".dcm":
                img = load_dicom_as_bgr(disk_path)
                pred_path = dicom_to_temp_png(disk_path)
                owned_tmp.append(pred_path)
            else:
                img = cv2.imread(disk_path)
                pred_path = disk_path

            if img is None:
                self.log.emit(f"  ✕  Cannot read image: {name}")
                return None

            yolo_results = self.model.predict(
                source=pred_path,
                conf=self.conf,
                save=False,
                verbose=False,
            )

            img_stem    = Path(name).stem
            img_out_dir = os.path.join(output_root, img_stem)
            os.makedirs(img_out_dir, exist_ok=True)
            txt_path    = os.path.join(img_out_dir, f"{img_stem}.txt")

            file_result: dict = {
                "filename":   name,
                "detections": [],
                "crops":      [],
                "output_dir": img_out_dir,
            }

            with open(txt_path, "w", encoding="utf-8") as fp:
                boxes = yolo_results[0].boxes
                for i, box in enumerate(boxes):
                    detection = self._process_box(
                        i, box, yolo_results[0].orig_img,
                        img_stem, img_out_dir,
                    )
                    file_result["detections"].append(detection)
                    if detection.get("crop"):
                        file_result["crops"].append(
                            os.path.join(img_out_dir, detection["crop"])
                        )

                    xc, yc, bw, bh = box.xywh[0].tolist()
                    fp.write(
                        f"OBJ_{i:03d} | text='{detection['text']}' "
                        f"| conf={detection['conf']:.3f} "
                        f"| center=({xc:.1f},{yc:.1f}) "
                        f"| size={bw:.1f}x{bh:.1f}\n"
                    )
                    self.log.emit(
                        f"  \u2714  obj_{i:02d}  "
                        f"conf={detection['conf']:.2f}  "
                        f"\u201c{detection['text'][:40]}\u201d"
                    )

            return file_result

        finally:
            for tmp in owned_tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

            if file_dict.get("type") != "path" and disk_path:
                try:
                    os.unlink(disk_path)
                except OSError:
                    pass

    def _process_box(
        self,
        idx: int,
        box,
        orig_img: np.ndarray,
        img_stem: str,
        img_out_dir: str,
    ) -> dict:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        crop = orig_img[y1:y2, x1:x2]

        ocr_results = self.reader.readtext(crop)
        full_text   = " ".join(r[1] for r in ocr_results)
        conf_val    = float(box.conf[0])
        xc, yc, bw, bh = box.xywh[0].tolist()

        crop_filename: str | None = None
        crop_arr: np.ndarray | None = None

        if self.save_crops:
            crop_filename = f"{img_stem}_crop{idx:02d}.jpg"
            crop_path     = os.path.join(img_out_dir, crop_filename)
            cv2.imwrite(crop_path, crop)
            crop_arr = crop

        return {
            "id":       idx,
            "text":     full_text,
            "conf":     conf_val,
            "xc":       xc,
            "yc":       yc,
            "w":        bw,
            "h":        bh,
            "crop":     crop_filename,
            "crop_arr": crop_arr,
        }

    @staticmethod
    def _resolve_to_disk(file_dict: dict) -> str | None:
        if file_dict.get("type") == "path":
            p = file_dict.get("path", "")
            return p if (p and os.path.isfile(p)) else None

        data = file_dict.get("data")
        if not data:
            return None
        suffix = Path(file_dict.get("name", ".tmp")).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(data)
        tmp.close()
        return tmp.name
