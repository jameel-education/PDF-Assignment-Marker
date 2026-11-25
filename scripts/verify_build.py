"""Verify essential files in the Windows application bundle."""

from pathlib import Path
import sys

base = Path("dist") / "PDF_Assignment_Marker"

required = [
    base / "PDF_Assignment_Marker.exe",
    base / "_internal",
    base / "_internal" / "PDF_Assignment_Marker.ico",
]

missing = [str(path) for path in required if not path.exists()]

if missing:
    print("FAIL: Missing required application files:")
    for path in missing:
        print(path)
    sys.exit(1)

print("PASS: Executable, supporting files and icon found.")
