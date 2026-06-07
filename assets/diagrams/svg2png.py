import sys, os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QImage, QPainter, QFontDatabase, QColor
from PySide6.QtCore import Qt

app = QApplication(sys.argv[:1])
# Times-совместимый serif
for f in ('LiberationSerif-Regular','LiberationSerif-Bold','LiberationSerif-Italic','LiberationSerif-BoldItalic'):
    QFontDatabase.addApplicationFont(f'/tmp/mvxfonts/dir/{f}.ttf')

def render(svg_path, png_path, scale=2.0):
    r = QSvgRenderer(svg_path)
    if not r.isValid():
        print('INVALID', svg_path); return False
    vb = r.viewBoxF()
    w, h = int(vb.width()*scale), int(vb.height()*scale)
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(QColor('white'))
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    r.render(p)
    p.end()
    ok = img.save(png_path, 'PNG')
    print('OK' if ok else 'SAVEFAIL', png_path, f'{w}x{h}')
    return ok

if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv)>3 else 2.0)
