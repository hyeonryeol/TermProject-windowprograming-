"""
Factory interior view (TAB).

Shows a 2-D grid representing the inside of the train cars.
The player can place machines that auto-process items from the
train's shared inventory.
"""
import math
import pygame
from .constants import (
    SCREEN_W, SCREEN_H,
    CELL, FGRID_W, FGRID_H, FGRID_X, FGRID_Y,
    M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER,
    MDEF, RNAMES, RCOLORS,
    UI_BG, UI_BD, UI_TXT, UI_ACC, GOOD, DANGER, WHITE, BLACK,
    IRON, SCRAP, COAL, FUEL, COPPER, CIRCUIT,
)

PALETTE_X = SCREEN_W - 200
PALETTE_Y = 60
PALETTE_W = 190
MACHINE_ORDER = [M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER]


class Machine:
    def __init__(self, mtype: str, gx: int, gy: int):
        self.type   = mtype
        self.gx, self.gy = gx, gy   # grid top-left
        defn = MDEF[mtype]
        self.gw, self.gh = defn["size"]
        self.color  = defn["color"]
        self.name   = defn["name"]
        self.timer  = 0.0           # production progress [0, time]
        self.active = False

    def rect_px(self) -> pygame.Rect:
        return pygame.Rect(
            FGRID_X + self.gx * CELL,
            FGRID_Y + self.gy * CELL,
            self.gw * CELL,
            self.gh * CELL,
        )

    def update(self, dt: float, train) -> None:
        defn = MDEF[self.type]
        inp  = defn["inp"]
        out  = defn["out"]
        t    = defn["time"]

        if inp is None or out is None:
            return   # belt / storage: passive

        if self.timer <= 0:
            # Try to start a new cycle
            if all(train.has(r, amt) for r, amt in inp.items()):
                for r, amt in inp.items():
                    train.take(r, amt)
                self.timer  = t
                self.active = True
        else:
            self.timer -= dt
            if self.timer <= 0:
                for r, amt in out.items():
                    train.add(r, amt)
                self.timer  = 0.0
                self.active = False

    def render(self, screen: pygame.Surface, font) -> None:
        r = self.rect_px()

        # Body
        pygame.draw.rect(screen, self.color, r, border_radius=4)
        pygame.draw.rect(screen, (min(self.color[0]+40,255),
                                  min(self.color[1]+40,255),
                                  min(self.color[2]+40,255)), r, 2, border_radius=4)

        defn = MDEF[self.type]
        t    = defn["time"]

        # Progress bar
        if self.active and t > 0:
            prog = 1.0 - self.timer / t
            bar  = pygame.Rect(r.x + 2, r.bottom - 8, r.width - 4, 6)
            pygame.draw.rect(screen, (30, 30, 30), bar)
            pygame.draw.rect(screen, GOOD, (bar.x, bar.y, int(bar.width * prog), bar.height))

        # Name label
        label = font.render(self.name, True, WHITE)
        lx = r.centerx - label.get_width() // 2
        ly = r.y + 4
        screen.blit(label, (lx, ly))

        # Belt: draw arrow
        if self.type == M_BELT:
            mid = r.centery
            pygame.draw.polygon(screen, WHITE, [
                (r.x + 8,       mid),
                (r.right - 12,  mid),
                (r.right - 12,  mid - 5),
                (r.right - 4,   mid + 1),
                (r.right - 12,  mid + 6),
                (r.right - 12,  mid + 2),
                (r.x + 8,       mid + 2),
            ])


class FactoryView:
    def __init__(self, train, assets: dict):
        self.train    = train
        self.assets   = assets
        self.machines: list[Machine] = []
        self.grid     = [[None] * FGRID_W for _ in range(FGRID_H)]
        self.selected = M_FURNACE    # selected machine type from palette
        self.anim_t   = 0.0

        # Pre-built starting machine
        self._place(M_FURNACE, 0, 1)

    # ── Grid helpers ───────────────────────────────────────
    def _place(self, mtype: str, gx: int, gy: int) -> bool:
        defn = MDEF[mtype]
        gw, gh = defn["size"]
        # Bounds check
        if gx + gw > FGRID_W or gy + gh > FGRID_H:
            return False
        # Overlap check
        for dy in range(gh):
            for dx in range(gw):
                if self.grid[gy + dy][gx + dx] is not None:
                    return False
        m = Machine(mtype, gx, gy)
        self.machines.append(m)
        for dy in range(gh):
            for dx in range(gw):
                self.grid[gy + dy][gx + dx] = m
        return True

    def _remove(self, gx: int, gy: int) -> None:
        m = self.grid[gy][gx]
        if m is None:
            return
        if m in self.machines:
            self.machines.remove(m)
        for row in self.grid:
            for i, cell in enumerate(row):
                if cell is m:
                    row[i] = None

    def _px_to_grid(self, px: int, py: int):
        gx = (px - FGRID_X) // CELL
        gy = (py - FGRID_Y) // CELL
        if 0 <= gx < FGRID_W and 0 <= gy < FGRID_H:
            return gx, gy
        return None, None

    # ── Event ──────────────────────────────────────────────
    def handle_click(self, mx: int, my: int, button: int) -> None:
        # Click palette
        for i, mtype in enumerate(MACHINE_ORDER):
            by = PALETTE_Y + 10 + i * 68
            if PALETTE_X <= mx <= PALETTE_X + PALETTE_W and by <= my <= by + 60:
                self.selected = mtype
                return

        gx, gy = self._px_to_grid(mx, my)
        if gx is None:
            return

        if button == 1:   # left-click: place
            cost = MDEF[self.selected]["cost"]
            can_afford = all(self.train.has(r, amt) for r, amt in cost.items())
            if can_afford:
                if self._place(self.selected, gx, gy):
                    for r, amt in cost.items():
                        self.train.take(r, amt)
        elif button == 3:  # right-click: remove
            self._remove(gx, gy)

    # ── Update ─────────────────────────────────────────────
    def update(self, dt: float) -> None:
        self.anim_t += dt
        for m in self.machines:
            m.update(dt, self.train)

    # ── Render ─────────────────────────────────────────────
    def render(self, screen: pygame.Surface) -> None:
        screen.fill(UI_BG)
        font_sm = self.assets["font_sm"]
        font_md = self.assets["font_md"]

        self._draw_grid(screen, font_sm)
        self._draw_machines(screen, font_sm)
        self._draw_palette(screen, font_sm, font_md)
        self._draw_car_labels(screen, font_sm)
        self._draw_inventory_strip(screen, font_sm)
        self._draw_header(screen, font_md)

    def _draw_header(self, screen, font):
        surf = font.render("공장 내부  [TAB] 세계 뷰로 복귀  |  좌클릭: 배치  우클릭: 제거", True, UI_ACC)
        screen.blit(surf, (FGRID_X, 12))

    def _draw_grid(self, screen, font):
        # Car section backgrounds
        car_widths = [7, 4, 6, 5]  # cells per car section
        colors = [(25, 20, 14), (22, 18, 12), (20, 16, 10), (18, 14, 9)]
        cx = FGRID_X
        for i, (cw, col) in enumerate(zip(car_widths, colors)):
            w = cw * CELL
            h = FGRID_H * CELL
            pygame.draw.rect(screen, col, (cx, FGRID_Y, w, h))
            pygame.draw.rect(screen, UI_BD, (cx, FGRID_Y, w, h), 1)
            cx += w

        # Grid lines
        for gy in range(FGRID_H + 1):
            y = FGRID_Y + gy * CELL
            pygame.draw.line(screen, (35, 28, 18),
                             (FGRID_X, y), (FGRID_X + FGRID_W * CELL, y))
        for gx in range(FGRID_W + 1):
            x = FGRID_X + gx * CELL
            pygame.draw.line(screen, (35, 28, 18),
                             (x, FGRID_Y), (x, FGRID_Y + FGRID_H * CELL))

    def _draw_machines(self, screen, font):
        for m in self.machines:
            m.render(screen, font)

    def _draw_car_labels(self, screen, font):
        labels = ["기관실", "연료칸", "화물칸 A", "화물칸 B"]
        widths = [7, 4, 6, 5]
        cx = FGRID_X
        for label, w in zip(labels, widths):
            px = cx + w * CELL // 2
            surf = font.render(label, True, UI_BD)
            screen.blit(surf, (px - surf.get_width() // 2,
                               FGRID_Y + FGRID_H * CELL + 4))
            cx += w * CELL

    def _draw_palette(self, screen, font_sm, font_md):
        px, py = PALETTE_X, PALETTE_Y
        pw     = PALETTE_W

        # Panel background
        panel = pygame.Surface((pw + 2, SCREEN_H - py - 20), pygame.SRCALPHA)
        panel.fill((20, 15, 10, 220))
        screen.blit(panel, (px - 1, py))
        pygame.draw.rect(screen, UI_BD, (px - 1, py, pw + 2, SCREEN_H - py - 20), 1)

        title = font_md.render("기계 팔레트", True, UI_ACC)
        screen.blit(title, (px + pw // 2 - title.get_width() // 2, py + 4))

        for i, mtype in enumerate(MACHINE_ORDER):
            defn = MDEF[mtype]
            by   = py + 10 + 36 + i * 68
            sel  = mtype == self.selected

            # Card
            card_col = (45, 35, 22) if sel else (28, 22, 14)
            border_col = UI_ACC if sel else UI_BD
            pygame.draw.rect(screen, card_col, (px + 5, by, pw - 10, 62), border_radius=4)
            pygame.draw.rect(screen, border_col, (px + 5, by, pw - 10, 62), 1, border_radius=4)

            # Colour swatch
            pygame.draw.rect(screen, defn["color"], (px + 10, by + 8, 20, 20), border_radius=3)

            # Name
            name_surf = font_md.render(defn["name"], True, UI_ACC if sel else UI_TXT)
            screen.blit(name_surf, (px + 36, by + 8))

            # Cost
            cost = defn["cost"]
            if cost:
                cost_str = "  ".join(
                    f"{RNAMES.get(r, r)}×{amt}" for r, amt in cost.items()
                )
                can = all(self.train.has(r, amt) for r, amt in cost.items())
                col = GOOD if can else DANGER
                cs  = font_sm.render(cost_str, True, col)
                screen.blit(cs, (px + 10, by + 34))
            else:
                free = font_sm.render("무료", True, GOOD)
                screen.blit(free, (px + 10, by + 34))

            # Recipe hint
            inp = defn["inp"]
            out = defn["out"]
            if inp and out:
                in_str  = "+".join(f"{RNAMES.get(r,r)}" for r in inp)
                out_str = "+".join(f"{RNAMES.get(r,r)}" for r in out)
                hint    = font_sm.render(f"{in_str}→{out_str}", True, (130, 120, 95))
                screen.blit(hint, (px + 10, by + 48))

    def _draw_inventory_strip(self, screen, font):
        """Small inventory bar at the bottom of the factory view."""
        bar_y = SCREEN_H - 44
        pygame.draw.rect(screen, (22, 18, 12), (0, bar_y, SCREEN_W, 44))
        pygame.draw.line(screen, UI_BD, (0, bar_y), (SCREEN_W, bar_y))

        resources = [
            (r, self.train.inventory.get(r, 0))
            for r in [SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT]
        ]
        x = 20
        for res, amt in resources:
            col = RCOLORS.get(res, WHITE)
            pygame.draw.rect(screen, col, (x, bar_y + 12, 14, 14))
            pygame.draw.rect(screen, (200, 190, 160), (x, bar_y + 12, 14, 14), 1)
            name_surf = font.render(f"{RNAMES.get(res, res)}: {amt}", True, UI_TXT)
            screen.blit(name_surf, (x + 18, bar_y + 14))
            x += name_surf.get_width() + 34
