# ui/scene_view.py
# SceneView — the left panel that draws atmospheric scene art using QPainter.
# Each scene gets a bespoke illustration: desk, server room, HR office, etc.

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPoint, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont,
    QLinearGradient, QRadialGradient, QPainterPath,
)

from core.game import (
    SCENE_YOUR_DESK, SCENE_DB_TERMINAL, SCENE_HR_FILES,
    SCENE_CFO_DEPT, SCENE_AUDIT_TRAIL, SCENE_CONFRONTATION,
)


# ── Palette — dark navy (readable, still atmospheric) ─────────────────────────

C_BG        = QColor("#1a2744")   # dark navy — readable, not void-black
C_BG2       = QColor("#162236")   # slightly darker variant
C_PANEL     = QColor("#1e2d4a")   # panel surfaces
C_BORDER    = QColor("#2d4268")   # borders
C_ACCENT    = QColor("#79b8ff")   # bright blue — clearly visible on navy
C_TEXT      = QColor("#cdd9e5")   # slightly warm white — easy on eyes
C_DIM       = QColor("#768ea8")   # muted blue-grey
C_SUCCESS   = QColor("#56d364")   # green
C_WARM      = QColor("#e3b97a")   # warm amber for labels
C_ERROR     = QColor("#ff7b72")   # red


class SceneView(QWidget):
    """
    Left panel — draws a different scene illustration per game location.
    Fully vector / QPainter so it scales cleanly at any window size.
    After the first clue is found, the bottom portion shows a sticky-note
    style clue list that grows as the player progresses.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene_id = SCENE_YOUR_DESK
        self._clues: list[str] = []
        self.setMinimumWidth(280)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

    def set_scene(self, scene_id: str) -> None:
        self._scene_id = scene_id
        self.update()

    def set_clues(self, clues: list[str]) -> None:
        self._clues = list(clues)
        self.update()

    # ── Qt paint event ────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # If clues exist, split the panel: top = scene art, bottom = clue sidebar
        if self._clues:
            clue_h = min(int(h * 0.40), max(120, len(self._clues) * 24 + 60))
            scene_h = h - clue_h
        else:
            scene_h = h
            clue_h = 0

        # Route to the correct scene drawer
        draw_fn = {
            SCENE_YOUR_DESK:     self._draw_desk,
            SCENE_DB_TERMINAL:   self._draw_server_room,
            SCENE_HR_FILES:      self._draw_hr_office,
            SCENE_CFO_DEPT:      self._draw_cfo_office,
            SCENE_AUDIT_TRAIL:   self._draw_desk_night,
            SCENE_CONFRONTATION: self._draw_coo_office,
        }.get(self._scene_id, self._draw_desk)

        # Clip scene drawing to top portion
        p.save()
        p.setClipRect(0, 0, w, scene_h)
        draw_fn(p, w, scene_h)
        p.restore()

        # Draw clue sidebar in bottom portion
        if self._clues:
            self._draw_clue_sidebar(p, w, h, scene_h, clue_h)

        p.end()

    # ── Scene: Your Desk (morning) ────────────────────────────────────────────

    def _draw_desk(self, p: QPainter, w: int, h: int):
        # Background — navy blue gradient, readable
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#1e2f50"))
        grad.setColorAt(1, QColor("#162236"))
        p.fillRect(0, 0, w, h, grad)

        desk_y = int(h * 0.58)

        # Monitor blue glow on wall — visible but not overwhelming
        glow = QRadialGradient(w // 2, desk_y - 60, int(w * 0.75))
        glow.setColorAt(0, QColor(100, 160, 255, 50))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, glow)

        # ── Monitor ────────────────────────────────────────────────────────
        mon_w = int(w * 0.80)
        mon_h = int(h * 0.34)
        mon_x = (w - mon_w) // 2
        mon_y = int(h * 0.06)

        # Bezel
        p.setBrush(QBrush(QColor("#1a2540")))
        p.setPen(QPen(QColor("#2d4268"), 1))
        p.drawRoundedRect(mon_x, mon_y, mon_w, mon_h, 8, 8)

        # Screen
        sm = 7
        screen = QRect(mon_x + sm, mon_y + sm, mon_w - 2*sm, mon_h - 2*sm)
        sg = QLinearGradient(0, screen.top(), 0, screen.bottom())
        sg.setColorAt(0, QColor("#0d1f3c"))
        sg.setColorAt(1, QColor("#091628"))
        p.fillRect(screen, sg)

        # Terminal content — big enough to actually read
        p.setFont(QFont("Consolas", 11))
        lines = [
            (">>> db.tables()", C_ACCENT),
            ("+──────────────────+", C_BORDER),
            ("| name             |", C_TEXT),
            ("+──────────────────+", C_BORDER),
            ("| employees        |", C_TEXT),
            ("| transactions     |", C_TEXT),
            ("| vendors          |", C_TEXT),
            ("+──────────────────+", C_BORDER),
            ("  4 row(s)", C_DIM),
            (">>> _", C_SUCCESS),
        ]
        line_h = 18
        ty = screen.top() + 12
        for text, color in lines:
            if ty + line_h > screen.bottom() - 4:
                break
            p.setPen(QPen(color))
            p.drawText(screen.left() + 10, ty, text)
            ty += line_h

        # Monitor stand
        stand_x = w // 2
        p.setBrush(QBrush(QColor("#1a2540")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(stand_x - 7, mon_y + mon_h, 14, 18)
        p.drawRect(stand_x - 36, mon_y + mon_h + 14, 72, 8)

        # ── Desk surface ───────────────────────────────────────────────────
        p.setBrush(QBrush(QColor("#1e2d40")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)
        p.setPen(QPen(QColor("#2d4268"), 2))
        p.drawLine(0, desk_y, w, desk_y)

        # ── Big sticky note — takes up lower-left third ────────────────────
        note_w = int(w * 0.44)
        note_h = int((h - desk_y) * 0.82)
        note_x = int(w * 0.05)
        note_y = desk_y + int((h - desk_y) * 0.10)

        # Drop shadow
        p.setBrush(QBrush(QColor(0, 0, 0, 60)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(note_x + 4, note_y + 4, note_w, note_h)

        # Note body — bright yellow
        p.setBrush(QBrush(QColor("#f6e05e")))
        p.drawRect(note_x, note_y, note_w, note_h)

        # Folded corner
        fold = 14
        path = QPainterPath()
        path.moveTo(note_x + note_w - fold, note_y)
        path.lineTo(note_x + note_w, note_y + fold)
        path.lineTo(note_x + note_w, note_y)
        path.closeSubpath()
        p.setBrush(QBrush(QColor("#d4a017")))
        p.drawPath(path)

        # Note text — big and readable
        p.setPen(QPen(QColor("#1a1200")))
        pad = 12
        p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        p.drawText(note_x + pad, note_y + 22, "Welcome aboard,")
        p.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        p.drawText(note_x + pad, note_y + 44, "Alex! 👋")

        p.setPen(QPen(QColor("#4a3800")))
        p.setFont(QFont("Arial", 10))
        line_gap = 20
        notes = [
            "Sam says: get familiar",
            "with the database before",
            "the 9am standup.",
            "",
            "Start with:",
            "  db.tables()",
            "",
            "— D.R.",
        ]
        ty2 = note_y + 70
        for line in notes:
            if ty2 > note_y + note_h - 10:
                break
            p.drawText(note_x + pad, ty2, line)
            ty2 += line_gap

        # ── Coffee mug ─────────────────────────────────────────────────────
        mug_x = int(w * 0.74)
        mug_y = desk_y + int((h - desk_y) * 0.12)
        mug_w, mug_h2 = 38, 46
        p.setBrush(QBrush(QColor("#2d4060")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(mug_x, mug_y, mug_w, mug_h2, 4, 4)
        # Mug handle
        p.setPen(QPen(QColor("#2d4060"), 3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(mug_x + mug_w - 2, mug_y + 10, 18, 22, -90*16, -180*16)
        # Steam wisps
        p.setPen(QPen(QColor("#768ea8"), 1))
        for i, ox in enumerate([-3, 3, 0]):
            sx = mug_x + 10 + i * 10
            p.drawLine(sx, mug_y - 5, sx + ox, mug_y - 16)
        # "NEXUS" on mug
        p.setFont(QFont("Arial", 7, QFont.Weight.Bold))
        p.setPen(QPen(QColor("#79b8ff")))
        p.drawText(mug_x + 4, mug_y + 28, "NEXUS")

        self._draw_label(p, w, h, "Your Desk", "7:43 AM  |  Day One")

    # ── Scene: Server Room ────────────────────────────────────────────────────

    def _draw_server_room(self, p: QPainter, w: int, h: int):
        # Dark green-navy background — readable
        p.fillRect(0, 0, w, h, QColor("#0f1f18"))

        # Floor
        floor_y = int(h * 0.78)
        p.setBrush(QBrush(QColor("#111f18")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, floor_y, w, h - floor_y)

        # Rack units — draw 3 server racks
        rack_w = int(w * 0.22)
        rack_h = int(h * 0.70)
        rack_gap = int(w * 0.06)
        rack_top = int(h * 0.08)

        rack_colors = [QColor("#162418"), QColor("#132016"), QColor("#162418")]
        rack_xs = [
            int(w * 0.05),
            int(w * 0.05) + rack_w + rack_gap,
            int(w * 0.05) + 2 * (rack_w + rack_gap),
        ]

        for i, (rx, rc) in enumerate(zip(rack_xs, rack_colors)):
            # Rack body
            p.setBrush(QBrush(rc))
            p.drawRect(rx, rack_top, rack_w, rack_h)
            p.setPen(QPen(QColor("#1e2e1e"), 1))
            p.drawRect(rx, rack_top, rack_w, rack_h)

            # Unit slots
            slot_h = 10
            slot_margin = 4
            sy = rack_top + 10
            slot_i = 0
            while sy + slot_h < rack_top + rack_h - 10:
                # Alternate slot colors
                slot_col = QColor("#0d1f0f") if slot_i % 3 != 0 else QColor("#0a1a0c")
                p.setBrush(QBrush(slot_col))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRect(rx + slot_margin, sy, rack_w - 2*slot_margin, slot_h)

                # LED (green for most, one red)
                led_col = QColor("#22c55e") if (i == 1 and slot_i == 4) else QColor("#16a34a")
                if i == 0 and slot_i == 7:
                    led_col = QColor("#ef4444")  # the "red switch" Diana warned about
                p.setBrush(QBrush(led_col))
                p.drawEllipse(rx + rack_w - 12, sy + 3, 4, 4)

                sy += slot_h + 2
                slot_i += 1

            # Rack glow
            if i == 1:
                glow = QRadialGradient(rx + rack_w // 2, rack_top + rack_h // 2, rack_w)
                glow.setColorAt(0, QColor(34, 197, 94, 18))
                glow.setColorAt(1, QColor(0, 0, 0, 0))
                p.fillRect(rx - 20, rack_top, rack_w + 40, rack_h, glow)

        # Floor reflection
        ref_grad = QLinearGradient(0, floor_y, 0, h)
        ref_grad.setColorAt(0, QColor(34, 197, 94, 12))
        ref_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, floor_y, w, h - floor_y, ref_grad)

        self._draw_label(p, w, h, "Server Room B1", "Authorized Personnel Only")

    # ── Scene: HR Office ──────────────────────────────────────────────────────

    def _draw_hr_office(self, p: QPainter, w: int, h: int):
        # Warm daytime office
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#1a1208"))
        grad.setColorAt(1, QColor("#0d0e0a"))
        p.fillRect(0, 0, w, h, grad)

        desk_y = int(h * 0.58)

        # Window with daylight (back wall)
        win_w = int(w * 0.38)
        win_h = int(h * 0.28)
        win_x = int(w * 0.55)
        win_y = int(h * 0.12)
        win_grad = QLinearGradient(win_x, win_y, win_x, win_y + win_h)
        win_grad.setColorAt(0, QColor("#b8d4f0"))
        win_grad.setColorAt(1, QColor("#7aa8d4"))
        p.fillRect(win_x, win_y, win_w, win_h, win_grad)
        p.setPen(QPen(QColor("#3d2e18"), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(win_x, win_y, win_w, win_h)
        # Window cross
        p.drawLine(win_x + win_w//2, win_y, win_x + win_w//2, win_y + win_h)
        p.drawLine(win_x, win_y + win_h//2, win_x + win_w, win_y + win_h//2)

        # Desk surface
        p.setBrush(QBrush(QColor("#2a1f10")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)
        p.setPen(QPen(QColor("#3d2e18"), 1))
        p.drawLine(0, desk_y, w, desk_y)

        # Filing cabinet (left)
        cab_x = int(w * 0.05)
        cab_y = int(h * 0.3)
        cab_w = int(w * 0.20)
        cab_h = int(h * 0.45)
        p.setBrush(QBrush(QColor("#4a5568")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(cab_x, cab_y, cab_w, cab_h)
        # Drawer divisions
        p.setPen(QPen(QColor("#2d3748"), 1))
        for i in range(1, 4):
            dy = cab_y + i * cab_h // 4
            p.drawLine(cab_x, dy, cab_x + cab_w, dy)
        # Drawer handles
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#a0aec0")))
        for i in range(4):
            hy = cab_y + i * cab_h // 4 + cab_h // 8 - 2
            p.drawRect(cab_x + cab_w // 2 - 10, hy, 20, 4)

        # Label: PERSONNEL CONFIDENTIAL
        p.setFont(QFont("Arial", 5))
        p.setPen(QPen(QColor("#e2e8f0")))
        p.drawText(cab_x + 2, cab_y + 14, "PERSONNEL")
        p.drawText(cab_x + 2, cab_y + 24, "CONFIDENTIAL")

        # Open drawer
        open_drawer_y = cab_y + cab_h // 4
        p.setBrush(QBrush(QColor("#5a6578")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(cab_x, open_drawer_y, cab_w + 20, cab_h // 4 - 2)
        # File tabs sticking up
        colors = [QColor("#f6e05e"), QColor("#fc8181"), QColor("#68d391")]
        for i, fc in enumerate(colors):
            fx = cab_x + 4 + i * 10
            p.setBrush(QBrush(fc))
            p.drawRect(fx, open_drawer_y - 8, 8, 8)

        # Poster on wall
        poster_x = int(w * 0.62)
        poster_y = int(h * 0.44)
        p.setBrush(QBrush(QColor("#fffbeb")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(poster_x, poster_y, 90, 60)
        p.setFont(QFont("Arial", 4))
        p.setPen(QPen(QColor("#92400e")))
        p.drawText(poster_x + 4, poster_y + 14, "PEOPLE ARE OUR")
        p.drawText(poster_x + 4, poster_y + 26, "GREATEST ASSET")

        self._draw_label(p, w, h, "HR Office", "Vanessa is at lunch")

    # ── Scene: CFO Office ─────────────────────────────────────────────────────

    def _draw_cfo_office(self, p: QPainter, w: int, h: int):
        p.fillRect(0, 0, w, h, QColor("#090d14"))

        # Floor-to-ceiling window with city view
        win_h = int(h * 0.62)
        win_grad = QLinearGradient(0, 0, 0, win_h)
        win_grad.setColorAt(0, QColor("#0a1628"))
        win_grad.setColorAt(0.6, QColor("#0d1f40"))
        win_grad.setColorAt(1, QColor("#1a1208"))
        p.fillRect(0, 0, w, win_h, win_grad)

        # City skyline silhouette
        p.setBrush(QBrush(QColor("#050810")))
        p.setPen(Qt.PenStyle.NoPen)
        buildings = [
            (0, 0.28, 0.08, 0.34),
            (0.06, 0.18, 0.07, 0.44),
            (0.12, 0.24, 0.06, 0.38),
            (0.17, 0.14, 0.09, 0.48),
            (0.25, 0.30, 0.08, 0.32),
            (0.32, 0.10, 0.10, 0.52),
            (0.41, 0.22, 0.07, 0.40),
            (0.47, 0.16, 0.11, 0.46),
            (0.57, 0.28, 0.08, 0.34),
            (0.64, 0.12, 0.09, 0.50),
            (0.72, 0.20, 0.08, 0.42),
            (0.79, 0.26, 0.10, 0.36),
            (0.88, 0.18, 0.12, 0.44),
        ]
        for (bx, by, bw, bh) in buildings:
            p.drawRect(int(bx*w), int(by*h), int(bw*w), int(bh*h))

        # Window lights in buildings
        p.setBrush(QBrush(QColor("#f6e05e")))
        import random
        rng = random.Random(42)  # fixed seed for consistency
        for (bx, by, bw, bh) in buildings:
            bpx, bpy = int(bx*w), int(by*h)
            bpw, bph = int(bw*w), int(bh*h)
            for row in range(2, bph // 8):
                for col in range(1, bpw // 6):
                    if rng.random() > 0.55:
                        lx = bpx + col * 5
                        ly = bpy + row * 7
                        if lx < bpx + bpw - 4 and ly < bpy + bph - 4:
                            p.drawRect(lx, ly, 3, 2)

        # Window frame
        desk_y = int(h * 0.60)
        p.setBrush(QBrush(QColor("#1c2128")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)
        p.setPen(QPen(QColor("#30363d"), 1))
        p.drawLine(0, desk_y, w, desk_y)

        # Mahogany desk surface texture
        p.setBrush(QBrush(QColor("#3d1a0a")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)

        # Crumpled invoice receipt
        inv_x = int(w * 0.15)
        inv_y = desk_y + 10
        p.setBrush(QBrush(QColor("#f5f0e8")))
        p.setPen(Qt.PenStyle.NoPen)
        path = QPainterPath()
        path.moveTo(inv_x, inv_y + 15)
        path.lineTo(inv_x + 5, inv_y)
        path.lineTo(inv_x + 50, inv_y + 5)
        path.lineTo(inv_x + 55, inv_y + 20)
        path.lineTo(inv_x + 48, inv_y + 45)
        path.lineTo(inv_x + 2, inv_y + 42)
        path.closeSubpath()
        p.drawPath(path)
        p.setFont(QFont("Arial", 4))
        p.setPen(QPen(QColor("#374151")))
        p.drawText(inv_x + 6, inv_y + 18, "APEX SOLUTIONS")
        p.drawText(inv_x + 6, inv_y + 28, "$243,000.00")
        p.drawText(inv_x + 6, inv_y + 38, "DEC 2023")

        self._draw_label(p, w, h, "CFO's Office", "Marcus Webb | Board Meeting until 4pm")

    # ── Scene: Your Desk at Night ─────────────────────────────────────────────

    def _draw_desk_night(self, p: QPainter, w: int, h: int):
        # Late evening — deep navy, monitor glow more dominant
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#0f1a2e"))
        grad.setColorAt(1, QColor("#162236"))
        p.fillRect(0, 0, w, h, grad)

        desk_y = int(h * 0.55)

        # Stronger monitor glow (it's dark outside now)
        glow = QRadialGradient(w // 2, desk_y - 50, int(w * 0.75))
        glow.setColorAt(0, QColor(88, 166, 255, 55))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(0, 0, w, h, glow)

        p.setBrush(QBrush(QColor("#0d1117")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)
        p.setPen(QPen(QColor("#30363d"), 1))
        p.drawLine(0, desk_y, w, desk_y)

        # Monitor
        mon_w = int(w * 0.72)
        mon_h = int(h * 0.30)
        mon_x = (w - mon_w) // 2
        mon_y = desk_y - mon_h - 20

        p.setBrush(QBrush(QColor("#1c2128")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(mon_x, mon_y, mon_w, mon_h, 8, 8)

        screen_m = 6
        screen_rect = QRect(mon_x + screen_m, mon_y + screen_m,
                            mon_w - 2*screen_m, mon_h - 2*screen_m)
        sg = QLinearGradient(screen_rect.topLeft(), screen_rect.bottomLeft())
        sg.setColorAt(0, QColor("#0d1f3a"))
        sg.setColorAt(1, QColor("#0a1528"))
        p.fillRect(screen_rect, sg)

        # Full report on screen
        p.setFont(QFont("Consolas", 11))
        report_lines = [
            ("NEXUS ANALYTICS — FRAUD AUDIT REPORT", C_WARN := QColor("#f59e0b")),
            ("──────────────────────────────────────", C_BORDER),
            ("Vendor: Apex Solutions LLC  (unverified)", C_ERROR),
            ("  Total paid: $1,256,500", C_ERROR),
            ("Vendor: Pinnacle Strategy   (unverified)", C_ERROR),
            ("  Total paid:   $613,000", C_ERROR),
            ("──────────────────────────────────────", C_BORDER),
            ("GRAND TOTAL: $1,869,500", QColor("#ef4444")),
            ("Approved by: Marcus Webb (CFO, id=4)", C_ERROR),
            ("Department:  Special Projects", C_DIM),
            ("──────────────────────────────────────", C_BORDER),
            ("Status: ██████████ BUILDING CASE", C_SUCCESS),
        ]
        line_h = 17
        ty = screen_rect.top() + 12
        for text, color in report_lines:
            if ty + line_h > screen_rect.bottom() - 4:
                break
            p.setPen(QPen(color))
            p.drawText(screen_rect.left() + 6, ty, text)
            ty += line_h

        # Cold coffee mug
        mug_x = int(w * 0.78)
        mug_y = desk_y - 25
        p.setBrush(QBrush(QColor("#2d333b")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(mug_x, mug_y, 20, 25, 3, 3)

        self._draw_label(p, w, h, "Your Desk", "6:47 PM  |  Floor mostly empty")

    # ── Scene: COO Office ─────────────────────────────────────────────────────

    def _draw_coo_office(self, p: QPainter, w: int, h: int):
        # Clean, functional — COO office is no-nonsense
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#0e1118"))
        grad.setColorAt(1, QColor("#0d1117"))
        p.fillRect(0, 0, w, h, grad)

        desk_y = int(h * 0.58)

        # COO desk
        p.setBrush(QBrush(QColor("#1c2128")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(0, desk_y, w, h - desk_y)
        p.setPen(QPen(QColor("#30363d"), 1))
        p.drawLine(0, desk_y, w, desk_y)

        # Report printout on desk — the one you're about to hand over
        report_x = int(w * 0.20)
        report_y = desk_y + 12
        p.setBrush(QBrush(QColor("#f9fafb")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(report_x, report_y, int(w * 0.60), int(h * 0.28))
        # Paper lines
        p.setPen(QPen(QColor("#e5e7eb"), 1))
        for li in range(4):
            ly = report_y + 20 + li * 14
            p.drawLine(report_x + 10, ly, report_x + int(w*0.60) - 10, ly)

        p.setFont(QFont("Arial", 6))
        p.setPen(QPen(QColor("#111827")))
        p.drawText(report_x + 12, report_y + 14, "FRAUD AUDIT — NEXUS ANALYTICS CORP")
        p.setFont(QFont("Arial", 5))
        p.drawText(report_x + 12, report_y + 28, "Total fraudulent payments: $1,869,500")
        p.drawText(report_x + 12, report_y + 42, "Vendors: Apex Solutions LLC, Pinnacle Strategy")
        p.drawText(report_x + 12, report_y + 56, "Approved by: Marcus Webb, CFO")

        # CASE CLOSED stamp
        p.setFont(QFont("Arial", 14))
        p.setPen(QPen(QColor("#dc2626")))
        # Rotate for diagonal stamp effect
        p.save()
        p.translate(report_x + int(w*0.30), report_y + int(h*0.16))
        p.rotate(-18)
        p.drawText(-50, 10, "CASE CLOSED")
        p.restore()

        self._draw_label(p, w, h, "COO's Office", "Rachel Kim — Close the door.")

    # ── Clue sidebar ────────────────────────────────────────────────────────

    def _draw_clue_sidebar(self, p: QPainter, w: int, h: int, top_y: int, clue_h: int):
        """Draw a prominent checklist-style clue tracker in the bottom of the scene panel."""
        # Background — slightly lighter panel, distinct from scene art
        bg_grad = QLinearGradient(0, top_y, 0, h)
        bg_grad.setColorAt(0, QColor("#1e2d4a"))
        bg_grad.setColorAt(1, QColor("#162236"))
        p.fillRect(0, top_y, w, clue_h, bg_grad)

        # Top accent line — bright, eye-catching
        p.setPen(QPen(QColor("#56d364"), 3))
        p.drawLine(0, top_y, w, top_y)

        # Header — large and prominent
        p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        p.setPen(QPen(QColor("#e3b97a")))
        header_y = top_y + 28
        p.drawText(14, header_y, f"INVESTIGATION LOG")

        # Progress bar
        total_objectives = 13
        done = len(self._clues)
        bar_x = 14
        bar_y = header_y + 10
        bar_w = w - 28
        bar_h = 6

        # Bar background
        p.setBrush(QBrush(QColor("#2d4268")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)

        # Bar fill
        fill_w = int(bar_w * min(done / total_objectives, 1.0))
        if fill_w > 0:
            fill_grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            fill_grad.setColorAt(0, QColor("#22c55e"))
            fill_grad.setColorAt(1, QColor("#16a34a"))
            p.setBrush(QBrush(fill_grad))
            p.drawRoundedRect(bar_x, bar_y, fill_w, bar_h, 3, 3)

        # Progress text
        p.setFont(QFont("Segoe UI", 10))
        p.setPen(QPen(QColor("#768ea8")))
        p.drawText(bar_x, bar_y + 20, f"{done} of {total_objectives} clues found")

        # Clue entries — checklist style with checkmarks
        entry_y = bar_y + 38
        row_h = 26
        max_visible = (h - entry_y - 8) // row_h

        # Show all clues, most recent first
        visible_clues = self._clues[-max_visible:] if len(self._clues) > max_visible else self._clues

        for i, clue in enumerate(visible_clues):
            if entry_y + row_h > h - 4:
                break

            # Strip the "[CLUE #N]" prefix for clean display
            display = clue
            if clue.startswith("[CLUE"):
                parts = clue.split("]", 1)
                if len(parts) == 2:
                    display = parts[1].strip()

            # Alternate row backgrounds
            if i % 2 == 0:
                p.fillRect(6, entry_y - 4, w - 12, row_h - 2, QColor(255, 255, 255, 6))

            # Checkmark icon
            is_latest = (i == len(visible_clues) - 1)
            check_color = QColor("#56d364") if is_latest else QColor("#4ade80")
            p.setFont(QFont("Segoe UI", 12))
            p.setPen(QPen(check_color))
            p.drawText(12, entry_y + 14, "✓")

            # Clue text
            text_color = QColor("#e6edf3") if is_latest else QColor("#cdd9e5")
            p.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold if is_latest else QFont.Weight.Normal))
            p.setPen(QPen(text_color))

            # Truncate if too wide
            metrics = p.fontMetrics()
            available_w = w - 44
            display_text = metrics.elidedText(display, Qt.TextElideMode.ElideRight, available_w)
            p.drawText(32, entry_y + 14, display_text)

            entry_y += row_h

        # If there are hidden clues, show count
        if len(self._clues) > max_visible:
            p.setPen(QPen(QColor("#768ea8")))
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Normal, True))
            p.drawText(32, entry_y + 12, f"+ {len(self._clues) - max_visible} earlier")

    # ── Utility ───────────────────────────────────────────────────────────────

    def _draw_label(self, p: QPainter, w: int, h: int, title: str, subtitle: str):
        """Draw the scene name + subtitle in the bottom-left corner."""
        label_h = 60
        label_grad = QLinearGradient(0, h - label_h, 0, h)
        label_grad.setColorAt(0, QColor(0, 0, 0, 0))
        label_grad.setColorAt(1, QColor(0, 0, 0, 200))
        p.fillRect(0, h - label_h, w, label_h, label_grad)

        p.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        p.setPen(QPen(C_WARM))
        p.drawText(14, h - 30, title)

        p.setFont(QFont("Segoe UI", 11))
        p.setPen(QPen(C_DIM))
        p.drawText(14, h - 10, subtitle)
