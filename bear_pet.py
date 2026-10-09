#!/usr/bin/env python3
"""Bear Pet: a pixel-art bear that wanders around your Linux desktop."""
import sys, time, math, random, subprocess
from PyQt6.QtCore import Qt, QTimer, QRect, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen
from PyQt6.QtWidgets import QApplication, QWidget

BASE = [
    ".XX.XXXXXXX.XX.", "X..X.......X..X", "X.............X", ".X...........X.", ".X...........X.",
    "X...XX...XX...X", "X....X...X....X", "X....X...X....X", "X.....XXX.....X", "X.....XXX.....X",
    ".X.....X.....X.", "..XX...X...XX..", "....XXXXXXX....",
]
FACES = {
    "normal": {},
    "blink": {5: "X.............X", 6: "X.............X", 7: "X...XX...XX...X"},
    "happy": {5: "X....X...X....X", 6: "X...X.X.X.X...X", 7: "X.............X", 8: "X.PP..XXX..PP.X"},
    "love": {5: "X..P.P...P.P..X", 6: "X..PPP...PPP..X", 7: "X...P.....P...X"},
    "surprised": {5: "X...XX...XX...X", 6: "X...XX...XX...X", 7: "X.............X", 10: ".X....XXX....X.", 11: "..XX..XXX..XX.."},
    "wink": {5: "X........XX...X", 6: "X.........X...X", 7: "X...XX....X...X"},
    "dizzy": {5: "X...X.X.X.X...X", 6: "X....X...X....X", 7: "X...X.X.X.X...X"},
    "sad": {8: "X...B.XXX.....X", 9: "X...B.XXX.....X", 11: "..XX..X.X..XX.."},
    "cool": {5: "X.XXXXXXXXXXX.X", 6: "X..XXX...XXX..X", 7: "X...X.....X...X"},
    "angry": {5: "X..X.......X..X", 6: "X...XX...XX...X", 7: "X....X...X....X"},
    "silly": {10: ".X....XXX....X.", 11: "..XX..PPP..XX.."},
    "sleepy": {5: "X.............X", 6: "X.............X", 7: "X...XX...XX...X", 8: "X.PP..XXX..PP.X"},
}
COLORS = {"X": "#3d59a1", ".": "#c0caf5", "P": "#ff79c6", "B": "#7dcfff"}


def es(s):
    for k, v in (("~a", 0xe1), ("~e", 0xe9), ("~i", 0xed), ("~o", 0xf3), ("~u", 0xfa), ("~n", 0xf1), ("~1", 0xa1), ("~2", 0xbf), ("~3", 0x21)):
        s = s.replace(k, chr(v))
    return s


MSGS = {
    "normal": ["Hola Randy :)", "Sigue aprendiendo Linux", "Prueba: tldr tar", "Ctrl+R busca en tu historial", "man > Google"],
    "happy": ["~1Qu~e buen d~ia~3", "~1Vas muy bien~3"],
    "love": ["Te quiero mucho <3", "Eres genial <3"],
    "surprised": ["~1Wow~3", "~2Usaste sudo?"],
    "wink": ["Guarda tus cambios ;)", "Haz commit seguido ;)"],
    "dizzy": ["Demasiados comandos...", "Necesito un caf~e"],
    "sad": ["Toma un descanso...", "No te rindas"],
    "cool": ["Modo hacker activado", "chmod +x a la vida"],
    "angry": ["~1No hagas rm -rf /~3", "~1Lee el error~3"],
    "silly": ["Bleh :P", "~1Juguemos~3"],
    "sleepy": ["Tengo sue~nito...", "zZz..."],
}
MOODS = [f for f in MSGS if f not in ("normal",)] + ["normal"] * 3


def build(face):
    g = list(BASE)
    for r, row in FACES[face].items():
        g[r] = row
    rows, cols = len(g), len(g[0])
    out = set()
    stack = [(r, c) for r in range(rows) for c in range(cols) if (r in (0, rows - 1) or c in (0, cols - 1)) and g[r][c] == "."]
    while stack:
        r, c = stack.pop()
        if (r, c) in out or g[r][c] in "XPB":
            continue
        out.add((r, c))
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                stack.append((nr, nc))
    return [(r, c, QColor(COLORS[g[r][c]])) for r in range(rows) for c in range(cols) if (r, c) not in out]


class Pet(QWidget):
    def __init__(self, geo):
        super().__init__()
        self.setWindowTitle("BearPet")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool | Qt.WindowType.WindowTransparentForInput | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        # The window only wraps the bear and its bubble and moves with it, so it never covers the desktop.
        self.geo = geo
        self.W, self.H, self.px = geo.width(), geo.height(), 6
        self.bw, self.bh = 15 * self.px, 13 * self.px
        self.mx, self.my = 160, 50
        self.resize(self.bw + 2 * self.mx, self.bh + self.my + 10)
        self.cache = {f: build(f) for f in FACES}
        self.x, self.y, self.dy = self.W - 300.0, self.H - 260.0, self.H - 260.0
        self.state, self.face, self.msg, self.until = "idle", "happy", es("~1Hola Randy~3"), time.time() + 4
        self.tx, self.ty = self.x, self.y
        self.font = QFont("Fira Code", 11)
        self.font.setBold(True)
        self.place()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        QTimer.singleShot(800, self.hide_from_taskbar)

    def hide_from_taskbar(self):
        # Qt has no portable skip-taskbar flag on X11, so ask the window manager through wmctrl.
        try:
            wid = hex(int(self.winId()))
            subprocess.run(["wmctrl", "-i", "-r", wid, "-b", "add,skip_taskbar,skip_pager"], check=False)
        except FileNotFoundError:
            pass

    def place(self):
        self.move(self.geo.x() + int(self.x) - self.mx, self.geo.y() + int(self.dy) - self.my)

    def tick(self):
        now = time.time()
        hour = time.localtime().tm_hour
        night = hour >= 23 or hour < 6
        if night:
            self.state, self.face, self.msg = "sleep", "sleepy", "Durmiendo... zZz"
        elif self.state == "sleep":
            self.state, self.until = "idle", 0
        if self.state == "walk":
            dx, dy = self.tx - self.x, self.ty - self.y
            d = math.hypot(dx, dy)
            if d < 3:
                self.state = "idle"
                self.face = random.choice(MOODS)
                self.msg = es(random.choice(MSGS[self.face]))
                self.until = now + random.uniform(4, 9)
            else:
                step = min(d, 2.2)
                self.x += dx / d * step
                self.y += dy / d * step
                self.face = "blink" if now % 4 < 0.15 else "normal"
                self.msg = ""
        elif self.state == "idle" and now > self.until:
            self.state = "walk"
            self.tx = random.randint(60, self.W - self.bw - 220)
            self.ty = random.randint(80, self.H - self.bh - 150)
        hop = abs(math.sin(now * 9)) * 6 if self.state == "walk" else 0
        self.dy = self.y - hop
        self.place()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        x, y, s = self.mx, self.my, self.px
        for r, c, col in self.cache[self.face]:
            p.fillRect(x + c * s, y + r * s, s, s, col)
        if self.msg:
            p.setFont(self.font)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            tw = p.fontMetrics().horizontalAdvance(self.msg) + 24
            box = QRectF(x + self.bw / 2 - tw / 2, y - 42, tw, 30)
            p.setBrush(QColor(26, 27, 38, 225))
            p.setPen(QPen(QColor("#3d59a1"), 2))
            p.drawRoundedRect(box, 10, 10)
            p.setPen(QColor("#7dcfff"))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, self.msg)
        p.end()


app = QApplication(sys.argv)
app.setApplicationName("BearPet")
pet = Pet(app.primaryScreen().availableGeometry())
pet.show()
sys.exit(app.exec())
