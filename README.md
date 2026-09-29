# JASS Photo Metadata Cleaner v1.0

A lightweight, offline PySide6 desktop application for creating cleaned copies of photos with embedded metadata removed.

## Features

- Add individual photos
- Add an entire photo folder
- Photo preview
- Metadata/EXIF inspection
- Remove EXIF metadata
- Remove GPS/location metadata
- Remove comments/descriptions
- Optional ICC profile removal
- Batch cleaning
- New output files — originals are never overwritten
- JPEG/JPG, PNG, WebP, TIFF and BMP support
- Offline operation
- No cloud service or API required
- Lightweight compared with AI/image-generation software

## Important

This application removes embedded metadata from the image file. It does **not** remove or bypass platform-generated AI/provenance labels such as labels that a social-media platform may apply after upload.

## Requirements

Python 3.10+ and PySide6/Pillow.

Install:

```powershell
python -m pip install PySide6 Pillow
```

Run:

```powershell
python .\JASS_Photo_Metadata_Cleaner_v1_0.py
```

## Recommended workflow

1. Add your edited photo.
2. Select it and inspect the metadata.
3. Choose the cleaning options.
4. Choose an output folder, or use the default `Cleaned_Photos`.
5. Click **Clean Selected** or **Clean All**.
6. Upload the newly created copy when you need a metadata-clean version.

The original photo remains untouched.
