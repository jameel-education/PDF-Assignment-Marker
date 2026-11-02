# Third-party licensing and attribution

This app imports `fitz` (PyMuPDF), `PySide6`, and optional `spellchecker` from `pyspellchecker`. The following identifies upstream licences; review exact bundled versions and all transitive package notices in the Windows build before publishing.

- **PyMuPDF / MuPDF** — AGPL-3.0 or commercial. Project plans the AGPL route. https://pymupdf.io/licensing
- **PySide6 / Qt** — available under LGPL/GPL/commercial options. The appropriate Qt licence notices and compliance requirements must accompany redistributed DLLs. https://doc.qt.io/qtforpython-6/
- **pyspellchecker** — check the installed package metadata and bundled word-frequency data licence; copy all required copyright and licence notices into released distributions.
- **PyInstaller** — build tool; check licensing for any bundled bootloader/runtime notices.

The `assets/PDF_Assignment_Marker.ico` file, if supplied, must be owned by or properly licensed to the project. Windows system fonts including Faruma or MV Boli are **not bundled**.

**Before publishing:** the full AGPLv3 is now included as `COPYING`. Also include component-specific licences and required attribution/Qt notices with both source and installer packages, and retain MuPDF/PyMuPDF producer metadata where applicable. This checklist requires manual review; no assurance of licence compliance is claimed.
