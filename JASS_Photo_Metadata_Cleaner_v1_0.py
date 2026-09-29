
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QFileDialog, QMessageBox, QSplitter, QGroupBox,
    QCheckBox, QLineEdit, QProgressBar
)

from PIL import Image, ImageOps, ExifTags


APP_NAME = "JASS Photo Metadata Cleaner"
VERSION = "1.0"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


class PhotoPreview(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(360, 300)
        self.setText("No photo selected")
        self.setStyleSheet("""
            QLabel {
                background: #151922;
                border: 1px solid #303746;
                border-radius: 10px;
                color: #8e98aa;
                padding: 10px;
            }
        """)

    def set_photo(self, path):
        pix = QPixmap(str(path))
        if pix.isNull():
            self.setText("Unable to preview image")
            return
        scaled = pix.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        super().resizeEvent(event)


class MetadataCleaner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.files = []
        self.current_path = None
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.resize(1250, 760)
        self.build_ui()
        self.apply_theme()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)

        title = QLabel(f"JASS Photo Metadata Cleaner  •  v{VERSION}")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color:#f2f5fa;")
        root.addWidget(title)

        subtitle = QLabel(
            "Offline privacy tool — remove embedded image metadata while keeping the visible photo."
        )
        subtitle.setStyleSheet("color:#9da7b8;")
        root.addWidget(subtitle)

        toolbar = QHBoxLayout()
        for text, slot in [
            ("＋ Add Photos", self.add_photos),
            ("＋ Add Folder", self.add_folder),
            ("Clear List", self.clear_list),
            ("Clean Selected", self.clean_selected),
            ("Clean All", self.clean_all),
        ]:
            b = QPushButton(text)
            b.clicked.connect(slot)
            toolbar.addWidget(b)

        toolbar.addStretch()
        root.addLayout(toolbar)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, 1)

        # Left: file list
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.addWidget(QLabel("PHOTO QUEUE"))

        self.file_list = QListWidget()
        self.file_list.currentRowChanged.connect(self.select_file)
        ll.addWidget(self.file_list, 1)

        self.count_label = QLabel("0 photos")
        self.count_label.setStyleSheet("color:#9da7b8;")
        ll.addWidget(self.count_label)

        splitter.addWidget(left)

        # Center: preview
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.addWidget(QLabel("PREVIEW"))

        self.preview = PhotoPreview()
        cl.addWidget(self.preview, 1)

        self.info_label = QLabel("Select a photo to inspect it.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color:#aab4c4;")
        cl.addWidget(self.info_label)

        splitter.addWidget(center)

        # Right: metadata
        right = QWidget()
        rl = QVBoxLayout(right)

        meta_title = QLabel("EMBEDDED METADATA")
        rl.addWidget(meta_title)

        self.metadata = QTextEdit()
        self.metadata.setReadOnly(True)
        rl.addWidget(self.metadata, 1)

        options = QGroupBox("Cleaning Options")
        og = QGridLayout(options)

        self.remove_exif = QCheckBox("Remove EXIF metadata")
        self.remove_exif.setChecked(True)

        self.remove_gps = QCheckBox("Remove GPS/location metadata")
        self.remove_gps.setChecked(True)

        self.remove_comments = QCheckBox("Remove comments/descriptions")
        self.remove_comments.setChecked(True)

        self.remove_profile = QCheckBox("Remove embedded ICC profile")
        self.remove_profile.setChecked(False)

        og.addWidget(self.remove_exif, 0, 0)
        og.addWidget(self.remove_gps, 1, 0)
        og.addWidget(self.remove_comments, 2, 0)
        og.addWidget(self.remove_profile, 3, 0)

        rl.addWidget(options)

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("Output folder — default: Cleaned_Photos")
        rl.addWidget(self.output_dir)

        choose = QPushButton("Choose Output Folder")
        choose.clicked.connect(self.choose_output)
        rl.addWidget(choose)

        splitter.addWidget(right)

        splitter.setSizes([300, 500, 400])

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        footer = QLabel(
            "Note: this tool cleans embedded file metadata. It does not control platform-generated AI/provenance labels."
        )
        footer.setStyleSheet("color:#7f8999; padding:4px;")
        root.addWidget(footer)

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background:#0f131a;
                color:#e8edf5;
                font-family:"Segoe UI";
                font-size:10pt;
            }
            QPushButton {
                background:#202735;
                border:1px solid #364052;
                border-radius:7px;
                padding:8px 13px;
            }
            QPushButton:hover {
                background:#2a3344;
            }
            QListWidget, QTextEdit, QLineEdit {
                background:#151922;
                border:1px solid #303746;
                border-radius:7px;
                padding:6px;
                color:#e8edf5;
            }
            QGroupBox {
                border:1px solid #303746;
                border-radius:8px;
                margin-top:8px;
                padding-top:8px;
            }
            QGroupBox::title {
                subcontrol-origin:margin;
                left:10px;
                padding:0 5px;
                color:#aeb8c8;
            }
            QCheckBox {
                padding:5px;
            }
            QProgressBar {
                border:1px solid #303746;
                border-radius:6px;
                text-align:center;
                background:#151922;
            }
        """)

    def add_photos(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Photos",
            "",
            "Images (*.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp)"
        )
        self.add_paths(files)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Photo Folder")
        if not folder:
            return
        paths = [
            str(p) for p in Path(folder).iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ]
        self.add_paths(paths)

    def add_paths(self, paths):
        existing = {str(Path(p).resolve()) for p in self.files}
        added = 0
        for p in paths:
            try:
                rp = str(Path(p).resolve())
            except Exception:
                continue
            if rp not in existing and Path(p).is_file():
                self.files.append(rp)
                existing.add(rp)
                self.file_list.addItem(QListWidgetItem(Path(p).name))
                added += 1

        self.count_label.setText(f"{len(self.files)} photos")
        if added and self.file_list.currentRow() < 0:
            self.file_list.setCurrentRow(0)

    def clear_list(self):
        self.files.clear()
        self.file_list.clear()
        self.current_path = None
        self.preview.setText("No photo selected")
        self.preview.setPixmap(QPixmap())
        self.metadata.clear()
        self.info_label.setText("Select a photo to inspect it.")
        self.count_label.setText("0 photos")

    def select_file(self, row):
        if row < 0 or row >= len(self.files):
            return
        self.current_path = self.files[row]
        self.preview.set_photo(self.current_path)
        self.inspect_metadata(self.current_path)

    def inspect_metadata(self, path):
        try:
            with Image.open(path) as im:
                exif = im.getexif()
                lines = [
                    f"File: {Path(path).name}",
                    f"Format: {im.format or 'Unknown'}",
                    f"Dimensions: {im.width} × {im.height}",
                    f"Mode: {im.mode}",
                    f"File size: {Path(path).stat().st_size / 1024:.1f} KB",
                    f"EXIF entries: {len(exif)}",
                    "",
                    "EXIF / metadata:"
                ]

                if exif:
                    for key, value in exif.items():
                        try:
                            name = ExifTags.TAGS.get(key, str(key))
                        except Exception:
                            name = str(key)
                        if isinstance(value, bytes):
                            display = f"<binary {len(value)} bytes>"
                        else:
                            display = str(value)
                        lines.append(f"• {name}: {display[:500]}")
                else:
                    lines.append("• No standard EXIF entries detected.")

                self.metadata.setPlainText("\n".join(lines))
                self.info_label.setText(
                    f"{im.width} × {im.height}  •  {im.format or 'image'}  •  "
                    f"{Path(path).stat().st_size / 1024:.1f} KB"
                )
        except Exception as e:
            self.metadata.setPlainText(f"Unable to inspect metadata:\n{e}")

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Output Folder")
        if folder:
            self.output_dir.setText(folder)

    def get_output_dir(self):
        text = self.output_dir.text().strip()
        if text:
            p = Path(text).expanduser()
        else:
            base = Path(self.current_path).parent if self.current_path else Path.cwd()
            p = base / "Cleaned_Photos"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def clean_selected(self):
        if not self.current_path:
            QMessageBox.information(self, APP_NAME, "Select a photo first.")
            return
        result = self.clean_one(self.current_path)
        if result:
            QMessageBox.information(
                self, "Photo Cleaned",
                f"Cleaned copy created:\n\n{result}"
            )

    def clean_all(self):
        if not self.files:
            QMessageBox.information(self, APP_NAME, "Add some photos first.")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, len(self.files))
        self.progress.setValue(0)
        QApplication.processEvents()

        output = self.get_output_dir()
        success = 0
        errors = []

        for i, path in enumerate(self.files, 1):
            result = self.clean_one(path, output_dir=output)
            if result:
                success += 1
            else:
                errors.append(Path(path).name)
            self.progress.setValue(i)
            QApplication.processEvents()

        self.progress.setVisible(False)

        message = f"Cleaned {success} of {len(self.files)} photos.\n\nOutput:\n{output}"
        if errors:
            message += "\n\nCould not process:\n" + "\n".join(errors[:20])
        QMessageBox.information(self, "Cleaning Complete", message)

    def clean_one(self, path, output_dir=None):
        try:
            source = Path(path)
            output_dir = output_dir or self.get_output_dir()
            output_dir.mkdir(parents=True, exist_ok=True)

            stem = source.stem + "_cleaned"
            suffix = source.suffix.lower()

            # Avoid overwriting previous cleaned copies.
            destination = output_dir / f"{stem}{suffix}"
            n = 2
            while destination.exists():
                destination = output_dir / f"{stem}_{n}{suffix}"
                n += 1

            with Image.open(source) as original:
                # Correct EXIF orientation before creating a fresh image.
                im = ImageOps.exif_transpose(original)

                # Copy only pixel data into a new image. This intentionally
                # prevents original EXIF/application metadata from being copied.
                clean = Image.new(im.mode, im.size)
                clean.putdata(list(im.getdata()))

                save_kwargs = {}

                if suffix in {".jpg", ".jpeg"}:
                    if clean.mode not in ("RGB", "L"):
                        clean = clean.convert("RGB")
                    save_kwargs = {
                        "quality": 95,
                        "optimize": True,
                        "subsampling": 0
                    }
                elif suffix == ".png":
                    save_kwargs = {"optimize": True}
                elif suffix == ".webp":
                    save_kwargs = {"quality": 95, "method": 6}

                if not self.remove_profile.isChecked():
                    icc = original.info.get("icc_profile")
                    if icc:
                        save_kwargs["icc_profile"] = icc

                # Do not pass exif, gps, comment, description, or other
                # application metadata to the new file.
                clean.save(destination, **save_kwargs)
                clean.close()

            return destination
        except Exception as e:
            print(f"Cleaning failed for {path}: {e}")
            return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setStyle("Fusion")
    window = MetadataCleaner()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
