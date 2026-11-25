# PDF Assignment Marker v11.1.2

## What's New in v11.1.2 — Enhanced Text Formatting and Multilingual Support (2026)

Version 11.1.2 introduces significant improvements to text annotations, font management and multilingual support, providing greater flexibility for teachers when marking PDF assignments.

- Expanded font size range from 5 to 36 px for Text, Part Marks and Total Marks.
- Font selection from installed Windows system fonts.
- Language-specific font preference remembrance.
- Automatic remembrance of font size and colour preferences.
- Live font, size and colour adjustment without closing the active text box.
- Automatic cursor positioning when switching between LTR and RTL languages.
- Resizable text boxes with automatic text wrapping.
- Automatic display of the selected annotation's font and font size.
- Consistent formatting behaviour across both panes in Split View.
- Improved text box rendering without duplicate text or outlines.
- Updated built-in Help and User Guide.

All existing default settings, annotation tools and automatic marks calculations have been preserved.

Available as a Windows installer, a portable ZIP package and through Microsoft Store following Store approval.

## What's New in v11.1.1— Text Selection, Copy Tool & Keyboard Shortcuts (2026)

Version 11.1.1 introduces text selection and copying improvements, allowing users to copy text from supported PDF documents and paste it into other applications. It also introduces keyboard shortcuts for selected tools and menu commands to improve marking efficiency.

### PDF Assignment Marker v11.1.0 — Interface and Annotation Improvements (2026)

- introduces improvements to the application interface, including a redesigned header and floating toolbox, additional annotation symbols, and more convenient colour and opacity controls.

### PDF Assignment Marker v11.0.2 
- introduces a compact, laptop-friendly interface with a Light Blue title bar, streamlined toolbars, more PDF viewing space, improved page navigation, and enhanced Single View and Split View handling.

### All existing PDF marking tools and features are retained.

This release corrects PDF display, zooming, horizontal scrolling, and page rotation issues without introducing new features.

Free, offline Windows software for opening, annotating and marking PDF documents. A teacher can use single or split view, use PDF annotation tools, place part marks and totals, and export marked or flattened PDFs. English and Dhivehi text supported with Windows fonts.

**Project initiator and developer:** Mohamed Jameel, Faculty of Education, The Maldives National University. Independent voluntary project; the affiliation does not imply institutional endorsement. Developed with assistance from AI-based programming tools.

## User Guide

An illustrated guide to installation, PDF marking, Split View, saving documents, and uninstallation.

📖 [Download the PDF Assignment Marker User Guide](docs/PDF_Assignment_Marker_v11_User_Guide.pdf)

## Release status

PDF Assignment Marker v11.0.2 — Compact Interface Update (2026)

PDF Assignment Marker v11.0.1 — Maintenance Update (2026)

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

Download the latest version of PDF Assignment Marker for Windows:

https://github.com/jameel-education/PDF-Assignment-Marker/releases/latest

Two Windows packages are available:

Windows Installer (.exe): Recommended for normal installation.

Windows Portable (.zip): Extract and run without installation.

A SHA256SUMS.txt file is provided to verify download integrity.

Bug reports and community contributions are welcome through GitHub Issues.

## Run from source (Windows)

Install Python 3.11+ and run:

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe Source\PDF_Assignment_Marker.py
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
