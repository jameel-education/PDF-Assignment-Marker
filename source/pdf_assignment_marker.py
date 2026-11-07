"""PDF Assignment Marker 11.0.2 — offline Windows PDF annotation, PySide6 and PyMuPDF.

Strokes remain editable during this session; saving creates a new annotated PDF.
"""
import math
import base64
import re
from decimal import Decimal, InvalidOperation
import io
import os
import sys
import ctypes
import subprocess
import tempfile
from shutil import copyfile as shutil_copy_file
from dataclasses import dataclass
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QPoint, QPointF, QRectF, QSize, Signal, QByteArray, QBuffer, QIODevice, QMimeData, QEvent, QLocale, QSettings, QThread, QObject
from PySide6.QtGui import QShortcut, QKeySequence, QAction, QColor, QFont, QIcon, QImage, QPainter, QPainterPath, QPen, QPixmap, QBrush, QTransform, QDrag, QFontMetricsF, QGuiApplication, QPalette, QTextCursor, QTextOption, QTextDocument, QTextBlockFormat, QSyntaxHighlighter, QTextCharFormat, QTextLayout
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QPushButton, QLabel, QLineEdit, QFileDialog, QMessageBox, QScrollArea, QMenu,
    QSlider, QButtonGroup, QToolButton, QSpinBox, QCheckBox, QComboBox,
    QListWidget, QListWidgetItem, QSplitter, QStatusBar, QSizePolicy, QInputDialog, QTextEdit, QPlainTextEdit, QTextBrowser, QDialog, QGridLayout, QLayout, QGraphicsColorizeEffect, QLineEdit, QAbstractSpinBox)
import fitz
from PySide6.QtSvg import QSvgRenderer

# Vector icons remain crisp even on high-DPI displays.
ICON_PATHS = {
"Image PDF": "<rect x='3' y='4' width='18' height='16' rx='2'/><circle cx='9' cy='9' r='2'/><path d='m4 18 6-6 4 4 3-3 4 5'/>",
"Close": "<path d='M5 5 19 19M19 5 5 19'/>",
"Rotate CW": "<path d='M20 9V4h-5M20 4a9 9 0 1 0 1 11'/>",
"Rotate CCW": "<path d='M4 9V4h5M4 4a9 9 0 1 1-1 11'/>",
"Combine PDF": "<rect x='3' y='3' width='12' height='16' rx='1'/><path d='M9 21h12V8h-6M6 7h6M6 11h6'/>",
"Sign": "<path d='m3 18 5-2 10-10-3-3L5 13zM13 5l3 3M3 22h18'/>",
"Pages": "<path d='M3 4h18v16H3zM9 4v16M12 8h6M12 12h6M12 16h5' />",
"Thumbnails": "<path d='M5 6h14M5 12h14M5 18h14' />",
"Single View": "<rect x='4' y='3' width='16' height='18' rx='1.5'/>",
"Split View": "<rect x='2' y='3' width='20' height='18' rx='1.5'/><path d='M12 3v18'/>",
"Open PDF": "<path d='M3 7h6l2 2h10v11H3z'/><path d='M3 7V5h7l2 2'/>",
"Save": "<path d='M4 3h14l3 3v15H4z'/><path d='M8 3v7h9V3M8 21v-8h9v8'/>",
"Save As": "<path d='M4 3h14l3 3v15H4z'/><path d='M8 3v7h9V3M8 21v-8h8'/><path d='m13 18 6-6 2 2-6 6-3 1z'/>",
"Print": "<path d='M6 9V3h12v6M6 18H4V9h16v9h-2'/><path d='M6 14h12v8H6zM17 11h1'/>",
"Undo": "<path d='M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2'/>",
"Redo": "<path d='m15 14 5-5-5-5m5 5H10a6 6 0 0 0 0 12h2'/>",
"Zoom Out": "<circle cx='10' cy='10' r='7'/><path d='M6 10h8m1 5 6 6'/>",
"Zoom In": "<circle cx='10' cy='10' r='7'/><path d='M6 10h8m-4-4v8m5 1 6 6'/>",
"Previous": "<path d='m15 5-7 7 7 7'/>",
"Next": "<path d='m9 5 7 7-7 7'/>",
"Fit Page": "<path d='M5 3h14v18H5zM8 7h8M8 11h8M8 15h5'/>",
"Rotate": "<path d='M20 7V3h-4M20 3a9 9 0 1 0 2 10'/>",
"Fullscreen": "<path d='M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5'/>",
"Move": "<path d='m4 3 15 9-7 1-3 7z'/>",
"Pen": "<path d='m4 20 5-1 11-11-4-4L5 15zM14 6l4 4M4 20l5-1'/>",
"Highlighter": "<path d='m4 17 10-10 5 5L9 22H4zM16 5l3-3 4 4-3 3M2 22h13'/>",
"Eraser": "<path d='m3 15 11-11a2 2 0 0 1 3 0l5 5a2 2 0 0 1 0 3l-9 9H9zM9 9l8 8M4 21h18'/>",
"Tick": "<path d='m3 13 6 6L21 5'/>",
"Cross": "<path d='M5 5 19 19M19 5 5 19'/>",
"Total Marks": "<path d='M19 5H6l7 7-7 7h13'/>",
"Marks": "<text x='12' y='16.4' text-anchor='middle' font-family='Arial, sans-serif' font-weight='700' font-size='12.5' stroke='none' fill='currentColor'>123</text>",
"Text": "<path d='M4 5h16M12 5v15M7 20h10'/>",
"Line": "<path d='M3 19L21 5'/>",
"Arrow": "<path d='M3 20 20 4m-8 0h8v8'/>",
"Emoji": "<circle cx='12' cy='12' r='9'/><path d='M8 10h.01M16 10h.01M8 15q4 5 8 0'/>",
}

ICON_COLOURS = {
    'Move': '#4b5563',
    'Pen': '#ef3340',
    'Highlighter': '#f5b400',
    'Eraser': '#5ea9f8',
    'Tick': '#2dbd5f',
    'Cross': '#ef3340',
    'Line': '#2f80ed',
    'Arrow': '#2f80ed',
    'Text': '#2f80ed',
    'Marks': '#ef3340',
    'Total Marks': '#ef3340',
    'Emoji': '#f5a623',
}

def vector_icon(name, size=36):
    stroke=ICON_COLOURS.get(name, '#0769bc')
    path=ICON_PATHS.get(name, ICON_PATHS["Pen"]).replace("currentColor", stroke)
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
         f'<g fill="none" stroke="{stroke}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">{path}</g></svg>')
    renderer=QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pix);renderer.render(painter);painter.end()
    return QIcon(pix)

def header_info_icon(kind, size=22):
    """White SVG help/about symbols for the blue application banner."""
    inner = ("<circle cx='12' cy='12' r='9'/>"
             "<circle cx='12' cy='7.5' r='1' fill='white' stroke='none'/>"
             "<path d='M12 11v6'/>") if kind == 'about' else (
             "<circle cx='12' cy='12' r='9'/>"
             "<path d='M9.4 9a2.7 2.7 0 0 1 5.2 1.1c0 1.8-2.6 2.3-2.6 4'/>"
             "<circle cx='12' cy='17.6' r='1' fill='white' stroke='none'/>")
    svg = ("<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'>"
           "<g fill='none' stroke='white' stroke-width='1.8' stroke-linecap='round' "
           f"stroke-linejoin='round'>{inner}</g></svg>")
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)

def show_invalid_mark_warning(parent, message):
    """Readable, theme-independent warning for invalid Part Marks input."""
    dialog = QMessageBox(parent)
    dialog.setWindowTitle('Invalid mark')
    dialog.setIcon(QMessageBox.Icon.Warning)
    dialog.setText(message)
    dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
    dialog.setDefaultButton(QMessageBox.StandardButton.Ok)
    dialog.setStyleSheet('''
        QMessageBox { background-color: #f7fbff; }
        QMessageBox QLabel { color: #174c81; background: transparent;
                            font-family: "Segoe UI"; font-size: 12px; }
        QMessageBox QPushButton { background-color: #edf5ff; color: #174c81;
                                 border: 1px solid #a5c8e7; border-radius: 4px;
                                 min-width: 72px; min-height: 27px;
                                 font-family: "Segoe UI"; font-size: 12px; }
        QMessageBox QPushButton:hover { background-color: #dceeff; }
    ''')
    dialog.exec()

def app_resource(name):
    """Locate files in both Python source and PyInstaller bundles."""
    return str(Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / name)

BLUE='#006bbd'
INKS=['#151515','#075ef7','#ed2024','#0a9863']  # Black, Blue, Red, Green
HIGHLIGHTS=['#ffe52f','#63e961','#ed89e6','#80caf8']

# Use the user's Windows fonts and Qt font fallback for Thaana / Arabic.
# No bundled Faruma font is loaded, installed, or embedded.
def annotation_font(text, tool='Text'):
    return QFont('Segoe UI Emoji' if tool == 'Emoji' else 'Segoe UI')


@dataclass
class Stroke:
    tool: str
    color: str
    size: float
    opacity: float
    points: list
    text: str = ""
    text_direction: str = "ltr"
    angle: int = 0  # Rotation of this mark with its PDF page
    text_width: float = 0.0  # User-sized text box width in PDF-page units


def qt_pixmap(page, scale):
    pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale), alpha=False)
    img=QImage(pix.samples,pix.width,pix.height,pix.stride,QImage.Format.Format_RGB888)
    return QPixmap.fromImage(img.copy())


class BackgroundPdfRenderer(QThread):
    """Render off-screen PDF pages without blocking the Qt interface thread.

    Each worker opens its own document; no PyMuPDF Document or Qt pixmap is
    shared across threads. QImage is copied before the PyMuPDF pixmap dies.
    """
    page_ready = Signal(int, int, QImage)

    def __init__(self, path, scale, pages, generation, rotations=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.scale = float(scale)
        self.pages = list(pages)
        self.generation = generation
        self.rotations = dict(rotations or {})

    def run(self):
        try:
            with fitz.open(self.path) as doc:
                for index in self.pages:
                    if self.isInterruptionRequested():
                        return
                    # The main viewer may have rotated this page since opening.
                    # Match its in-memory rotation instead of the on-disk original.
                    rotation = self.rotations.get(index)
                    if rotation is not None and doc[index].rotation != rotation:
                        doc[index].set_rotation(rotation)
                    pix = doc[index].get_pixmap(
                        matrix=fitz.Matrix(self.scale, self.scale), alpha=False)
                    img = QImage(pix.samples, pix.width, pix.height,
                                 pix.stride, QImage.Format.Format_RGB888).copy()
                    if self.isInterruptionRequested():
                        return
                    self.page_ready.emit(self.generation, index, img)
                    # Let the main thread display queued images and handle input.
                    self.msleep(12)
        except Exception:
            # Visible pages are always able to render directly on demand.
            return


class LiveSpellingHighlighter(QSyntaxHighlighter):
    """Underline likely English misspellings while the inline Text editor is open."""
    def __init__(self, document):
        super().__init__(document)
        try:
            from spellchecker import SpellChecker
            self.checker = SpellChecker(language='en', distance=1)
        except Exception:
            # Packaged Windows executables may not include the optional word
            # frequency dictionary. Do not prevent the text editor from opening.
            self.checker = None
        self.word_pattern = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
        self.misspelling_format = QTextCharFormat()
        self.misspelling_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        self.misspelling_format.setUnderlineColor(QColor('#e31b35'))

    def highlightBlock(self, text):
        if self.checker is None:
            return
        matches = [(m, m.group().lower().replace('’', "'"))
                   for m in self.word_pattern.finditer(text)]
        words = {word for _,word in matches if len(word)>1}
        try:
            unknown = self.checker.unknown(words)
        except Exception:
            return
        for m, word in matches:
            if word in unknown:
                self.setFormat(m.start(), len(m.group()), self.misspelling_format)



# Consistent light context menu for all languages and input methods.
CONTEXT_MENU_STYLE = """
QMenu { background-color: #f9fbff; color: #0f4592;
        border: 1px solid #a6c8e8; border-radius: 4px;
        padding: 3px; font-family: 'Segoe UI'; font-size: 12px; }
QMenu::item { background: transparent; color: #0f4592;
              padding: 5px 22px 5px 24px; margin: 1px 2px;
              border-radius: 3px; }
QMenu::item:selected { background: #dceeff; color: #0f4592; }
QMenu::item:disabled { color: #899aaa; }
QMenu::separator { height: 1px; background: #d4e1ef; margin: 3px 8px; }
"""

class GrowingTextEdit(QPlainTextEdit):
    """Test 6-based plain text editor: one writing direction per annotation."""

    def __init__(self, canvas, mark):
        super().__init__(canvas)
        self.canvas = canvas
        self.mark = mark
        self._rtl = mark.text_direction == 'rtl'
        self._direction_decided = bool(mark.text.strip())
        self._existing_right_anchor = self._rtl and bool(mark.text.strip())
        self._manual_width = float(getattr(mark, 'text_width', 0.0) or 0.0)
        self._auto_width = 0.0
        self._resizing_by_mouse = False
        self._drag_origin = None
        self._drag_width = None
        self._resizing_box = False
        self._resize_queued = False
        self._context_menu_open = False
        self.setMouseTracking(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        # Use the selected annotation colour in the live editor, not the
        # application's default dark-blue text colour.
        # Explicit stylesheet size overrides the app-wide 12px widget style.
        # Maintain the selected 8–14 size (default 9) scaled to PDF zoom.
        zoom = max(0.01, getattr(canvas, 'scale', canvas.app.zoom))
        editor_px = max(8, round(mark.size * zoom))
        self.setStyleSheet('QPlainTextEdit {background:rgba(255,255,245,235); '
                           f'color:{QColor(mark.color).name()}; '
                           f'font-family:"Segoe UI"; font-size:{editor_px}px; '
                           'border:2px dashed #2982d4; border-radius:4px; padding:3px;}')
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        font = annotation_font(mark.text)
        font.setPixelSize(max(8, round(mark.size * getattr(canvas, 'scale', canvas.app.zoom))))
        self._fixed_font = font
        self.setFont(font)
        self.document().setDefaultFont(font)
        # Explicit palette colour also applies to cursor-created paragraphs.
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Text, QColor(mark.color))
        self.setPalette(pal)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self._apply_direction(self._rtl)
        self.setPlainText(mark.text)
        self.moveCursor(QTextCursor.MoveOperation.End)
        if mark.tool == 'Text':
            try:
                self.spelling_highlighter = LiveSpellingHighlighter(self.document())
            except Exception:
                self.spelling_highlighter = None
        self.textChanged.connect(self._text_changed)
        self.updateRequest.connect(self._queue_resize)
        self.resize_to_content()
        self.show()
        self.setFocus()

    @staticmethod
    def _first_direction(text):
        import unicodedata
        for ch in text:
            cls = unicodedata.bidirectional(ch)
            if cls in ('R', 'AL') or 0x0780 <= ord(ch) <= 0x07BF:
                return True
            if cls == 'L':
                return False
        return None

    def _apply_direction(self, rtl):
        # Crucial Test 6 behaviour: BOTH widget layout and document settings.
        self._rtl = bool(rtl)
        direction = Qt.LayoutDirection.RightToLeft if rtl else Qt.LayoutDirection.LeftToRight
        alignment = Qt.AlignmentFlag.AlignRight if rtl else Qt.AlignmentFlag.AlignLeft
        self.setLayoutDirection(direction)
        option = self.document().defaultTextOption()
        option.setTextDirection(direction)
        option.setAlignment(alignment)
        self.document().setDefaultTextOption(option)
        cursor = self.textCursor()
        fmt = QTextBlockFormat()
        fmt.setLayoutDirection(direction)
        fmt.setAlignment(alignment)
        cursor.mergeBlockFormat(fmt)
        self.setTextCursor(cursor)
        self.mark.text_direction = 'rtl' if rtl else 'ltr'

    def _text_changed(self):
        if not self._direction_decided and self.mark.tool == 'Text':
            direction = self._first_direction(self.toPlainText())
            if direction is not None:
                self._direction_decided = True
                self._apply_direction(direction)
        self.resize_to_content()

    def _queue_resize(self, *args):
        """Measure after Qt has laid out a new line or soft-wrapped text."""
        if self._resize_queued or not self.isVisible():
            return
        self._resize_queued = True
        QTimer.singleShot(0, self._deferred_resize)

    def _deferred_resize(self):
        self._resize_queued = False
        if self.isVisible():
            self.resize_to_content()

    def resize_to_content(self):
        """Fixed editing area: text wraps and scrolls; typing never changes geometry.

        The width stored on the annotation is the width used by PDF rendering.
        Only the page edge and PDF zoom can limit the nominal fixed size.
        """
        if self._resizing_box:
            return
        self._resizing_box = True
        try:
            zoom = max(0.01, getattr(self.canvas, 'scale', self.canvas.app.zoom))
            anchor_x = round(self.mark.points[0][0] * zoom)
            anchor_y = round(self.mark.points[0][1] * zoom)
            # Compact fixed comment box: 180 x 65 PDF-page units at normal zoom.
            # Neither dimension depends on the number or length of typed lines.
            wanted_width = round((self._manual_width or 180.0) * zoom)
            wanted_height = round(65.0 * zoom)
            available_width = (anchor_x if self._existing_right_anchor
                               else self.canvas.width() - anchor_x) - 8
            width = max(45, min(wanted_width, max(45, available_width)))
            height = max(34, min(wanted_height, max(34, self.canvas.height() - anchor_y - 5)))
            left = max(0, anchor_x - width) if self._existing_right_anchor else anchor_x
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            target = (int(left), max(0, int(anchor_y)), int(width), int(height))
            if (self.x(), self.y(), self.width(), self.height()) != target:
                self.setGeometry(*target)
            self._auto_width = width / zoom
        finally:
            self._resizing_box = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        self._context_menu_open = True
        menu = self.createStandardContextMenu()
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()
            self._context_menu_open = False
            if self.isVisible():
                self.setFocus(Qt.FocusReason.MouseFocusReason)

    def focusOutEvent(self, event):
        if self._context_menu_open:
            return
        super().focusOutEvent(event)
        # A click on the PDF can blur the inline editor before the canvas
        # receives that same click. Do not create another Part Marks box from it.
        if (self.mark.tool == 'Marks'
                and event.reason() == Qt.FocusReason.MouseFocusReason):
            self.canvas._suppress_marks_click = True
            QTimer.singleShot(250, lambda canvas=self.canvas: setattr(canvas, '_suppress_marks_click', False))
        self.canvas.finish_editor()

class PartMarksEdit(GrowingTextEdit):
    """Compact numeric input; the ordinary Text editor is unchanged."""

    def _text_changed(self):
        # Four digits maximum, plus one optional decimal point. The user may
        # enter e.g. 1000, 2.5 or 12.75. Reject letters, signs and excess digits
        # on typing AND paste without changing the normal Text editor.
        raw = self.toPlainText()
        accepted = []
        digits = 0
        decimal_used = False
        for ch in raw:
            if '0' <= ch <= '9' and digits < 4:
                accepted.append(ch)
                digits += 1
            elif ch == '.' and not decimal_used:
                accepted.append(ch)
                decimal_used = True
        corrected = ''.join(accepted)
        if raw != corrected:
            old_pos = self.textCursor().position()
            prefix = raw[:old_pos]
            prefix_digits = 0
            prefix_dot = False
            new_pos = 0
            for ch in prefix:
                if '0' <= ch <= '9' and prefix_digits < 4:
                    prefix_digits += 1
                    new_pos += 1
                elif ch == '.' and not prefix_dot:
                    prefix_dot = True
                    new_pos += 1
            self.blockSignals(True)
            try:
                self.setPlainText(corrected)
                cursor = self.textCursor()
                cursor.setPosition(min(new_pos, len(corrected)))
                self.setTextCursor(cursor)
            finally:
                self.blockSignals(False)
        self.resize_to_content()

    def resize_to_content(self):
        """Use the proven Text editor's zoom-aware box layout, in a compact size.

        The live dashed edit box is deliberately taller than one line. This
        avoids cropping glyph ascenders during Qt font/layout updates at zoom.
        The saved PDF mark is not resized.
        """
        if self._resizing_box:
            return
        self._resizing_box = True
        try:
            zoom = max(0.01, getattr(self.canvas, 'scale', self.canvas.app.zoom))
            anchor_x = round(self.mark.points[0][0] * zoom)
            anchor_y = round(self.mark.points[0][1] * zoom)
            # Match Document 1's approved compact Part Marks editor geometry.
            # Use text metrics and the QTextDocument margin for the live editor
            # only; the saved PDF mark and user-selected font size do not change.
            fm = QFontMetricsF(self.font())
            lines = self.toPlainText().split('\n')
            wanted_width = max(70, max((fm.horizontalAdvance(x) for x in lines), default=0) + 24)
            line_height = max(fm.height(), fm.lineSpacing())
            document_margin = self.document().documentMargin()
            needed_height = (len(lines) * line_height + 2 * document_margin
                             + 18 + max(8, round(0.7 * fm.height())))
            available_width = max(28, self.canvas.width() - anchor_x - 8)
            width = max(28, min(round(wanted_width), available_width))
            height = max(18, math.ceil(max(round(44 * zoom), needed_height) / 2))
            top = max(0, min(anchor_y, self.canvas.height() - height - 3))
            height = min(height, max(17, self.canvas.height() - top - 2))
            self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setGeometry(int(anchor_x), int(top), int(width), int(height))
            self._auto_width = width / zoom
        finally:
            self._resizing_box = False


def emoji_icon(emoji):
    """Rasterize/crop glyph bounds so Windows' small emoji glyphs fill the button.

    Red tick is painted as a vector, independent of Segoe Emoji fallback.
    """
    canvas=QImage(192,192,QImage.Format.Format_ARGB32_Premultiplied)
    canvas.fill(Qt.GlobalColor.transparent)
    painter=QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    if emoji=='RED_TICK':
        painter.setPen(QPen(QColor('#E02020'),15,Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
        path=QPainterPath(QPointF(25,103))
        path.lineTo(QPointF(70,145))
        path.lineTo(QPointF(164,38))
        painter.drawPath(path)
    else:
        f=QFont('Segoe UI Emoji')
        f.setPixelSize(130)
        painter.setFont(f)
        painter.drawText(QRectF(0,0,192,192),Qt.AlignmentFlag.AlignCenter,emoji)
    painter.end()
    bounds=QRectF()
    # Crop transparent margins (glyphs on some Windows builds occupy a small
    # part of the nominal font em square).
    # Scan image bytes rather than making one Python/Qt pixelColor call per pixel.
    # The previous method scanned 36,864 pixels for every emoji and delayed
    # the first opening of the palette on Windows.
    rgba=canvas.convertToFormat(QImage.Format.Format_RGBA8888)
    pixels=rgba.bits()
    stride=rgba.bytesPerLine()
    left=rgba.width();top=rgba.height();right=-1;bottom=-1
    for y in range(rgba.height()):
        row=y*stride
        for x in range(rgba.width()):
            if pixels[row+x*4+3]>16:
                if x<left:left=x
                if x>right:right=x
                if y<top:top=y
                bottom=y
    if right>=left:
        cropped=canvas.copy(left,top,right-left+1,bottom-top+1)
        return QPixmap.fromImage(cropped).scaled(28,28,Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
    # Font could be missing: retain the original label as a fallback.
    return QPixmap()

class EmojiDragButton(QPushButton):
    def __init__(self, emoji, owner):
        super().__init__()
        self.emoji=emoji;self.owner=owner
        self.setFixedSize(82,80)
        pix=emoji_icon(emoji)
        if not pix.isNull():
            self.setIcon(QIcon(pix));self.setIconSize(QSize(28,28))
        else:
            self.setText('✓' if emoji=='RED_TICK' else emoji)
            self.setFont(QFont('Segoe UI Emoji',22))
        self.setToolTip('Click to select, or drag onto the STUDENT PDF')
        self.clicked.connect(lambda:owner.select_emoji(emoji))
        self._press_position=None
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self._press_position=event.position().toPoint()
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if (event.buttons() & Qt.MouseButton.LeftButton and self._press_position is not None
                and (event.position().toPoint()-self._press_position).manhattanLength()>=8):
            self._press_position=None
            drag=QDrag(self)
            mime=QMimeData();mime.setText('pdfpen-emoji:'+self.emoji)
            drag.setMimeData(mime)
            if not self.icon().isNull():drag.setPixmap(self.icon().pixmap(QSize(28,28)))
            drag.exec(Qt.DropAction.CopyAction)
        else:
            super().mouseMoveEvent(event)

class EmojiPalette(QDialog):
    SYMBOLS=['🙂','😊','😀','😍','😃','😐','😢','😮','⭐','🌟','👍','👎','👏','❤️','💯','⚠️','❗','❓','RED_TICK','❌','🎉','📌','💡','📝']
    def __init__(self, app):
        super().__init__(app)
        self.app=app;self.setWindowTitle('Emoji Picker — Drag onto PDF')
        # A normal floating window allows the PDF window to receive drops reliably.
        grid=QGridLayout(self)
        grid.addWidget(QLabel('Drag an emoji onto the STUDENT PDF, or click a symbol then click the page.'),0,0,1,6)
        grid.setSpacing(7)
        grid.setContentsMargins(12,12,12,12)
        for i,e in enumerate(self.SYMBOLS):grid.addWidget(EmojiDragButton(e,self),1+i//6,i%6)
    def select_emoji(self,emoji):
        if emoji=='RED_TICK':
            self.app.select_tool('Tick')
            self.app.set_pen_color('#ed2024')
            self.app.statusBar().showMessage('Red tick selected — click the PDF, or drag the tick from the palette')
            return
        self.app.emoji_choice=emoji
        self.app.select_tool('Emoji')
        self.app.statusBar().showMessage('Emoji selected: '+emoji+' — click page to insert or drag from palette')

class PageCanvas(QWidget):
    changed=Signal()
    def __init__(self, app, page_index=0):
        super().__init__()
        self.app=app
        self.page_index=page_index
        self.paper=QPixmap()
        self.active=None
        self.editor=None;self.edit_mark=None;self.drag_mark=None;self.drag_mark_start=None
        self.eraser_hover=None
        self.resize_signature=None;self.resize_anchor=None
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents,True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setMinimumSize(300,400)
    def set_page(self, pix):
        self.finish_editor()
        self.paper=pix
        self.setFixedSize(pix.size())
        self.update()
    def paintEvent(self,event):
        p=QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.paper.isNull(): p.drawPixmap(0,0,self.paper)
        for stroke in self.app.strokes.get(self.page_index,[]): self.draw_stroke(p,stroke)
        if self.active is not None: self.draw_stroke(p,self.active)
        # Translucent eraser footprint: pointer preview only, never saved or printed.
        if self.app.tool == 'Eraser' and self.eraser_hover is not None and self.app.doc:
            p.save()
            p.setPen(QPen(QColor(25,106,189,180),1.2))
            p.setBrush(QBrush(QColor(63,145,229,65)))
            r=max(1.0,self.app.eraser_size*self.app.zoom/2)
            p.drawEllipse(self.eraser_hover,r,r)
            p.restore()
        p.end()
    def draw_stroke(self,p,stroke,render_zoom=None):
        if not stroke.points:return
        z=self.app.zoom if render_zoom is None else render_zoom
        if stroke.tool == 'Signature':
            p.save()
            try:
                picture=QPixmap()
                picture.loadFromData(base64.b64decode(stroke.text))
                if not picture.isNull():
                    x,y=stroke.points[0]
                    rect=QRectF(x*z,y*z,stroke.text_width*z,stroke.size*z)
                    angle = float(getattr(stroke, 'angle', 0) or 0)
                    if angle:
                        center = rect.center()
                        p.translate(center)
                        p.rotate(angle)
                        p.translate(-center)
                    p.drawPixmap(rect,picture,QRectF(picture.rect()))
                    # Resize handle only in the interactive window, never in exports.
                    if render_zoom is None and self.app.tool=='Move' and getattr(self, 'selected_signature', None) is stroke:
                        p.setPen(QPen(QColor('#126fbd'),1))
                        p.setBrush(QColor('#ffffff'))
                        p.drawRect(QRectF(rect.right()-5,rect.bottom()-5,10,10))
            except (ValueError,TypeError):
                pass
            p.restore()
            return
        if stroke.tool in ('Tick','Cross','Text','Marks','Total Marks','Emoji'):
            self.draw_symbol(p,stroke,z)
            return
        color=QColor(stroke.color)
        color.setAlphaF(stroke.opacity)
        if stroke.tool in ('Line','Arrow','Highlighter') and len(stroke.points)>=2:
            a,b=stroke.points[0],stroke.points[-1]
            if math.dist(a,b)<0.5:return
            p.save()
            w=max(.7,stroke.size*z)
            p.setPen(QPen(color,w,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            p.drawLine(QPointF(a[0]*z,a[1]*z),QPointF(b[0]*z,b[1]*z))
            if stroke.tool=='Arrow':
                dx,dy=b[0]-a[0],b[1]-a[1]
                d=math.hypot(dx,dy)
                u=(dx/d,dy/d);v=(-u[1],u[0]);head=min(14,max(6,stroke.size*6),d*.45)
                left=QPointF((b[0]-u[0]*head+v[0]*head*.45)*z,(b[1]-u[1]*head+v[1]*head*.45)*z)
                right=QPointF((b[0]-u[0]*head-v[0]*head*.45)*z,(b[1]-u[1]*head-v[1]*head*.45)*z)
                p.drawLine(QPointF(b[0]*z,b[1]*z),left)
                p.drawLine(QPointF(b[0]*z,b[1]*z),right)
            p.restore()
            return
        width=max(.6,stroke.size*z)
        p.save()
        pen=QPen(color,width,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        if len(stroke.points)==1:
            x,y=stroke.points[0]
            p.setBrush(QBrush(color))  # A single click is a small dot.
            p.drawEllipse(QPointF(x*z,y*z),width/2,width/2)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)  # Never fill freehand pen/highlighter paths.
            path=QPainterPath(QPointF(stroke.points[0][0]*z,stroke.points[0][1]*z))
            for x,y in stroke.points[1:]:path.lineTo(x*z,y*z)
            p.drawPath(path)
        p.restore()
    def draw_symbol(self,p,stroke,z):
        x,y=stroke.points[0]; x*=z; y*=z
        size=stroke.size*z
        col=QColor(stroke.color)
        p.save();p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Keep stamped marks and text attached to the PDF's page orientation.
        # rotate_page() moves the anchor and accumulates this angle.
        angle = getattr(stroke, 'angle', 0) % 360
        if angle:
            p.translate(x, y)
            p.rotate(angle)
            x, y = 0.0, 0.0
        if stroke.tool in ('Tick','Cross'):
            # Explicit polyline geometry, independent of fonts and painter-path state.
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(col, max(0.5, self.app.pen_size * z), Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            if stroke.tool == 'Tick':
                points = [QPointF(x, y + size * .43),
                          QPointF(x + size * .30, y + size * .75),
                          QPointF(x + size, y)]
                p.drawPolyline(points)
            else:
                p.drawLine(QPointF(x, y), QPointF(x + size, y + size))
                p.drawLine(QPointF(x + size, y), QPointF(x, y + size))
        else:
            font=annotation_font(stroke.text, stroke.tool)
            font.setPixelSize(max(8,round(size)))
            p.setFont(font);p.setPen(col)
            from PySide6.QtGui import QFontMetricsF
            fm=QFontMetricsF(font)
            text=stroke.text
            if (stroke.tool == 'Text' and stroke.text_direction == 'rtl'
                    and getattr(stroke, 'text_width', 0.0)):
                # The former single QPainter.drawText(rect, TextWordWrap) call
                # used Qt's taller fallback-font paragraph leading for Thaana.
                # Lay out the SAME words with QTextLayout but position each
                # visual line at a consistent, compact baseline interval.
                # Do not touch the working live QPlainTextEdit or its geometry.
                text_width = max(20.0, stroke.text_width * z - 8.0)
                line_step = max(1.0, float(size) * 1.65)
                option = QTextOption()
                option.setTextDirection(Qt.LayoutDirection.RightToLeft)
                option.setAlignment(Qt.AlignmentFlag.AlignRight)
                option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
                p.save()
                p.translate(x - text_width, y)
                # Each explicit paragraph is laid out independently. Explicit
                # empty lines are retained and consume one line of spacing.
                current_row = 0
                for paragraph in text.split('\n'):
                    if not paragraph:
                        current_row += 1
                        continue
                    layout = QTextLayout(paragraph, font)
                    layout.setTextOption(option)
                    layout.beginLayout()
                    while True:
                        line = layout.createLine()
                        if not line.isValid():
                            break
                        line.setLineWidth(text_width)
                        # QTextLayout supplies bidi shaping and the glyph
                        # baseline; only its extra paragraph spacing is replaced.
                        line.setPosition(QPointF(0, current_row * line_step))
                        current_row += 1
                    layout.endLayout()
                    layout.draw(p, QPointF(0, 0))
                p.restore()
                p.restore()
                return
            if stroke.tool == 'Text' and getattr(stroke, 'text_width', 0.0):
                doc=QTextDocument()
                doc.setDocumentMargin(0)
                doc.setDefaultFont(font)
                option=doc.defaultTextOption()
                option.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
                option.setTextDirection(Qt.LayoutDirection.RightToLeft if stroke.text_direction == 'rtl' else Qt.LayoutDirection.LeftToRight)
                option.setAlignment(Qt.AlignmentFlag.AlignRight if stroke.text_direction == 'rtl' else Qt.AlignmentFlag.AlignLeft)
                doc.setDefaultTextOption(option)
                doc.setPlainText(text)
                edit_cursor = QTextCursor(doc)
                edit_cursor.select(QTextCursor.SelectionType.Document)
                block_fmt = QTextBlockFormat()
                block_fmt.setLayoutDirection(Qt.LayoutDirection.RightToLeft if stroke.text_direction == 'rtl' else Qt.LayoutDirection.LeftToRight)
                block_fmt.setAlignment(Qt.AlignmentFlag.AlignRight if stroke.text_direction == 'rtl' else Qt.AlignmentFlag.AlignLeft)
                edit_cursor.mergeBlockFormat(block_fmt)
                wrapped_width=max(20.0, stroke.text_width*z-8)
                doc.setTextWidth(wrapped_width)
                from PySide6.QtGui import QAbstractTextDocumentLayout
                ctx=QAbstractTextDocumentLayout.PaintContext()
                ctx.palette.setColor(QPalette.ColorRole.Text, col)
                p.save()
                p.translate(x-wrapped_width if stroke.text_direction == 'rtl' else x, y)
                doc.documentLayout().draw(p,ctx)
                p.restore()
                p.restore()
                return
            lines=text.split('\n')
            widest=max((fm.horizontalAdvance(line) for line in lines),default=0)
            h=fm.height()*len(lines)
            if stroke.tool in ('Text','Marks','Total Marks'):
                p.setPen(col)
            if stroke.tool == 'Text' and stroke.text_direction == 'rtl':
                # Align each rendered line to the right edge of the text block,
                # matching the Windows keyboard direction shown in the editor.
                for i, line in enumerate(lines):
                    p.drawText(QRectF(x-max(widest,1)-2, y+i*fm.height(), max(widest,1)+2, fm.height()+2),
                               Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                               line)
            else:
                for i,line in enumerate(lines):
                    p.drawText(QPointF(x,y+fm.ascent()+i*fm.height()),line)
        p.restore()
    def finish_editor(self):
        editor=self.editor
        if editor is None:return
        self.editor=None;self.edit_mark=None
        content=editor.toPlainText().rstrip()
        mark=editor.mark
        editor.hide();editor.deleteLater()
        if content:
            if mark.tool=='Marks':
                try:
                    number=Decimal(content.strip())
                    if not number.is_finite() or number < 0 or number > Decimal('10000'):
                        raise ValueError()
                    content=format(number.normalize(),'f')
                except (InvalidOperation,ValueError):
                    show_invalid_mark_warning(self, 'Enter a non-negative number, such as 2, 2.5 or 10. This box will not be counted.')
                    self.update()
                    return
            mark.text=content
            if mark.tool == 'Text':
                mark.text_width = float(getattr(editor, '_manual_width', 0.0) or getattr(editor, '_auto_width', 0.0) or 0.0)
                if mark.text_direction == 'rtl' and not editor._existing_right_anchor:
                    mark.points = [(mark.points[0][0] + editor.width() / max(self.app.zoom, .01), mark.points[0][1])]
            if mark not in self.app.strokes.setdefault(self.page_index, []):
                self.app.record_action()
                self.app.strokes[self.page_index].append(mark)
            self.app.set_dirty(True)
            self.changed.emit()
        self.update()
        if mark.tool == 'Text' and self.app.tool == 'Text':
            self.app.select_tool('Move')
    def find_movable(self,pt):
        """Select the nearest drawn mark, including handwriting, lines and arrows."""
        for mark in reversed(self.app.strokes.get(self.page_index, [])):
            if not mark.points:
                continue
            if mark.tool == 'Signature':
                x,y=mark.points[0]
                angle=math.radians(float(getattr(mark,'angle',0) or 0))
                cx,cy=x+mark.text_width/2,y+mark.size/2
                dx,dy=pt[0]-cx,pt[1]-cy
                ux=cx+math.cos(angle)*dx+math.sin(angle)*dy
                uy=cy-math.sin(angle)*dx+math.cos(angle)*dy
                if x-5 <= ux <= x+mark.text_width+5 and y-5 <= uy <= y+mark.size+5:
                    return mark
                continue
            if mark.tool in ('Pen','Highlighter','Line','Arrow'):
                threshold=max(7.0, mark.size/2+4)
                segments=list(zip(mark.points,mark.points[1:]))
                if not segments:
                    segments=[(mark.points[0],mark.points[0])]
                for a,b in segments:
                    dx,dy=b[0]-a[0],b[1]-a[1]
                    den=dx*dx+dy*dy
                    t=max(0.0,min(1.0,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/den)) if den else 0.0
                    if math.dist(pt,(a[0]+t*dx,a[1]+t*dy))<=threshold:
                        return mark
                continue
            x,y=mark.points[0]
            if mark.tool in ('Text','Marks','Total Marks'):
                font=annotation_font(mark.text, mark.tool)
                font.setPixelSize(max(9,round(mark.size)))
                fm=QFontMetricsF(font)
                lines=mark.text.split('\n')
                width=max((fm.horizontalAdvance(line) for line in lines),default=0)+20
                height=max(1,len(lines))*fm.lineSpacing()+15
                left=x-width if mark.tool=='Text' and mark.text_direction=='rtl' else x
            else:
                width=height=mark.size*1.4
                left=x
            if left-9<=pt[0]<=left+width+9 and y-9<=pt[1]<=y+height+9:
                return mark
        return None

    def contextMenuEvent(self,event):
        """Right-click an existing text annotation to edit/cut/copy/paste it."""
        if self.app.doc and self.editor is None:
            point=(event.pos().x()/self.app.zoom,event.pos().y()/self.app.zoom)
            mark=self.find_movable(point)
            if mark is not None and mark.tool=='Text':
                self.app.page_index=self.page_index
                self.app.canvas=self
                self.editor=GrowingTextEdit(self,mark)
                self.edit_mark=mark
                local=self.editor.mapFrom(self,event.pos())
                from PySide6.QtGui import QContextMenuEvent
                menu_event=QContextMenuEvent(QContextMenuEvent.Reason.Mouse, local, event.globalPos())
                self.editor.contextMenuEvent(menu_event)
                event.accept()
                return
        super().contextMenuEvent(event)

    def dragEnterEvent(self,event):
        if self.app.doc and event.mimeData().hasText() and event.mimeData().text().startswith('pdfpen-emoji:'):
            event.acceptProposedAction()
    def dragMoveEvent(self, event):
        if (self.app.doc is not None and event.mimeData().hasText()
                and event.mimeData().text().startswith('pdfpen-emoji:')):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self,event):
        if not self.app.doc:return
        value=event.mimeData().text().removeprefix('pdfpen-emoji:')
        if not value:return
        z=self.app.zoom
        x=max(0,event.position().x()/z);y=max(0,event.position().y()/z)
        mark=Stroke('Tick' if value=='RED_TICK' else 'Emoji','#E02020' if value=='RED_TICK' else self.app.pen_color,float(self.app.stamp_size if value=='RED_TICK' else self.app.emoji_size),1,[(x,y)],'' if value=='RED_TICK' else value)
        self.app.record_action();self.app.strokes.setdefault(self.page_index,[]).append(mark)
        self.app.set_dirty(True);self.update();event.acceptProposedAction()

    def xy(self,e):
        z=self.app.zoom
        x=min(max(e.position().x()/z,0),self.width()/z)
        y=min(max(e.position().y()/z,0),self.height()/z)
        return (x,y)
    def mousePressEvent(self,e):
        if e.button()!=Qt.MouseButton.LeftButton or not self.app.doc:return
        if getattr(self, '_suppress_marks_click', False):
            self._suppress_marks_click = False
            e.accept()
            return
        if self.editor:
            # An outside click commits the current Text/Part Marks entry only.
            # Do not reuse that click to place a second annotation.
            self.finish_editor()
            e.accept()
            return
        self.app.page_index=self.page_index
        self.app.canvas=self
        self.app.refresh_page_navigation()
        pt=self.xy(e)
        if self.app.tool=='Sign':
            self.app.place_signature(self.page_index,pt,rubric=False)
            return
        if self.app.tool=='Move':
            mark=self.find_movable(pt)
            self.selected_signature = mark if mark is not None and mark.tool == 'Signature' else None
            self.update()
            if mark:
                self.app.record_action()
                if mark.tool=='Signature' and math.dist(pt,(mark.points[0][0]+mark.text_width,mark.points[0][1]+mark.size)) <= 14/max(self.app.zoom,.1):
                    self.resize_signature=mark;self.resize_anchor=mark.points[0]
                    return
                self.drag_mark=mark;self.drag_mark_start=pt
                self.setCursor(Qt.CursorShape.ArrowCursor)
                return
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.app.drag_origin=e.globalPosition().toPoint()
            self.app.scroll_origin=(self.app.scroll.horizontalScrollBar().value(),self.app.scroll.verticalScrollBar().value())
            return
        if self.app.tool=='Eraser':
            self.eraser_hover=e.position()
            self.erase_at(pt);return
        if self.app.tool in ('Text','Marks'):
            mark=Stroke(self.app.tool,self.app.pen_color,float(self.app.text_size),1,[pt],'')
            self.editor=(PartMarksEdit(self,mark) if mark.tool == 'Marks'
                         else GrowingTextEdit(self,mark));self.edit_mark=mark
            return
        if self.app.tool=='Total Marks':
            value=self.app.student_marks_text()
            mark=Stroke('Total Marks',self.app.pen_color,float(self.app.text_size),1.0,[pt],'Total: '+value)
            self.app.record_action();self.app.strokes.setdefault(self.page_index,[]).append(mark)
            self.app.set_dirty(True);self.changed.emit();self.update()
            self.app.select_tool('Move')
            return
        if self.app.tool in ('Tick','Cross','Emoji'):
            t=self.app.tool;value=self.app.emoji_choice if t=='Emoji' else ''
            mark=Stroke(t,self.app.pen_color,float(self.app.cross_size if t=='Cross' else self.app.emoji_size if t=='Emoji' else self.app.stamp_size),1.0,[pt],value)
            self.app.record_action();self.app.strokes.setdefault(self.page_index,[]).append(mark)
            self.app.set_dirty(True);self.changed.emit();self.update();return
        c=self.app.highlight_color if self.app.tool=='Highlighter' else self.app.pen_color
        width=self.app.highlighter_size if self.app.tool=='Highlighter' else self.app.pen_size
        opacity=self.app.highlight_opacity if self.app.tool=='Highlighter' else 1.0
        self.active=Stroke(self.app.tool,c,width,opacity,[self.xy(e)])
        self.update()
    def leaveEvent(self,e):
        self.eraser_hover=None
        self.update()
        super().leaveEvent(e)
    def mouseMoveEvent(self,e):
        if self.app.tool == 'Eraser':
            self.eraser_hover=e.position()
            self.update()
        elif self.eraser_hover is not None:
            self.eraser_hover=None
            self.update()
        if self.resize_signature is not None and e.buttons() & Qt.MouseButton.LeftButton:
            pt=self.xy(e); mark=self.resize_signature
            ratio=mark.text_width/max(mark.size,1)
            new_width=max(15,pt[0]-self.resize_anchor[0]);mark.text_width=new_width;mark.size=new_width/ratio
            self.app.set_dirty(True);self.update();return
        if self.drag_mark is not None and e.buttons() & Qt.MouseButton.LeftButton:
            pt=self.xy(e);dx=pt[0]-self.drag_mark_start[0];dy=pt[1]-self.drag_mark_start[1]
            self.drag_mark.points=[(x+dx,y+dy) for x,y in self.drag_mark.points]
            self.drag_mark_start=pt;self.app.set_dirty(True);self.update();return
        if self.app.tool=='Move' and hasattr(self.app,'drag_origin') and e.buttons() & Qt.MouseButton.LeftButton:
            d=e.globalPosition().toPoint()-self.app.drag_origin
            self.app.scroll.horizontalScrollBar().setValue(self.app.scroll_origin[0]-d.x())
            self.app.scroll.verticalScrollBar().setValue(self.app.scroll_origin[1]-d.y());return
        if self.app.tool=='Eraser' and e.buttons() & Qt.MouseButton.LeftButton:
            self.erase_at(self.xy(e));return
        if self.active is not None and e.buttons() & Qt.MouseButton.LeftButton:
            pt=self.xy(e)
            if self.active.tool in ('Line','Arrow','Highlighter'):
                self.active.points=[self.active.points[0],pt]
            elif math.dist(pt,self.active.points[-1])>0.5: self.active.points.append(pt)
            self.update()
    def mouseReleaseEvent(self,e):
        self.resize_signature=None;self.resize_anchor=None
        if self.drag_mark is not None:
            self.drag_mark=None;self.drag_mark_start=None;self.changed.emit();self.update()
        if self.active is not None:
            if self.active.tool in ('Line','Arrow') and (len(self.active.points) < 2 or math.dist(self.active.points[0], self.active.points[-1]) * max(self.app.zoom, 0.01) < 3):
                self.active=None;self.update();return
            self.app.record_action()
            self.app.strokes.setdefault(self.page_index,[]).append(self.active)
            self.active=None
            self.app.set_dirty(True)
            self.changed.emit();self.update()
        if self.app.tool=='Move':
            if hasattr(self.app,'drag_origin'):delattr(self.app,'drag_origin')
            self.setCursor(Qt.CursorShape.OpenHandCursor)
    def erase_at(self,pt):
        strokes=self.app.strokes.get(self.page_index,[])
        threshold=self.app.eraser_size/max(self.app.zoom,0.1)/2
        def near(s):
            if s.tool == 'Signature':
                x,y=s.points[0]
                return x-threshold <= pt[0] <= x+s.text_width+threshold and y-threshold <= pt[1] <= y+s.size+threshold
            if s.tool in ('Tick','Cross','Text','Marks','Total Marks','Emoji'):
                x,y=s.points[0]
                width=s.size * (max(1,len(s.text)*.55) if s.tool in ('Text','Marks') else 1.15)
                height=s.size*(max(1,len(s.text.splitlines())) if s.tool in ('Text','Marks') else 1.2)
                return x-threshold<=pt[0]<=x+width+threshold and y-threshold<=pt[1]<=y+height+threshold
            if any(math.dist(pt,q)<=threshold+s.size/2 for q in s.points):return True
            for a,b in zip(s.points,s.points[1:]):
                dx,dy=b[0]-a[0],b[1]-a[1]
                den=dx*dx+dy*dy
                t=max(0,min(1,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/den)) if den else 0
                if math.dist(pt,(a[0]+dx*t,a[1]+dy*t))<=threshold+s.size/2:return True
            return False
        for i in range(len(strokes)-1,-1,-1):
            if near(strokes[i]):
                self.app.record_action();strokes.pop(i);self.app.set_dirty(True);self.update();break


class RubricMarksEdit(QTextEdit):
    """Inline dotted marks editor, mirroring the student assignment editor."""
    def __init__(self, canvas, mark):
        super().__init__(canvas)
        self.canvas=canvas
        self.mark=mark
        self.setAcceptRichText(False)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet('QTextEdit {background:rgba(255,255,245,235); border:2px dashed #2982d4; border-radius:4px; padding:3px;}')
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        font=QFont('Segoe UI')
        font.setPixelSize(max(8,round(float(mark.get('size',canvas.app.text_size))*canvas.scale)))
        self.setFont(font)
        self.document().setDefaultFont(font)
        self._fixed_format=QTextCharFormat()
        self._fixed_format.setFont(font)
        self._fixed_format.setForeground(QColor(mark.get('color', canvas.app.pen_color)))
        self.setCurrentCharFormat(self._fixed_format)
        self.document().contentsChanged.connect(self.resize_to_content)
        self.setPlainText(mark['text'])
        previous_cursor = self.textCursor()
        all_text = QTextCursor(self.document())
        all_text.select(QTextCursor.SelectionType.Document)
        all_text.mergeCharFormat(self._fixed_format)
        self.setTextCursor(previous_cursor)
        self.setCurrentCharFormat(self._fixed_format)
        self.move(round(mark['x']*canvas.scale),round(mark['y']*canvas.scale))
        self.resize_to_content()
        self.show();self.setFocus()
        self._sync_visible_caret_font()
        QTimer.singleShot(0, self._sync_visible_caret_font)
    def _sync_visible_caret_font(self):
        if not self.isVisible():
            return
        self.document().setDefaultFont(self.font())
        self.setCurrentCharFormat(self._fixed_format)
        self.document().markContentsDirty(0, max(1, self.document().characterCount()))
        self.viewport().update()

    def resize_to_content(self):
        # Document 1 uses QTextEdit, unlike Document 2's PartMarksEdit.
        # Leave extra vertical room for the QTextDocument's own margin,
        # text-layout leading, stylesheet padding and dashed border.
        fm=QFontMetricsF(self.font())
        lines=self.toPlainText().split('\n')
        w=max(70,max((fm.horizontalAdvance(x) for x in lines),default=0)+24)
        line_height=max(fm.height(),fm.lineSpacing())
        document_margin=self.document().documentMargin()
        needed_height=(len(lines)*line_height + 2*document_margin
                       + 18 + max(8,round(0.7*fm.height())))
        # Match the proven Text editor's generous zoom-scaled live box:
        # this changes editing geometry only, not the final PDF annotation.
        h=max(18, math.ceil(max(round(44*self.canvas.scale), needed_height) / 2))
        self.resize(int(w),int(math.ceil(h)))
        # The QTextEdit viewport and underlying QTextDocument both need a
        # layout pass before the digit can be shown without clipping.
        self.document().adjustSize()
        self.viewport().update()
    def keyPressEvent(self,event):
        self.setCurrentCharFormat(self._fixed_format)
        super().keyPressEvent(event)
        self.setCurrentCharFormat(self._fixed_format)

    def inputMethodEvent(self,event):
        self.setCurrentCharFormat(self._fixed_format)
        super().inputMethodEvent(event)
        self.setCurrentCharFormat(self._fixed_format)

    def insertFromMimeData(self,source):
        if source.hasText():
            cursor=self.textCursor()
            cursor.insertText(source.text(),self._fixed_format)
            self.setTextCursor(cursor)
            self.setCurrentCharFormat(self._fixed_format)
            return
        super().insertFromMimeData(source)

    def contextMenuEvent(self,event):
        menu=self.createStandardContextMenu()
        menu.setStyleSheet(CONTEXT_MENU_STYLE)
        try:
            menu.exec(event.globalPos())
        finally:
            menu.deleteLater()
            if self.isVisible():
                self.setFocus(Qt.FocusReason.MouseFocusReason)

    def focusOutEvent(self,event):
        super().focusOutEvent(event)
        if (self.mark.get('type') == 'part'
                and event.reason() == Qt.FocusReason.MouseFocusReason):
            self.canvas._suppress_marks_click = True
            QTimer.singleShot(250, lambda canvas=self.canvas: setattr(canvas, '_suppress_marks_click', False))
        self.canvas.finish_editor()

class RubricCanvas(QLabel):
    """Rubric canvas: the same central tools can now work on both PDFs."""
    def __init__(self, app, page_index=0):
        super().__init__('')
        self.app=app
        self.page_index=page_index
        self.scale=1.0
        self.drag_mark=None
        self.drag_stroke=None
        self.resize_signature=None;self.resize_anchor=None
        self.press_pos=None
        self._pan_origin=None
        self._pan_scroll_origin=None
        self.editor=None
        self.edit_mark=None
        self.active=None
        self.eraser_hover=None  # hover circle only; never saved in the PDF
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet('background:transparent;color:#596b81;')
        self.setMouseTracking(True)
        self.setAcceptDrops(True)  # Enable emoji drops on Document 1.
        self.setMinimumSize(300, 400)

    def dragEnterEvent(self, event):
        if (self.app.rubric_doc is not None and event.mimeData().hasText()
                and event.mimeData().text().startswith('pdfpen-emoji:')):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if (self.app.rubric_doc is not None and event.mimeData().hasText()
                and event.mimeData().text().startswith('pdfpen-emoji:')):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.app.rubric_doc is None or not event.mimeData().hasText():
            event.ignore()
            return
        payload = event.mimeData().text()
        if not payload.startswith('pdfpen-emoji:'):
            event.ignore()
            return
        emoji = payload[len('pdfpen-emoji:'):]
        if not emoji:
            event.ignore()
            return
        x, y = self.xy(event)
        red_tick = emoji == 'RED_TICK'
        mark = Stroke('Tick' if red_tick else 'Emoji',
                      '#E02020' if red_tick else self.app.pen_color,
                      float(self.app.stamp_size if red_tick else self.app.emoji_size),
                      1.0, [(x, y)], '' if red_tick else emoji)
        self.app.record_rubric_action()
        self.app.rubric_strokes.setdefault(self.page_index, []).append(mark)
        self.app.rubric_dirty = True
        self.app._update_document_heading('rubric')
        self.app.update_actions()
        self.update()
        event.acceptProposedAction()

    def paintEvent(self,event):
        super().paintEvent(event)
        if not self.app.rubric_doc:
            return
        painter=QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.app.paint_rubric_marks(painter, self.page_index, self.scale)
        if self.app.tool=='Move' and getattr(self, 'selected_signature', None) is not None:
            painter.save()
            painter.setPen(QPen(QColor('#126fbd'),1))
            painter.setBrush(QColor('white'))
            for mark in self.app.rubric_strokes.get(self.page_index,[]):
                if mark is getattr(self, 'selected_signature', None) and mark.tool=='Signature' and mark.points:
                    x,y=mark.points[0]
                    painter.drawRect(QRectF((x+mark.text_width)*self.scale-5,(y+mark.size)*self.scale-5,10,10))
            painter.restore()
        if self.active is not None:
            PageCanvas.draw_stroke(self.app.canvas, painter, self.active, self.scale)
        if self.app.tool == 'Eraser' and self.eraser_hover is not None:
            painter.save()
            painter.setPen(QPen(QColor(25,106,189,180),1.2))
            painter.setBrush(QBrush(QColor(63,145,229,65)))
            radius=max(1.0,self.app.eraser_size*self.scale/2)
            painter.drawEllipse(self.eraser_hover,radius,radius)
            painter.restore()
        painter.end()

    def setPixmap(self,pix):
        self.finish_editor()
        super().setPixmap(pix)

    def xy(self,e):
        x=min(max(e.position().x()/self.scale,0),self.width()/self.scale)
        y=min(max(e.position().y()/self.scale,0),self.height()/self.scale)
        return (x,y)

    def finish_editor(self):
        if self.editor is None:
            return
        editor=self.editor
        mark=self.edit_mark
        self.editor=None
        self.edit_mark=None
        value=editor.toPlainText().rstrip()
        editor.hide()
        editor.deleteLater()
        if not value:
            self.update()
            if mark.get('type') == 'text' and self.app.tool == 'Text':
                self.app.select_tool('Move')
            return
        if mark.get('type') == 'text':
            mark['text'] = value
            mark['text_direction'] = editor.mark.text_direction
            mark['color'] = editor.mark.color
            mark['size'] = editor.mark.size
            mark['text_width'] = float(getattr(editor, '_manual_width', 0.0) or getattr(editor, '_auto_width', 0.0) or 0.0)
            if mark['text_direction'] == 'rtl' and not editor._existing_right_anchor:
                mark['x'] += editor.width() / max(self.scale, .01)
        else:
            try:
                number=Decimal(value.strip())
                if not number.is_finite() or not (0 <= number <= 10000):
                    raise ValueError()
            except (InvalidOperation,ValueError):
                show_invalid_mark_warning(self, 'Enter a valid non-negative mark, such as 2 or 2.5. The invalid mark was not counted.')
                self.update()
                return
            mark['text']=format(number.normalize(),'f')
            mark['size']=float(mark.get('size',self.app.text_size))
            mark.setdefault('type','part')
        if mark not in self.app.rubric_marks.setdefault(self.page_index,[]):
            self.app.record_rubric_action()
            self.app.rubric_marks[self.page_index].append(mark)
        self.app.rubric_dirty=True
        self.app.update_marks_total()
        self.update()
        if mark.get('type') == 'text' and self.app.tool == 'Text':
            self.app.select_tool('Move')
    def start_editor(self,mark):
        self.finish_editor()
        self.edit_mark=mark
        if mark.get('type') == 'text':
            stroke = Stroke('Text', mark.get('color', self.app.pen_color),
                            float(mark.get('size', self.app.text_size)), 1.0,
                            [(mark['x'], mark['y'])], mark.get('text', ''),
                            mark.get('text_direction', 'ltr'), text_width=float(mark.get('text_width', 0.0)))
            self.editor = GrowingTextEdit(self, stroke)
        else:
            self.editor=RubricMarksEdit(self,mark)

    def hit_mark(self,x,y):
        for mark in reversed(self.app.rubric_marks.get(self.page_index,[])):
            size = float(mark.get('size', self.app.text_size))
            font=annotation_font(mark['text'], 'Text') if mark.get('type')=='text' else QFont('Segoe UI')
            font.setPixelSize(max(9,round(size)))
            metrics=QFontMetricsF(font)
            width=float(mark.get('text_width') or 0) or max((metrics.horizontalAdvance(t) for t in mark['text'].split('\n')),default=0)+18
            height=max(1,len(mark['text'].split('\n')))*metrics.lineSpacing()+12
            left=mark['x']-width if mark.get('type')=='text' and mark.get('text_direction')=='rtl' else mark['x']
            if left-8 <= x <= left+width+8 and mark['y']-8 <= y <= mark['y']+height+8:
                return mark
        return None

    def hit_stroke(self,x,y):
        for stroke in reversed(self.app.rubric_strokes.get(self.page_index, [])):
            pts = stroke.points or []
            if not pts:
                continue
            if stroke.tool == 'Signature':
                sx,sy=pts[0]
                angle=math.radians(float(getattr(stroke,'angle',0) or 0))
                cx,cy=sx+stroke.text_width/2,sy+stroke.size/2
                dx,dy=x-cx,y-cy
                ux=cx+math.cos(angle)*dx+math.sin(angle)*dy
                uy=cy-math.sin(angle)*dx+math.cos(angle)*dy
                if sx-6<=ux<=sx+stroke.text_width+6 and sy-6<=uy<=sy+stroke.size+6:
                    return stroke
                continue
            if stroke.tool in ('Tick','Cross','Text','Marks','Total Marks','Emoji'):
                sx,sy=pts[0]
                if stroke.tool in ('Text','Marks','Total Marks'):
                    font=annotation_font(stroke.text, stroke.tool)
                    font.setPixelSize(max(9,round(stroke.size)))
                    fm=QFontMetricsF(font)
                    lines=stroke.text.split('\n')
                    width=max((fm.horizontalAdvance(line) for line in lines),default=0)+20
                    height=max(1,len(lines))*fm.lineSpacing()+15
                    if stroke.tool=='Text' and stroke.text_direction=='rtl':
                        left=sx-width
                    else:
                        left=sx
                else:
                    width=height=stroke.size*1.4
                    left=sx
                if left-9 <= x <= left+width+9 and sy-9 <= y <= sy+height+9:
                    return stroke
            else:
                xs=[pt[0] for pt in pts]
                ys=[pt[1] for pt in pts]
                margin=max(8.0, stroke.size)
                if min(xs)-margin <= x <= max(xs)+margin and min(ys)-margin <= y <= max(ys)+margin:
                    return stroke
        return None


    def leaveEvent(self,e):
        self.eraser_hover=None
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self,e):
        if not self.app.rubric_doc or e.button()!=Qt.MouseButton.LeftButton:
            return
        if getattr(self, '_suppress_marks_click', False):
            self._suppress_marks_click = False
            e.accept()
            return
        self.app.rubric_page=self.page_index
        self.app.ref_image=self
        self.app.refresh_page_navigation()
        if self.editor:
            # The first outside click finishes the current entry; a subsequent
            # click is required before another Part Marks editor can be opened.
            self.finish_editor()
            e.accept()
            return
        if self.app.tool == 'Eraser':
            self.eraser_hover=e.position()
            self.update()
        x,y=self.xy(e)
        mark=self.hit_mark(x,y)
        stroke=self.hit_stroke(x,y)
        if self.app.tool=='Sign':
            self.app.place_signature(self.page_index,(x,y),rubric=True)
            return
        if self.app.tool=='Total Marks':
            self.app.record_rubric_action()
            self.app.rubric_marks.setdefault(self.page_index,[]).append(dict(x=x,y=y,text='Total: '+self.app.rubric_marks_text(),type='total'))
            self.app.rubric_dirty=True
            self.app.update_marks_total()
            self.update()
            self.app.select_tool('Move')
        elif self.app.tool=='Text':
            self.start_editor(dict(x=x,y=y,text='',type='text',
                                   color=self.app.pen_color,size=self.app.text_size,
                                   text_direction='ltr'))
        elif self.app.tool=='Marks':
            self.start_editor(dict(x=x,y=y,text='',type='part',
                                   color=self.app.pen_color,size=self.app.text_size))
        elif self.app.tool in ('Tick','Cross','Emoji'):
            self.app.record_rubric_action()
            value=self.app.emoji_choice if self.app.tool=='Emoji' else ''
            mark_obj=Stroke(self.app.tool,self.app.pen_color,float(self.app.cross_size if self.app.tool=='Cross' else self.app.emoji_size if self.app.tool=='Emoji' else self.app.stamp_size),1.0,[(x,y)],value)
            self.app.rubric_strokes.setdefault(self.page_index,[]).append(mark_obj)
            self.app.rubric_dirty=True
            self.update()
        elif self.app.tool in ('Pen','Highlighter','Line','Arrow'):
            c=self.app.highlight_color if self.app.tool=='Highlighter' else self.app.pen_color
            width=self.app.highlighter_size if self.app.tool=='Highlighter' else self.app.pen_size
            opacity=self.app.highlight_opacity if self.app.tool=='Highlighter' else 1.0
            self.active=Stroke(self.app.tool,c,width,opacity,[self.xy(e)])
            self.update()
        elif self.app.tool=='Move':
            self.selected_signature = stroke if stroke is not None and stroke.tool == 'Signature' else None
            self.update()
            if stroke is not None:
                self.app.record_rubric_action()
                if stroke.tool=='Signature' and math.dist((x,y),(stroke.points[0][0]+stroke.text_width,stroke.points[0][1]+stroke.size))<=14/max(self.scale,.1):
                    self.resize_signature=stroke;self.resize_anchor=stroke.points[0]
                    return
                self.drag_stroke=stroke
                self.press_pos=(x,y)
            elif mark is not None:
                self.drag_mark=mark
                self.press_pos=(x,y)
            else:
                # Drag unused page space to pan this PDF only.
                self._pan_origin=e.globalPosition().toPoint()
                scroll=self.app.ref_scroll
                self._pan_scroll_origin=(scroll.horizontalScrollBar().value(),
                                         scroll.verticalScrollBar().value())
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif self.app.tool=='Eraser':
            self.erase_at((x,y))

    def mouseMoveEvent(self,e):
        if (self._pan_origin is not None and self.app.tool == 'Move'
                and e.buttons() & Qt.MouseButton.LeftButton):
            delta=e.globalPosition().toPoint()-self._pan_origin
            scroll=self.app.ref_scroll
            scroll.horizontalScrollBar().setValue(self._pan_scroll_origin[0]-delta.x())
            scroll.verticalScrollBar().setValue(self._pan_scroll_origin[1]-delta.y())
            return
        if self.app.tool == 'Eraser' and self.app.rubric_doc:
            self.eraser_hover=e.position()
            self.update()
        elif self.eraser_hover is not None:
            self.eraser_hover=None
            self.update()
        if self.drag_mark is not None and e.buttons() & Qt.MouseButton.LeftButton:
            x,y=self.xy(e)
            self.drag_mark['x']+=x-self.press_pos[0]
            self.drag_mark['y']+=y-self.press_pos[1]
            self.press_pos=(x,y)
            self.app.rubric_dirty=True
            self.update()
            return
        if self.resize_signature is not None and e.buttons() & Qt.MouseButton.LeftButton:
            x,y=self.xy(e); mark=self.resize_signature
            ratio=mark.text_width/max(mark.size,1)
            width=max(15,x-self.resize_anchor[0]);mark.text_width=width;mark.size=width/ratio
            self.app.rubric_dirty=True;self.update();return
        if self.drag_stroke is not None and e.buttons() & Qt.MouseButton.LeftButton:
            x,y=self.xy(e)
            dx,dy=x-self.press_pos[0],y-self.press_pos[1]
            self.drag_stroke.points=[(px+dx,py+dy) for px,py in self.drag_stroke.points]
            self.press_pos=(x,y)
            self.app.rubric_dirty=True
            self.update()
            return
        if self.app.tool=='Eraser' and e.buttons() & Qt.MouseButton.LeftButton:
            self.erase_at(self.xy(e))
            return
        if self.active is not None and e.buttons() & Qt.MouseButton.LeftButton:
            pt=self.xy(e)
            if self.active.tool in ('Line','Arrow','Highlighter'):
                self.active.points=[self.active.points[0],pt]
            elif math.dist(pt,self.active.points[-1])>0.5:
                self.active.points.append(pt)
            self.update()

    def mouseReleaseEvent(self,e):
        self._pan_origin=None
        self._pan_scroll_origin=None
        if self.app.tool == 'Move':
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.drag_mark=None
        self.drag_stroke=None
        self.resize_signature=None;self.resize_anchor=None
        self.press_pos=None
        if self.active is not None:
            if self.active.tool in ('Line','Arrow') and (len(self.active.points) < 2 or math.dist(self.active.points[0], self.active.points[-1]) * max(self.scale, 0.01) < 3):
                self.active=None
                self.update()
                return
            self.app.record_rubric_action()
            self.app.rubric_strokes.setdefault(self.page_index,[]).append(self.active)
            self.active=None
            self.app.rubric_dirty=True
            self.update()

    def contextMenuEvent(self,event):
        if self.app.rubric_doc and self.editor is None:
            x,y=event.pos().x()/self.scale,event.pos().y()/self.scale
            mark=self.hit_mark(x,y)
            if mark and mark.get('type')=='text':
                self.start_editor(mark)
                from PySide6.QtGui import QContextMenuEvent
                local=self.editor.mapFrom(self,event.pos())
                ctx=QContextMenuEvent(QContextMenuEvent.Reason.Mouse,local,event.globalPos())
                self.editor.contextMenuEvent(ctx)
                event.accept()
                return
        super().contextMenuEvent(event)

    def mouseDoubleClickEvent(self,e):
        if not self.app.rubric_doc:
            return
        mark=self.hit_mark(e.position().x()/self.scale,e.position().y()/self.scale)
        if mark and mark.get('type','part') in ('part','text'):
            self.start_editor(mark)

    def erase_at(self, pt):
        strokes=self.app.rubric_strokes.get(self.page_index, [])
        threshold=self.app.eraser_size/max(self.scale,0.1)/2
        def near(stroke):
            if not stroke.points:
                return False
            if stroke.tool=='Signature':
                x,y=stroke.points[0]
                return x-threshold<=pt[0]<=x+stroke.text_width+threshold and y-threshold<=pt[1]<=y+stroke.size+threshold
            if stroke.tool in ('Tick','Cross','Text','Marks','Total Marks','Emoji'):
                x,y=stroke.points[0]
                width=stroke.size * (max(1,len(stroke.text)*.55) if stroke.tool in ('Text','Marks','Total Marks') else 1.15)
                height=stroke.size*(max(1,len(stroke.text.splitlines())) if stroke.tool in ('Text','Marks','Total Marks') else 1.2)
                return x-threshold<=pt[0]<=x+width+threshold and y-threshold<=pt[1]<=y+height+threshold
            if any(math.dist(pt,q)<=threshold+stroke.size/2 for q in stroke.points):
                return True
            for a,b in zip(stroke.points,stroke.points[1:]):
                dx,dy=b[0]-a[0],b[1]-a[1]
                den=dx*dx+dy*dy
                t=max(0,min(1,((pt[0]-a[0])*dx+(pt[1]-a[1])*dy)/den)) if den else 0
                if math.dist(pt,(a[0]+dx*t,a[1]+dy*t))<=threshold+stroke.size/2:
                    return True
            return False
        for i in range(len(strokes)-1,-1,-1):
            if near(strokes[i]):
                self.app.record_rubric_action()
                strokes.pop(i)
                self.app.rubric_dirty=True
                self.update()
                return
        marks=self.app.rubric_marks.get(self.page_index,[])
        mark=self.hit_mark(*pt)
        if mark and mark in marks:
            self.app.record_rubric_action()
            marks.remove(mark)
            self.app.rubric_dirty=True
            self.app.update_marks_total()
            self.update()



HELP_HTML = """
<html><head><style>
body { font-family:'Segoe UI', Arial, sans-serif; color:#203b56; font-size:12px; }
h2 { color:#075294; font-size:17px; margin-top:20px; }
p, li { line-height:1.5; }
table { border-collapse:collapse; width:100%; margin:8px 0; }
th { color:white; background:#075b9f; text-align:left; padding:7px; }
td { padding:7px; border-bottom:1px solid #dae4ee; vertical-align:top; }
.note { color:#536c85; }
</style></head><body>
<p>PDF Assignment Marker lets you open, review, annotate and save one or two PDF documents with a pen, stylus or mouse. Each document keeps its own marks, page position, zoom and save status.</p>
<h2>1. Start here: Document 1 and Document 2</h2>
<ol>
<li>The application starts in <b>Single View</b>, showing <b>Document 1</b>.</li>
<li>Choose <b>Open</b> on the grey toolbar to open a PDF into the active document window.</li>
<li>Once a PDF has been opened, choose <b>Split View</b> to display Document 1 (left) and Document 2 (right).</li>
<li><b>Click inside the PDF you want to work on</b>. A thin blue outline identifies the active PDF.</li>
<li>Use the common grey toolbar or the marking tools to work on that active PDF.</li>
<li>Choose <b>Save</b> or <b>Save As</b> to save marked work to a separate PDF file.</li>
</ol>
<p class='note'>The bottom status bar displays the loaded PDF's clickable filename and save status. The save status on the right stays blank until a document is loaded; it then shows No changes yet, Unsaved changes or All changes saved. Long filenames are shortened to fit; hovering shows the complete filename and folder path. Clicking the <b>filename</b> opens the PDF selection dialog for replacing that document.</p>
<h2>2. Active document and shared grey toolbar</h2>
<p>The compact icon-only grey toolbar beneath the light-blue application title bar is <b>common to both PDF windows</b>. Select the PDF first; then Open, Save, Save As, Image PDF, Undo, Redo, Close, Rotate and Zoom act on <b>that document only</b>. The blue outline shows your selection. In Single View the visible document is active.</p>
<table><tr><th>Control</th><th>How it works</th></tr>
<tr><td>Open</td><td>Open a PDF in the active document window.</td></tr>
<tr><td>Save</td><td>On the first save, choose a new destination filename. Later saves reuse that destination.</td></tr>
<tr><td>Save As</td><td>Always choose a new destination or filename. The original opened PDF is protected from being overwritten.</td></tr>
<tr><td>Image PDF</td><td>Export the active document as a flattened, image-only PDF with visible markings.</td></tr>
<tr><td>Undo / Redo</td><td>Undo or restore recent actions in the active document. Each PDF has an independent history.</td></tr>
<tr><td>Close</td><td>Close only the active PDF. If it has unsaved changes, you are asked before closing.</td></tr>
<tr><td>Rotate CW / Rotate CCW</td><td>Rotate the current page of the active PDF 90 degrees clockwise or anticlockwise. Existing marks follow the rotation.</td></tr>
<tr><td>Zoom − / percentage / +</td><td>Control the active PDF zoom (30–350%). Ctrl + mouse wheel over a PDF zooms that PDF independently; normal wheel scrolling moves through the document.</td></tr>
<tr><td>Single View</td><td>Show only the <b>currently active</b> PDF. The slim marking ribbon moves to the far right.</td></tr>
<tr><td>Split View</td><td>Show both PDFs side by side, with the marking ribbon in the centre. The two buttons are separate commands, not a single toggle.</td></tr>
<tr><td>Combine PDF</td><td>Available when both PDFs are loaded. Creates a new flattened PDF containing <b>Document 1 first, followed by Document 2</b>; the confirmation no longer refers to a rubric or assignment.</td></tr>
<tr><td>Sign</td><td>Open Signature Manager to upload, view or place a saved signature.</td></tr>
</table>
<h2>3. Single View and Split View</h2>
<ol>
<li>On launch, Document 1 is the visible single-page document.</li>
<li>Click <b>Split View</b> to see Document 1 (left) and Document 2 (right).</li>
<li>To show either document by itself, <b>click that document to make it active</b>, then click <b>Single View</b> or press <b>Ctrl+1</b>.</li>
<li>Choose <b>Split View</b> to return to two documents. Single View and Split View are separate buttons: the button for the current view is disabled.</li>
</ol>
<p><b>Initial viewing size:</b> A PDF opened in Single View uses a 217% initial zoom. In Split View, each newly opened PDF is fitted independently to its document pane width and centred horizontally. The Zoom buttons and Ctrl + mouse wheel can then adjust the active PDF. Switching views or replacing a document should not discard annotations or unsaved work.</p>
<p>In Split View, the inactive PDF remains visible while its tool settings can be displayed over it. Before a PDF is loaded, both view buttons and document-specific controls are disabled; Open and Sign remain available.</p>
<h2>4. Vertical marking ribbon: click once or twice</h2>
<p>On startup, <b>Select</b> is the active tool. With Select active, drag empty PDF space to pan the document; drag an existing annotation to move it. The slim, single-column marking ribbon contains vector icons with small labels. <b>Single-click</b> a tool to activate it. <b>Double-click</b> the tool button to open its floating settings panel; double-click the same button again to close it. The settings panel opens beside the clicked button: <b>over the inactive PDF in Split View</b> and <b>to the left of the ribbon in Single View</b>. It does not resize the PDF windows.</p>
<table><tr><th>Tool</th><th>What it does</th></tr>
<tr><td>Select</td><td>Default startup tool. Move inserted marks by dragging them, or drag empty PDF space to pan the document.</td></tr>
<tr><td>Pen</td><td>Write or draw freehand with a mouse or stylus.</td></tr>
<tr><td>Highlighter</td><td>Click and drag to draw a <b>straight</b> translucent highlight line over the PDF; width, colour and opacity are configurable.</td></tr>
<tr><td>Eraser</td><td>Remove inserted marks. Its circle previews eraser size.</td></tr>
<tr><td>Tick / Cross</td><td>Click to place marking symbols. Each has its own configurable colour and size.</td></tr>
<tr><td>Line / Arrow</td><td>Click and drag to create a line or arrow.</td></tr>
<tr><td>Text</td><td>Click to create a fixed-size, editable text comment.</td></tr>
<tr><td>123 (Marks)</td><td>Enter part marks beside answers or rubric criteria.</td></tr>
<tr><td>Σ (Sum)</td><td>Place the calculated total for the active PDF.</td></tr>
<tr><td>Emoji</td><td>Open the emoji palette beside the ribbon; click or drag an emoji to the active PDF.</td></tr>
</table>
<h2>5. Individual colours, sizes and tool settings</h2>
<p>Each applicable marking tool <b>remembers its own chosen colour</b>. The SVG tool icon shows that choice. Changing one tool's colour does not automatically change other tools or previously placed marks. <b>Emoji and Signature</b> keep their fixed icon colours. For Select and Eraser, any icon colour choice changes the icon only, not what the tool does.</p>
<p>Double-click the tool to adjust its available colour and size controls. Slider labels display actual values (px, or % for opacity). Pen widths are 0.5, 1, 1.5 or 2 px; Highlighter width is 8–14 px; Text/Marks size is 8–14 px (default 9 px). Tick and Cross default to 14 px, and Emoji defaults to 14 px. Available controls vary by tool.</p>
<h2>6. Writing English and Dhivehi comments</h2>
<ol>
<li>Single-click <b>Text</b> to select it. Double-click the Text button first if you want to adjust its colour or size.</li>
<li>Click the position in the active PDF and type into the fixed-size dotted editing box.</li>
<li>Use Windows keyboard language selection for English or Dhivehi. The text direction follows the language.</li>
<li>Enter starts a new line. Long text wraps and can scroll inside the editor.</li>
<li>Right-click the editor for Cut, Copy, Paste and Select All; click outside to finish.</li>
</ol>
<p class='note'>Check how Dhivehi and other comments appear in the saved PDF before sharing it.</p>
<h2>7. Part Marks and Sum</h2>
<ol><li>Select <b>123 (Marks)</b> and click the active PDF where a part mark is needed.</li>
<li>Enter a non-negative number such as 2, 2.5 or 10; continue for the remaining answers.</li>
<li>Select <b>Σ (Sum)</b> and click where the total should appear.</li></ol>
<p>Totals are calculated separately for Document 1 and Document 2. Normal text comments do not contribute to the numerical total.</p>
<h2>8. Saving, closing, exporting and status</h2>
<p>Save and Save As apply to the active PDF; use a different filename for each student's marked assignment. <b>Save</b> remembers its successful output destination for that document, whereas <b>Save As</b> asks for a name. Both PDF windows have separate save status indicators. Closing either PDF or exiting the application checks for unsaved work.</p>
<p><b>Image PDF</b> flattens only the active PDF. <b>Combine PDF</b> is available only when both PDFs are loaded and flattens both together (Document 1 pages first, followed by Document 2 pages). Image-only export is not encryption or a tamper-proof digital signature.</p>
<h2>9. Select or replace a PDF by clicking its filename</h2>
<ol>
<li>Open a PDF using <b>Open</b>. The bottom document status bar then shows its clickable filename.</li>
<li><b>Click the filename</b> below the PDF (not the folder path or save-status text). A compact Windows <b>Select replacement PDF</b> file dialog opens in the current PDF's folder.</li>
<li>Browse the local computer, available drive, network location or synced cloud folder. Select a <b>.pdf</b> file and choose <b>Open</b>.</li>
<li>If the existing PDF has <b>no unsaved changes</b>, confirm <b>Replace</b> or choose <b>Cancel</b>.</li>
<li>If the existing PDF has <b>unsaved changes</b>, choose <b>Save and Replace</b> (save the current work first), <b>Replace Without Saving</b> (discard unsaved marks), or <b>Cancel</b> (keep the current PDF).</li>
<li>If saving fails or you cancel the Save dialog, the original document stays open and will not be replaced.</li>
</ol>
<p class="note">The selected replacement opens in the document window whose filename was clicked. The other document remains unchanged. Clicking the displayed filename opens a file-selection dialog, not ordinary File Explorer.</p>
<h2>10. Signature Manager</h2>
<p>Choose <b>Sign</b> on the grey toolbar to open Signature Manager. Use Upload / Replace to save an image, View to inspect it, Add to PDF to place it, or Delete to remove the stored image. Select/Move can reposition a placed signature; its corner control can resize it. A saved signature can be reused, so protect your computer account. Shortcut: <b>Ctrl+Alt+G</b>.</p>
<h2>11. Bottom page navigation and page thumbnails</h2>
<p>In <b>Single View</b>, the <b>Pages</b> button can open or hide a scrollable panel of page thumbnails on the left. Select a thumbnail to jump to that page. The Pages button is grey and unavailable until the displayed PDF has loaded, and remains disabled in Split View.</p>
<p>The separate filename strip and old page-navigation row have been combined into one slim bottom status bar. Each PDF has its own clickable filename, save-status indicator and independent Previous, editable page number and Next controls. Type a page number and press Enter to jump directly to it. Invalid page numbers are not used. In Split View, use the controls under the document you want to navigate; the other PDF stays on its own page.</p>
<p>Long filenames are shortened automatically with an ellipsis. Hover over the filename to read the full filename and folder path, or click it to choose a replacement PDF. Temporary notification messages are no longer displayed beneath the bottom bar; important warnings and confirmation dialogs still appear.</p>
<h2>12. Languages and fonts</h2>
<p>PDF Assignment Marker has been <b>tested for text entry in English, Dhivehi, Arabic and Urdu</b>, including typing direction and text alignment.</p>
<table><tr><th>Language</th><th>Writing direction</th></tr>
<tr><td>English</td><td>Left to right (LTR).</td></tr>
<tr><td>Dhivehi</td><td>Right to left (RTL).</td></tr>
<tr><td>Arabic</td><td>Right to left (RTL).</td></tr>
<tr><td>Urdu</td><td>Right to left (RTL).</td></tr></table>
<p><b>Dhivehi fonts:</b> MV Boli is the default. When Faruma is installed in Windows, Dhivehi text can also be displayed using Faruma.</p>
<p><b>Choose a language:</b> Install or enable the appropriate keyboard language in <b>Windows Language Settings</b>, then select that input language before typing in the Text tool. For reliable alignment, use one writing language per text box.</p>
<p><b>Other RTL languages:</b> Additional right-to-left languages may work in the text editor if suitable fonts are installed and the corresponding input language is selected in Windows. These languages have not been fully tested.</p>
<p class='note'>Typing and alignment have been tested for the four languages above. For important documents, reopen a saved PDF to check the appearance of its text.</p>
<h2>13. Common problems</h2>
<p><b>Edits went to the other PDF:</b> Click the intended PDF to make its blue active border appear, then mark or use the shared toolbar.</p>
<p><b>Can't find colour or size settings:</b> Double-click the relevant vertical tool icon (a single-click only selects it).</p>
<p><b>Settings cover part of a PDF:</b> The floating panel overlays the inactive document in Split View, or opens beside the ribbon in Single View. Close it with the red X or another double-click.</p>
<p><b>Replace without losing marks:</b> Click the PDF filename and choose Save and Replace if unsaved annotations need to be kept. Cancel if unsure.</p>
<p><b>Cannot save:</b> The destination might be open in another program or the folder may be protected. Close that program or use Save As with a different path.</p>
<p><b>Wrong orientation:</b> Select the correct active PDF, then use Rotate CW or Rotate CCW.</p>
<p><b>Typing behaves unexpectedly:</b> Check the Windows keyboard language and keep the dotted editor active.</p>
<p><b>Large PDFs:</b> The first page appears quickly; remaining pages load progressively.</p>
<h2>14. Keyboard shortcuts</h2>
<p>Shared document shortcuts operate on the PDF with the blue active border. Click within a document to make it active, then use the shortcuts below. The Up and Down arrow keys scroll a short distance; Page Up and Page Down move one complete PDF page. Ctrl + Page Up goes to the first page, and Ctrl + Page Down goes to the last. These keys are not intercepted while editing text or typing a page number. Hover over an icon-only ribbon button to see its command and shortcut where available.</p>
<table><tr><th>Function</th><th>Shortcut</th></tr>
<tr><td>Open / Close active PDF</td><td>Ctrl+O / Ctrl+W</td></tr>
<tr><td>Save / Save As active PDF</td><td>Ctrl+S / Ctrl+Shift+S</td></tr>
<tr><td>Undo / Redo in active PDF</td><td>Ctrl+Z / Ctrl+Y</td></tr>
<tr><td>Image PDF export of active PDF</td><td>Ctrl+Shift+I</td></tr>
<tr><td>Rotate CW / CCW active PDF</td><td>Ctrl+R / Ctrl+Shift+R</td></tr>
<tr><td>Zoom In / Out active PDF</td><td>Toolbar Zoom buttons or Ctrl + mouse wheel (not Ctrl + Plus/Minus)</td></tr>
<tr><td>Previous / Next page in active PDF</td><td>Page Up / Page Down</td></tr>
<tr><td>First / Last page in active PDF</td><td>Ctrl+Page Up / Ctrl+Page Down</td></tr>
<tr><td>Scroll a short distance up / down</td><td>Up Arrow / Down Arrow</td></tr>
<tr><td>Single View / Split View</td><td>Ctrl+1 / Ctrl+Shift+V</td></tr>
<tr><td>Combine PDF / Sign</td><td>Ctrl+Shift+M / Ctrl+Alt+G</td></tr>
<tr><td>Help / About</td><td>F1 / Ctrl+Alt+A</td></tr>
<tr><td>Select / Pen / Highlighter / Eraser</td><td>Alt+1 / Alt+2 / Alt+3 / Alt+4</td></tr>
<tr><td>Tick / Cross / Line / Arrow</td><td>Alt+5 / Alt+6 / Alt+7 / Alt+8</td></tr>
<tr><td>Text / Part Marks</td><td>Alt+9 / Alt+0</td></tr>
<tr><td>Total Marks / Emoji</td><td>Ctrl+Alt+M / Ctrl+Alt+E</td></tr>
<tr><td>Pen colours: Black / Blue / Red / Green</td><td>Ctrl+Shift+1 / 2 / 3 / 4</td></tr>
<tr><td>Highlighter colours: Yellow / Green / Pink / Light blue</td><td>Ctrl+Shift+5 / 6 / 7 / 8</td></tr>
<tr><td>Zoom with mouse</td><td>Ctrl + Mouse Wheel (30–350%)</td></tr>
<tr><td>Paste into text box</td><td>Ctrl+V or right-click &gt; Paste</td></tr>
</table>
<h2>15. Useful reminders</h2>
<ul><li>Check which PDF has the blue active border before applying a command.</li>
<li>Save regularly, ideally to distinct output files rather than overwriting originals.</li>
<li>Reopen an exported PDF to verify the saved result before distributing it.</li>
<li>PDF Assignment Marker is intended for grading and annotation; it does not provide tamper-proof certification.</li></ul>
<p class='note'>PDF Assignment Marker — User Guide, version 11.0.2 (compact interface)</p>
</body></html>
"""

class ActivePdfOutline(QWidget):
    """Lightweight overlay that paints its outline and never intercepts clicks."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setPen(QPen(QColor('#1683ed'), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(1, 1, -2, -2))
        painter.end()

class CompactNotificationBar(QStatusBar):
    """Retained as an invisible compatibility sink for legacy status messages.

    Feedback must not create a second bar underneath the compact filename and
    page-navigation row. Existing explicit dialogs still report errors and
    request confirmation when needed.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        self.setFixedHeight(0)
        self.hide()

    def showMessage(self, message, timeout=0):
        # Never show transient messages or consume PDF working space.
        return

class FileNameLabel(QLabel):
    """Clickable filename, automatically middle-elided to the actual label width."""
    clicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._has_document = False
        self._hovering = False
        self._full_filename = ''
        self._full_path = ''
        self._update_link_appearance()

    def set_filename(self, filename, full_path=''):
        """Keep the unabridged name; fit only the display text to available pixels."""
        self._full_filename = filename
        self._full_path = full_path
        self.setToolTip(full_path if full_path and full_path != 'No file loaded' else '')
        self._fit_filename()

    def _fit_filename(self):
        if not self._full_filename:
            return
        # Width comes from the actual allocated QLabel geometry, AFTER the
        # save-status and navigation controls have reserved their space.
        width = max(1, self.contentsRect().width() - 3)
        shown = self.fontMetrics().elidedText(
            self._full_filename, Qt.TextElideMode.ElideMiddle, width)
        if shown != self.text():
            self.setText(shown)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_filename()

    def set_document_available(self, available):
        self._has_document = bool(available)
        self._update_link_appearance()

    def _update_link_appearance(self):
        active_hover = self._has_document and self._hovering
        self.setStyleSheet(
            'color: ' + ('#087ccc' if active_hover else '#174c81') +
            '; background: transparent; text-decoration: ' +
            ('underline' if active_hover else 'none') + ';'
        )
        self.setCursor(Qt.CursorShape.PointingHandCursor if self._has_document else Qt.CursorShape.ArrowCursor)

    def enterEvent(self, event):
        self._hovering = True
        self._update_link_appearance()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovering = False
        self._update_link_appearance()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._has_document and event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
            self.clicked.emit()
        else:
            super().mouseReleaseEvent(event)

class CompactBlueTitleBar(QFrame):
    """Compact, readable blue title area with normal window actions.

    The stock Windows caption cannot have per-app font/icon size changes.
    This app-owned title bar is isolated to the compact-layout test build.
    """
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setObjectName('compactBlueTitleBar')
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 0, 0)
        layout.setSpacing(9)
        icon = QLabel(self)
        icon.setFixedSize(30, 30)
        icon.setPixmap(QIcon(app_resource('PDF_Assignment_Marker.ico')).pixmap(QSize(30,30)))
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(icon)
        text = QLabel('PDF Assignment Marker', self)
        text.setObjectName('compactBlueTitleText')
        text_font = QFont('Segoe UI')
        # Approved larger, bold application title; filename links have their own smaller font.
        text_font.setPixelSize(19)
        text_font.setWeight(QFont.Weight.Bold)
        text.setFont(text_font)
        text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(text)
        layout.addStretch(1)

        for label, hint, callback, key in (
            ('−','Minimize',window.showMinimized,'min'),
            ('□','Maximize / Restore',self.toggle_maximize,'max'),
            ('×','Close',window.close,'close'),
        ):
            button = QPushButton(label,self)
            button.setObjectName('compactTitleClose' if key=='close' else 'compactTitleControl')
            button.setFixedSize(46,40)
            button.setToolTip(hint)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button.clicked.connect(callback)
            if key == 'max':
                self.maximize_button=button
            layout.addWidget(button)

    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()
        self.sync_maximize_button()

    def sync_maximize_button(self):
        if hasattr(self,'maximize_button'):
            self.maximize_button.setText('❐' if self.window.isMaximized() else '□')
            self.maximize_button.setToolTip('Restore' if self.window.isMaximized() else 'Maximize')

    def mousePressEvent(self,event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window.windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self,event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.folder_settings = QSettings("PDF Assignment Marker", "PDF Assignment Marker UI Trial")
        self.signature_image=str(self.folder_settings.value("signature/png", "") or "")
        self.doc=None;self.path=None;self.page_index=0;self.zoom=1.0;self.student_auto_fit_width=False
        self.tool='Move';self.pen_color=INKS[2];self.highlight_color=HIGHLIGHTS[0]
        # Independent colours, scoped to this experimental build.
        self.tool_colors={n: str(self.folder_settings.value('experiment/tool_color/'+n, default))
                          for n,default in {'Pen':INKS[2],'Highlighter':HIGHLIGHTS[0],
                          'Tick':'#0a9863','Cross':'#ed2024','Line':'#075ef7',
                          'Arrow':'#075ef7','Text':'#ed2024','Marks':'#ed2024',
                          'Total Marks':'#ed2024','Move':'#075ef7','Eraser':'#075ef7'}.items()}
        self._floating_tool_dialog=None
        self._floating_tool_name=None
        self._active_pdf_side='rubric'
        self.pen_size=1.0;self.highlighter_size=8.0;self.highlight_opacity=.40;self.eraser_size=14
        self.stamp_size=14;self.cross_size=14;self.emoji_size=14;self.text_size=9;self.emoji_choice='🙂'
        self.rubric_doc=None;self.rubric_page=0;self.rubric_marks={};self.rubric_strokes={};self.rubric_history=[];self.rubric_future=[];self.rubric_dirty=False;self.split_mode=False;self.ref_zoom=1.0;self.ref_auto_fit=False 
        self.strokes={};self.history=[];self.future=[];self.dirty=False
        self._student_saved_once=False;self._rubric_saved_once=False
        self.rubric_saved_target=None
        self.setWindowTitle('PDF Assignment Marker')
        # A custom compact title bar permits a larger icon and name without duplication.
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # Keep the native title bar; Windows 11 can colour it without custom chrome.
        self._compact_title_colour = '#85B8DF'
        self.setWindowIcon(QIcon(app_resource('PDF_Assignment_Marker.ico')))
        self.resize(1360,860)
        self.setMinimumSize(900,620)  # Windows desktop can be resized normally
        # Background workers render nearby pages; caches retain a bounded window.
        self._render_generation = {'student': 0, 'rubric': 0}
        self._background_renderers = []
        self._page_cache_order = {'student': [], 'rubric': []}
        self._max_cached_pages = 16
        self._building_pages = {"student": False, "rubric": False}
        self._preview_pending = {"student": False, "rubric": False}
        # Short-lived scaled page previews keep fast repeated zoom operations
        # visually stable. Render exact-resolution images after zoom input settles.
        self._zoom_preview_pages = {'student': set(), 'rubric': set()}
        self._zoom_settle_timers = {}
        self.make_ui();self.add_keyboard_shortcuts();self.update_actions();self.refresh_page_navigation()
        QApplication.instance().installEventFilter(self)
        self._set_native_title_colour()
        # Prepare the emoji dialog once after the main window appears, so its
        # initial font and icon loading happens before the user opens it.
        QTimer.singleShot(0, self._preload_emoji_palette)
        self._heading_status_timer=QTimer(self)
        self._heading_status_timer.setInterval(450)
        self._heading_status_timer.timeout.connect(self._refresh_document_statuses)
        self._heading_status_timer.start()
    def _set_native_title_colour(self):
        """Colour the Windows 11 native caption; unsupported systems stay native."""
        if sys.platform != 'win32':
            return
        try:
            hwnd = int(self.winId())
            blue = ctypes.c_int(0x009F5B07)  # Windows COLORREF BGR for #075B9F
            white = ctypes.c_int(0x00FFFFFF)
            dwm = ctypes.windll.dwmapi.DwmSetWindowAttribute
            dwm(ctypes.c_void_p(hwnd), 35, ctypes.byref(blue), ctypes.sizeof(blue))
            dwm(ctypes.c_void_p(hwnd), 36, ctypes.byref(white), ctypes.sizeof(white))
        except (AttributeError, OSError, ValueError):
            pass

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self,'compact_title_bar'):
            self.compact_title_bar.sync_maximize_button()

    def nativeEvent(self, event_type, message):
        # Enable ordinary Windows edge/corner resize even with a custom caption.
        # Native system move is handled by CompactBlueTitleBar.startSystemMove.
        if sys.platform == 'win32' and str(event_type) in ('windows_generic_MSG','windows_dispatcher_MSG'):
            try:
                import ctypes
                from ctypes import wintypes
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == 0x0084 and not self.isMaximized():  # WM_NCHITTEST
                    x = ctypes.c_short(msg.lParam & 0xffff).value
                    y = ctypes.c_short((msg.lParam >> 16) & 0xffff).value
                    rect = self.frameGeometry()
                    margin = max(6, round(7 * self.devicePixelRatioF()))
                    left = x < rect.left() + margin
                    right = x >= rect.right() - margin
                    top = y < rect.top() + margin
                    bottom = y >= rect.bottom() - margin
                    hit = (13 if top and left else 14 if top and right else
                           16 if bottom and left else 17 if bottom and right else
                           12 if top else 15 if bottom else 10 if left else
                           11 if right else None)
                    if hit is not None:
                        return True, hit
            except (ValueError, OSError, AttributeError, TypeError):
                pass
        return super().nativeEvent(event_type, message)

    def _preload_emoji_palette(self):
        if not hasattr(self, 'emoji_palette'):
            self.emoji_palette=EmojiPalette(self)

    def add_keyboard_shortcuts(self):
        """Register non-conflicting app shortcuts and show them only in tooltips."""
        self._extra_shortcuts = []
        # One active-document shortcut per shared command. No legacy pane-specific bindings.
        mappings = [
            ('F1', self.show_help),
            ('Ctrl+Alt+A', self.show_about),
            ('Ctrl+Shift+V', self.show_split_view),
            ('Ctrl+W', self.close_active_pdf),
            ('Ctrl+1', self.show_single_view),
            ('Ctrl+Shift+M', self.save_combined_flat_pdf),
            ('Ctrl+Alt+G', self.show_signature_manager),
            ('Ctrl+Shift+I', self.export_active_image_pdf),
            ('Ctrl+R', self.rotate_active_cw),
            ('Ctrl+Shift+R', self.rotate_active_ccw),
        ]
        for keys, callback in mappings:
            shortcut = QShortcut(QKeySequence(keys), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(callback)
            self._extra_shortcuts.append(shortcut)

        def assign(button, keys, name):
            if button is None: return
            original = button.toolTip()
            hint = f'{name} ({keys})'
            button.setProperty('shortcutHint', hint)
            # Colour selectors and icon tools have one-line tooltips only.
            # Never append the old text as a second line.
            if button in tuple(self.pen_buttons.values()) + tuple(self.highlight_buttons.values()) or button.objectName() == 'toolButton':
                button.setToolTip(hint)
            else:
                button.setToolTip(hint + (f'\n{original}' if original and original.strip() != name else ''))

        assign(self.header_single_button, 'Ctrl+1', 'Single View')
        assign(self.header_split_button, 'Ctrl+Shift+V', 'Split View')
        assign(self.header_combine_button, 'Ctrl+Shift+M', 'Combine PDF')
        assign(self.header_sign_button, 'Ctrl+Alt+G', 'Sign')
        assign(self.help_button, 'F1', 'Help')
        assign(self.about_button, 'Ctrl+Alt+A', 'About')
        tool_keys = {
            'Move':'Alt+1','Pen':'Alt+2','Highlighter':'Alt+3','Eraser':'Alt+4',
            'Tick':'Alt+5','Cross':'Alt+6','Line':'Alt+7','Arrow':'Alt+8',
            'Text':'Alt+9','Marks':'Alt+0','Total Marks':'Ctrl+Alt+M','Emoji':'Ctrl+Alt+E'
        }
        for name,button in self.tool_buttons.items():
            keys = tool_keys[name]
            title = {'Move':'Select','Marks':'Part Marks'}.get(name,name)
            assign(button,keys,title)
            shortcut=QShortcut(QKeySequence(keys),self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(self.show_emoji_window if name == 'Emoji' else (lambda n=name: self.select_tool(n)))
            self._extra_shortcuts.append(shortcut)
        for index,color in enumerate(INKS):
            keys=f'Ctrl+Shift+{index+1}'
            name=['Black','Blue','Red','Green'][index]
            assign(self.pen_buttons[color], keys, name + ' pen colour')
            shortcut=QShortcut(QKeySequence(keys),self)
            shortcut.activated.connect(lambda c=color: self.set_pen_color(c))
            self._extra_shortcuts.append(shortcut)
        for index,color in enumerate(HIGHLIGHTS):
            keys=f'Ctrl+Shift+{index+5}'
            name=['Yellow','Green','Pink','Light blue'][index]
            assign(self.highlight_buttons[color],keys,name + ' highlighter colour')
            shortcut=QShortcut(QKeySequence(keys),self)
            shortcut.activated.connect(lambda c=color: self.set_highlight_color(c))
            self._extra_shortcuts.append(shortcut)

        # Approved top-ribbon tooltip format: one single line, shortcut once.
        # Shortcuts are bound above or by the existing active-PDF QActions.
        ribbon_tips = {
            'Open PDF': 'Open (Ctrl+O)',
            'Close': 'Close (Ctrl+W)',
            'Save': 'Save (Ctrl+S)',
            'Save As': 'Save As (Ctrl+Shift+S)',
            'Undo': 'Undo (Ctrl+Z)',
            'Redo': 'Redo (Ctrl+Y)',
            '−': 'Zoom Out',
            '+': 'Zoom In',
        }
        for name, tip in ribbon_tips.items():
            self.shared_header_buttons[name].setToolTip(tip)
        self.header_single_button.setToolTip('Single View (Ctrl+1)')
        self.header_split_button.setToolTip('Split View (Ctrl+Shift+V)')
        # Commands without an advertised shortcut have just their names.
        for widget, tip in (
            (self.thumbnail_toggle, 'Pages'),
            (self.shared_header_buttons['Image PDF'], 'Image PDF'),
            (self.header_combine_button, 'Combine PDF'),
            (self.shared_header_buttons['↻'], 'Rotate CW'),
            (self.shared_header_buttons['↺'], 'Rotate CCW'),
            (self.header_sign_button, 'Sign'),
        ):
            widget.setToolTip(tip)

    @staticmethod
    def _utility_icon(kind):
        """Blue versions of the existing About/Help icons for a pale ribbon."""
        svg_inner = ("<circle cx='12' cy='12' r='9'/><circle cx='12' cy='7.5' r='1' "
                     "fill='#0769bc' stroke='none'/><path d='M12 11v6'/>") if kind == 'about' else (
                     "<circle cx='12' cy='12' r='9'/><path d='M9.4 9a2.7 2.7 0 0 1 5.2 1.1c0 1.8-2.6 2.3-2.6 4'/>"
                     "<circle cx='12' cy='17.6' r='1' fill='#0769bc' stroke='none'/>")
        svg = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
               "<g fill='none' stroke='#0769bc' stroke-width='1.8' stroke-linecap='round' "
               f"stroke-linejoin='round'>{svg_inner}</g></svg>")
        pix = QPixmap(24,24)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(painter)
        painter.end()
        return QIcon(pix)

    def make_ui(self):
        base=QWidget();self.setCentralWidget(base)
        root=QVBoxLayout(base);root.setContentsMargins(0,0,0,0);root.setSpacing(0)
        header=QFrame(objectName='header');hl=QHBoxLayout(header);hl.setContentsMargins(10,9,10,9)
        # Match icon height to the title-and-subtitle group; no other header changes.
        header_app_icon=QLabel()
        header_app_icon.setObjectName('headerApplicationIcon')
        header_app_icon.setFixedSize(40,40)
        header_app_icon.setPixmap(QIcon(app_resource('PDF_Assignment_Marker.ico')).pixmap(QSize(40,40)))
        header_app_icon.setToolTip('PDF Assignment Marker')
        hl.addWidget(header_app_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        hl.addSpacing(10)
        brand=QVBoxLayout();brand.setSpacing(0)
        t=QLabel('PDF Assignment Marker',objectName='brand');brand.addWidget(t)
        brand.addWidget(QLabel('Read, Write, Mark and Save PDF Documents',objectName='tagline'))
        hl.addLayout(brand)
        # Keep branding and About / Help in the original blue banner.
        hl.addStretch(1)
        # Option B: separate white information/help SVG icons with compact white labels.
        about_button=QPushButton('About')
        about_button.setObjectName('headerInfoButton')
        about_button.setIcon(header_info_icon('about'))
        about_button.setIconSize(QSize(21,21))
        about_button.setCursor(Qt.CursorShape.PointingHandCursor)
        about_button.setFixedSize(98,34)
        about_button.setToolTip('About PDF Assignment Marker (Ctrl+Alt+A)')
        about_button.clicked.connect(self.show_about)
        self.about_button=about_button
        hl.addWidget(about_button)
        header_sep=QFrame(objectName='headerInfoDivider')
        header_sep.setFixedSize(1,20)
        hl.addWidget(header_sep)
        help_button=QPushButton('Help')
        help_button.setObjectName('headerInfoButton')
        help_button.setIcon(header_info_icon('help'))
        help_button.setIconSize(QSize(21,21))
        help_button.setCursor(Qt.CursorShape.PointingHandCursor)
        help_button.setFixedSize(88,34)
        help_button.setToolTip('Open the application user guide (F1)')
        help_button.clicked.connect(self.show_help)
        self.help_button=help_button
        hl.addWidget(help_button)
        self.header_frame=header
        header.installEventFilter(self)
        # The redundant 59px blue application banner is intentionally not shown.
        # The compact 40px light-blue title has a 30px icon and bold 19px name.
        self.compact_title_bar = CompactBlueTitleBar(self)
        root.addWidget(self.compact_title_bar)


        # Compact, grouped hybrid document ribbon.  Commands continue routing
        # through the existing active-document methods; no PDF logic changes.
        document_ribbon=QFrame(objectName='documentRibbon')
        dr=QHBoxLayout(document_ribbon)
        dr.setContentsMargins(8,2,8,2)
        dr.setSpacing(2)
        self.shared_header_buttons={}
        self.top_buttons={}

        def separator():
            line=QFrame(document_ribbon)
            line.setObjectName('ribbonDivider')
            line.setFrameShape(QFrame.Shape.VLine)
            line.setFixedWidth(1)
            line.setFixedHeight(26)
            dr.addSpacing(5)
            dr.addWidget(line,0,Qt.AlignmentFlag.AlignVCenter)
            dr.addSpacing(5)

        def ribbon_button(key, caption, tooltip, callback, icon_name=None, width=59):
            button=QPushButton(document_ribbon)
            button.setObjectName('hybridRibbonButton')
            button.setFixedSize(36,34)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setToolTip(tooltip)
            # Render the original SVG paths directly at the display's pixel
            # density.  The earlier 26px -> 23px pixmap downscale softened lines.
            icon_key=icon_name or key
            icon_colour=ICON_COLOURS.get(icon_key, '#0769bc')
            icon_path=ICON_PATHS.get(icon_key, ICON_PATHS['Pen']).replace('currentColor',icon_colour)
            icon_svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
                      f'<g fill="none" stroke="{icon_colour}" stroke-width="2.1" '
                      f'stroke-linecap="round" stroke-linejoin="round">{icon_path}</g></svg>')
            # Keep the original 23px icon dimensions, but rasterize the SVG at
            # high DPI for sharp rendering on both ordinary and scaled displays.
            icon_px=23
            dpr=max(1.0, min(4.0, float(button.devicePixelRatioF())))
            raw_px=round(icon_px*dpr)
            icon_pix=QPixmap(raw_px,raw_px)
            icon_pix.fill(Qt.GlobalColor.transparent)
            painter=QPainter(icon_pix)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
            QSvgRenderer(QByteArray(icon_svg.encode('utf-8'))).render(painter)
            painter.end()
            icon_pix.setDevicePixelRatio(dpr)

            # Fixed layout, matching the vertical ribbon's dedicated caption:
            # explicit Segoe UI 9 *pixel* font, not points or inherited size.
            picture=QLabel(button)
            picture.setObjectName('hybridRibbonIcon')
            picture.setGeometry(1,4,34,26)
            picture.setPixmap(icon_pix)
            picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
            picture.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            caption_label=QLabel(caption,button)
            caption_label.setObjectName('hybridRibbonCaption')
            caption_label.setGeometry(1,30,34,0)
            caption_label.hide()  # Hover tooltip supplies its name and shortcut.
            caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            caption_font=QFont('Segoe UI')
            caption_font.setBold(False)
            caption_font.setPixelSize(9)
            caption_label.setFont(caption_font)
            # A direct QLabel stylesheet enforces the identical visual text
            # colour as vertical toolCaption without overriding the font size.
            caption_label.setStyleSheet('QLabel#hybridRibbonCaption {background:transparent; border:none; color:#174c81; padding:0px;}')
            button.clicked.connect(callback)
            dr.addWidget(button)
            return button

        # Thumbnails: exactly the same vector icon / separate 9px caption
        # architecture as the rest of the approved horizontal ribbon.
        self.thumbnail_toggle = ribbon_button(
            'Thumbnails', 'Pages',
            'Show or hide page thumbnails (Single View only)',
            self.toggle_page_thumbnails, 'Thumbnails', 59)
        self.thumbnail_toggle.setObjectName('thumbnailToggle')
        self._thumbnail_icon_label = self.thumbnail_toggle.findChild(QLabel, 'hybridRibbonIcon')
        self._thumbnail_caption_label = self.thumbnail_toggle.findChild(QLabel, 'hybridRibbonCaption')
        self._thumbnail_grey_effect = QGraphicsColorizeEffect(self._thumbnail_icon_label)
        self._thumbnail_grey_effect.setColor(QColor('#a0a6ae'))
        self._thumbnail_grey_effect.setStrength(0.0)
        self._thumbnail_icon_label.setGraphicsEffect(self._thumbnail_grey_effect)
        # The Pages control is unavailable until a PDF is loaded in Single View.
        self._set_thumbnail_toggle_enabled(False)
        separator()
        # Open / Close group
        self.shared_header_buttons['Open PDF']=ribbon_button(
            'Open PDF','Open','Open a PDF in the active pane',self.open_active_pdf,'Open PDF',60)
        self.shared_header_buttons['Close']=ribbon_button(
            'Close','Close','Close the active PDF',self.close_active_pdf,'Close',55)
        separator()
        # Save / export / combine group
        for label,caption,tip,method,ico,w in (
            ('Save','Save','Save active PDF',self.save_active_pdf,'Save',53),
            ('Save As','Save As','Save active PDF to a new filename',self.save_active_as,'Save As',61),
            ('Image PDF','Image PDF','Export active PDF as a flattened image PDF',self.export_active_image_pdf,'Image PDF',70),
        ):
            self.shared_header_buttons[label]=ribbon_button(label,caption,tip,method,ico,w)
        combine_button=ribbon_button(
            'Combine PDF','Combine PDF','Combine the two documents into one image PDF',
            self.save_combined_flat_pdf,'Combine PDF',83)
        self.header_combine_button=combine_button
        self.top_buttons['Combine PDF']=combine_button
        separator()
        # Undo / redo group
        for label,tip,method in (
            ('Undo','Undo in the active PDF',self.undo_active_pdf),
            ('Redo','Redo in the active PDF',self.redo_active_pdf),
        ):
            self.shared_header_buttons[label]=ribbon_button(label,label,tip,method,label,55)
        separator()
        # Rotation group
        self.shared_header_buttons['↻']=ribbon_button('↻','Rotate CW','Rotate active page clockwise',self.rotate_active_cw,'Rotate CW',68)
        self.shared_header_buttons['↺']=ribbon_button('↺','Rotate CCW','Rotate active page counterclockwise',self.rotate_active_ccw,'Rotate CCW',68)
        separator()
        # Zoom group (existing zoom-percentage readout kept between buttons)
        self.shared_header_buttons['−']=ribbon_button('−','Zoom −','Zoom out active PDF',self.zoom_active_out,'Zoom Out',59)
        self.shared_zoom_label=QLabel('100%',document_ribbon)
        self.shared_zoom_label.setObjectName('ribbonZoomLabel')
        zoom_font=QFont('Segoe UI')
        zoom_font.setBold(False)
        zoom_font.setPixelSize(9)
        self.shared_zoom_label.setFont(zoom_font)
        self.shared_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.shared_zoom_label.setFixedWidth(49)
        dr.addWidget(self.shared_zoom_label)
        self.shared_header_buttons['+']=ribbon_button('+','Zoom +','Zoom in active PDF',self.zoom_active_in,'Zoom In',59)
        separator()
        # View group
        single_button=ribbon_button('Single View','Single View','Show only the active document',self.show_single_view,'Single View',76)
        self.header_single_button=single_button
        self.top_buttons['Single View']=single_button
        split_button=ribbon_button('Split View','Split View','Show both documents',self.show_split_view,'Split View',76)
        self.header_split_button=split_button
        self.top_buttons['Split View']=split_button
        separator()
        # Signature group
        sign_button=ribbon_button('Sign','Sign','Manage signatures (Ctrl+Alt+G)',self.show_signature_manager,'Sign',52)
        self.header_sign_button=sign_button
        self.top_buttons['Sign']=sign_button
        dr.addStretch(1)
        for utility, kind in ((self.about_button, 'about'), (self.help_button, 'help')):
            utility.setParent(document_ribbon)
            utility.setObjectName('ribbonUtilityButton')
            utility.setText('')
            utility.setIcon(self._utility_icon(kind))
            utility.setIconSize(QSize(19,19))
            utility.setFixedSize(33,32)
            dr.addWidget(utility, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addWidget(document_ribbon)
        split=QSplitter(Qt.Orientation.Horizontal);split.setChildrenCollapsible(False)
        split.setHandleWidth(1)  # nearly invisible, non-draggable separator
        left=QFrame(objectName='thumbnailSide');self.pages_panel=left;ll=QVBoxLayout(left);ll.setContentsMargins(8,9,8,8)
        pages_heading = QLabel('Pages', objectName='sideTitle')
        pages_heading.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        pages_heading.setStyleSheet('font-weight: 400;')
        ll.addWidget(pages_heading)
        self.thumb_list=QListWidget();self.thumb_list.setObjectName('thumbnails');self.thumb_list.setIconSize(QSize(88,116))
        self.thumb_list.setSpacing(6)
        # Icon mode places the page number *under* each preview, not alongside it.
        self.thumb_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumb_list.setFlow(QListWidget.Flow.TopToBottom)
        self.thumb_list.setWrapping(False)
        self.thumb_list.setResizeMode(QListWidget.ResizeMode.Fixed)
        self.thumb_list.setGridSize(QSize(128, 160))
        self.thumb_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.thumb_list.currentRowChanged.connect(self._thumbnail_page_selected)
        ll.addWidget(self.thumb_list);split.addWidget(left)
        left.setFixedWidth(154)
        left.hide()  # Hidden by default; only Single View can expand it.
        self._thumbnails_open = False
        self._thumb_generation = 0
        self._thumb_cache = {}
        self._thumb_side = None
        mid=QFrame(objectName='workspace');self.student_workspace=mid;ml=QVBoxLayout(mid);ml.setContentsMargins(3,2,3,0)
        self.student_title=FileNameLabel('Document 2');self.student_title.setObjectName('compactFilenameLink')
        self.student_title.clicked.connect(lambda: self._show_pdf_in_explorer('student'))
        self.student_document_id=QLabel('Document 2')
        self.student_path_label=QLabel('Document 2')
        self._setup_document_heading(ml,self.student_title,self.student_document_id,self.student_path_label)
        student_controls=QHBoxLayout();student_controls.setSpacing(4)
        self.student_file_buttons={}
        for label,callback in (
            ('Open PDF',self.open_pdf),('Save',self.save_pdf),
            ('Save As',self.save_as),('Image PDF',self.export_image_pdf)):
            button=QPushButton(label)
            button.setObjectName('documentFileButton')
            button.setToolTip({
                'Open PDF':'Open a student assignment or examination paper',
                'Save':'Save a marked copy of the student PDF',
                'Save As':'Save markings to a different PDF filename',
                'Image PDF':'Export the marked paper as a flattened, image-only PDF'
            }[label])
            button.clicked.connect(callback)
            if label == 'Open PDF': student_controls.addWidget(button)
            self.student_file_buttons[label]=button
        # Student-only actions live beside Open/Save and are no longer in the global toolbar.
        self.student_action_buttons={}
        for label, icon_name, callback in (
            ('Undo', 'Undo', self.undo),
            ('Redo', 'Redo', self.redo),
            ('Rotate CW', 'Rotate', self.rotate_page),
            ('Rotate CCW', 'Rotate', self.rotate_page_counterclockwise),
        ):
            button=QPushButton('↻' if label == 'Rotate CW' else '↺' if label == 'Rotate CCW' else label)
            button.setObjectName('documentFileButton')
            if label.startswith('Rotate '):
                button.setProperty('rotationIcon', True)
            button.setToolTip({'Undo':'Undo the last student-paper marking',
                               'Redo':'Redo the last undone marking',
                               'Rotate CW':'Rotate the current student PDF page 90° clockwise',
                               'Rotate CCW':'Rotate the current student PDF page 90° counterclockwise'}[label])
            button.clicked.connect(callback)
            if not label.startswith('Rotate ' ): student_controls.addWidget(button)
            self.student_action_buttons[label]=button
        student_controls.addStretch(1)
        # Shared zoom is displayed in the blue header.
        self.student_zoom_out=QPushButton('−');self.student_zoom_out.setToolTip('Zoom out student paper')
        self.student_zoom_out.clicked.connect(lambda:self.scale_zoom(1/1.2))
        self.student_zoom_label=QLabel('100%');self.student_zoom_label.setFixedWidth(42)
        self.student_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.student_zoom_in=QPushButton('+');self.student_zoom_in.setToolTip('Zoom in student paper')
        self.student_zoom_in.clicked.connect(lambda:self.scale_zoom(1.2))
        # Match the rubric's compact Close button in the student-document toolbar.
        self.student_close=QPushButton('×')
        self.student_close.setToolTip('Close student PDF (leave rubric open)')
        self.student_close.setFixedWidth(24)
        self.student_close.clicked.connect(self.close_student_pdf)
        student_controls.addWidget(self.student_close)
        # Old document control row is retired; controls are now in the shared header.
        # Keep the underlying buttons for existing action/state/shortcut logic.
        # A single compact status strip contains both document identity and navigation.
        student_nav_bar=QFrame(objectName='compactDocumentStatus')
        student_nav_bar.setFixedHeight(29)
        student_nav_bar.setMinimumWidth(0)
        student_nav_bar.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        student_pages=QHBoxLayout(student_nav_bar)
        student_pages.setContentsMargins(8,1,8,1)
        student_pages.setSpacing(4)
        self.student_title.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        student_pages.addWidget(self.student_title,1)
        student_pages.addWidget(self.student_document_id,0)
        self.student_path_label.hide()
        self.student_page_previous=QPushButton('◀')
        self.student_page_previous.setObjectName('compactPageButton')
        self.student_page_previous.setFixedSize(25,23)
        self.student_page_previous.setToolTip('Previous page (Page Up)')
        self.student_page_previous.clicked.connect(lambda:self.navigate(-1))
        student_pages.addWidget(self.student_page_previous)
        self.student_page_number=QLineEdit('0')
        self.student_page_number.setObjectName('compactPageEdit')
        self.student_page_number.setFixedSize(38,23)
        self.student_page_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.student_page_number.setToolTip('Type a page number and press Enter')
        self.student_page_number.returnPressed.connect(lambda:self.jump_to_page_entry('student'))
        self.student_page_number.editingFinished.connect(lambda:self.restore_page_entry('student'))
        student_pages.addWidget(self.student_page_number)
        self.student_page_count=QLabel('/ 0',objectName='pageNavigationText')
        student_pages.addWidget(self.student_page_count)
        self.student_page_next=QPushButton('▶')
        self.student_page_next.setObjectName('compactPageButton')
        self.student_page_next.setFixedSize(25,23)
        self.student_page_next.setToolTip('Next page (Page Down)')
        self.student_page_next.clicked.connect(lambda:self.navigate(1))
        student_pages.addWidget(self.student_page_next)
        self.scroll=QScrollArea();self.scroll.setObjectName('pageArea');self.scroll.setWidgetResizable(False)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        self.student_stack=QWidget()
        self.student_stack_layout=QVBoxLayout(self.student_stack)
        self.student_stack_layout.setContentsMargins(12,12,12,12)
        self.student_stack_layout.setSpacing(16)
        self.student_pages=[]
        self.canvas=PageCanvas(self,0);self.canvas.setStyleSheet('background:white;')
        self.student_stack_layout.addWidget(self.canvas,0,Qt.AlignmentFlag.AlignHCenter)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.student_stack);ml.addWidget(self.scroll)
        self.scroll.viewport().installEventFilter(self)
        self.scroll.verticalScrollBar().valueChanged.connect(self.sync_student_scroll)
        split.addWidget(mid)
        right=QScrollArea();right.setObjectName('toolsScroll');right.setWidgetResizable(True)
        right.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        right.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # retain wheel scrolling without the dark vertical bar
        right.setFixedWidth(44)  # slim 44px tool strip; 36px tool tiles unchanged
        self.marking_tools_panel=right
        right_inner=QFrame(objectName='toolsInner')
        rl=QVBoxLayout(right_inner);rl.setContentsMargins(2,8,2,8);rl.setSpacing(2)
        rl.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.tool_buttons={};self.highlight_buttons={}
        # Only icons: labels remain available through hover tooltips.  A subtle
        # separator preserves grouping without wasting the narrow width.
        for name,symbol in [('Move','↖'),('Pen','✎'),('Highlighter','▰'),('Eraser','⌫')]:
            b=self.mark_button(symbol,name)
            b.clicked.connect(lambda checked,n=name:self.select_tool(n))
            b.mouseDoubleClickEvent=lambda event,n=name:self.show_tool_settings(n)
            rl.addWidget(b._caption_tile,0,Qt.AlignmentFlag.AlignHCenter)
            self.tool_buttons[name]=b
        section_line=QFrame()
        section_line.setFrameShape(QFrame.Shape.HLine)
        section_line.setFixedHeight(1)
        section_line.setStyleSheet('background:#b8cde6;border:none;')
        section_line.setToolTip('Stamps and Comments')
        rl.addSpacing(3);rl.addWidget(section_line);rl.addSpacing(3)
        for name,symbol in [('Tick','✓'),('Cross','✗'),('Line','╱'),('Arrow','➜'),('Text','T'),('Marks','123'),('Total Marks','Σ'),('Emoji','☺')]:
            b=self.mark_button(symbol,name)
            b.clicked.connect((lambda checked:self.show_emoji_window()) if name=='Emoji' else (lambda checked,n=name:self.select_tool(n)))
            b.mouseDoubleClickEvent=(lambda event:self.show_emoji_window()) if name=='Emoji' else (lambda event,n=name:self.show_tool_settings(n))
            rl.addWidget(b._caption_tile,0,Qt.AlignmentFlag.AlignHCenter)
            self.tool_buttons[name]=b
        # Original settings widgets are constructed below, but their group is hidden
        # in the compact experiment; controls are exposed in a floating dialog.
        original_settings=QWidget()
        settings_layout=QVBoxLayout(original_settings)
        settings_layout.setContentsMargins(0,0,0,0)
        rl.addWidget(original_settings)
        rl= settings_layout
        rl.addSpacing(9)  # clear separation before the first settings label
        rl.addWidget(QLabel('Tick Size',objectName='sectionTitle'))
        self.stamp_slider=self.labeled_slider(rl,12,18,14,self.set_stamp_size,'px')
        rl.addWidget(QLabel('Cross Size',objectName='sectionTitle'))
        self.cross_slider=self.labeled_slider(rl,8,18,14,self.set_cross_size,'px')
        rl.addWidget(QLabel('Emoji Size',objectName='sectionTitle'))
        self.emoji_slider=self.labeled_slider(rl,8,18,14,self.set_emoji_size,'px')
        self.select_tool('Move')
        rl.addWidget(QLabel('Tool Settings',objectName='groupTitle'))
        rl.addWidget(QLabel('Pen Colour',objectName='sectionTitle'))
        inkrow=QHBoxLayout();inkrow.setSpacing(0);self.pen_buttons={}
        for color in INKS:
            if inkrow.count():inkrow.addStretch(1)
            b=self.color_button(color,lambda checked=False,c=color:self.set_pen_color(c));inkrow.addWidget(b);self.pen_buttons[color]=b
        rl.addLayout(inkrow)
        self.selected_color_label=QLabel('Selected: Red')
        self.selected_color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.selected_color_label.setStyleSheet('color:#ed2024;font-weight:700;font-size:11px;')
        rl.addWidget(self.selected_color_label)
        self.refresh_color_buttons()
        rl.addWidget(QLabel('Pen Size',objectName='sectionTitle'))
        # Integer slider positions 1–4 correspond to 0.5, 1, 1.5 and 2 px.
        self.pen_slider=self.labeled_slider(rl,1,4,2,self.set_pen_size,'px')
        self.pen_slider.setSingleStep(1)
        self.pen_slider.setPageStep(1)
        self.pen_slider.valueChanged.connect(self.update_pen_size_label)
        self.update_pen_size_label(self.pen_slider.value())
        rl.addWidget(QLabel('Highlighter Colour',objectName='sectionTitle'))
        hirow=QHBoxLayout();hirow.setSpacing(0)
        for color in HIGHLIGHTS:
            if hirow.count():hirow.addStretch(1)
            b=self.color_button(color,lambda checked=False,c=color:self.set_highlight_color(c));hirow.addWidget(b);self.highlight_buttons[color]=b
        rl.addLayout(hirow)
        self.refresh_color_buttons()
        rl.addWidget(QLabel('Highlighter Size',objectName='sectionTitle'))
        self.highlighter_slider=self.labeled_slider(rl,8,14,8,self.set_highlighter_size,'px')
        rl.addWidget(QLabel('Opacity',objectName='sectionTitle'))
        self.opacity_slider=self.labeled_slider(rl,10,85,40,self.set_opacity,'%')
        rl.addWidget(QLabel('Eraser Size',objectName='sectionTitle'))
        self.eraser_slider=self.labeled_slider(rl,12,18,14,self.set_eraser_size,'px')
        rl.addWidget(QLabel('Text / Marks Size',objectName='sectionTitle'))
        self.text_slider=self.labeled_slider(rl,8,14,9,self.set_text_size,'px')
        rl.addWidget(QLabel('MARKS TOTALS',objectName='groupTitle'))
        total_style = ('font-size:14px;font-weight:700;color:#075294;'
                       'background:#e1f0ff;border-radius:5px;padding:8px 3px;')
        self.marks_total_label=QLabel('Assignment: 0')
        self.marks_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.marks_total_label.setStyleSheet(total_style)
        self.marks_total_label.setToolTip('Total Part Marks entered on the student assignment')
        rl.addWidget(self.marks_total_label)
        self.rubric_total_label=QLabel('Rubric: 0')
        self.rubric_total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rubric_total_label.setStyleSheet(total_style)
        self.rubric_total_label.setToolTip('Total Part Marks entered on the rubric')
        rl.addWidget(self.rubric_total_label)
        rl.addStretch(1)
        # Centre every heading within the marking tools panel, including
        # category headings and size/colour control labels.
        for heading in right_inner.findChildren(QLabel):
            if heading.objectName() in ('sideTitle', 'groupTitle', 'sectionTitle'):
                heading.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        original_settings.hide()
        right.setWidget(right_inner)
        right_inner.setMinimumHeight(0)
        split.addWidget(right)
        # Hidden independent PDF reference viewer for rubric or marking scheme.
        self.reference_panel=QFrame(objectName='workspace')
        ref_layout=QVBoxLayout(self.reference_panel);ref_layout.setContentsMargins(3,2,3,0);ref_layout.setSpacing(0)
        ref_title=FileNameLabel('Document 1');ref_title.setObjectName('compactFilenameLink');self.rubric_title=ref_title
        ref_title.clicked.connect(lambda: self._show_pdf_in_explorer('rubric'))
        self.rubric_document_id=QLabel('Document 1')
        self.rubric_path_label=QLabel('Document 1')
        self._setup_document_heading(ref_layout,ref_title,self.rubric_document_id,self.rubric_path_label)
        # Mirror the student toolbar so both document areas feel the same.
        rubric_controls=QHBoxLayout();rubric_controls.setSpacing(4)
        self.ref_file_buttons={}
        for label,callback in (
            ('Open PDF',self.open_rubric),('Save',self.save_rubric),
            ('Save As',self.save_rubric),('Image PDF',self.export_rubric_image_pdf)):
            button=QPushButton(label)
            button.setObjectName('documentFileButton')
            button.setToolTip({
                'Open PDF':'Open a marking scheme or rubric PDF',
                'Save':'Save a marked copy of the rubric PDF',
                'Save As':'Save rubric markings to a different PDF filename',
                'Image PDF':'Export the rubric as a flattened, image-only PDF'
            }[label])
            button.clicked.connect(callback)
            if label == 'Open PDF': rubric_controls.addWidget(button)
            self.ref_file_buttons[label]=button
        self.ref_action_buttons={}
        for label, callback in (
            ('Undo', self.undo_rubric),
            ('Redo', self.redo_rubric),
            ('Rotate CW', self.rotate_rubric_page),
            ('Rotate CCW', self.rotate_rubric_page_counterclockwise),
        ):
            button=QPushButton('↻' if label == 'Rotate CW' else '↺' if label == 'Rotate CCW' else label)
            button.setObjectName('documentFileButton')
            if label.startswith('Rotate '):
                button.setProperty('rotationIcon', True)
            button.setToolTip({'Undo':'Undo the last rubric-side marking',
                               'Redo':'Redo the last undone rubric-side marking',
                               'Rotate CW':'Rotate the current rubric page 90° clockwise',
                               'Rotate CCW':'Rotate the current rubric page 90° counterclockwise'}[label])
            button.clicked.connect(callback)
            if not label.startswith('Rotate '): rubric_controls.addWidget(button)
            self.ref_action_buttons[label]=button
        rubric_controls.addStretch(1)
        # Shared zoom is displayed in the blue header.
        self.ref_zoom_out=QPushButton('−');self.ref_zoom_out.setToolTip('Zoom out marking scheme')
        self.ref_zoom_out.clicked.connect(lambda:self.scale_rubric_zoom(1/1.2))
        self.ref_zoom_label=QLabel('100%');self.ref_zoom_label.setFixedWidth(42)
        self.ref_zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ref_zoom_in=QPushButton('+');self.ref_zoom_in.setToolTip('Zoom in marking scheme')
        self.ref_zoom_in.clicked.connect(lambda:self.scale_rubric_zoom(1.2))
        self.ref_close=QPushButton('×')
        self.ref_close.setToolTip('Close reference PDF')
        self.ref_close.setFixedWidth(24)
        self.ref_close.clicked.connect(self.close_rubric)
        rubric_controls.addWidget(self.ref_close)
        # Old rubric control row is retired; shared header controls route by active pane.
        rubric_nav_bar=QFrame(objectName='compactDocumentStatus')
        rubric_nav_bar.setFixedHeight(29)
        rubric_nav_bar.setMinimumWidth(0)
        rubric_nav_bar.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
        rubric_pages=QHBoxLayout(rubric_nav_bar)
        rubric_pages.setContentsMargins(8,1,8,1)
        rubric_pages.setSpacing(4)
        self.rubric_title.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        rubric_pages.addWidget(self.rubric_title,1)
        rubric_pages.addWidget(self.rubric_document_id,0)
        self.rubric_path_label.hide()
        self.rubric_page_previous=QPushButton('◀')
        self.rubric_page_previous.setObjectName('compactPageButton')
        self.rubric_page_previous.setFixedSize(25,23)
        self.rubric_page_previous.setToolTip('Previous page (Page Up)')
        self.rubric_page_previous.clicked.connect(lambda:self.navigate_rubric(-1))
        rubric_pages.addWidget(self.rubric_page_previous)
        self.rubric_page_number=QLineEdit('0')
        self.rubric_page_number.setObjectName('compactPageEdit')
        self.rubric_page_number.setFixedSize(38,23)
        self.rubric_page_number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rubric_page_number.setToolTip('Type a page number and press Enter')
        self.rubric_page_number.returnPressed.connect(lambda:self.jump_to_page_entry('rubric'))
        self.rubric_page_number.editingFinished.connect(lambda:self.restore_page_entry('rubric'))
        rubric_pages.addWidget(self.rubric_page_number)
        self.rubric_page_count=QLabel('/ 0',objectName='pageNavigationText')
        rubric_pages.addWidget(self.rubric_page_count)
        self.rubric_page_next=QPushButton('▶')
        self.rubric_page_next.setObjectName('compactPageButton')
        self.rubric_page_next.setFixedSize(25,23)
        self.rubric_page_next.setToolTip('Next page (Page Down)')
        self.rubric_page_next.clicked.connect(lambda:self.navigate_rubric(1))
        rubric_pages.addWidget(self.rubric_page_next)
        self.ref_scroll=QScrollArea();self.ref_scroll.setObjectName('pageArea');self.ref_scroll.setWidgetResizable(False)
        self.ref_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ref_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.ref_scroll.setAlignment(Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)
        self.rubric_stack=QWidget()
        self.rubric_stack_layout=QVBoxLayout(self.rubric_stack)
        self.rubric_stack_layout.setContentsMargins(12,12,12,12)
        self.rubric_stack_layout.setSpacing(16)
        self.rubric_pages=[]
        self.rubric_path=None
        self._update_document_heading('rubric')
        self.ref_image=RubricCanvas(self,0)
        self.rubric_stack_layout.addWidget(self.ref_image,0,Qt.AlignmentFlag.AlignHCenter)
        self.ref_scroll.setWidgetResizable(True)
        self.ref_scroll.setWidget(self.rubric_stack);ref_layout.addWidget(self.ref_scroll,1)
        # Layout regression test: oversized PDF pages must remain inside their
        # own scrolling viewport, never expanding one Split View workspace.
        for workspace, scroll_area in ((self.reference_panel, self.ref_scroll),
                                       (self.student_workspace, self.scroll)):
            workspace.setMinimumWidth(0)
            workspace.setSizePolicy(QSizePolicy.Policy.Ignored,
                                    QSizePolicy.Policy.Expanding)
            scroll_area.setMinimumWidth(0)
            scroll_area.setSizePolicy(QSizePolicy.Policy.Ignored,
                                      QSizePolicy.Policy.Expanding)
        for page_stack in (self.rubric_stack, self.student_stack):
            page_stack.setMinimumWidth(0)
            page_stack.setSizePolicy(QSizePolicy.Policy.Ignored,
                                     QSizePolicy.Policy.Preferred)
        self.ref_scroll.viewport().installEventFilter(self)
        self.ref_scroll.verticalScrollBar().valueChanged.connect(self.sync_rubric_scroll)
        split.addWidget(self.reference_panel)
        # In single-page mode, Document 1 is the sole visible document.
        split.insertWidget(1, self.reference_panel)
        split.insertWidget(2, self.marking_tools_panel)
        self.student_workspace.hide()
        self.reference_panel.show()
        split.setSizes([0,1015,44,0]);root.addWidget(split,1)
        self.split=split
        self.bottom_status_row=QFrame(objectName='compactStatusRow')
        bottom_layout=QHBoxLayout(self.bottom_status_row)
        bottom_layout.setContentsMargins(0,0,0,0)
        bottom_layout.setSpacing(0)
        self.bottom_thumb_spacer=QWidget()
        self.bottom_rubric_nav=rubric_nav_bar
        self.bottom_student_nav=student_nav_bar
        self.bottom_tools_spacer=QWidget()
        for widget in (self.bottom_thumb_spacer,self.bottom_rubric_nav,
                       self.bottom_tools_spacer,self.bottom_student_nav):
            bottom_layout.addWidget(widget)
        root.addWidget(self.bottom_status_row)
        self._sync_bottom_status_layout()
        self.split.splitterMoved.connect(self.on_splitter_moved)
        self._create_active_pdf_borders()
        self._update_document_heading('rubric')
        self._update_document_heading('student')
        self.lock_centre_panel()
        QTimer.singleShot(0, self.position_single_page_ribbon)
        self.setStatusBar(CompactNotificationBar(self))
        self.setStyleSheet('''
            QWidget {font-family: 'Segoe UI',Arial; font-size: 12px; color:#102a49;}
            QFrame#header {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #075294,stop:1 #087ccc);}
            QLabel#brand {font-size:26px;font-weight:700;color:white;}
            QLabel#tagline {color:#e1effd;font-size:12px;}
            QFrame#toolbar {background:#f7f9fc;border-bottom:1px solid #d2dbe7;}
            QFrame#compactBlueTitleBar {background:#85B8DF;border:0;}
            QLabel#compactBlueTitleText {color:#173A5A;background:transparent;border:0;font-family:'Segoe UI';font-size:16px;font-weight:400;}
            QPushButton#compactTitleControl,QPushButton#compactTitleClose {
                border:none;border-radius:0;background:transparent;color:#173A5A;
                font-family:'Segoe UI Symbol';font-size:20px;padding:0;
            }
            QPushButton#compactTitleControl:hover {background:#72A9D2;}
            QPushButton#compactTitleClose:hover {background:#d52b36;}
            QPushButton#compactTitleControl:pressed {background:#3887bf;}
            QPushButton#compactTitleClose:pressed {background:#ba2031;}
            QFrame#documentRibbon {background:#eef1f4;border-bottom:1px solid #cbd3dc;}
            QPushButton#thumbnailToggle {background:transparent;border:1px solid transparent;border-radius:5px;padding:0;}
            QPushButton#thumbnailToggle:hover:enabled {background:white;border-color:#a7c6e7;}
            QPushButton#thumbnailToggle:disabled {background:transparent;border:1px solid transparent;}
            QFrame#ribbonDivider {background:#c1cbd7;border:0;}
            QPushButton#hybridRibbonButton {background:transparent;border:1px solid transparent;border-radius:5px;padding:0;color:#125b99;}
            QPushButton#hybridRibbonButton:hover {background:#ffffff;border-color:#a7c6e7;}
            QPushButton#hybridRibbonButton:pressed {background:#d5e8f8;}
            QPushButton#hybridRibbonButton:disabled {background:transparent;border-color:transparent;}
            QLabel#hybridRibbonIcon {background:transparent;border:none;}
            QLabel#hybridRibbonCaption {background:transparent;border:none;color:#174c81;padding:0px;}
            QLabel#ribbonZoomLabel {color:#174c81;font-family:"Segoe UI";font-size:9px;font-weight:400;}
            QFrame#compactStatusRow, QFrame#compactDocumentStatus {background:#eef1f4;border:none;}
            QPushButton#compactPageButton {background:transparent;border:1px solid #d0d9e5;border-radius:3px;color:#174c81;padding:0;font-size:11px;}
            QPushButton#compactPageButton:hover:enabled {background:white;border-color:#8bbbea;}
            QPushButton#compactPageButton:disabled {color:#a5b0bf;}
            QLineEdit#compactPageEdit {background:white;border:1px solid #bfcfe0;border-radius:3px;color:#174c81;padding:0;font-family:'Segoe UI';font-size:12px;font-weight:400;}
            QLineEdit#compactPageEdit:disabled {background:#eef1f4;color:#a5b0bf;}
            QLabel#pageNavigationText {color:#104c82;font-family:'Segoe UI';font-size:12px;font-weight:400;}
            QLabel#compactFilenameLink {font-family:'Segoe UI';font-size:12px;font-weight:400;color:#397bb3;}
            QToolButton {background:transparent;border:1px solid transparent;border-radius:5px;min-width:54px;padding:4px;}
            QToolButton:hover {background:#e1efff;border-color:#afcef6;}
            QLabel#sideTitle {font-family:'Segoe UI';font-size:16px;font-weight:400;color:#397bb3;}
            QLabel#toolButtonLabel {font-size:10px;font-weight:600;color:#0f4592;}
            QPushButton#documentFileButton {padding:3px 5px;min-height:22px;font-size:11px;}

            QLabel#sectionTitle {font-size:11px;font-weight:700;color:#0f4592;margin-top:1px;}
            QLabel#groupTitle {font-size:12px;font-weight:700;color:#1670d5;margin-top:2px;}
            QScrollArea#toolsScroll {border:0;background:transparent;}
            QFrame#thumbnailSide {background:#f8fbff;border:1px solid #b8d7fb;border-radius:0px;}
            QFrame#side {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fbff,stop:1 #edf5ff);border:2px solid #b8d7fb;border-radius:14px;}
            QFrame#toolsInner {background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #f8fbff,stop:1 #edf5ff);border:none;}
            QFrame#workspace {background:#e5eaf1;}
            QSplitter::handle {background:transparent;border:none;}
            QSplitter::handle:horizontal {background:transparent;border:none;}
            QScrollArea#pageArea {background:#dfe5ec;border:0;}
            QScrollArea#pageArea QScrollBar:vertical {background:#eef3f9;width:12px;margin:0;border:0;}
            QScrollArea#pageArea QScrollBar::handle:vertical {background:#9cb5cf;min-height:28px;border-radius:5px;margin:2px;}
            QScrollArea#pageArea QScrollBar::handle:vertical:hover {background:#6e98c3;}
            QScrollArea#pageArea QScrollBar::add-line:vertical,
            QScrollArea#pageArea QScrollBar::sub-line:vertical {height:0;border:0;background:transparent;}
            QScrollArea#pageArea QScrollBar::add-page:vertical,
            QScrollArea#pageArea QScrollBar::sub-page:vertical {background:transparent;}
            QScrollArea#pageArea QScrollBar:horizontal {background:#eef3f9;height:12px;margin:0;border:0;}
            QScrollArea#pageArea QScrollBar::handle:horizontal {background:#9cb5cf;min-width:28px;border-radius:5px;margin:2px;}
            QScrollArea#pageArea QScrollBar::handle:horizontal:hover {background:#6e98c3;}
            QScrollArea#pageArea QScrollBar::add-line:horizontal,
            QScrollArea#pageArea QScrollBar::sub-line:horizontal {width:0;border:0;background:transparent;}
            QScrollArea#pageArea QScrollBar::add-page:horizontal,
            QScrollArea#pageArea QScrollBar::sub-page:horizontal {background:transparent;}
            QListWidget#thumbnails {background:#f8fbff;border:0;outline:0;}
            QListWidget#thumbnails::item:focus {outline:none;}
            QListWidget::item {padding:5px;border:2px solid transparent;border-radius:4px;}
            QListWidget::item:selected {border:2px solid #1684e8;background:#e6f2ff;color:#0058a7;}
            QPushButton#headerInfoButton {background:transparent;border:1px solid transparent;border-radius:5px;color:white;font-family:'Segoe UI';font-size:13px;font-weight:400;padding:3px 5px;text-align:center;}
            QPushButton#ribbonUtilityButton {background:transparent;border:1px solid transparent;border-radius:5px;padding:0;}
            QPushButton#ribbonUtilityButton:hover {background:white;border-color:#a7c6e7;}
            QPushButton#headerInfoButton:hover {background:rgba(255,255,255,0.15);border-color:rgba(255,255,255,0.22);}
            QPushButton#headerInfoButton:pressed {background:rgba(255,255,255,0.23);}
            QFrame#headerInfoDivider {background:rgba(255,255,255,0.5);border:none;}
            QPushButton#headerSplitButton {background:#e0eefb;border:1px solid #9ec5e8;border-radius:6px;color:#125b99;font-size:12px;font-weight:600;padding:3px 8px;}
            QPushButton#headerSplitButton:hover {background:#ffffff;}
            QPushButton#documentFileButton {background:#f9fbff;border:1px solid #c4d5e6;border-radius:4px;padding:5px 8px;min-height:22px;color:#104c82;}
            QPushButton#documentFileButton[rotationIcon="true"] {font-family:'Segoe UI Symbol';font-size:25px;font-weight:600;padding:0px 7px;}
            QPushButton#documentFileButton:hover {background:#e1efff;border-color:#8bbbea;}
            QPushButton#documentFileButton:disabled {color:#96a1ad;background:#f0f3f7;}
            QPushButton#toolButton {background:#f8fbff;border:1px solid #c9d8ea;border-radius:10px;padding:0px;font-size:10px;}
            QPushButton#toolButton:hover {background:#e5f2ff;}
            QPushButton#toolButton:checked, QPushButton#toolButton:checked:hover {
                background:#cce7ff;border:2px solid #087ccc;color:#0754a1;
            }
            QLabel#sliderValueLabel {background:#ffffff;border:1px solid #c9d8ea;border-radius:7px;padding:3px 4px;color:#0f4592;font-weight:600;}
            QSlider::groove:horizontal {height:3px;background:#cfdae8;border-radius:2px;}
            QSlider::sub-page:horizontal {background:#6ea8e8;border-radius:2px;}
            QSlider::handle:horizontal {background:#1785ee;width:14px;margin:-6px 0;border-radius:7px;}
            QSpinBox,QComboBox {background:white;border:1px solid #becddd;padding:5px;border-radius:3px;}
            QToolTip {background-color:#f9fbff; color:#0f4592; border:1px solid #a6c8e8; border-radius:3px; padding:3px 5px; font-size:12px;}
            QMenu { background-color: #f9fbff; color: #0f4592;
                    border: 1px solid #a6c8e8; border-radius: 4px;
                    padding: 3px; font-family: 'Segoe UI'; font-size: 12px; }
            QMenu::item { background: transparent; color: #0f4592;
                          padding: 5px 22px 5px 24px; margin: 1px 2px;
                          border-radius: 3px; }
            QMenu::item:selected { background: #dceeff; color: #0f4592; }
            QMenu::item:disabled { color: #899aaa; }
            QMenu::separator { height: 1px; background: #d4e1ef; margin: 3px 8px; }
            QStatusBar {background:#f5f8fc;color:#45607a;}
        ''')
        for shortcut,fn in [('Ctrl+O',self.open_active_pdf),('Ctrl+S',self.save_active_pdf),('Ctrl+Shift+S',self.save_active_as),('Ctrl+Z',self.undo_active_pdf),('Ctrl+Y',self.redo_active_pdf)]:
            a=QAction(self);a.setShortcut(shortcut);a.triggered.connect(fn);self.addAction(a)
    def _shared_on_rubric(self):
        return self._active_pdf_side == 'rubric'

    def _refresh_shared_header(self):
        if not hasattr(self,'shared_header_buttons'):
            return
        rubric=self._shared_on_rubric()
        has_doc = self.rubric_doc is not None if rubric else self.doc is not None
        for label,b in self.shared_header_buttons.items():
            if label == 'Open PDF':
                b.setEnabled(True)
            elif label == 'Undo':
                b.setEnabled(has_doc and bool(self.rubric_history if rubric else self.history))
            elif label == 'Redo':
                b.setEnabled(has_doc and bool(self.rubric_future if rubric else self.future))
            else:
                b.setEnabled(has_doc)
        # View buttons are mutually exclusive and remain disabled until
        # at least one PDF is loaded.
        if hasattr(self, 'header_single_button'):
            self._set_ribbon_button_available(
                self.header_single_button,
                bool(self.doc is not None or self.rubric_doc is not None) and self.split_mode)
        if hasattr(self, 'header_split_button'):
            self._set_ribbon_button_available(self.header_split_button, bool(self.doc is not None or self.rubric_doc is not None) and not self.split_mode)
        # Combine requires both documents; Open and Sign are always available.
        if hasattr(self, 'header_combine_button'):
            self._set_ribbon_button_available(
                self.header_combine_button,
                self.doc is not None and self.rubric_doc is not None)
        if hasattr(self, 'header_sign_button'):
            self._set_ribbon_button_available(self.header_sign_button, True)
        current_zoom = self.ref_zoom if rubric else self.zoom
        self.shared_zoom_label.setText(f'{round(current_zoom*100)}%')

    def _set_ribbon_button_available(self, button, available):
        """Grey an unavailable ribbon command without changing approved sizing."""
        button.setEnabled(bool(available))
        for child in button.findChildren(QLabel):
            if child.objectName() == 'hybridRibbonCaption':
                child.setStyleSheet(
                    'QLabel#hybridRibbonCaption {background:transparent; border:none; '
                    f'color:{"#174c81" if available else "#9ba3ae"}; padding:0px;}}')
            elif child.objectName() == 'hybridRibbonIcon':
                effect = child.graphicsEffect()
                if effect is None:
                    effect = QGraphicsColorizeEffect(child)
                    effect.setColor(QColor('#9ba3ae'))
                    child.setGraphicsEffect(effect)
                if isinstance(effect, QGraphicsColorizeEffect):
                    effect.setStrength(0.0 if available else 1.0)

    def navigate_active_pdf(self, offset):
        """Keyboard page navigation acts on the active PDF, just like the shared ribbon."""
        if self._shared_on_rubric():
            self.navigate_rubric(offset)
        else:
            self.navigate(offset)

    def jump_active_pdf_to_end(self, last=False):
        """Jump to the first or last page of the selected PDF."""
        if self._shared_on_rubric():
            if self.rubric_doc is None or len(self.rubric_doc) == 0:
                return
            self.ref_image.finish_editor()
            self.rubric_page = len(self.rubric_doc) - 1 if last else 0
            self.jump_to_rubric_page()
        else:
            if self.doc is None or len(self.doc) == 0:
                return
            self.go_page(len(self.doc) - 1 if last else 0)

    def open_active_pdf(self):
        if self._shared_on_rubric(): self.open_rubric()
        else: self.open_pdf()

    def undo_active_pdf(self):
        if self._shared_on_rubric(): self.undo_rubric()
        else: self.undo()
        self._refresh_shared_header()

    def redo_active_pdf(self):
        if self._shared_on_rubric(): self.redo_rubric()
        else: self.redo()
        self._refresh_shared_header()

    def close_active_pdf(self):
        if self._shared_on_rubric(): self.close_rubric()
        else: self.close_student_pdf()
        self._refresh_shared_header()

    def save_active_pdf(self):
        if self._shared_on_rubric(): self.save_rubric(False)
        else: self.save_pdf()

    def save_active_as(self):
        if self._shared_on_rubric(): self.save_rubric(True)
        else: self.save_as()

    def export_active_image_pdf(self):
        if self._shared_on_rubric(): self.export_rubric_image_pdf()
        else: self.export_image_pdf()

    def rotate_active_cw(self):
        if self._shared_on_rubric(): self.rotate_rubric_page()
        else: self.rotate_page()

    def rotate_active_ccw(self):
        if self._shared_on_rubric(): self.rotate_rubric_page_counterclockwise()
        else: self.rotate_page_counterclockwise()

    def zoom_active_in(self):
        if self._shared_on_rubric(): self.scale_rubric_zoom(1.2)
        else: self.scale_zoom(1.2)
        self._refresh_shared_header()

    def zoom_active_out(self):
        if self._shared_on_rubric(): self.scale_rubric_zoom(1/1.2)
        else: self.scale_zoom(1/1.2)
        self._refresh_shared_header()

    def _place_replacement_file_dialog(self, chooser, target_side):
        """Place the replacement chooser alongside the marking ribbon.

        In Split View the clicked filename belongs to the active pane, so the
        chooser goes over the opposite (inactive) PDF pane. In Single View it
        opens within the visible PDF area, near the ribbon on the left.
        """
        if not chooser.isVisible():
            return
        if self.split_mode:
            pane = (self.student_workspace if target_side == 'rubric'
                    else self.reference_panel)
        else:
            pane = (self.reference_panel if target_side == 'rubric'
                    else self.student_workspace)
        ribbon = self.marking_tools_panel
        top_left = pane.mapToGlobal(QPoint(0, 0))
        pane_right = top_left.x() + pane.width()
        pane_bottom = top_left.y() + pane.height()
        if pane.width() < 160 or pane.height() < 160:
            return

        margin = 10
        # Fit inside the destination pane as much as its size permits.
        width = min(740, max(330, pane.width() - 2 * margin))
        height = min(480, max(250, pane.height() - 2 * margin))
        chooser.resize(width, height)
        ribbon_pos = ribbon.mapToGlobal(QPoint(0, 0))
        ribbon_center = ribbon_pos.x() + ribbon.width() / 2
        if pane_right <= ribbon_center:
            x = pane_right - width - margin
        else:
            x = top_left.x() + margin
        x = max(top_left.x() + margin, min(x, pane_right - width - margin))
        y = top_left.y() + max(margin, (pane.height() - height) // 2)
        # Constrain to the available display, including multi-monitor setups.
        screen = QGuiApplication.screenAt(pane.mapToGlobal(pane.rect().center()))
        if screen is not None:
            available = screen.availableGeometry()
            x = max(available.left(), min(x, available.right() - width + 1))
            y = max(available.top(), min(y, available.bottom() - height + 1))
        chooser.move(int(x), int(y))
        chooser.raise_()
        chooser.activateWindow()

    def _show_pdf_in_explorer(self, side):
        """Choose a replacement for the clicked PDF; protect unsaved work."""
        if self.split_mode:
            self._activate_pdf_side(side)
        target = side  # The clicked filename, never an unrelated pane.
        current = self.rubric_path if target == 'rubric' else self.path
        loaded = self.rubric_doc is not None if target == 'rubric' else self.doc is not None
        if not loaded or not current:
            return
        # A regular native Explorer-style dialog may be positioned by Windows
        # wherever its last location was. Use Qt's file dialog so its placement
        # over the INACTIVE pane in Split View is predictable.
        chooser = QFileDialog(self, 'Select replacement PDF',
                              os.path.dirname(os.path.abspath(current)),
                              'PDF Files (*.pdf)')
        chooser.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        chooser.setFileMode(QFileDialog.FileMode.ExistingFile)
        chooser.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
        chooser.resize(740, 480)
        QTimer.singleShot(0, lambda: self._place_replacement_file_dialog(chooser, target))
        if chooser.exec() != QDialog.DialogCode.Accepted:
            return
        chosen_files = chooser.selectedFiles()
        selection = chosen_files[0] if chosen_files else ''
        if not selection:
            return
        if os.path.normcase(os.path.abspath(selection)) == os.path.normcase(os.path.abspath(current)):
            return

        # Do not discard the current page if the selected PDF is invalid.
        try:
            candidate = fitz.open(selection)
            try:
                if candidate.needs_pass or len(candidate) == 0:
                    raise ValueError('The selected PDF is empty or password-protected.')
            finally:
                candidate.close()
        except Exception as exc:
            QMessageBox.warning(self, 'Cannot open replacement PDF', str(exc))
            return

        # Commit an in-progress annotation before checking for unsaved work.
        if target == 'rubric':
            if self.rubric_doc is None:
                return
            self.ref_image.finish_editor()
            dirty = bool(self.rubric_dirty)
        else:
            if self.doc is None:
                return
            self.canvas.finish_editor()
            dirty = bool(self.dirty)

        old_name = os.path.basename(os.fspath(current))
        new_name = os.path.basename(os.fspath(selection))
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Replace document?')
        if dirty:
            dialog.setIcon(QMessageBox.Icon.Warning)
            dialog.setText(f'You have unsaved changes in "{old_name}".')
            dialog.setInformativeText(
                f'Do you want to replace "{old_name}" with "{new_name}" without saving your changes?')
            save_button = dialog.addButton('Save and Replace', QMessageBox.ButtonRole.AcceptRole)
            discard_button = dialog.addButton('Replace Without Saving', QMessageBox.ButtonRole.DestructiveRole)
        else:
            dialog.setIcon(QMessageBox.Icon.Question)
            dialog.setText(f'Do you want to replace "{old_name}" with "{new_name}"?')
            discard_button = dialog.addButton('Replace', QMessageBox.ButtonRole.AcceptRole)
            save_button = None
        cancel_button = dialog.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)
        dialog.setDefaultButton(cancel_button)
        dialog.exec()
        chosen = dialog.clickedButton()
        if chosen is None or chosen is cancel_button:
            return
        if dirty and chosen is save_button:
            if target == 'rubric':
                saved_path = self.save_rubric(False)
                successful = (bool(saved_path) and not self.rubric_dirty and
                              os.path.isfile(saved_path))
            else:
                saved_path = self._save(False)
                successful = (bool(saved_path) and not self.dirty and
                              os.path.isfile(saved_path))
            if not successful:
                return  # Failed/cancelled Save must never replace the current PDF.
        elif chosen is not discard_button:
            return

        # We have already obtained a safe, explicit replacement decision.
        # Suppress the old duplicate discard-warning for this one open action.
        if target == 'rubric':
            self.open_rubric(selection, skip_unsaved_prompt=True)
        else:
            self.open_pdf(selection, skip_unsaved_prompt=True)

    def _setup_document_heading(self, layout, filename_label, id_label, path_label):
        """Filename and saving status in the first row; full folder path below."""
        heading=QVBoxLayout()
        # Align both filename and folder path with the left edge of the actual
        # PDF page content, not the outer window edge. Both page stacks have a
        # 12 px inside margin. Keep the parent pane margins untouched.
        heading.setContentsMargins(12,0,12,0)
        heading.setSpacing(1)
        first=QHBoxLayout()
        first.setContentsMargins(0,0,0,0)
        first.setSpacing(8)
        # Match the tool ribbon's Segoe UI / regular style, while retaining
        # the compact bottom filename's 12 px font size.
        title_font = QFont('Segoe UI')
        title_font.setBold(False)
        title_font.setPixelSize(12)
        filename_label.setFont(title_font)
        filename_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        filename_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        filename_label.setMinimumWidth(0)
        status_font = QFont('Segoe UI')
        status_font.setBold(False)
        status_font.setPixelSize(9)
        id_label.setFont(status_font)
        id_label.setStyleSheet('color: #174c81; background: transparent;')
        id_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        id_label.setSizePolicy(QSizePolicy.Policy.Minimum,QSizePolicy.Policy.Preferred)
        first.addWidget(filename_label,1)
        first.addWidget(id_label,0)
        heading.addLayout(first)
        # Use precisely the same actual pixel-sized font as the ribbon labels.
        path_font = QFont('Segoe UI')
        path_font.setBold(False)
        path_font.setPixelSize(9)
        path_label.setFont(path_font)
        path_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        path_label.setStyleSheet('color: #174c81; background: transparent;')
        path_label.setMinimumWidth(0)
        path_label.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Preferred)
        heading.addWidget(path_label)
        # In compact mode, these existing widgets move into the bottom bar.

    def _update_document_heading(self, side):
        if side == 'rubric':
            filename, status, path_label = self.rubric_title,self.rubric_document_id,self.rubric_path_label
            path, host = getattr(self,'rubric_path',None),self.reference_panel
            is_loaded=self.rubric_doc is not None
            changed=self.rubric_dirty
            saved=self._rubric_saved_once
        else:
            filename, status, path_label = self.student_title,self.student_document_id,self.student_path_label
            path, host = getattr(self,'path',None),self.student_workspace
            is_loaded=self.doc is not None
            changed=self.dirty
            saved=self._student_saved_once
        if not is_loaded or not path:
            filename_text='No file loaded'
            folder=''
            full='No file loaded'
            state=''  # Hide save status until this PDF has been opened.
        else:
            full=os.path.normpath(path)
            filename_text=os.path.basename(full)
            folder=os.path.dirname(full)
            state='Unsaved changes' if changed else ('All changes saved' if saved else 'No changes yet')
        status.setText(state)
        # The filename QLabel now fits its own actual layout width, not the
        # workspace width. Long names shorten on resizing, in both view modes.
        status.setToolTip('')
        filename.set_document_available(bool(is_loaded and path))
        filename.set_filename(filename_text, full if is_loaded and path else '')
        path_label.setToolTip('')
        path_label.setText(folder)  # Internal compatibility; hidden in compact UI.

    def _refresh_document_statuses(self):
        for side, state in (('rubric', (self.rubric_dirty,self._rubric_saved_once,self.rubric_path)),
                            ('student', (self.dirty,self._student_saved_once,self.path))):
            key='_heading_last_'+side
            if getattr(self,key,None)!=state:
                setattr(self,key,state)
                self._update_document_heading(side)

    def _create_active_pdf_borders(self):
        """Non-clickable, explicitly painted active-pane outlines."""
        self._active_pdf_outlines = {}
        for side, host in (('student', self.student_workspace),
                           ('rubric', self.reference_panel)):
            outline = ActivePdfOutline(host)
            outline.setGeometry(host.rect())
            host.installEventFilter(self)
            self._active_pdf_outlines[side] = outline
        QTimer.singleShot(0, self._refresh_active_pdf_borders)

    def _refresh_active_pdf_borders(self):
        if not hasattr(self, '_active_pdf_outlines'):
            return
        for side, outline in self._active_pdf_outlines.items():
            host = self.student_workspace if side == 'student' else self.reference_panel
            outline.setGeometry(host.rect())
            active = (side == self._active_pdf_side and
                      True)
            outline.setVisible(active and host.isVisible())
            if active:
                outline.raise_()
        # Additional visible state in the existing PDF titles, without shifting layout.
        if hasattr(self, 'student_title'):
            self.student_title._update_link_appearance()
        if hasattr(self, 'rubric_title'):
            self.rubric_title._update_link_appearance()

    def _activate_pdf_side(self, side):
        if not self.split_mode and side != self._active_pdf_side:
            return
        self._active_pdf_side = side
        self._refresh_active_pdf_borders()
        self._refresh_shared_header()

    def eventFilter(self, watched, event):
        # Page Up/Down move one page; Ctrl+Page Up/Down go to first/last.
        # Up/Down arrow keys scroll the selected PDF by a small amount.
        # Never capture these keys while a text or numeric input is being edited.
        if event.type() == QEvent.Type.KeyPress and self.isActiveWindow():
            focused = QApplication.focusWidget()
            editing = isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit,
                                           QAbstractSpinBox, QComboBox))
            if not editing:
                key = event.key()
                modifiers = event.modifiers()
                side = self._active_pdf_side
                loaded = self.rubric_doc if side == 'rubric' else self.doc
                if loaded is not None and key in (Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
                    if modifiers == Qt.KeyboardModifier.ControlModifier:
                        self.jump_active_pdf_to_end(last=(key == Qt.Key.Key_PageDown))
                        event.accept()
                        return True
                    if modifiers == Qt.KeyboardModifier.NoModifier:
                        self.navigate_active_pdf(-1 if key == Qt.Key.Key_PageUp else 1)
                        event.accept()
                        return True
                if loaded is not None and modifiers == Qt.KeyboardModifier.NoModifier:
                    if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                        scroll = self.ref_scroll if side == 'rubric' else self.scroll
                        bar = scroll.verticalScrollBar()
                        step = max(32, bar.singleStep() * 2)
                        bar.setValue(bar.value() + (-step if key == Qt.Key.Key_Up else step))
                        event.accept()
                        return True
        if (event.type() == QEvent.Type.Resize and
                watched in (getattr(self, 'student_workspace', None),
                            getattr(self, 'reference_panel', None))):
            outline = getattr(self, '_active_pdf_outlines', {}).get(
                'student' if watched is getattr(self, 'student_workspace', None) else 'rubric')
            if outline is not None:
                outline.setGeometry(watched.rect())
            if hasattr(self,'rubric_path_label') and hasattr(self,'student_path_label'):
                self._update_document_heading('student' if watched is getattr(self,'student_workspace',None) else 'rubric')
        # Remember the last PDF pane the user worked in, not the keyboard focus
        # (toolbar clicks change focus and must not change the active document).
        if event.type() == QEvent.Type.MouseButtonPress:
            student_targets=([self.scroll.viewport()] + getattr(self,'student_pages',[])) if hasattr(self,'scroll') else []
            rubric_targets=([self.ref_scroll.viewport()] + getattr(self,'rubric_pages',[])) if hasattr(self,'ref_scroll') else []
            if watched in student_targets:
                self._activate_pdf_side('student')
            elif watched in rubric_targets:
                self._activate_pdf_side('rubric')
            elif watched is getattr(self, 'student_workspace', None):
                self._activate_pdf_side('student')
            elif watched is getattr(self, 'reference_panel', None):
                self._activate_pdf_side('rubric')
        # Ctrl + wheel zooms only the PDF pane under the cursor. Without Ctrl,
        # Qt handles the wheel normally for independent vertical scrolling.
        if event.type() == QEvent.Type.Wheel and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            student_targets = ([self.scroll.viewport()] + self.student_pages) if hasattr(self, 'student_pages') else []
            rubric_targets = ([self.ref_scroll.viewport()] + self.rubric_pages) if hasattr(self, 'rubric_pages') else []
            angle = event.angleDelta().y()
            if not angle:
                angle = event.pixelDelta().y()
            if angle and watched in student_targets and self.doc:
                # At the zoom boundary consume repeat wheel events without
                # re-rendering the page or forwarding them as scroll events.
                if not ((angle > 0 and self.zoom >= 3.50 - 1e-9) or
                        (angle < 0 and self.zoom <= .30 + 1e-9)):
                    self.scale_zoom(1.2 ** (angle / 120.0))
                event.accept()
                return True
            if angle and watched in rubric_targets and self.rubric_doc:
                if not ((angle > 0 and self.ref_zoom >= 3.50 - 1e-9) or
                        (angle < 0 and self.ref_zoom <= .30 + 1e-9)):
                    self.scale_rubric_zoom(1.2 ** (angle / 120.0))
                event.accept()
                return True
        return super().eventFilter(watched,event)

    def _add_branded_dialog_header(self, dialog, title):
        """Use the same blue gradient and red close X as tool settings."""
        dialog.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        root = QVBoxLayout(dialog)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        head = self._SettingsHeader(dialog)
        head.setFixedHeight(32)
        head.setStyleSheet('QFrame {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #075294,stop:1 #087ccc); border:0;}')
        header_row = QHBoxLayout(head)
        header_row.setContentsMargins(11, 0, 4, 0)
        header_row.setSpacing(6)
        heading = QLabel(title, head)
        heading.setStyleSheet('color:white; font-family:"Segoe UI"; font-size:12px; font-weight:normal; border:0; background:transparent;')
        heading.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        header_row.addWidget(heading, 1)
        x_button = QPushButton('×', head)
        x_button.setObjectName('brandedHeaderClose')
        x_button.setFixedSize(28, 26)
        x_button.setToolTip('Close')
        x_button.setCursor(Qt.CursorShape.PointingHandCursor)
        x_button.setStyleSheet('QPushButton#brandedHeaderClose { background-color:#ce333b; color:#ffffff; border:0px; border-radius:3px; padding:0px; margin:0px; font: bold 18px "Segoe UI"; }'
                               'QPushButton#brandedHeaderClose:hover {background-color:#a91922;}'
                               'QPushButton#brandedHeaderClose:pressed {background-color:#8a121c;}')
        x_button.clicked.connect(dialog.accept)
        header_row.addWidget(x_button)
        root.addWidget(head)
        body = QWidget(dialog)
        root.addWidget(body, 1)
        return body

    def show_help(self):
        """Display a scrollable guide with independent text zoom controls."""
        dialog = QDialog(self)
        dialog.setWindowTitle('Help — PDF Assignment Marker')
        dialog.resize(760, 650)
        dialog.setMinimumSize(540, 440)
        dialog.setStyleSheet("""
            QDialog { background: #f4f8fc; }
            QTextBrowser { background: white; border: 1px solid #cbdbea;
                border-radius: 7px; padding: 14px; }
            QPushButton { background:#126fbd; color:white; border:0;
                border-radius:5px; padding:8px 22px; font-weight:600; }
            QPushButton:hover { background:#0c5b9e; }
            QPushButton#brandedHeaderClose { background:#ce333b; color:white; padding:0px; border:0px; border-radius:3px; }
            QPushButton#brandedHeaderClose:hover { background:#a91922; }
        """)
        body = self._add_branded_dialog_header(dialog, 'Help — PDF Assignment Marker')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 14, 16, 14)
        heading = QLabel('PDF Assignment Marker — User Guide')
        heading.setStyleSheet('font-size:20px; font-weight:700; color:#075294; padding:5px 0 8px 0;')
        layout.addWidget(heading)

        # HTML contains explicit pixel font sizes. Rebuild the formatted HTML at
        # the chosen scale so headings and body text increase together.
        class HelpBrowser(QTextBrowser):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.zoom_callback = None

            def wheelEvent(self, event):
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier and self.zoom_callback:
                    direction = event.angleDelta().y()
                    if direction:
                        self.zoom_callback(10 if direction > 0 else -10)
                    event.accept()
                    return
                super().wheelEvent(event)

        browser = HelpBrowser(dialog)
        browser.setOpenExternalLinks(False)
        layout.addWidget(browser, 1)

        controls = QHBoxLayout()
        controls.addStretch()
        close_button = QPushButton('Close')
        close_button.setFixedSize(100, 42)
        close_button.clicked.connect(dialog.accept)
        controls.addWidget(close_button)
        layout.addLayout(controls)

        zoom_percent = [100]
        def render_guide():
            # Preserve reading position when changing text size.
            scrollbar = browser.verticalScrollBar()
            old_max = scrollbar.maximum()
            fraction = scrollbar.value() / old_max if old_max else 0.0
            factor = zoom_percent[0] / 100.0
            html = re.sub(
                r'(font-size\s*:\s*)(\d+(?:\.\d+)?)(px|pt)',
                lambda match: (match.group(1) +
                    f'{float(match.group(2))*factor:g}' + match.group(3)),
                HELP_HTML, flags=re.IGNORECASE)
            browser.setHtml(html)
            scrollbar.setValue(round(fraction * scrollbar.maximum()))


        def change_zoom(change):
            value = min(200, max(70, zoom_percent[0] + change))
            if value != zoom_percent[0]:
                zoom_percent[0] = value
                render_guide()

        browser.zoom_callback = change_zoom
        for key, delta in [('Ctrl++', 10), ('Ctrl+=', 10), ('Ctrl+-', -10)]:
            shortcut = QShortcut(QKeySequence(key), dialog)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(lambda d=delta: change_zoom(d))
        render_guide()
        dialog.exec()

    def show_about(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('About PDF Assignment Marker')
        dialog.setModal(True)
        dialog.resize(530, 485)
        dialog.setMinimumSize(530, 400)
        dialog.setStyleSheet("""
            QDialog { background: #ffffff; }
            QLabel#aboutTitle { font-family: 'Segoe UI'; font-weight: 700; color: #145da6; }
            QLabel#aboutSubtitle { color: #52687f; }
            QLabel#aboutHeading { color: #315b80; font-weight: 700; }
            QLabel#aboutBody { color: #273d50; }
            QLabel#aboutFine { color: #61758a; }
            QLabel#aboutMeta { color: #435d77; }
            QPushButton { background: #126fbd; color: white; border: none; border-radius: 5px; padding: 7px 22px; font-weight: 600; }
            QPushButton:hover { background: #0c5b9e; }
            QPushButton#brandedHeaderClose { background:#ce333b; color:white; padding:0px; border:0px; border-radius:3px; }
            QPushButton#brandedHeaderClose:hover { background:#a91922; }
        """)
        class AboutScrollArea(QScrollArea):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.zoom_callback = None

            def wheelEvent(self, event):
                if (event.modifiers() & Qt.KeyboardModifier.ControlModifier
                        and self.zoom_callback):
                    delta = event.angleDelta().y()
                    if delta:
                        self.zoom_callback(10 if delta > 0 else -10)
                    event.accept()
                    return
                super().wheelEvent(event)

        body = self._add_branded_dialog_header(dialog, 'About PDF Assignment Marker')
        layout = QVBoxLayout(body)
        layout.setContentsMargins(28, 14, 28, 18)
        layout.setSpacing(7)
        area = AboutScrollArea(dialog)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidgetResizable(True)
        area.setStyleSheet('QScrollArea { background: white; border: none; }')
        content = QWidget()
        content.setStyleSheet('background: white;')
        text_layout = QVBoxLayout(content)
        text_layout.setContentsMargins(0, 7, 0, 7)
        text_layout.setSpacing(7)
        title = QLabel('PDF Assignment Marker')
        title.setObjectName('aboutTitle')
        text_layout.addWidget(title)
        tagline = QLabel('Open-source PDF annotation and educational assessment software')
        tagline.setObjectName('aboutSubtitle')
        text_layout.addWidget(tagline)
        text_layout.addSpacing(8)

        heading = QLabel('PROJECT INITIATOR & DEVELOPER')
        heading.setObjectName('aboutHeading')
        text_layout.addWidget(heading)
        credit = QLabel('Mohamed Jameel\nFaculty of Education, The Maldives National University')
        credit.setObjectName('aboutBody')
        credit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text_layout.addWidget(credit)
        text_layout.addSpacing(9)

        heading = QLabel('PUBLIC CONTRIBUTION')
        heading.setObjectName('aboutHeading')
        text_layout.addWidget(heading)
        description = QLabel(
            'An independent, voluntary educational technology initiative '
            'to provide teachers and lecturers with a freely available tool '
            'for annotating, marking and reviewing student work. '
            'The project aims to make practical digital assessment tools '
            'accessible to educators globally.'
        )
        description.setObjectName('aboutBody')
        description.setWordWrap(True)
        text_layout.addWidget(description)
        text_layout.addSpacing(9)

        heading = QLabel('DEVELOPMENT ACKNOWLEDGEMENT')
        heading.setObjectName('aboutHeading')
        text_layout.addWidget(heading)
        acknowledgement = QLabel('Developed with assistance from AI-based programming tools.')
        acknowledgement.setObjectName('aboutBody')
        acknowledgement.setWordWrap(True)
        text_layout.addWidget(acknowledgement)
        text_layout.addSpacing(6)

        note = QLabel('Independent project; university affiliation does not imply institutional endorsement.')
        note.setObjectName('aboutFine')
        note.setWordWrap(True)
        text_layout.addWidget(note)
        text_layout.addStretch(1)
        meta = QLabel('Version 11.0.2  •  2026  •  Mohamed Jameel')
        meta.setObjectName('aboutMeta')
        text_layout.addWidget(meta)
        area.setWidget(content)
        layout.addWidget(area, 1)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton('Close')
        close.setFixedWidth(92)
        close.clicked.connect(dialog.accept)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        # Magnify About with Ctrl + wheel anywhere inside its dialog.
        # QLabel stylesheets can override QFont changes; set the font size on
        # each label itself so the size visibly changes on Windows.
        zoom = [100]
        label_sizes = {
            'aboutTitle': 23, 'aboutSubtitle': 11, 'aboutHeading': 11,
            'aboutBody': 12, 'aboutFine': 10, 'aboutMeta': 11,
        }
        about_labels = [item for item in content.findChildren(QLabel)
                        if item.objectName() in label_sizes]

        def apply_about_zoom():
            factor = zoom[0] / 100.0
            for item in about_labels:
                size = max(1, round(label_sizes[item.objectName()] * factor))
                # A widget-local font-size declaration takes priority over
                # the dialog's stylesheet and ensures the size actually changes.
                item.setStyleSheet(f'font-size: {size}px;')
                item.updateGeometry()
            text_layout.invalidate()
            content.adjustSize()
            content.updateGeometry()

        def update_about_zoom(change):
            target = max(70, min(200, zoom[0] + change))
            if target != zoom[0]:
                zoom[0] = target
                apply_about_zoom()

        class AboutZoomWheelFilter(QObject):
            def eventFilter(self, watched, event):
                if (event.type() == QEvent.Type.Wheel
                        and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    # Filter at application level, but only handle events inside
                    # this About dialog; avoid affecting the PDF viewers.
                    obj = watched
                    while obj is not None and obj is not dialog:
                        obj = obj.parent() if isinstance(obj, QObject) else None
                    if obj is dialog:
                        delta = event.angleDelta().y()
                        if delta:
                            update_about_zoom(10 if delta > 0 else -10)
                        event.accept()
                        return True
                return False

        apply_about_zoom()
        zoom_filter = AboutZoomWheelFilter(dialog)
        area.zoom_callback = update_about_zoom
        app = QApplication.instance()
        app.installEventFilter(zoom_filter)
        shortcuts = []
        for sequence, amount in [('Ctrl++', 10), ('Ctrl+=', 10), ('Ctrl+-', -10)]:
            key = QShortcut(QKeySequence(sequence), dialog)
            key.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            key.activated.connect(lambda d=amount: update_about_zoom(d))
            shortcuts.append(key)
        try:
            dialog.exec()
        finally:
            app.removeEventFilter(zoom_filter)

    def mark_button(self,symbol,title):
        """Make a 36x48 tool tile: button on top, separate caption below.

        Tiles are explicitly kept alive through the tool button, avoiding
        orphaned Qt widgets. A 2px layout gap separates tiles; the caption has a clear 6px gap.
        """
        tile=QWidget()
        tile.setFixedSize(36,48)
        b=QPushButton(tile)
        b.setObjectName('toolButton')
        b.setCheckable(True)
        b.setGeometry(0,0,36,27)
        b.setToolTip({'Move':'Select','Marks':'Part Marks'}.get(title,title))
        b.setIconSize(QSize(20,20))
        b.setIcon(self.coloured_tool_icon(title))
        short_labels={'Move':'Select','Highlighter':'Hi-lite',
                      'Eraser':'Eraser','Marks':'Marks',
                      'Total Marks':'Sum'}
        caption=QLabel(short_labels.get(title,title),tile)
        caption.setObjectName('toolCaption')
        caption.setGeometry(0,33,36,15)
        caption.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        caption.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,True)
        caption.setStyleSheet('QLabel#toolCaption {background:transparent; border:none; color:#174c81; padding:0px;}')
        font=QFont('Segoe UI')
        font.setBold(False)
        font.setPixelSize(9)
        caption.setFont(font)
        b._caption_tile=tile
        return b
    def color_button(self,color,fn):
        # Draw swatches as icons instead of applying a coloured QPushButton stylesheet.
        # Coloured button styles can be inherited by QToolTip on Windows, producing
        # red/green tooltip backgrounds rather than the normal tool tooltip.
        b=QPushButton()
        b.setFixedSize(24,24)
        b.setFlat(True)
        b.setStyleSheet('QPushButton { background: transparent; border: none; padding: 0px; }')
        b.setIconSize(QSize(24,24))
        b.setProperty('swatchColor',color)
        b.setToolTip(color)
        b.clicked.connect(fn)
        return b

    def swatch_icon(self, color, selected):
        pix=QPixmap(28,28)
        pix.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if selected:
            painter.setPen(QPen(QColor('#17324f'),2.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(1.5,1.5,25,25))
        painter.setPen(QPen(QColor('#e9f0f8'),0.8))
        painter.setBrush(QBrush(QColor(color)))
        painter.drawEllipse(QRectF(5,5,18,18))
        painter.end()
        return QIcon(pix)

    def labeled_slider(self,layout,low,high,val,fn,suffix):
        row=QHBoxLayout();row.setContentsMargins(0,0,0,0);row.setSpacing(8)
        slider=QSlider(Qt.Orientation.Horizontal);slider.setRange(low,high);slider.setValue(val)
        slider.setObjectName('panelSlider')
        lab=QLabel(f'{val}{suffix}');lab.setObjectName('sliderValueLabel');lab.setFixedWidth(48)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slider.valueChanged.connect(lambda v:(lab.setText(f'{v}{suffix}'),fn(v)))
        row.addWidget(slider,1);row.addWidget(lab);layout.addLayout(row);return slider
    def upload_signature(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose your signature image',self.remembered_folder('signature_open'),'Images (*.png *.jpg *.jpeg *.bmp *.webp)')
        if not path:return False
        picture=QImage(path)
        if picture.isNull():
            QMessageBox.warning(self,'Signature','Could not open the selected image.')
            return False
        if picture.width()>1600 or picture.height()>1600:
            picture=picture.scaled(1600,1600,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        buffer=QByteArray();qbuf=QBuffer(buffer);qbuf.open(QIODevice.OpenModeFlag.WriteOnly)
        picture.save(qbuf,'PNG');qbuf.close()
        self.signature_image=base64.b64encode(bytes(buffer)).decode('ascii')
        self.folder_settings.setValue('signature/png',self.signature_image)
        self.remember_folder('signature_open',path)
        return True

    def show_signature_manager(self):
        """Manage a reusable local signature and preview it before placing it."""
        dialog=QDialog(self)
        dialog.setWindowTitle('Signature Manager')
        dialog.setMinimumWidth(390)
        dialog.setModal(True)
        layout=QVBoxLayout(dialog)
        layout.setContentsMargins(18,16,18,16)
        layout.setSpacing(12)
        title=QLabel('Your signature')
        title.setStyleSheet('font-size: 15px; font-weight: 600; color: #154675;')
        layout.addWidget(title)
        preview=QLabel()
        preview.setFixedHeight(150)
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setStyleSheet('QLabel {background: white; border: 1px solid #cbd5e1; border-radius: 7px; color: #64748b;}')
        layout.addWidget(preview)
        info=QLabel('Upload a PNG image with a transparent background for best results.')
        info.setWordWrap(True)
        layout.addWidget(info)
        actions=QHBoxLayout()
        upload=QPushButton('Upload / Replace')
        add=QPushButton('Add to PDF')
        delete=QPushButton('Delete')
        close=QPushButton('Close')
        for button in (upload,add,delete,close):
            button.setMinimumHeight(34)
            actions.addWidget(button)
        layout.addLayout(actions)

        def refresh():
            picture=QImage()
            if self.signature_image:
                try:picture=QImage.fromData(base64.b64decode(self.signature_image))
                except (ValueError, TypeError):pass
            valid=not picture.isNull()
            if valid:
                pix=QPixmap.fromImage(picture).scaled(340,130,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
                preview.setPixmap(pix)
                preview.setText('')
            else:
                preview.clear()
                preview.setText('No signature uploaded')
            add.setEnabled(valid)
            delete.setEnabled(valid)

        def upload_new():
            if self.upload_signature():refresh()

        def delete_saved():
            result=QMessageBox.question(dialog,'Delete saved signature',
                'Delete the uploaded signature from this computer?\n\nSignatures already placed on PDF pages will not be removed.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if result!=QMessageBox.StandardButton.Yes:return
            self.signature_image=''
            self.folder_settings.remove('signature/png')
            if self.tool=='Sign':self.select_tool('Move')
            refresh()

        def add_to_document():
            if not (self.doc or self.rubric_doc):
                QMessageBox.information(dialog,'Open a PDF','Open an Assignment or Rubric PDF before adding a signature.')
                return
            dialog.accept()
            self.activate_signature()

        upload.clicked.connect(upload_new)
        add.clicked.connect(add_to_document)
        delete.clicked.connect(delete_saved)
        close.clicked.connect(dialog.reject)
        refresh()
        dialog.exec()

    def activate_signature(self):
        if not self.signature_image and not self.upload_signature():return
        self.select_tool('Sign')
        self.statusBar().showMessage('Sign: click the PDF to place your signature. Use Select / Move to drag or resize its bottom-right corner.',9000)

    def place_signature(self,page_index,pos,rubric=False):
        if not self.signature_image and not self.upload_signature():return
        picture=QImage.fromData(base64.b64decode(self.signature_image))
        if picture.isNull():return
        w=115.0;h=w*picture.height()/picture.width()
        mark=Stroke('Signature','#000000',h,1.0,[pos],self.signature_image,text_width=w)
        if rubric:
            self.record_rubric_action()
            self.rubric_strokes.setdefault(page_index,[]).append(mark)
            self.rubric_dirty=True
            self.ref_image.update()
        else:
            self.record_action()
            self.strokes.setdefault(page_index,[]).append(mark)
            self.set_dirty(True)
            self.canvas.update()
        # Newly placed signatures are not selected for resizing until clicked.
        if rubric and hasattr(self, 'ref_image'):
            self.ref_image.selected_signature = None
            self.ref_image.update()
        elif hasattr(self, 'canvas'):
            self.canvas.selected_signature = None
            self.canvas.update()
        self.select_tool('Move')

    def coloured_tool_icon(self, name):
        """Render original vector icon geometry with the tool's individual colour."""
        color=self.tool_colors.get(name, '#1269bc') if hasattr(self,'tool_colors') else '#1269bc'
        if name in ('Emoji','Sign'): color='#1269bc'
        if name == 'Highlighter' and hasattr(self,'tool_colors'):
            color=self.tool_colors.get('Highlighter', HIGHLIGHTS[0])
        paths = ICON_PATHS.get(name, ICON_PATHS['Text']).replace('currentColor', color)
        svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
             f'<g fill="none" stroke="{color}" stroke-width="1.65" stroke-linecap="round" '
             f'stroke-linejoin="round">{paths}</g></svg>')
        pix=QPixmap(64,64);pix.fill(Qt.GlobalColor.transparent)
        painter=QPainter(pix)
        QSvgRenderer(QByteArray(svg.encode('utf-8'))).render(painter)
        painter.end()
        return QIcon(pix)

    def update_tool_icons(self):
        for name,btn in getattr(self,'tool_buttons',{}).items():
            btn.setIcon(self.coloured_tool_icon(name))
            btn.setIconSize(QSize(20,20))

    def set_individual_tool_color(self, name, color):
        if name not in self.tool_colors: return
        palette=HIGHLIGHTS if name=='Highlighter' else INKS
        if color not in palette: return
        self.tool_colors[name]=color
        self.folder_settings.setValue('experiment/tool_color/'+name, color)
        if self.tool==name:
            if name=='Highlighter': self.highlight_color=color
            elif name not in ('Move','Eraser'): self.pen_color=color
        self.update_tool_icons()

    def _settings_active_side(self):
        """Return a document viewport for a non-modal settings overlay.

        Split view: overlay the inactive side. Single view: overlay the
        right side of the visible document, with no page resizing.
        """
        if self.split_mode and self.reference_panel.isVisible():
            return (self.ref_scroll.viewport() if self._active_pdf_side=='student'
                    else self.scroll.viewport())
        # In Single View the active document may be Document 1 or Document 2.
        # Use the visible viewport so placement is beside the ribbon in both.
        return (self.scroll.viewport() if self._active_pdf_side == 'student'
                else self.ref_scroll.viewport())

    def _place_tool_settings(self, dialog, tool_name=None):
        """Anchor the floating box beside the clicked ribbon button.

        A single visible PDF occupies the LEFT of the ribbon. In split mode,
        the settings appear on whichever side has the inactive PDF. The box
        overlays the document: no splitter widths or page sizes are changed.
        """
        target = self._settings_active_side()
        ribbon = self.marking_tools_panel
        button = self.tool_buttons.get(tool_name or self._floating_tool_name)
        if target.width() <= 0 or target.height() <= 0:
            return

        margin = 8
        ribbon_top_left = ribbon.mapToGlobal(QPoint(0, 0))
        target_top_left = target.mapToGlobal(QPoint(0, 0))
        target_right = target_top_left.x() + target.width()
        target_bottom = target_top_left.y() + target.height()

        # Physical layout: the student PDF is to the left of the toolbar,
        # and the rubric PDF is to its right when split view is enabled.
        to_left = (not self.split_mode or target_right <= ribbon_top_left.x() + ribbon.width() // 2)
        if to_left:
            x = ribbon_top_left.x() - dialog.width() - margin
        else:
            x = ribbon_top_left.x() + ribbon.width() + margin

        # Stay inside the inactive document when the window is narrow.
        min_x = target_top_left.x() + margin
        max_x = max(min_x, target_right - dialog.width() - margin)
        x = max(min_x, min(x, max_x))

        # Align the settings box with the button which opened it.
        if button is not None:
            button_point = button.mapToGlobal(QPoint(0, button.height() // 2))
            y = button_point.y() - 22
        else:
            y = target_top_left.y() + margin
        min_y = target_top_left.y() + margin
        max_y = max(min_y, target_bottom - dialog.height() - margin)
        y = max(min_y, min(y, max_y))
        dialog.move(x, y)

    class _SettingsHeader(QFrame):
        """Draggable blue heading for a small floating settings dialog."""
        def __init__(self, parent=None):
            super().__init__(parent)
            self._drag_origin = None

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_origin = event.globalPosition().toPoint() - self.window().pos()
                event.accept()
            else:
                super().mousePressEvent(event)

        def mouseMoveEvent(self, event):
            if self._drag_origin is not None and event.buttons() & Qt.MouseButton.LeftButton:
                self.window().move(event.globalPosition().toPoint() - self._drag_origin)
                event.accept()
            else:
                super().mouseMoveEvent(event)

        def mouseReleaseEvent(self, event):
            self._drag_origin = None
            super().mouseReleaseEvent(event)

    def show_tool_settings(self, name):
        # A second double-click on the same tool hides its settings.
        if self._floating_tool_dialog is not None and self._floating_tool_name==name:
            self._floating_tool_dialog.close()
            return
        self.select_tool(name)
        if self._floating_tool_dialog is not None:
            self._floating_tool_dialog.close()
        if name == 'Emoji': return
        dialog=QDialog(self)
        dialog.setWindowTitle(('Part Marks' if name=='Marks' else name)+' Settings')
        # A consistent blue settings header, independent of Windows light/dark title bar theme.
        # The visible red X closes the dialog; double-clicking its ribbon icon also toggles it.
        dialog.setWindowFlags(Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        dialog.setStyleSheet('QDialog {background:#f7fbff; border:1px solid #8ca9c4;} QLabel {color:#174d88;}')
        layout=QVBoxLayout(dialog)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        head=self._SettingsHeader(dialog)
        head.setFixedHeight(32)
        head.setStyleSheet('QFrame {background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #075294,stop:1 #087ccc); border:0;}')
        head_layout=QHBoxLayout(head)
        head_layout.setContentsMargins(11,0,4,0)
        head_layout.setSpacing(6)
        title_label=QLabel(('Part Marks' if name=='Marks' else name)+' Settings')
        title_label.setStyleSheet('color:white; font-family:"Segoe UI"; font-size:12px; font-weight:normal; border:0; background:transparent;')
        title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        head_layout.addWidget(title_label,1)
        close_x=QPushButton('×',head)
        close_x.setFixedSize(25,24)
        close_x.setToolTip('Close settings')
        close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        close_x.setStyleSheet('QPushButton {background:#ce333b; color:white; border:0; border-radius:3px; font-size:17px; font-weight:bold;}'
                              'QPushButton:hover {background:#a91922;} QPushButton:pressed {background:#8a121c;}')
        close_x.clicked.connect(dialog.close)
        head_layout.addWidget(close_x)
        layout.addWidget(head)
        content=QWidget(dialog)
        content.setStyleSheet('QWidget {border:0; background:#f7fbff;}')
        content_layout=QVBoxLayout(content)
        content_layout.setContentsMargins(15,12,15,12)
        content_layout.setSpacing(9)
        if name in self.tool_colors:
            content_layout.addWidget(QLabel('Icon colour' if name in ('Move','Eraser') else 'Colour'))
            colours=HIGHLIGHTS if name=='Highlighter' else INKS
            swatches=QHBoxLayout()
            colour_buttons={}
            def refresh_colour_selection():
                selected=self.tool_colors.get(name)
                for colour,button in colour_buttons.items():
                    chosen=(colour==selected)
                    # The bold selection ring/check is visible without a colour-name label.
                    button.setText('✓' if chosen else '')
                    button.setStyleSheet(
                        'QPushButton {'
                        f'background-color:{colour};'
                        f'border:{"3px solid #075294" if chosen else "1px solid #9aafc4"};'
                        'border-radius:14px; padding:0px;'
                        f'color:{"#16283a" if colour.lower() in ("#ffe52f", "#63e961", "#ed89e6", "#80caf8") else "white"};'
                        'font-family:"Segoe UI"; font-size:16px; font-weight:bold;'
                        '}'
                    )
            def choose_colour(colour):
                self.set_individual_tool_color(name,colour)
                refresh_colour_selection()
            for color in colours:
                button=QPushButton()
                button.setFixedSize(28,28)
                button.setToolTip('')
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.clicked.connect(lambda checked=False,c=color:choose_colour(c))
                colour_buttons[color]=button
                swatches.addWidget(button)
            refresh_colour_selection()
            content_layout.addLayout(swatches)
        setting={
            'Pen':[('Thickness', 'pen_slider')],
            'Highlighter':[('Size','highlighter_slider'),('Opacity','opacity_slider')],
            'Eraser':[('Eraser size','eraser_slider')],
            'Tick':[('Tick size','stamp_slider')],
            'Cross':[('Cross size','cross_slider')],
            'Emoji':[('Emoji size','emoji_slider')],
            'Text':[('Text size','text_slider')],
            'Marks':[('Marks size','text_slider')],
            'Total Marks':[('Total marks size','text_slider')]
        }
        for caption,attr in setting.get(name,[]):
            original=getattr(self,attr,None)
            if original is None: continue
            content_layout.addWidget(QLabel(caption))
            slider=QSlider(Qt.Orientation.Horizontal)
            slider.setRange(original.minimum(),original.maximum())
            slider.setValue(original.value())
            slider.valueChanged.connect(original.setValue)
            original.valueChanged.connect(slider.setValue)
            # Mirror the displayed measurements from stable v10.1.
            # Pen uses half-pixel steps (1..4 = 0.5..2 px);
            # opacity is a percentage, and all other sizes are pixels.
            def display_size(value, slider_name=attr):
                if slider_name == 'pen_slider':
                    return f'{value * 0.5:g} px'
                if slider_name == 'opacity_slider':
                    return f'{value}%'
                return f'{value} px'
            value_label = QLabel(display_size(slider.value()))
            value_label.setObjectName('sliderValueLabel')
            value_label.setFixedWidth(56)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            slider.valueChanged.connect(lambda value, lab=value_label, name=attr:
                                        lab.setText(f'{value * 0.5:g} px' if name == 'pen_slider'
                                                    else f'{value}%' if name == 'opacity_slider'
                                                    else f'{value} px'))
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(slider, 1)
            row.addWidget(value_label)
            content_layout.addLayout(row)
        layout.addWidget(content)
        dialog.adjustSize()
        self._floating_tool_dialog=dialog
        self._floating_tool_name=name
        def clear_dialog(result):
            if self._floating_tool_dialog is dialog:
                self._floating_tool_dialog=None
                self._floating_tool_name=None
        dialog.finished.connect(clear_dialog)
        self._place_tool_settings(dialog, name)
        # Make the floating settings window active as soon as it appears.
        # Without this, Qt/Windows can open a tool window without activating it,
        # making users click it a second time before using its controls.
        dialog.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        # Reapply activation after Qt completes the show event on Windows.
        QTimer.singleShot(0, lambda d=dialog: (d.raise_(), d.activateWindow())
                          if d.isVisible() else None)

    def select_tool(self,name):
        if (self._floating_tool_dialog is not None and
                self._floating_tool_name != name):
            self._floating_tool_dialog.close()
        # Restore each tool's colour on selection: it is not shared with other tools.
        previous=getattr(self,'tool',None)
        if previous and previous in self.tool_colors and previous==name:
            pass
        self.tool=name
        if name=='Highlighter':
            self.highlight_color=self.tool_colors.get(name,HIGHLIGHTS[0])
        elif name in self.tool_colors and name not in ('Move','Eraser'):
            self.pen_color=self.tool_colors[name]
        for n,b in self.tool_buttons.items():b.setChecked(n==name)
        self.update_tool_icons()
        self.canvas.update()
        self.canvas.setCursor(Qt.CursorShape.OpenHandCursor if name=='Move' else Qt.CursorShape.CrossCursor)
        if hasattr(self,'ref_image'):
            self.ref_image.setCursor(Qt.CursorShape.OpenHandCursor if name=='Move' else Qt.CursorShape.CrossCursor)
        if name != 'Eraser' and hasattr(self,'ref_image'):
            self.ref_image.eraser_hover=None
            self.ref_image.update()

    def refresh_color_buttons(self):
        for mapping,active in ((getattr(self,'pen_buttons',{}),self.pen_color),
                               (getattr(self,'highlight_buttons',{}),self.highlight_color)):
            for color,button in mapping.items():
                button.setIcon(self.swatch_icon(color, color==active))
                hint=button.property('shortcutHint')
                color_name={'#151515':'Black','#075ef7':'Blue','#ed2024':'Red','#0a9863':'Green',
                            '#ffe52f':'Yellow','#63e961':'Green','#ed89e6':'Pink','#80caf8':'Light Blue'}.get(color,color)
                button.setToolTip(str(hint) if hint else color_name)

    def set_pen_color(self,c):
        if c not in INKS:return
        self.pen_color=c
        if self.tool in self.tool_colors and self.tool not in ('Highlighter','Move','Eraser'):
            self.tool_colors[self.tool]=c
            self.folder_settings.setValue('experiment/tool_color/'+self.tool,c)
        self.update_tool_icons()
        if hasattr(self,'selected_color_label'):
            names=dict(zip(INKS,['Black','Blue','Red','Green']))
            self.selected_color_label.setText('Selected: '+names[c])
            self.selected_color_label.setStyleSheet('color:'+c+';font-weight:700;font-size:12px;')
        # Colour changes affect only the active tool; Emoji and Signature are fixed-colour.
        self.refresh_color_buttons()
        self.statusBar().showMessage('Selected marking colour: '+c,3000)
    def set_highlight_color(self,c):
        if c not in HIGHLIGHTS:return
        self.highlight_color=c
        self.tool_colors['Highlighter']=c
        self.folder_settings.setValue('experiment/tool_color/Highlighter',c)
        self.select_tool('Highlighter')
        self.refresh_color_buttons()
        self.statusBar().showMessage('Selected highlighter colour: '+c,3000)
    def set_stamp_size(self,v):self.stamp_size=v
    def set_cross_size(self,v):self.cross_size=v
    def set_emoji_size(self,v):self.emoji_size=v
    def set_text_size(self,v):self.text_size=v
    def set_emoji(self,v):self.emoji_choice=v
    def show_emoji_window(self):
        if not hasattr(self,'emoji_palette'):
            self.emoji_palette=EmojiPalette(self)
        self.select_tool('Emoji')
        palette=self.emoji_palette
        palette.adjustSize()
        palette.show()
        # Anchor the emoji picker exactly like the other ribbon settings:
        # beside Emoji, over the inactive PDF in split mode; to the left
        # of the far-right ribbon in single-page mode.  Keep it floating
        # so drag-and-drop onto the document continues to work.
        self._place_tool_settings(palette, 'Emoji')
        palette.raise_()
        palette.activateWindow()
    def set_pen_size(self,v):
        self.pen_size=float(v)*0.5

    def update_pen_size_label(self,v):
        # Keep the slider display in true pixel units rather than slider steps.
        label=self.pen_slider.parent().findChild(QLabel, 'sliderValueLabel') if False else None
        # The pen-size value label sits alongside the slider in the tools layout.
        layout=self.pen_slider.parentWidget().layout()
        for i in range(layout.count()):
            item=layout.itemAt(i)
            nested=item.layout() if item else None
            if nested and nested.indexOf(self.pen_slider)>=0:
                value_item=nested.itemAt(nested.indexOf(self.pen_slider)+1)
                if value_item and isinstance(value_item.widget(),QLabel):
                    value_item.widget().setText(f'{v*0.5:g}px')
                break
    def set_highlighter_size(self,v):self.highlighter_size=float(v)
    def set_opacity(self,v):self.highlight_opacity=v/100
    def set_eraser_size(self,v):self.eraser_size=float(v)
    def student_marks_text(self):
        return self.marks_total_label.text().removeprefix('Assignment: ').strip()

    def rubric_marks_text(self):
        return self.rubric_total_label.text().removeprefix('Rubric: ').strip()

    def update_marks_total(self):
        if not hasattr(self,'marks_total_label'):return
        total=Decimal('0')
        count=0
        for marks in self.strokes.values():
            for mark in marks:
                if mark.tool=='Marks':
                    try:
                        number=Decimal(mark.text)
                        if number.is_finite() and number>=0:
                            total+=number
                            count+=1
                    except InvalidOperation:pass
        self.marks_total_label.setText('Assignment: '+format(total.normalize(),'f'))
        self.marks_total_label.setToolTip(f'{count} student marks boxes across all pages')
        rubric_total=sum((Decimal(m['text']) for marks in self.rubric_marks.values() for m in marks if m.get('type','part')=='part'),Decimal('0'))
        self.rubric_total_label.setText('Rubric: '+format(rubric_total.normalize(),'f'))
        # Synchronise all placed total stamps with their respective document totals.
        # Total stamps are display-only: they never contribute to the sums.
        student_text='Total: '+format(total.normalize(),'f')
        rubric_text='Total: '+format(rubric_total.normalize(),'f')
        student_changed=False
        rubric_changed=False
        for marks in self.strokes.values():
            for mark in marks:
                if mark.tool=='Total Marks' and mark.text!=student_text:
                    mark.text=student_text
                    student_changed=True
        for marks in self.rubric_marks.values():
            for mark in marks:
                if mark.get('type')=='total' and mark.get('text')!=rubric_text:
                    mark['text']=rubric_text
                    rubric_changed=True
        if student_changed:
            if hasattr(self,'canvas'):self.update_all_student_pages()
            self.dirty=True
        if rubric_changed:
            if hasattr(self,'ref_image'):self.update_all_rubric_pages()
            self.rubric_dirty=True

    def set_dirty(self,value):
        self.update_marks_total()
        self.dirty=value
        # Keep the Windows title bar clean; PDF name and save state live in the bottom bar.
        self.setWindowTitle('PDF Assignment Marker')
    def _confirm_discard_changes(self, side):
        dirty = self.rubric_dirty if side == 'rubric' else self.dirty
        if not dirty:
            return True
        filename = (self.rubric_path if side == 'rubric' else self.path) or ('Document 1' if side == 'rubric' else 'Document 2')
        response = QMessageBox.question(
            self, 'Unsaved markings',
            f'{os.path.basename(filename)} contains unsaved markings.\n\nDiscard these changes?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        return response == QMessageBox.StandardButton.Yes

    def confirm_close_document(self):
        return self._confirm_discard_changes('student')

    def confirm_close_rubric(self):
        return self._confirm_discard_changes('rubric')
    def lock_centre_panel(self):
        """Keep the tools stationary: equal-width PDF panes and non-draggable separators."""
        for i in range(1, self.split.count()):
            handle = self.split.handle(i)
            if handle:
                handle.setEnabled(False)
        if self.split_mode:
            self.split.setStretchFactor(1, 1)
            self.split.setStretchFactor(2, 0)
            self.split.setStretchFactor(3, 1)
        else:
            self.split.setStretchFactor(1, 1)
            self.split.setStretchFactor(2, 0)
            self.split.setStretchFactor(3, 0)

    def _sync_bottom_status_layout(self):
        """Align each document's one-line status with its corresponding PDF pane."""
        if not hasattr(self, 'bottom_status_row'):
            return
        thumbs = self.pages_panel if getattr(self, '_thumbnails_open', False) else None
        thumb_w = thumbs.width() if thumbs and thumbs.isVisible() else 0
        tools_w = self.marking_tools_panel.width()
        self.bottom_thumb_spacer.setFixedWidth(thumb_w)
        self.bottom_tools_spacer.setFixedWidth(tools_w)
        # Reorder the single visible document before the marking ribbon.
        bar_layout = self.bottom_status_row.layout()
        first_doc = (self.bottom_rubric_nav if self.split_mode or
                     self._active_pdf_side == 'rubric' else self.bottom_student_nav)
        bar_layout.removeWidget(first_doc)
        bar_layout.insertWidget(1, first_doc)
        if self.split_mode:
            self.bottom_rubric_nav.show()
            self.bottom_student_nav.show()
            self.bottom_rubric_nav.setFixedWidth(max(1,self.reference_panel.width()))
            self.bottom_student_nav.setFixedWidth(max(1,self.student_workspace.width()))
        else:
            show_student = self._active_pdf_side == 'student'
            self.bottom_student_nav.setVisible(show_student)
            self.bottom_rubric_nav.setVisible(not show_student)
            shown = self.bottom_student_nav if show_student else self.bottom_rubric_nav
            shown.setFixedWidth(max(1, self.student_workspace.width() if show_student else self.reference_panel.width()))

    def restore_page_entry(self, side):
        """Restore an invalid or abandoned navigation entry."""
        field = self.rubric_page_number if side == 'rubric' else self.student_page_number
        if not field.hasFocus():
            self.refresh_page_navigation()

    def jump_to_page_entry(self, side):
        """Navigate to an explicitly entered 1-based page number."""
        field = self.rubric_page_number if side == 'rubric' else self.student_page_number
        doc = self.rubric_doc if side == 'rubric' else self.doc
        try:
            target = int(field.text().strip())
        except ValueError:
            target = -1
        if doc and 1 <= target <= len(doc):
            if side == 'rubric':
                self.rubric_page_selected(target)
            else:
                self.go_page(target-1)
        else:
            self.refresh_page_navigation()
        field.clearFocus()
        self.refresh_page_navigation()

    def position_single_page_ribbon(self):
        """Keep the fixed-width marking ribbon at the far-right of single view."""
        if not hasattr(self, 'split') or self.split_mode:
            return
        available = self.split.width()
        width = self.marking_tools_panel.width()
        # The hidden page-list and reference widgets receive no space.
        # The visible active document takes the width left of the ribbon.
        thumb_width = self.pages_panel.width() if getattr(self, '_thumbnails_open', False) else 0
        page_width = max(0, available - thumb_width - width - (2 if thumb_width else 1)*self.split.handleWidth())
        self.split.setSizes([thumb_width, page_width, width, 0])
        self._sync_bottom_status_layout()

    def center_tools_panel(self):
        """Keep the fixed-width tool column exactly between equal document panes."""
        if not hasattr(self, 'split') or not self.split_mode:
            return
        available = self.split.width()
        centre = self.marking_tools_panel.width()
        handle_space = self.split.handleWidth() * 2
        side = max(0, (available - centre - handle_space) // 2)
        self.split.setSizes([0, side, centre, side])
        self._sync_bottom_status_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, 'split_mode', False):
            QTimer.singleShot(0, self.center_tools_panel)
        else:
            QTimer.singleShot(0, self.position_single_page_ribbon)

    def _schedule_split_width_fit(self):
        """Coalesce Split View fit until Qt finishes sizing both PDF viewports.

        Running fit in the same event-loop turn as QSplitter.setSizes() can
        measure the previous (Single View) viewport width. A short single-shot
        delay reads the final geometry and does not rebuild the PDF stacks.
        """
        if not self.split_mode or not (self.doc or self.rubric_doc):
            return
        timer = getattr(self, '_split_fit_timer', None)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(self._apply_split_width_fit)
            self._split_fit_timer = timer
        timer.start(90)

    def _apply_split_width_fit(self):
        if not self.split_mode:
            return
        # Only fit once both pane viewports have their real, visible widths.
        for pdf, area in ((self.doc, self.scroll),
                          (self.rubric_doc, self.ref_scroll)):
            if pdf is not None and (not area.isVisible() or area.viewport().width() < 120):
                self._schedule_split_width_fit()
                return
        self.set_shared_initial_zoom()
        # Split View should start with the PDF centred in each document pane.
        # Defer until zoomed page and scrollbar geometries have settled.
        QTimer.singleShot(0, self._center_split_pdf_pages)

    def _center_split_pdf_pages(self):
        """Centre each PDF horizontally after a Split View fit.

        The outer scroll areas already use AlignHCenter, and each page widget
        is aligned in its vertical stack. Centre the horizontal scroll range
        too: a previous 217% Single View can leave it at the former offset.
        This runs only after a view transition, not during user panning.
        """
        if not self.split_mode:
            return
        for doc, area in ((self.rubric_doc, self.ref_scroll),
                          (self.doc, self.scroll)):
            if doc is None or not area.isVisible():
                continue
            area.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
            bar = area.horizontalScrollBar()
            # Usually zero after fit-to-width; for mixed-width PDF pages,
            # centre the oversize page instead of anchoring it to the left.
            bar.setValue((bar.minimum() + bar.maximum()) // 2)

    def on_splitter_moved(self, pos, index):
        """Fit after Split View's viewport geometries stabilise."""
        if self.split_mode and (self.rubric_doc or self.doc):
            self._schedule_split_width_fit()
        elif self.doc and self.student_auto_fit_width:
            self.fit_width()

    def _set_thumbnail_toggle_enabled(self, enabled):
        """Match the approved ribbon; grey out icon and caption when unavailable."""
        self.thumbnail_toggle.setEnabled(enabled)
        self._thumbnail_grey_effect.setStrength(0.0 if enabled else 1.0)
        label_colour = '#174c81' if enabled else '#9ba3ae'
        self._thumbnail_caption_label.setStyleSheet(
            'QLabel#hybridRibbonCaption {background:transparent; border:none; '
            f'color:{label_colour}; padding:0px;}}')

    def show_single_view(self):
        """Show the currently active PDF alone; preserve both documents' state."""
        if not self.split_mode:
            return
        if self._floating_tool_dialog is not None:
            self._floating_tool_dialog.close()
        self.canvas.finish_editor()
        self.ref_image.finish_editor()
        self.split_mode = False
        if getattr(self, '_split_fit_timer', None) is not None:
            self._split_fit_timer.stop()
        self._set_thumbnail_toggle_enabled(
            self.rubric_doc is not None if self._active_pdf_side == 'rubric' else self.doc is not None
        )
        show_student = self._active_pdf_side == 'student'
        self.reference_panel.setVisible(not show_student)
        self.student_workspace.setVisible(show_student)
        if show_student:
            self.split.insertWidget(1, self.student_workspace)
            self.split.insertWidget(2, self.marking_tools_panel)
            self.split.setSizes([0, 1100, 44, 0])
        else:
            self.split.insertWidget(1, self.reference_panel)
            self.split.insertWidget(2, self.marking_tools_panel)
            self.split.setSizes([0, 1100, 44, 0])
        self.lock_centre_panel()
        QTimer.singleShot(0, self.position_single_page_ribbon)
        QTimer.singleShot(0, self._refresh_active_pdf_borders)
        QTimer.singleShot(0, self._sync_bottom_status_layout)
        QTimer.singleShot(0, self._refresh_shared_header)
        if self.doc or self.rubric_doc:
            QTimer.singleShot(0, self.set_shared_initial_zoom)

    def show_split_view(self):
        """Always show Document 1 and Document 2, with ribbon between them."""
        if self.split_mode:
            return
        if self._floating_tool_dialog is not None:
            self._floating_tool_dialog.close()
        self.canvas.finish_editor()
        self.ref_image.finish_editor()
        self._hide_page_thumbnails()
        self._set_thumbnail_toggle_enabled(False)
        self.split_mode = True
        self.reference_panel.show()
        self.student_workspace.show()
        self.split.insertWidget(1, self.reference_panel)
        self.split.insertWidget(2, self.marking_tools_panel)
        self.split.insertWidget(3, self.student_workspace)
        self.split.setSizes([0, 560, 44, 560])
        self.lock_centre_panel()
        QTimer.singleShot(0, self.center_tools_panel)
        QTimer.singleShot(0, self._refresh_active_pdf_borders)
        QTimer.singleShot(0, self._sync_bottom_status_layout)
        QTimer.singleShot(0, self._refresh_shared_header)
        if self.doc or self.rubric_doc:
            # Fit AFTER both viewports reach their final Split View widths.
            # Keep the existing page images visible until the new scale is ready.
            self._schedule_split_width_fit()

    def toggle_split_view(self):
        """Compatibility shim for existing toggle callers."""
        if self.split_mode:
            self.show_single_view()
        else:
            self.show_split_view()

    @staticmethod
    def _open_pdf_without_file_lock(path):
        """Load an editable PDF into memory, releasing the input file handle.

        Windows can refuse an atomic Save-to-original replacement while PyMuPDF
        still owns an open handle to that same path. Keep the real path separately
        for folder navigation and background page rendering.
        """
        with open(path, 'rb') as source:
            pdf_bytes = source.read()
        return fitz.open(stream=pdf_bytes, filetype='pdf')

    def open_rubric(self, path=None, skip_unsaved_prompt=False):
        # QAction/QPushButton may pass a boolean; treat it as no provided path.
        if not isinstance(path, (str, os.PathLike)):
            path,_=QFileDialog.getOpenFileName(self,'Open PDF',self.remembered_folder('rubric_open'),'PDF Files (*.pdf)')
        if not path:return
        path=os.fspath(path)
        # Finalise pending text before checking for unsaved annotations.
        # Otherwise opening another PDF could discard an edit still in its editor.
        if self.rubric_doc is not None and not skip_unsaved_prompt:
            self.ref_image.finish_editor()
            if not self.confirm_close_rubric():
                return
        self.remember_folder('rubric_open',path)
        try:
            doc=self._open_pdf_without_file_lock(path)
            if doc.needs_pass or len(doc)==0:
                doc.close()
                raise ValueError('PDF is empty or password protected')
        except Exception as exc:
            QMessageBox.warning(self,'Cannot open reference PDF',str(exc));return
        self._cancel_background_render('rubric')
        if self.rubric_doc:self.rubric_doc.close()
        self.rubric_doc=doc;self.rubric_page=0;self.ref_auto_fit=False;self.rubric_path=path;self.rubric_marks={};self.rubric_strokes={};self.rubric_history=[];self.rubric_future=[];self.rubric_dirty=False;self._rubric_saved_once=False;self.rubric_saved_target=None;self.update_marks_total()
        self._clear_page_stack(self.rubric_stack_layout)
        self.rubric_pages=[]
        self.update_actions()
        # Initial zoom does the rendering; don't build the same page stack twice.
        # When Split View is already open, its pane size may still be changing.
        # Apply a bounded initial fit, then settle/centre after the new stack loads.
        QTimer.singleShot(0, self.set_shared_initial_zoom)
        if self.split_mode:
            self._schedule_split_width_fit()

    def close_rubric(self):
        if self.rubric_doc is not None:
            self.ref_image.finish_editor()
            if not self.confirm_close_rubric():return
        self._cancel_background_render('rubric')
        if self.rubric_doc:self.rubric_doc.close()
        self.rubric_doc=None;self.rubric_page=0;self.rubric_marks={};self.rubric_strokes={};self.rubric_history=[];self.rubric_future=[];self.rubric_dirty=False;self._rubric_saved_once=False;self.rubric_saved_target=None;self.update_marks_total()
        self._clear_page_stack(self.rubric_stack_layout)
        self.rubric_pages=[]
        self.rubric_path=None
        self._update_document_heading('rubric')
        self.ref_image=RubricCanvas(self,0)
        self.rubric_stack_layout.addWidget(self.ref_image,0,Qt.AlignmentFlag.AlignHCenter)
        self.refresh_page_navigation();self.update_actions()

    def student_page_selected(self, value):
        self.go_page(value-1)

    def rubric_page_selected(self, value):
        self.rubric_page=max(0,min(len(self.rubric_doc)-1,value-1)) if self.rubric_doc else 0
        self.jump_to_rubric_page()

    def update_all_student_pages(self):
        for page in getattr(self,'student_pages',[]):page.update()
    def update_all_rubric_pages(self):
        for page in getattr(self,'rubric_pages',[]):page.update()

    def refresh_page_navigation(self):
        student_total=len(self.doc) if self.doc else 0
        rubric_total=len(self.rubric_doc) if self.rubric_doc else 0
        if not self.student_page_number.hasFocus():
            self.student_page_number.setText(str(self.page_index+1) if student_total else '0')
        if not self.rubric_page_number.hasFocus():
            self.rubric_page_number.setText(str(self.rubric_page+1) if rubric_total else '0')
        self.student_page_count.setText(f'/ {student_total}')
        self.rubric_page_count.setText(f'/ {rubric_total}')
        self.student_page_number.setEnabled(student_total > 0)
        self.rubric_page_number.setEnabled(rubric_total > 0)
        self.student_page_previous.setEnabled(student_total>0 and self.page_index>0)
        self.student_page_next.setEnabled(student_total>0 and self.page_index<student_total-1)
        self.rubric_page_previous.setEnabled(rubric_total>0 and self.rubric_page>0)
        self.rubric_page_next.setEnabled(rubric_total>0 and self.rubric_page<rubric_total-1)
        self._sync_thumbnail_selection()

    def _clear_page_stack(self, layout):
        # Release the previous document's horizontal extent before rebuilding.
        # The outer PDF viewport remains free to shrink in Split View.
        owner = layout.parentWidget()
        if owner is not None:
            owner.setMinimumWidth(0)
        while layout.count():
            item=layout.takeAt(0)
            w=item.widget()
            if w is not None:
                if hasattr(w,'finish_editor'):w.finish_editor()
                w.setParent(None)
                w.deleteLater()

    def _update_page_stack_width(self, side):
        """Keep oversized page widths scrollable, not transferred to the pane.

        QScrollArea stays widget-resizable as in the original working renderer.
        A minimum width on its INNER page stack gives the horizontal scrollbar
        a real scroll range, while the outer scroll area keeps Ignored sizing.
        No page pixmaps, visibility calculations or render schedules change.
        """
        stack = self.rubric_stack if side == 'rubric' else self.student_stack
        canvases = self.rubric_pages if side == 'rubric' else self.student_pages
        # The two inner page layouts have 12px left and right margins.
        required = max((page.width() for page in canvases), default=0)
        stack.setMinimumWidth(required + 24 if required else 0)

    def _visible_pdf_pages(self, scroll, canvases):
        """Return pages near the viewport, avoiding rasterization of offscreen pages."""
        top=scroll.verticalScrollBar().value()
        bottom=top+max(1,scroll.viewport().height())
        selected=[]
        for i,canvas in enumerate(canvases):
            y=canvas.y()
            if y+canvas.height()>=top-250 and y<=bottom+250:
                selected.append(i)
        return selected

    def _render_visible_student_pages(self):
        if not self.doc:return
        for i in self._visible_pdf_pages(self.scroll,self.student_pages):
            canvas=self.student_pages[i]
            if canvas.paper.isNull():
                try:
                    canvas.paper=qt_pixmap(self.doc[i],self.zoom)
                    canvas.update()
                    self._remember_rendered_page('student', i)
                except Exception:
                    pass

    def _render_visible_rubric_pages(self):
        if not self.rubric_doc:return
        for i in self._visible_pdf_pages(self.ref_scroll,self.rubric_pages):
            canvas=self.rubric_pages[i]
            if canvas.pixmap().isNull():
                try:
                    canvas.setPixmap(qt_pixmap(self.rubric_doc[i],canvas.scale))
                    self._remember_rendered_page('rubric', i)
                except Exception:
                    pass

    def _remember_rendered_page(self, side, index):
        """Bound raster memory; never evict pages currently on screen."""
        order = self._page_cache_order[side]
        if index in order:
            order.remove(index)
        order.append(index)
        canvases = self.student_pages if side == 'student' else self.rubric_pages
        scroll = self.scroll if side == 'student' else self.ref_scroll
        protected = set(self._visible_pdf_pages(scroll, canvases))
        while len(order) > self._max_cached_pages:
            victim = next((i for i in order if i not in protected), None)
            if victim is None:
                break
            order.remove(victim)
            if victim >= len(canvases):
                continue
            canvas = canvases[victim]
            if side == 'student':
                canvas.paper = QPixmap()
                canvas.update()
            else:
                # Avoid RubricCanvas.setPixmap here: it finalizes an editor.
                QLabel.setPixmap(canvas, QPixmap())
                canvas.update()

    def _nearby_pending_pages(self, side):
        """Only pre-render a small moving window; don't rasterize 131 pages at once."""
        canvases = self.student_pages if side == 'student' else self.rubric_pages
        scroll = self.scroll if side == 'student' else self.ref_scroll
        if not canvases:
            return []
        visible = self._visible_pdf_pages(scroll, canvases)
        anchor = visible[0] if visible else (self.page_index if side == 'student' else self.rubric_page)
        indices = sorted(range(len(canvases)), key=lambda i: abs(i-anchor))[:self._max_cached_pages]
        return [i for i in indices if (canvases[i].paper.isNull() if side == 'student'
                        else canvases[i].pixmap().isNull())]

    def _cancel_background_render(self, side):
        self._render_generation[side] += 1
        self._page_cache_order[side].clear()
        for worker in self._background_renderers:
            if getattr(worker, 'side', '') == side:
                worker.requestInterruption()

    def _launch_background_render(self, side, path, scale, pages):
        if not path or not pages:
            return
        if any(w.side == side and w.isRunning() and
               not w.isInterruptionRequested() for w in self._background_renderers):
            return
        generation = self._render_generation[side]
        document = self.doc if side == 'student' else self.rubric_doc
        rotations = {i: document[i].rotation for i in pages} if document else {}
        worker = BackgroundPdfRenderer(path, scale, pages, generation,
                                       rotations=rotations, parent=self)
        worker.side = side
        self._background_renderers.append(worker)
        worker.page_ready.connect(lambda gen, idx, image, kind=side:
                                  self._accept_background_page(kind, gen, idx, image))
        worker.finished.connect(lambda w=worker: self._background_renderers.remove(w)
                                if w in self._background_renderers else None)
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def _accept_background_page(self, side, generation, index, image):
        # Discard results from earlier zoom levels, PDFs, or pane rebuilds.
        if generation != self._render_generation[side]:
            return
        if side == 'student':
            if index < len(self.student_pages):
                canvas = self.student_pages[index]
                if (canvas.paper.isNull() or index in self._zoom_preview_pages['student']
                        or (index == 0 and self._preview_pending["student"])):
                    self._zoom_preview_pages['student'].discard(index)
                    self._preview_pending["student"] = False
                    canvas.paper = QPixmap.fromImage(image)
                    canvas.update()
                    self._remember_rendered_page('student', index)
        else:
            if index < len(self.rubric_pages):
                canvas = self.rubric_pages[index]
                if (canvas.pixmap().isNull() or index in self._zoom_preview_pages['rubric']
                        or (index == 0 and self._preview_pending["rubric"])):
                    self._zoom_preview_pages['rubric'].discard(index)
                    self._preview_pending["rubric"] = False
                    canvas.setPixmap(QPixmap.fromImage(image))
                    self._remember_rendered_page('rubric', index)

    def _zoom_existing_pages(self, side):
        """Retain the existing page stack during zoom; never flash/rebuild it.

        Only a fully populated stack is eligible. Initial document loading and
        page rotation continue to use the original incremental render path.
        Previous images serve as temporary scaled previews of visible pages.
        """
        rubric = side == 'rubric'
        doc = self.rubric_doc if rubric else self.doc
        pages = self.rubric_pages if rubric else self.student_pages
        if (not doc or len(pages) != len(doc) or not pages
                or self._building_pages[side]):
            return False
        scroll = self.ref_scroll if rubric else self.scroll
        stack = self.rubric_stack if rubric else self.student_stack
        zoom = self.ref_zoom if rubric else self.zoom
        active_index = min(len(pages) - 1,
                           self.rubric_page if rubric else self.page_index)
        # Save the viewport's relative position within the active page before
        # changing geometry, including when the book has mixed page sizes.
        old_scroll = scroll.verticalScrollBar().value()
        anchor = min(range(len(pages)), key=lambda i:
                     abs(pages[i].y() - old_scroll))
        old_page = pages[anchor]
        old_fraction = ((old_scroll - old_page.y()) /
                        max(1, old_page.height()))
        visible_before = set(self._visible_pdf_pages(scroll, pages))
        # Preserve images that are already cached, including pages that may
        # enter the viewport after the pane is resized. This avoids gaps in
        # the initial Single -> Split transition.
        cached = {i for i, canvas in enumerate(pages)
                  if not (canvas.pixmap().isNull() if rubric else canvas.paper.isNull())}
        keep = visible_before | {anchor, active_index} | cached
        self._cancel_background_render(side)
        generation = self._render_generation[side]
        self._zoom_preview_pages[side].clear()
        scroll.setUpdatesEnabled(False)
        stack.setUpdatesEnabled(False)
        try:
            for i, canvas in enumerate(pages):
                page = doc[i]
                new_scale = zoom
                if rubric:
                    canvas.scale = new_scale
                width = max(1, round(page.rect.width * new_scale))
                height = max(1, round(page.rect.height * new_scale))
                old_pix = canvas.pixmap() if rubric else canvas.paper
                # Keep previews only around the viewport to bound image memory.
                if i in keep and old_pix is not None and not old_pix.isNull():
                    preview = old_pix.scaled(width, height,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.FastTransformation)
                    if rubric:
                        # Do not call RubricCanvas.setPixmap: it finishes editing.
                        QLabel.setPixmap(canvas, preview)
                    else:
                        canvas.paper = preview
                    self._zoom_preview_pages[side].add(i)
                else:
                    if rubric:
                        QLabel.setPixmap(canvas, QPixmap())
                    else:
                        canvas.paper = QPixmap()
                canvas.setFixedSize(width, height)
            # Preserve a horizontal scroll range at the new magnification.
            self._update_page_stack_width(side)
            stack.layout().activate()
            page = pages[anchor]
            new_scroll = page.y() + round(old_fraction * page.height())
            scroll.verticalScrollBar().setValue(max(0, new_scroll))
            # Render any newly visible uncached pages at the new scale before
            # releasing the redraw lock. Background prefetch still handles
            # neighbouring pages once the zoom settles.
            if rubric:
                self._render_visible_rubric_pages()
            else:
                self._render_visible_student_pages()
        finally:
            stack.setUpdatesEnabled(True)
            scroll.setUpdatesEnabled(True)
            scroll.viewport().update()
        # A separate timer for each PDF pane; resetting it does not make the
        # zoom itself sluggish. Toolbar and wheel zoom both use this method.
        timer = self._zoom_settle_timers.get(side)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            self._zoom_settle_timers[side] = timer
            timer.timeout.connect(lambda k=side: self._finish_zoom_preview(k))
        timer.start(130)
        return True

    def _finish_zoom_preview(self, side):
        """Replace viewport previews with current-scale page images only."""
        rubric = side == 'rubric'
        doc = self.rubric_doc if rubric else self.doc
        pages = self.rubric_pages if rubric else self.student_pages
        if not doc or not pages or self._building_pages[side]:
            return
        scroll = self.ref_scroll if rubric else self.scroll
        visible = self._visible_pdf_pages(scroll, pages)
        # Pages with no cached image are synchronously rendered on demand;
        # existing low-resolution previews are upgraded on the background thread.
        if rubric:
            self._render_visible_rubric_pages()
        else:
            self._render_visible_student_pages()
        preview = self._zoom_preview_pages[side]
        candidates = [i for i in visible if i in preview]
        if candidates:
            path = self.rubric_path if rubric else self.path
            scale = self.ref_zoom if rubric else self.zoom
            self._launch_background_render(side, path, scale, candidates)
        else:
            self._start_rubric_prefetch() if rubric else self._start_student_prefetch()

    def _start_student_prefetch(self):
        if not self.doc or not self.student_pages or self._building_pages["student"]:
            return
        timer = self._zoom_settle_timers.get('student')
        if timer is not None and timer.isActive():
            return
        self._render_visible_student_pages()
        pending = (list(i for i in self._visible_pdf_pages(self.scroll, self.student_pages)
                        if i in self._zoom_preview_pages['student'])
                   + self._nearby_pending_pages('student'))
        self._launch_background_render('student', self.path, self.zoom,
                                       list(dict.fromkeys(pending)))

    def _start_rubric_prefetch(self):
        if not self.rubric_doc or not self.rubric_pages or self._building_pages["rubric"]:
            return
        timer = self._zoom_settle_timers.get('rubric')
        if timer is not None and timer.isActive():
            return
        self._render_visible_rubric_pages()
        pending = (list(i for i in self._visible_pdf_pages(self.ref_scroll, self.rubric_pages)
                        if i in self._zoom_preview_pages['rubric'])
                   + self._nearby_pending_pages('rubric'))
        self._launch_background_render('rubric', self.rubric_path,
                                       self.ref_zoom, list(dict.fromkeys(pending)))

    def sync_student_scroll(self, value):
        if not self.doc or not self.student_pages:return
        QTimer.singleShot(0,self._render_visible_student_pages)
        QTimer.singleShot(150,self._start_student_prefetch)
        centre=value+self.scroll.viewport().height()*.35
        index=min(range(len(self.student_pages)), key=lambda i:abs(
            self.student_pages[i].y()+self.student_pages[i].height()/2-centre))
        if index!=self.page_index:
            self.page_index=index
            self.canvas=self.student_pages[index]
            self.refresh_page_navigation()

    def sync_rubric_scroll(self, value):
        if not self.rubric_doc or not self.rubric_pages:return
        QTimer.singleShot(0,self._render_visible_rubric_pages)
        QTimer.singleShot(150,self._start_rubric_prefetch)
        centre=value+self.ref_scroll.viewport().height()*.35
        index=min(range(len(self.rubric_pages)), key=lambda i:abs(
            self.rubric_pages[i].y()+self.rubric_pages[i].height()/2-centre))
        if index!=self.rubric_page:
            self.rubric_page=index
            self.ref_image=self.rubric_pages[index]
            self.refresh_page_navigation()

    def jump_to_rubric_page(self):
        if self.rubric_pages and 0<=self.rubric_page<len(self.rubric_pages):
            self.ref_image=self.rubric_pages[self.rubric_page]
            self.ref_scroll.verticalScrollBar().setValue(self.ref_image.y())
            QTimer.singleShot(0,self._render_visible_rubric_pages)
        QTimer.singleShot(200,self._start_rubric_prefetch)
        self.refresh_page_navigation()

    def navigate_rubric(self,step):
        if self.rubric_doc:
            self.ref_image.finish_editor()
            self.rubric_page=max(0,min(len(self.rubric_doc)-1,self.rubric_page+step))
            self.jump_to_rubric_page()

    def _rubric_canvas_for_page(self, index):
        page=self.rubric_doc[index]
        width=max(100,self.ref_scroll.viewport().width()-38)
        scale=min(3.50,width/page.rect.width) if self.ref_auto_fit else self.ref_zoom
        canvas=RubricCanvas(self,index)
        canvas.installEventFilter(self)
        canvas.scale=scale
        canvas.setFixedSize(max(1,round(page.rect.width*scale)),
                            max(1,round(page.rect.height*scale)))
        self.rubric_stack_layout.addWidget(canvas,0,Qt.AlignmentFlag.AlignHCenter)
        self.rubric_pages.append(canvas)
        self._update_page_stack_width('rubric')
        return canvas

    def _continue_rubric_pages(self, generation):
        if generation != self._render_generation['rubric'] or not self.rubric_doc:
            return
        end=min(len(self.rubric_doc),len(self.rubric_pages)+12)
        for i in range(len(self.rubric_pages),end):
            self._rubric_canvas_for_page(i)
        if len(self.rubric_pages)<len(self.rubric_doc):
            QTimer.singleShot(0,lambda g=generation:self._continue_rubric_pages(g))
        else:
            self._building_pages['rubric']=False
            if self.rubric_page<len(self.rubric_pages):
                self.ref_image=self.rubric_pages[self.rubric_page]
                self.ref_scroll.verticalScrollBar().setValue(self.ref_image.y())
            QTimer.singleShot(0,self._render_visible_rubric_pages)
            QTimer.singleShot(60,self._start_rubric_prefetch)

    def render_rubric(self):
        if not self.rubric_doc:return
        self._zoom_preview_pages['rubric'].clear()
        self._cancel_background_render('rubric')
        self._building_pages['rubric']=True
        self._preview_pending['rubric']=False
        self._clear_page_stack(self.rubric_stack_layout)
        self.rubric_pages=[]
        canvas=self._rubric_canvas_for_page(0)
        self.ref_image=canvas
        self.ref_zoom_label.setText(f'{round(canvas.scale*100)}%');self._refresh_shared_header()
        if self.split_mode:
            QTimer.singleShot(0, self.center_tools_panel)
        if self.rubric_page==0:
            try:
                preview_scale=min(canvas.scale,.55)
                preview=qt_pixmap(self.rubric_doc[0],preview_scale)
                canvas.setPixmap(preview.scaled(canvas.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.FastTransformation))
                self._preview_pending['rubric']=preview_scale<canvas.scale
            except Exception:
                pass
        generation=self._render_generation['rubric']
        self.refresh_page_navigation()
        QTimer.singleShot(0,lambda g=generation:self._continue_rubric_pages(g))
        if self._preview_pending['rubric']:
            QTimer.singleShot(35,lambda g=generation:self._launch_background_render(
                'rubric',self.rubric_path,self.ref_zoom,[0])
                if self._render_generation['rubric']==g else None)
        elif canvas.pixmap().isNull():
            QTimer.singleShot(0,self._render_visible_rubric_pages)

    def confirm_replace_existing(self, target):
        """Ask before replacing an existing output; protect source files upstream."""
        if not os.path.exists(target):
            return True
        response = QMessageBox.question(
            self, 'Replace existing PDF?',
            f'A PDF named "{os.path.basename(target)}" already exists.\n\n'
            'Do you want to replace it? The existing file will be overwritten.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        return response == QMessageBox.StandardButton.Yes

    def commit_saved_pdf(self, pending, target):
        """Replace the destination only after a complete file has been built."""
        # Stage on the destination filesystem so os.replace is atomic there.
        target_folder = os.path.dirname(os.path.abspath(target))
        staged = None
        try:
            with tempfile.NamedTemporaryFile(prefix='.pdf_marker_', suffix='.tmp',
                                             dir=target_folder, delete=False) as handle:
                staged = handle.name
            # Verify the complete staged copy before touching an existing PDF.
            expected_size = os.path.getsize(pending)
            if expected_size <= 0:
                raise OSError('The generated PDF is empty; the destination was not changed.')
            shutil_copy_file(pending, staged)
            if os.path.getsize(staged) != expected_size:
                raise OSError('The staged PDF copy is incomplete; the destination was not changed.')
            # Flush the staged data before the atomic destination replacement.
            # Windows requires a writable file descriptor for fsync().
            # Reopen the completed copy for update before flushing it to disk.
            with open(staged, 'r+b') as staged_file:
                staged_file.flush()
                os.fsync(staged_file.fileno())
            os.replace(staged, target)
            staged = None
        except (PermissionError, OSError) as exc:
            # On Windows locked PDFs often give EACCES / EBUSY / winerror 32.
            if (isinstance(exc, PermissionError) or getattr(exc, 'winerror', None) in (5, 32, 33)
                    or getattr(exc, 'errno', None) in (13, 16)):
                QMessageBox.warning(
                    self, 'Unable to save PDF',
                    'Windows could not replace this PDF. The file may be in use or access may be restricted.\n\n'
                    'Try again after any PDF background activity finishes, or use Save As '
                    'to choose a different filename.\n\n'
                    f'File: {os.path.basename(target)}')
                return False
            raise
        finally:
            if staged and os.path.exists(staged):
                try: os.unlink(staged)
                except OSError: pass
        return True

    def remembered_folder(self, key, fallback=None):
        """Restore a per-action folder from the current Windows user profile."""
        stored = self.folder_settings.value('folders/' + key, '', type=str)
        if stored and Path(stored).is_dir():
            return stored
        if fallback:
            candidate = Path(fallback)
            parent = candidate if candidate.is_dir() else candidate.parent
            if parent.is_dir():
                return str(parent)
        return str(Path.home())

    def remember_folder(self, key, selected_file):
        """Only update a remembered folder after a user actually selects a file."""
        if selected_file:
            self.folder_settings.setValue('folders/' + key, str(Path(selected_file).resolve().parent))
            self.folder_settings.sync()

    def proposed_file(self, key, source_path, suffix, fallback_key=None):
        """Preserve the document filename while using the last chosen output folder."""
        folder = self.remembered_folder(key, source_path)
        if not self.folder_settings.contains('folders/' + key) and fallback_key:
            folder = self.remembered_folder(fallback_key, source_path)
        return str(Path(folder) / (Path(source_path).stem + suffix + '.pdf'))

    def paint_rubric_marks(self, painter, page_index, scale):
        """Render live rubric marks identically in the viewer and flattened PDF."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for stroke in self.rubric_strokes.get(page_index, []):
            PageCanvas.draw_stroke(self.canvas, painter, stroke, scale)
        for mark in self.rubric_marks.get(page_index, []):
            x = float(mark['x']) * scale
            y = float(mark['y']) * scale
            painter.save()
            angle = float(mark.get('angle', 0))
            if angle:
                painter.translate(x, y)
                painter.rotate(angle)
                painter.translate(-x, -y)
            if mark.get('type') == 'text':
                annotation = Stroke('Text', mark.get('color', self.pen_color),
                                    float(mark.get('size', self.text_size)), 1.0,
                                    [(float(mark['x']), float(mark['y']))],
                                    mark['text'], mark.get('text_direction', 'ltr'), text_width=float(mark.get('text_width', 0.0)))
                self.canvas.draw_symbol(painter, annotation, scale)
            else:
                font=QFont('Segoe UI')
                font.setPixelSize(max(8, round(float(mark.get('size', self.text_size))*scale)))
                painter.setFont(font)
                painter.setPen(QColor(mark.get('color', '#ed2024')))
                painter.drawText(QPointF(x,y+QFontMetricsF(font).ascent()), mark['text'])
            painter.restore()
        painter.restore()


    def _refresh_rotated_page(self, side, index):
        """Refresh only the rotated page, preserving progressive loading and scroll.

        A full render() rebuild would temporarily switch to page one and let
        in-flight background images replace the page's new orientation.
        """
        self._cancel_background_render(side)
        if side == 'student':
            pages, doc, scroll = self.student_pages, self.doc, self.scroll
            if not doc or index >= len(pages):
                return
            canvas = pages[index]
            scale = self.zoom
            page = doc[index]
            canvas.setFixedSize(max(1, round(page.rect.width * scale)),
                                max(1, round(page.rect.height * scale)))
            canvas.paper = qt_pixmap(page, scale)
            canvas.update()
            self.canvas = canvas
        else:
            pages, doc, scroll = self.rubric_pages, self.rubric_doc, self.ref_scroll
            if not doc or index >= len(pages):
                return
            canvas = pages[index]
            page = doc[index]
            scale = canvas.scale
            canvas.setFixedSize(max(1, round(page.rect.width * scale)),
                                max(1, round(page.rect.height * scale)))
            canvas.setPixmap(qt_pixmap(page, scale))
            self.ref_image = canvas
        self._remember_rendered_page(side, index)
        # Rotation changes the widest page in the stack. Recalculate the INNER
        # stack width just as zoom does, so the horizontal scrollbar updates
        # for landscape/portrait orientations without resizing the PDF pane.
        self._update_page_stack_width(side)
        stack = self.rubric_stack if side == 'rubric' else self.student_stack
        stack.layout().invalidate()
        stack.layout().activate()
        # Keep this same page on screen after its dimensions change.
        scroll.verticalScrollBar().setValue(canvas.y())
        self.refresh_page_navigation()
        QTimer.singleShot(80, self._start_student_prefetch if side == 'student'
                          else self._start_rubric_prefetch)

    def rotate_rubric_page(self):
        self._rotate_rubric_page(90)

    def rotate_rubric_page_counterclockwise(self):
        self._rotate_rubric_page(-90)

    def _rotate_rubric_page(self, degrees):
        """Rotate this page and all its marks together, in either direction."""
        if not self.rubric_doc:
            return
        for canvas in self.rubric_pages:
            canvas.finish_editor()
        self.record_rubric_action()
        page = self.rubric_doc[self.rubric_page]
        old_width, old_height = float(page.rect.width), float(page.rect.height)
        def rotated_point(x, y):
            return ((old_height-y, x) if degrees == 90 else (y, old_width-x))
        for mark in self.rubric_marks.get(self.rubric_page, []):
            mark['x'], mark['y'] = rotated_point(float(mark['x']), float(mark['y']))
            mark['angle'] = (float(mark.get('angle', 0)) + degrees) % 360
        for stroke in self.rubric_strokes.get(self.rubric_page, []):
            if stroke.tool == 'Signature' and stroke.points:
                x, y = stroke.points[0]
                cx, cy = rotated_point(x + stroke.text_width / 2, y + stroke.size / 2)
                stroke.points[0] = (cx - stroke.text_width / 2, cy - stroke.size / 2)
                stroke.angle = (getattr(stroke, 'angle', 0) + degrees) % 360
                continue
            stroke.points = [rotated_point(x, y) for x, y in stroke.points]
            if stroke.tool in ('Tick', 'Cross', 'Text', 'Marks', 'Total Marks', 'Emoji'):
                stroke.angle = (getattr(stroke, 'angle', 0) + degrees) % 360
        page.set_rotation((page.rotation + degrees) % 360)
        self.rubric_dirty = True
        self._refresh_rotated_page('rubric', self.rubric_page)
        direction = 'clockwise' if degrees == 90 else 'counterclockwise'
        self.statusBar().showMessage(f'Rotated rubric page 90° {direction}. Save to keep its orientation.', 4000)

    def export_rubric_image_pdf(self):
        """Flatten rubric pages together with the currently visible typed marks."""
        if not self.rubric_doc:
            return
        for canvas in self.rubric_pages:
            canvas.finish_editor()
        self.update_marks_total()
        proposed=self.proposed_file('rubric_image_save', self.rubric_path,
                                    '_marked_flattened', 'rubric_save')
        target,_=QFileDialog.getSaveFileName(self, 'Export rubric as Image PDF',
                                             proposed, 'PDF Files (*.pdf)')
        if not target:
            return
        self.remember_folder('rubric_image_save', target)
        if os.path.normcase(os.path.abspath(target)) == os.path.normcase(os.path.abspath(self.rubric_path)):
            QMessageBox.warning(self, 'Original rubric protected',
                                'Choose another filename. The original rubric will not be overwritten.')
            return
        if not self.confirm_replace_existing(target):
            return
        flattened=fitz.open()
        try:
            scale=200.0/72.0
            for idx,original in enumerate(self.rubric_doc):
                pix=original.get_pixmap(matrix=fitz.Matrix(scale,scale),
                                         alpha=False, colorspace=fitz.csRGB, annots=True)
                image=QImage(pix.samples,pix.width,pix.height,pix.stride,
                             QImage.Format.Format_RGB888).copy()
                if image.isNull():
                    raise RuntimeError(f'Unable to render rubric page {idx+1}.')
                painter=QPainter(image)
                try:
                    self.paint_rubric_marks(painter,idx,scale)
                finally:
                    painter.end()
                data=QByteArray();buffer=QBuffer(data)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                try:
                    if not image.save(buffer,'PNG'):
                        raise RuntimeError(f'Unable to encode rubric page {idx+1}.')
                finally:
                    buffer.close()
                dest=flattened.new_page(width=original.rect.width,
                                        height=original.rect.height)
                dest.insert_image(dest.rect,stream=bytes(data),keep_proportion=False)
                QApplication.processEvents()
            with tempfile.TemporaryDirectory(prefix='rubric_flat_') as tmp:
                pending=os.path.join(tmp,'rubric_flattened.pdf')
                flattened.save(pending,garbage=3,deflate=True)
                check=fitz.open(pending)
                try:
                    if len(check)!=len(self.rubric_doc):
                        raise RuntimeError('The flattened rubric page count is incorrect.')
                finally:
                    check.close()
                if not self.commit_saved_pdf(pending,target):
                    return
            self.statusBar().showMessage('Document 1 Image PDF saved: '+target,12000)
            QMessageBox.information(self,'Export complete',
                'Document 1 has been successfully saved as an image-only PDF, including all annotations and marks.')
        except Exception as exc:
            QMessageBox.critical(self,'Rubric Image PDF export failed',str(exc))
        finally:
            flattened.close()

    def confirm_first_original_save(self, side, original_path):
        """Confirm the first overwrite of an opened PDF in this session."""
        confirmed = getattr(self, '_original_save_confirmed', {})
        if confirmed.get(side) == os.path.normcase(os.path.abspath(original_path)):
            return True
        answer = QMessageBox.question(
            self, 'Save Changes',
            f'Do you want to save your changes to the original document "{os.path.basename(original_path)}"?\n\n'
            'This will overwrite the original PDF. Use Save As to keep an unmarked copy.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        return answer == QMessageBox.StandardButton.Yes

    def remember_original_save(self, side, original_path):
        if not hasattr(self, '_original_save_confirmed'):
            self._original_save_confirmed = {}
        self._original_save_confirmed[side] = os.path.normcase(os.path.abspath(original_path))

    def save_rubric(self, force_dialog=False):
        """Save Document 1 marks as permanent page content, respecting PDF rotation.

        Returns the saved path on success, otherwise None (cancel/failure).

        RubricCanvas stores positions in *displayed* page coordinates. Render
        marks in those coordinates, unrotate the overlay, and insert it into
        the unrotated PDF page. This preserves the page's original orientation.
        """
        self.ref_image.finish_editor()
        self.update_marks_total()
        if not self.rubric_doc:
            return None
        if not force_dialog:
            target = getattr(self, 'rubric_saved_target', None) or self.rubric_path
            repeat_save = True
        else:
            proposal = self.proposed_file('rubric_save', self.rubric_path, '_marked', 'rubric_open')
            target, _ = QFileDialog.getSaveFileName(
                self, 'Save Document 1 As', proposal, 'PDF Files (*.pdf)')
            if not target:
                return None
            self.remember_folder('rubric_save', target)
            repeat_save = False
        original_target = (os.path.normcase(os.path.abspath(target)) ==
                           os.path.normcase(os.path.abspath(self.rubric_path)))
        if original_target:
            if force_dialog:
                QMessageBox.warning(self, 'Use Save for original PDF',
                                    'Use Save to update the original PDF, or choose another filename in Save As.')
                return None
            if not self.confirm_first_original_save('rubric', self.rubric_path):
                return None
        elif not repeat_save and not self.confirm_replace_existing(target):
            return None
        try:
            with tempfile.TemporaryDirectory(prefix='rubric_save_') as tmpdir:
                pending = os.path.join(tmpdir, 'rubric_marked.pdf')
                output = fitz.open(stream=self.rubric_doc.tobytes(), filetype='pdf')
                try:
                    pages_with_rubric_content = sorted(set(self.rubric_marks.keys()) | set(self.rubric_strokes.keys()))
                    for index in pages_with_rubric_content:
                        if not self.rubric_marks.get(index) and not self.rubric_strokes.get(index):
                            continue
                        page = output[index]
                        # Match RubricCanvas text placement at the displayed page
                        # orientation, without depending on the currently selected zoom.
                        scale = 3.0
                        image = QImage(max(1, math.ceil(page.rect.width * scale)),
                                       max(1, math.ceil(page.rect.height * scale)),
                                       QImage.Format.Format_ARGB32)
                        image.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(image)
                        try:
                            self.paint_rubric_marks(painter,index,scale)
                        finally:
                            painter.end()
                        rotation = int(page.rotation) % 360
                        if rotation:
                            image = image.transformed(QTransform().rotate(-rotation),
                                                      Qt.TransformationMode.SmoothTransformation)
                        data = QByteArray()
                        buffer = QBuffer(data)
                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                        try:
                            if not image.save(buffer, 'PNG'):
                                raise RuntimeError(f'Cannot render rubric marks on page {index + 1}')
                        finally:
                            buffer.close()
                        if rotation:
                            page.set_rotation(0)
                        try:
                            page.insert_image(page.rect, stream=bytes(data),
                                              overlay=True, keep_proportion=False)
                        finally:
                            if rotation:
                                page.set_rotation(rotation)
                    output.save(pending, garbage=3, deflate=True)
                finally:
                    output.close()
                check = fitz.open(pending)
                try:
                    if len(check) != len(self.rubric_doc):
                        raise RuntimeError('Saved rubric page count mismatch')
                    pages_with_rubric_content = sorted(set(self.rubric_marks.keys()) | set(self.rubric_strokes.keys()))
                    for index in pages_with_rubric_content:
                        if (self.rubric_marks.get(index) or self.rubric_strokes.get(index)) and not check[index].get_images(full=True):
                            raise RuntimeError(f'Rubric marks missing from page {index + 1}')
                        if check[index].rotation != self.rubric_doc[index].rotation:
                            raise RuntimeError(f'Rubric orientation changed on page {index + 1}')
                finally:
                    check.close()
                if not self.commit_saved_pdf(pending, target):
                    return None
            if original_target:
                self.remember_original_save('rubric', self.rubric_path)
            self.rubric_saved_target = target
            self.rubric_dirty = False
            self._rubric_saved_once=True
            self._update_document_heading('rubric')
            self.statusBar().showMessage('Saved rubric with marks and original orientation: ' + target, 10000)
            return target
        except Exception as exc:
            QMessageBox.critical(self, 'Cannot save rubric', str(exc))
            return None

    def scale_rubric_zoom(self, factor):
        if not self.rubric_doc:return
        if self.ref_auto_fit:
            page=self.rubric_doc[self.rubric_page]
            self.ref_zoom=min(3.50,max(.3,(self.ref_scroll.viewport().width()-20)/page.rect.width))
        self.ref_auto_fit=False
        self.ref_zoom=max(.3,min(3.50,self.ref_zoom*factor))
        if not self._zoom_existing_pages('rubric'):
            self.render_rubric()
        else:
            self.ref_zoom_label.setText(f'{round(self.ref_zoom*100)}%')
            self._refresh_shared_header()


    def open_pdf(self, path=None, skip_unsaved_prompt=False):
        # Allow selection from the header filename, as well as the Open button.
        if not isinstance(path, (str, os.PathLike)):
            path,_=QFileDialog.getOpenFileName(self,'Open PDF',self.remembered_folder('student_open'),'PDF Files (*.pdf)')
        if not path:return
        path=os.fspath(path)
        # Match Document 1: commit live text before the unsaved-work check.
        if self.doc is not None and not skip_unsaved_prompt:
            self.canvas.finish_editor()
            if not self.confirm_close_document():
                return
        self.remember_folder('student_open',path)
        try:
            doc=self._open_pdf_without_file_lock(path)
            if doc.needs_pass or not len(doc):
                protected = bool(doc.needs_pass)
                doc.close()
                raise ValueError('Password-protected PDFs must be unlocked first.' if protected else 'The document is empty.')
        except Exception as exc:QMessageBox.critical(self,'Open failed',str(exc));return
        self._cancel_background_render('student')
        if self.doc:self.doc.close()
        self.doc=doc;self.path=path;self.page_index=0;self.strokes={};self.history=[];self.future=[];self._student_saved_once=False
        if hasattr(self,'saved_target'):delattr(self,'saved_target')
        self.set_dirty(False)
        self._update_document_heading('student')
        self._clear_page_stack(self.student_stack_layout)
        self.student_pages=[]
        self.refresh_thumbs();self.set_shared_initial_zoom();self.update_actions()
        # Opening/replacing a PDF while already split must fit and centre it too,
        # not only when the user first clicks the Split View button.
        if self.split_mode:
            self._schedule_split_width_fit()
        self.statusBar().showMessage('Draw with your stylus or mouse. Save updates the opened PDF; Save As makes a separate copy.')
    def close_student_pdf(self):
        """Close only the student PDF; the rubric and its marks are unaffected."""
        if self.doc is None:
            return
        self.canvas.finish_editor()
        if not self.confirm_close_document():
            return
        self._cancel_background_render('student')
        self.doc.close()
        self.doc=None
        self.path=None
        self._student_saved_once=False
        self._update_document_heading('student')
        self.page_index=0
        self.strokes={}
        self.history=[]
        self.future=[]
        self.dirty=False
        if hasattr(self,'saved_target'):
            delattr(self,'saved_target')
        self._clear_page_stack(self.student_stack_layout)
        self.student_pages=[]
        self.canvas=PageCanvas(self,0)
        self.student_stack_layout.addWidget(self.canvas,0,Qt.AlignmentFlag.AlignHCenter)
        self.thumb_list.clear()
        self.refresh_page_navigation()
        self.update_marks_total()
        self.update_actions()
        self.setWindowTitle('PDF Assignment Marker')
        self.statusBar().showMessage('Student PDF closed. Open another document to continue.')

    def refresh_thumbs(self):
        """Update thumbnails only while the optional Single View panel is open."""
        if getattr(self, '_thumbnails_open', False) and not self.split_mode:
            self._populate_page_thumbnails()

    def toggle_page_thumbnails(self):
        """Toggle the left thumbnail strip without affecting the document itself."""
        active_doc = self.rubric_doc if self._active_pdf_side == 'rubric' else self.doc
        if self.split_mode or active_doc is None:
            return
        self._thumbnails_open = not self._thumbnails_open
        if self._thumbnails_open:
            self.pages_panel.show()
            self._populate_page_thumbnails()
        else:
            self._thumb_generation += 1
            self.pages_panel.hide()
        self.position_single_page_ribbon()

    def _hide_page_thumbnails(self):
        self._thumbnails_open = False
        self._thumb_generation += 1
        self.pages_panel.hide()

    def _populate_page_thumbnails(self):
        """Load small previews progressively; supports either document in Single View."""
        if self.split_mode or not self._thumbnails_open:
            return
        side = self._active_pdf_side
        doc = self.rubric_doc if side == 'rubric' else self.doc
        self._thumb_side = side
        self._thumb_generation += 1
        generation = self._thumb_generation
        self.thumb_list.blockSignals(True)
        self.thumb_list.clear()
        if doc:
            for index in range(len(doc)):
                item = QListWidgetItem(f'Page {index + 1}')
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter)
                item.setSizeHint(QSize(128, 160))
                self.thumb_list.addItem(item)
            current = self.rubric_page if side == 'rubric' else self.page_index
            self.thumb_list.setCurrentRow(current)
        self.thumb_list.blockSignals(False)
        self.thumb_list.setIconSize(QSize(112,125))
        self.thumb_list.setToolTip('Click a thumbnail to navigate to that page')
        if doc:
            QTimer.singleShot(0, lambda: self._fill_thumb_batch(side, generation, 0))

    def _fill_thumb_batch(self, side, generation, start):
        if generation != self._thumb_generation or self.split_mode or not self._thumbnails_open:
            return
        doc = self.rubric_doc if side == 'rubric' else self.doc
        if doc is None or self._thumb_side != side:
            return
        end = min(len(doc), start + 5)
        for index in range(start, end):
            try:
                page = doc[index]
                scale = min(112 / max(1, page.rect.width), 125 / max(1, page.rect.height))
                preview = qt_pixmap(page, scale)
                self.thumb_list.item(index).setIcon(QIcon(preview))
            except Exception:
                pass
        if end < len(doc):
            QTimer.singleShot(15, lambda: self._fill_thumb_batch(side, generation, end))

    def _thumbnail_page_selected(self, index):
        if self.split_mode or not self._thumbnails_open or index < 0:
            return
        if self._active_pdf_side == 'rubric' and self.rubric_doc:
            self.ref_image.finish_editor()
            self.rubric_page = index
            self.jump_to_rubric_page()
        elif self._active_pdf_side == 'student' and self.doc:
            self.go_page(index)

    def _sync_thumbnail_selection(self):
        if not getattr(self, '_thumbnails_open', False) or self.split_mode:
            return
        current = self.rubric_page if self._active_pdf_side == 'rubric' else self.page_index
        if self.thumb_list.currentRow() != current:
            self.thumb_list.blockSignals(True)
            self.thumb_list.setCurrentRow(current)
            self.thumb_list.blockSignals(False)
    def _student_canvas_for_page(self, index):
        page = self.doc[index]
        canvas = PageCanvas(self, index)
        canvas.installEventFilter(self)
        canvas.setStyleSheet('background:white;')
        canvas.setFixedSize(max(1, round(page.rect.width*self.zoom)),
                            max(1, round(page.rect.height*self.zoom)))
        self.student_stack_layout.addWidget(canvas, 0, Qt.AlignmentFlag.AlignHCenter)
        self.student_pages.append(canvas)
        self._update_page_stack_width('student')
        return canvas

    def _continue_student_pages(self, generation):
        if generation != self._render_generation['student'] or not self.doc:
            return
        end = min(len(self.doc), len(self.student_pages)+12)
        for i in range(len(self.student_pages), end):
            self._student_canvas_for_page(i)
        if len(self.student_pages) < len(self.doc):
            QTimer.singleShot(0, lambda g=generation: self._continue_student_pages(g))
        else:
            self._building_pages['student'] = False
            if self.page_index < len(self.student_pages):
                self.canvas = self.student_pages[self.page_index]
                self.scroll.verticalScrollBar().setValue(self.canvas.y())
            QTimer.singleShot(0, self._render_visible_student_pages)
            QTimer.singleShot(60, self._start_student_prefetch)

    def render(self):
        if not self.doc:return
        self._zoom_preview_pages['student'].clear()
        self._cancel_background_render('student')
        self._building_pages['student'] = True
        self._preview_pending['student'] = False
        self._clear_page_stack(self.student_stack_layout)
        self.student_pages=[]
        # Display a reduced-resolution first-page preview before creating
        # dozens of page widgets. The background worker replaces the preview
        # with the full-resolution page, preserving its on-screen dimensions.
        requested_index = self.page_index
        canvas = self._student_canvas_for_page(0)
        self.canvas = canvas
        self.student_zoom_label.setText(f'{round(self.zoom*100)}%');self._refresh_shared_header()
        if self.split_mode:
            QTimer.singleShot(0, self.center_tools_panel)
        if self.page_index == 0:
            try:
                preview_scale = min(self.zoom, .55)
                preview = qt_pixmap(self.doc[0], preview_scale)
                canvas.paper = preview.scaled(canvas.size(),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.FastTransformation)
                canvas.update()
                self._preview_pending['student'] = preview_scale < self.zoom
            except Exception:
                pass
        generation = self._render_generation['student']
        self.refresh_page_navigation()
        self.update_actions()
        QTimer.singleShot(0, lambda g=generation: self._continue_student_pages(g))
        if self._preview_pending['student']:
            QTimer.singleShot(35, lambda g=generation: self._launch_background_render(
                'student', self.path, self.zoom, [0])
                if self._render_generation['student'] == g else None)
        elif canvas.paper.isNull():
            QTimer.singleShot(0, self._render_visible_student_pages)

    def go_page(self,index,force=False):
        if not self.doc or not 0<=index<len(self.doc):return
        if self.canvas.editor:self.canvas.finish_editor()
        self.page_index=index
        if self.student_pages and index<len(self.student_pages):
            self.canvas=self.student_pages[index]
            self.scroll.verticalScrollBar().setValue(self.canvas.y())
            QTimer.singleShot(0,self._render_visible_student_pages)
        self.refresh_page_navigation()
    def navigate(self,d):self.go_page(self.page_index+d)
    def _stable_split_fit_width(self, side):
        """Available PDF width, bounded by the actual Split View workspace.

        During PDF replacement the inner page stack can momentarily keep a
        stale, very large width. Never use that width as a zoom target; the
        outer QSplitter pane provides the real physical limit.
        """
        if side == 'rubric':
            pane, area, gutter = self.reference_panel, self.ref_scroll, 38
        else:
            pane, area, gutter = self.student_workspace, self.scroll, 24
        pane_width = pane.width()
        viewport_width = area.viewport().width()
        # Split panes are guaranteed visible while this calculation is used.
        # A temporarily large viewport must not force 350% zoom.
        return max(60, min(viewport_width, max(120, pane_width - 24)) - gutter)

    def set_shared_initial_zoom(self):
        """Default opening zoom: 217% in Single View, page width in Split View.

        Only initial opening/view-mode switching calls this routine. Normal
        toolbar, Ctrl+wheel and per-document scrolling remain unchanged.
        """
        if not (self.doc or self.rubric_doc):
            return
        if self.split_mode:
            # Derive each fit from its own viewport, never the other pane.
            # Use the actual PDF page width, with a little room for gutters.
            if self.doc:
                page = self.doc[self.page_index]
                width = self._stable_split_fit_width('student')
                student_scale = max(.30, min(3.50, width / max(1.0, page.rect.width)))
                self.student_auto_fit_width = False
                if not self.student_pages or abs(self.zoom - student_scale) > .001:
                    self.set_zoom(student_scale)
            if self.rubric_doc:
                page = self.rubric_doc[self.rubric_page]
                width = self._stable_split_fit_width('rubric')
                rubric_scale = max(.30, min(3.50, width / max(1.0, page.rect.width)))
                self.ref_auto_fit = False
                if not self.rubric_pages or abs(self.ref_zoom - rubric_scale) > .001:
                    self.ref_zoom = rubric_scale
                    if not self._zoom_existing_pages('rubric'):
                        self.render_rubric()
                    self.ref_zoom_label.setText(f'{round(self.ref_zoom*100)}%')
        else:
            default_scale = 2.17
            if self.doc:
                self.student_auto_fit_width = False
                if not self.student_pages or abs(self.zoom - default_scale) > .001:
                    self.set_zoom(default_scale)
            if self.rubric_doc:
                self.ref_auto_fit = False
                if not self.rubric_pages or abs(self.ref_zoom - default_scale) > .001:
                    self.ref_zoom = default_scale
                    if not self._zoom_existing_pages('rubric'):
                        self.render_rubric()
                    self.ref_zoom_label.setText(f'{round(self.ref_zoom*100)}%')
        self._refresh_shared_header()

    def scale_zoom(self,factor):self.set_zoom(self.zoom*factor)
    def set_zoom(self,z,auto_fit=False):
        if not self.doc:return
        self.student_auto_fit_width=auto_fit
        self.zoom=max(.3,min(3.50,z))
        if not self._zoom_existing_pages('student'):
            self.render()
        self.student_zoom_label.setText(f'{round(self.zoom*100)}%');self._refresh_shared_header()
    def fit_width(self):
        if self.doc:self.set_zoom((self.scroll.viewport().width()-12)/self.doc[self.page_index].rect.width,auto_fit=True)
    def rotate_page(self):
        self._rotate_student_page(90)

    def rotate_page_counterclockwise(self):
        self._rotate_student_page(-90)

    def _rotate_student_page(self, degrees):
        """Rotate just the current student page and its marking coordinates."""
        if not self.doc:
            return
        self.canvas.finish_editor()
        self.record_action()
        page = self.doc[self.page_index]
        old_width, old_height = float(page.rect.width), float(page.rect.height)
        def rotated_point(x, y):
            return ((old_height-y, x) if degrees == 90 else (y, old_width-x))
        for mark in self.strokes.get(self.page_index, []):
            if mark.tool == 'Signature' and mark.points:
                x, y = mark.points[0]
                cx, cy = rotated_point(x + mark.text_width / 2, y + mark.size / 2)
                mark.points[0] = (cx - mark.text_width / 2, cy - mark.size / 2)
                mark.angle = (getattr(mark, 'angle', 0) + degrees) % 360
                continue
            mark.points = [rotated_point(x, y) for x, y in mark.points]
            if mark.tool in ('Tick', 'Cross', 'Text', 'Marks', 'Total Marks', 'Emoji'):
                mark.angle = (getattr(mark, 'angle', 0) + degrees) % 360
        page.set_rotation((page.rotation + degrees) % 360)
        self.set_dirty(True)
        self._refresh_rotated_page('student', self.page_index)
        self.refresh_thumbs()
        direction = 'clockwise' if degrees == 90 else 'counterclockwise'
        self.statusBar().showMessage(f'Rotated page 90° {direction}. Save to keep its orientation.', 4000)

    def toggle_fullscreen(self):
        self.canvas.finish_editor()
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    def _student_history_state(self):
        import copy
        return (copy.deepcopy(self.strokes),
                tuple(p.rotation for p in self.doc) if self.doc else ())

    def _rubric_history_state(self):
        import copy
        return (copy.deepcopy(self.rubric_marks), copy.deepcopy(self.rubric_strokes),
                tuple(p.rotation for p in self.rubric_doc) if self.rubric_doc else ())

    def _restore_page_rotations(self, side, rotations):
        """Restore actual PDF page orientations, not only the drawn annotations."""
        doc = self.doc if side == 'student' else self.rubric_doc
        if doc is None or not rotations:
            return
        changed = []
        for i, desired in enumerate(rotations):
            if i >= len(doc):
                break
            if doc[i].rotation != desired:
                doc[i].set_rotation(desired)
                changed.append(i)
        if changed:
            self._cancel_background_render(side)
            pages = self.student_pages if side == 'student' else self.rubric_pages
            # Refresh the modified page canvases; others will render on demand.
            for i in changed:
                if i < len(pages):
                    self._refresh_rotated_page(side, i)

    def record_action(self):
        self.history.append(self._student_history_state())
        self.history = self.history[-60:]
        self.future.clear()
        self.update_actions()

    def record_rubric_action(self):
        self.rubric_history.append(self._rubric_history_state())
        self.rubric_history = self.rubric_history[-60:]
        self.rubric_future.clear()
        self.update_actions()

    def undo(self):
        if self.history:
            self.canvas.finish_editor()
            self.future.append(self._student_history_state())
            self.future = self.future[-60:]
            state = self.history.pop()
            # Accept existing annotation-only snapshots from older sessions.
            if isinstance(state, tuple) and len(state) == 2:
                self.strokes, rotations = state
                self._restore_page_rotations('student', rotations)
            else:
                self.strokes = state
            self.update_all_student_pages()
            self.set_dirty(True)
            self.update_actions()

    def redo(self):
        if self.future:
            self.canvas.finish_editor()
            self.history.append(self._student_history_state())
            self.history = self.history[-60:]
            state = self.future.pop()
            if isinstance(state, tuple) and len(state) == 2:
                self.strokes, rotations = state
                self._restore_page_rotations('student', rotations)
            else:
                self.strokes = state
            self.update_all_student_pages()
            self.set_dirty(True)
            self.update_actions()

    def undo_rubric(self):
        if self.rubric_history:
            self.ref_image.finish_editor()
            self.rubric_future.append(self._rubric_history_state())
            self.rubric_future = self.rubric_future[-60:]
            state = self.rubric_history.pop()
            if len(state) == 3:
                self.rubric_marks, self.rubric_strokes, rotations = state
                self._restore_page_rotations('rubric', rotations)
            else:
                self.rubric_marks, self.rubric_strokes = state
            self.rubric_dirty = True
            self.update_marks_total()
            self.update_all_rubric_pages()
            self.update_actions()

    def redo_rubric(self):
        if self.rubric_future:
            self.ref_image.finish_editor()
            self.rubric_history.append(self._rubric_history_state())
            self.rubric_history = self.rubric_history[-60:]
            state = self.rubric_future.pop()
            if len(state) == 3:
                self.rubric_marks, self.rubric_strokes, rotations = state
                self._restore_page_rotations('rubric', rotations)
            else:
                self.rubric_marks, self.rubric_strokes = state
            self.rubric_dirty = True
            self.update_marks_total()
            self.update_all_rubric_pages()
            self.update_actions()

    def update_actions(self):
        if not hasattr(self,'top_buttons'):return
        self._refresh_shared_header()
        if hasattr(self, 'thumbnail_toggle'):
            active_doc = self.rubric_doc if self._active_pdf_side == 'rubric' else self.doc
            thumbnail_available = not self.split_mode and active_doc is not None
            if not thumbnail_available and getattr(self, '_thumbnails_open', False):
                self._hide_page_thumbnails()
            self._set_thumbnail_toggle_enabled(thumbnail_available)
        if hasattr(self,'student_close'):
            self.student_close.setEnabled(self.doc is not None)
        for k in ('Save','Save As','Image PDF'):
            if hasattr(self,'student_file_buttons'):
                self.student_file_buttons[k].setEnabled(self.doc is not None)
        if hasattr(self,'student_action_buttons'):
            self.student_action_buttons['Undo'].setEnabled(bool(self.history))
            self.student_action_buttons['Redo'].setEnabled(bool(self.future))
            self.student_action_buttons['Rotate CW'].setEnabled(self.doc is not None)
            self.student_action_buttons['Rotate CCW'].setEnabled(self.doc is not None)
        if hasattr(self,'ref_close'):
            self.ref_close.setEnabled(self.rubric_doc is not None)
        if hasattr(self,'ref_file_buttons'):
            for k in ('Save', 'Save As', 'Image PDF'):
                if k in self.ref_file_buttons:
                    self.ref_file_buttons[k].setEnabled(self.rubric_doc is not None)
        if hasattr(self,'ref_action_buttons'):
            self.ref_action_buttons['Undo'].setEnabled(bool(self.rubric_history))
            self.ref_action_buttons['Redo'].setEnabled(bool(self.rubric_future))
            self.ref_action_buttons['Rotate CW'].setEnabled(self.rubric_doc is not None)
            self.ref_action_buttons['Rotate CCW'].setEnabled(self.rubric_doc is not None)
    def save_pdf(self):self._save(False)
    def save_as(self):self._save(True)
    def _save(self,force_dialog, internal_target=None):
        """Save annotations as a transparent page-content overlay.

        A PNG transparency overlay is standard PDF page content, not an optional
        annotation layer; readers which ignore PDF annotations will still show it.
        The underlying original PDF text remains searchable and selectable.
        """
        if not self.doc:
            return None
        self.canvas.finish_editor()
        self.update_marks_total()
        if internal_target is not None:
            target = internal_target
        elif force_dialog:
            proposed = self.proposed_file('student_save', self.path, '_marked', 'student_open')
            target, _ = QFileDialog.getSaveFileName(self, 'Save marked PDF As', proposed, 'PDF Files (*.pdf)')
            if not target:
                return None
            self.remember_folder('student_save', target)
        else:
            target = getattr(self, 'saved_target', None) or self.path
        original_target = (os.path.normcase(os.path.abspath(target)) ==
                           os.path.normcase(os.path.abspath(self.path)))
        if original_target and internal_target is None:
            if force_dialog:
                QMessageBox.warning(self, 'Use Save for original PDF',
                                    'Use Save to update the original PDF, or choose another filename in Save As.')
                return None
            if not self.confirm_first_original_save('student', self.path):
                return None
        repeat_save = internal_target is None and not force_dialog
        if internal_target is None and not original_target and not repeat_save:
            if not self.confirm_replace_existing(target):
                return None
        try:
            # Save the complete file to a temporary destination before replacing
            # any previously saved output, so an interrupted save cannot erase it.
            with tempfile.TemporaryDirectory(prefix='pdfmarker_save_') as tmpdir:
                pending = os.path.join(tmpdir, 'marked.pdf')
                output = fitz.open(stream=self.doc.tobytes(), filetype='pdf')
                try:
                    for page_index, marks in self.strokes.items():
                        if not marks:
                            continue
                        page = output[page_index]
                        # Render *only* marks with alpha, then add the transparent
                        # image over the original PDF page. No separate OCG / layer.
                        scale = 3.0
                        width = max(1, int(math.ceil(page.rect.width * scale)))
                        height = max(1, int(math.ceil(page.rect.height * scale)))
                        overlay = QImage(width, height, QImage.Format.Format_ARGB32)
                        overlay.fill(Qt.GlobalColor.transparent)
                        painter = QPainter(overlay)
                        if not painter.isActive():
                            raise RuntimeError(f'Cannot render markings on page {page_index + 1}')
                        try:
                            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
                            for mark in marks:
                                self.canvas.draw_stroke(painter, mark, render_zoom=scale)
                        finally:
                            painter.end()
                        image_data = QByteArray()
                        buffer = QBuffer(image_data)
                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                        try:
                            if not overlay.save(buffer, 'PNG'):
                                raise RuntimeError(f'Cannot encode markings on page {page_index + 1}')
                        finally:
                            buffer.close()
                        # Marks are drawn in the DISPLAYED (rotated) page's
                        # coordinate system. PDF image insertion uses the page's
                        # unrotated coordinates. Undo the display rotation on
                        # the transparent marks image before inserting it.
                        rotation = int(page.rotation) % 360
                        if rotation:
                            overlay = overlay.transformed(
                                QTransform().rotate(-rotation),
                                Qt.TransformationMode.SmoothTransformation)
                            image_data = QByteArray()
                            buffer = QBuffer(image_data)
                            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                            try:
                                if not overlay.save(buffer, 'PNG'):
                                    raise RuntimeError('Cannot rotate annotation overlay')
                            finally:
                                buffer.close()
                            page.set_rotation(0)
                        try:
                            page.insert_image(page.rect, stream=bytes(image_data),
                                              overlay=True, keep_proportion=False)
                        finally:
                            if rotation:
                                page.set_rotation(rotation)
                    output.save(pending, garbage=3, deflate=True)
                finally:
                    output.close()
                # Confirm the file can be opened and pages have the same count.
                check = fitz.open(pending)
                try:
                    if len(check) != len(self.doc):
                        raise RuntimeError('Saved PDF page count mismatch')
                    # Saving must never change landscape / portrait orientation.
                    for idx in range(len(self.doc)):
                        if check[idx].rotation != self.doc[idx].rotation:
                            raise RuntimeError(f'Page {idx + 1} orientation changed during save')
                        actual = check[idx].rect
                        expected = self.doc[idx].rect
                        if abs(actual.width - expected.width) > .05 or abs(actual.height - expected.height) > .05:
                            raise RuntimeError(f'Page {idx + 1} size changed during save')
                    # Confirm the marks are part of the PDF page image resources.
                    for page_index, marks in self.strokes.items():
                        if marks and not check[page_index].get_images(full=True):
                            raise RuntimeError(f'Mark overlay missing on page {page_index + 1}')
                finally:
                    check.close()
                if not self.commit_saved_pdf(pending, target):
                    return None
            if internal_target is None:
                if original_target:
                    self.remember_original_save('student', self.path)
                self.saved_target = target
                self._student_saved_once=True
                self.set_dirty(False)
                self._update_document_heading('student')
                self.statusBar().showMessage('Saved compatible PDF with marks: ' + target, 12000)
            return target
        except Exception as exc:
            QMessageBox.critical(self, 'Save failed', str(exc))
            return None

    def export_image_pdf(self):
        """Flatten each PDF page and its *live* annotation strokes into one image.

        Do not use a previously saved PDF as the source: the marks are held in
        self.strokes until export, and we paint those strokes directly on the
        rendered page with the same painter used by the live PDF canvas.
        """
        if not self.doc:
            return
        self.canvas.finish_editor()
        self.update_marks_total()
        proposed = self.proposed_file('image_save', self.path, '_marked_flattened', 'student_open')
        target, _ = QFileDialog.getSaveFileName(
            self, 'Export image-only PDF with all markings', proposed, 'PDF Files (*.pdf)'
        )
        if not target:
            return
        self.remember_folder('image_save', target)
        protected = {os.path.normcase(os.path.abspath(self.path))}
        if hasattr(self, 'saved_target'):
            protected.add(os.path.normcase(os.path.abspath(self.saved_target)))
        if os.path.normcase(os.path.abspath(target)) in protected:
            QMessageBox.warning(self, 'Choose another filename',
                                'Save the flattened PDF with a different name.')
            return
        if not self.confirm_replace_existing(target):
            return

        try:
            # 200 dpi: handwriting and document contents remain legible.
            scale = 200.0 / 72.0
            flattened = fitz.open()
            try:
                for idx in range(len(self.doc)):
                    original = self.doc[idx]
                    pix = original.get_pixmap(
                        matrix=fitz.Matrix(scale, scale), alpha=False,
                        colorspace=fitz.csRGB, annots=True
                    )
                    image = QImage(pix.samples, pix.width, pix.height, pix.stride,
                                   QImage.Format.Format_RGB888).copy()
                    if image.isNull():
                        raise RuntimeError(f'Unable to render page {idx + 1}')

                    painter = QPainter(image)
                    try:
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
                        for mark in self.strokes.get(idx, []):
                            self.canvas.draw_stroke(painter, mark, render_zoom=scale)
                    finally:
                        painter.end()

                    encoded = QByteArray()
                    buffer = QBuffer(encoded)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    try:
                        if not image.save(buffer, 'PNG'):
                            raise RuntimeError(f'Unable to encode page {idx + 1}')
                    finally:
                        buffer.close()
                    new_page = flattened.new_page(width=original.rect.width,
                                                  height=original.rect.height)
                    new_page.insert_image(new_page.rect, stream=bytes(encoded),
                                          keep_proportion=False)
                    QApplication.processEvents()

                # Build fully before writing output; avoid partial destination.
                with tempfile.TemporaryDirectory(prefix='pdfmarker_flat_') as tmpdir:
                    pending = os.path.join(tmpdir, 'completed.pdf')
                    flattened.save(pending, garbage=3, deflate=True)
                    verify = fitz.open(pending)
                    try:
                        if len(verify) != len(self.doc):
                            raise RuntimeError('Page count changed during export.')
                    finally:
                        verify.close()
                    if not self.commit_saved_pdf(pending, target):
                        return
            finally:
                flattened.close()
            self.statusBar().showMessage('Flattened PDF saved with all marks: ' + target, 12000)
            QMessageBox.information(self, 'Export complete',
                'Document 2 has been successfully saved as an image-only PDF, including all annotations and marks.')
        except Exception as exc:
            QMessageBox.critical(self, 'Image PDF export failed', str(exc))

    def save_combined_flat_pdf(self):
        """Combine Document 1 (first) + Document 2 (second) as image-only PDF.

        Draws the current live marks onto page images; source files are not changed.
        """
        if not self.rubric_doc or not self.doc:
            QMessageBox.information(self,'Open both PDFs',
                                    'Open Document 1 and Document 2 before combining.')
            return
        for canvas in getattr(self,'rubric_pages',[]):
            canvas.finish_editor()
        for canvas in getattr(self,'student_pages',[]):
            canvas.finish_editor()
        self.update_marks_total()
        proposed=self.proposed_file('combined_save',self.path,'_document1_and_document2','student_save')
        target,_=QFileDialog.getSaveFileName(self,'Save Combined Flat PDF',proposed,'PDF Files (*.pdf)')
        if not target:return
        if not target.lower().endswith('.pdf'):target+='.pdf'
        sources={os.path.normcase(os.path.abspath(self.path)),
                 os.path.normcase(os.path.abspath(self.rubric_path))}
        if os.path.normcase(os.path.abspath(target)) in sources:
            QMessageBox.warning(self,'Original PDFs protected',
                                'Choose a new filename; the original PDFs cannot be overwritten.')
            return
        if not self.confirm_replace_existing(target):return
        flattened=fitz.open()
        scale=200.0/72.0
        try:
            for section,source in (('Document 1',self.rubric_doc),('Document 2',self.doc)):
                for idx,page in enumerate(source):
                    pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False,
                                        colorspace=fitz.csRGB,annots=True)
                    image=QImage(pix.samples,pix.width,pix.height,pix.stride,
                                 QImage.Format.Format_RGB888).copy()
                    if image.isNull():
                        raise RuntimeError(f'Unable to render {section} page {idx+1}')
                    painter=QPainter(image)
                    try:
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing,True)
                        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing,True)
                        if section=='Document 1':
                            self.paint_rubric_marks(painter,idx,scale)
                        else:
                            for mark in self.strokes.get(idx,[]):
                                self.canvas.draw_stroke(painter,mark,render_zoom=scale)
                    finally:
                        painter.end()
                    payload=QByteArray();buffer=QBuffer(payload)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    try:
                        if not image.save(buffer,'PNG'):
                            raise RuntimeError(f'Unable to encode {section} page {idx+1}')
                    finally:
                        buffer.close()
                    dest=flattened.new_page(width=page.rect.width,height=page.rect.height)
                    dest.insert_image(dest.rect,stream=bytes(payload),keep_proportion=False)
                    QApplication.processEvents()
            with tempfile.TemporaryDirectory(prefix='pdfmarker_combine_') as tmpdir:
                pending=os.path.join(tmpdir,'combined.pdf')
                flattened.save(pending,garbage=3,deflate=True)
                with fitz.open(pending) as check:
                    if len(check)!=len(self.rubric_doc)+len(self.doc):
                        raise RuntimeError('Combined PDF page count mismatch.')
                if not self.commit_saved_pdf(pending,target):return
            self.remember_folder('combined_save',target)
            self.statusBar().showMessage('Combined flat PDF saved: '+target,12000)
            QMessageBox.information(self,'Combined PDF saved',
                                    'Document 1 pages followed by Document 2 pages were saved as a combined PDF.')
        except Exception as exc:
            QMessageBox.critical(self,'Combine PDF failed',str(exc))
        finally:
            flattened.close()

    def closeEvent(self,e):
        # Commit in-progress text on BOTH panes before testing unsaved work.
        # Previously only Document 2's editor was finalised here.
        self.canvas.finish_editor()
        self.ref_image.finish_editor()
        if self.confirm_close_document() and self.confirm_close_rubric():
            self._cancel_background_render('student')
            self._cancel_background_render('rubric')
            # QThread objects must finish before their parent window is destroyed.
            for worker in list(self._background_renderers):
                worker.requestInterruption()
                worker.wait()
            if self.doc:self.doc.close()
            if self.rubric_doc:self.rubric_doc.close()
            e.accept()
        else:
            e.ignore()


def main():
    # Named Windows mutex lets the uninstaller detect a running application.
    # Keep the handle alive until the process exits.
    running_mutex = None
    if sys.platform == 'win32':
        import ctypes
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        running_mutex = kernel32.CreateMutexW(None, False, 'Local\\PDF_Assignment_Marker_Running')
    app=QApplication(sys.argv)
    # Style floating Qt tooltips at application scope: window-only QSS can be
    # ignored by native/standalone tooltip popups on some Windows themes.
    tooltip_palette=app.palette()
    tooltip_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor('#f9fbff'))
    tooltip_palette.setColor(QPalette.ColorRole.ToolTipText, QColor('#0f4592'))
    app.setPalette(tooltip_palette)
    app.setStyleSheet(app.styleSheet() +
        'QToolTip {background-color:#f9fbff; color:#0f4592; '
        'border:1px solid #a6c8e8; border-radius:3px; '
        'padding:3px 5px; font-family:"Segoe UI"; font-size:12px;}')
    app.setApplicationName('PDF Assignment Marker')
    w=App();w.show();sys.exit(app.exec())
if __name__=='__main__':main()
