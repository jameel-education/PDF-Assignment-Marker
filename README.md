# PDF Assignment Marker v11.0.0

Free, offline Windows software for opening, annotating and marking PDF documents. A teacher can use single or split view, use PDF annotation tools, place part marks and totals, and export marked or flattened PDFs. English and Dhivehi text supported with Windows fonts.

**Project initiator and developer:** Mohamed Jameel, Faculty of Education, The Maldives National University. Independent voluntary project; the affiliation does not imply institutional endorsement. Developed with assistance from AI-based programming tools.

## User Guide

An illustrated guide to installation, PDF marking, Split View, saving documents, and uninstallation.

📖 [Download the PDF Assignment Marker User Guide](docs/PDF_Assignment_Marker_v11_User_Guide.pdf)

## Release status

PDF Assignment Marker v11.0.0 — First Public Release (2026)

PDF Assignment Marker v11.0.0 has been publicly released as free, open-source Windows software. The application has undergone functional testing and release validation on Windows 11 (64-bit).

The following checks have been completed successfully:

- PDF annotation and marking tools.

- Single View and Split View functionality.

- English and Dhivehi text entry.

- Part Marks and automatic Total Marks calculation.

- Save, Save As, and PDF export.

- Windows installer installation and application startup.

- Portable edition extraction and application startup.
  
- Application icon and About version verification.

- Windows uninstallation.

- AVG antivirus scan reported no threats during testing.

Windows 10 (64-bit) is expected to be compatible but has not yet been tested.

These results reflect development and release testing and do not constitute certification for every Windows computer or configuration.

## Download the latest release:
https://github.com/jameel-education/PDF-Assignment-Marker/releases/tag/v11.0.0

Bug reports and community contributions are welcome through GitHub Issues.

## Run from source (Windows)

Install Python 3.11+ and run:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe source\pdf_assignment_marker.py
```

Optional English spellchecking uses pyspellchecker and its word list. The app still opens if the dictionary is unavailable.

## Build Windows installer

1. The user-supplied application icon is already included as `assets/PDF_Assignment_Marker.ico` (Windows multi-resolution) and `assets/PDF_Assignment_Marker.png` (transparent image).
2. The full GNU AGPLv3 licence is included in `COPYING`; review its terms and the third-party notices before distribution.
3. Install **Inno Setup 6** on Windows (optional until installer creation).
4. Run `build_windows.bat`; it creates `dist\PDF Assignment Marker\`, a portable ZIP in `release\`, and automatically compiles the per-user Windows installer if Inno Setup 6 is installed in its standard location. If not found, manually compile `installer\PDF_Assignment_Marker.iss` after installing Inno Setup.
5. Validate the installed app and all checks in `docs/RELEASE_CHECKLIST.md` **before public publication**.

All dependencies are fetched from package repositories during **building**; packaged software does not require an internet connection to run. For fully reproducible builds, create and publish a per-platform pinned lockfile with hashes after Windows validation.

## Licensing

Open-source release route: **AGPL-3.0-only, pending final compliance verification**. The earlier preliminary MIT template is **not** used, because PyMuPDF is AGPL/commercial dual licensed. The full AGPLv3 licence is included in `COPYING`; third-party licence compliance and Windows builds still require final checks. See `LICENSE` and `docs/THIRD_PARTY_NOTICES.md`. See [PyMuPDF licensing](https://pymupdf.io/licensing) and [PySide6 licensing](https://doc.qt.io/qtforpython-6/).

## Contribute

Bug reports and improvements are welcome following the feature freeze. Do not introduce new features without a separate project decision. See docs/CONTRIBUTING.md.
