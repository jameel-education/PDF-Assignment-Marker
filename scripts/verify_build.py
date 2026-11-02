"""Verify bundled PyMuPDF layout assets rather than relying on a fixed library version."""
from pathlib import Path
import sys
base = Path('dist') / 'PDF Assignment Marker'
exe = base / 'PDF Assignment Marker.exe'
resources = list((base / '_internal' / 'pymupdf' / 'layout' / 'resources' / 'onnx').glob('layout_rf*.yaml'))
if not exe.is_file() or not resources:
    print('FAIL: missing exe or PyMuPDF ONNX layout YAML resources')
    sys.exit(1)
print('PASS: executable and PyMuPDF layout resources found:', [p.name for p in resources])
