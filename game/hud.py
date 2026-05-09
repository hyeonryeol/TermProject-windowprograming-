"""
World-view HUD: resource bar, fuel gauge, speed controls, status.
"""
import math
import pygame
from .constants import (
    SCREEN_W, SCREEN_H, MAX_FUEL, MAX_CREW, BASE_SPEED, MAX_SPEED,
    SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT,
    RNAMES, RCOLORS,
    UI_BG, UI_BD, UI_TXT, UI_ACC, DANGER, GOOD, WHITE, BLACK,
)


class HUD:
    def __init__(self, train, world, assets: dict):
        self.train  = train
        self.world  = world
        self.assets = assets

    def render(self, screen: pygame.Surface, paused: bool) -> None:
        font_sm = self.assets["font_sm"]
        font_md = self.assets["font_md"]

        self._draw_top_bar(screen, font_sm, font_md)
        self._draw_fuel_gauge(screen, font_sm)
        self._draw_speed_bar(screen, font_sm)
        self._draw_hints(screen, font_sm)
        self._draw_worker_status(screen, font_sm)
        if paused:
            self._draw_paused(screen, self.assets["font_xl"])

    # ── Top resource bar ───────────────────────────────────
    def _draw_top_bar(self, screen, font_sm, font_md):
        bar_h = 38
        surf  = pygame.Surface((SCREEN_W, bar_h), pygame.SRCALPHA)
        surf.fill((16, 12, 8, 210))
        screen.blit(surf, (0, 0))
        pygame.draw.line(screen, UI_BD, (0, bar_h), (SCREEN_W, bar_h))

        resources = [SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT]
        x = 14
        for res in resources:
            amt = self.train.inventory.get(res, 0)
            col = RCOLORS.get(res, WHITE)
            # colour swatch
            pygame.draw.rect(screen, col,               (x, 12, 12, 12))
            pygame.draw.rect(screen, (200, 190, 160),   (x, 12, 12, 12), 1)
            txt = font_sm.render(f"{RNAMES.get(res, res)}: {amt}", True, UI_TXT)
            screen.blit(txt, (x + 16, 13))
            x += txt.get_width() + 28

    # ── Fuel gauge (bottom-right) ──────────────────────────
    def _draw_fuel_gauge(self, screen, font):
        pct   = self.train.fuel / MAX_FUEL
        gx, gy = SCREEN_W - 220, SCREEN_H - 52
        gw, gh = 180, 18

        surf = pygame.Surface((gw + 60, gh + 26), pygame.SRCALPHA)
        surf.fill((16, 12, 8, 190))
        screen.blit(surf, (gx - 10, gy - 4))
        pygame.draw.rect(screen, UI_BD, (gx - 10, gy - 4, gw + 60, gh + 26), 1)

        label = font.render("연료", True, UI_ACC)
        screen.blit(label, (gx - 6, gy + 2))

        # Track
        pygame.draw.rect(screen, (35, 28, 18), (gx + 28, gy, gw, gh))
        # Fill
        fill_col = GOOD if pct > 0.25 else DANGER
        pygame.draw.rect(screen, fill_col, (gx + 28, gy, int(gw * pct), gh))
        pygame.draw.rect(screen, UI_BD, (gx + 28, gy, gw, gh), 1)

        pct_txt = font.render(f"{int(pct * 100)}%", True, UI_TXT)
        screen.blit(pct_txt, (gx + 28 + gw + 4, gy + 2))

    # ── Speed bar (bottom-left) ────────────────────────────
    def _draw_speed_bar(self, screen, font):
        pct   = self.train.speed / MAX_SPEED
        bx, by = 14, SCREEN_H - 52
        bw, bh = 140, 18

        surf = pygame.Surface((bw + 100, bh + 26), pygame.SRCALPHA)
        surf.fill((16, 12, 8, 190))
        screen.blit(surf, (bx - 6, by - 4))
        pygame.draw.rect(screen, UI_BD, (bx - 6, by - 4, bw + 100, bh + 26), 1)

        label = font.render("속도", True, UI_ACC)
        screen.blit(label, (bx, by + 2))

        pygame.draw.rect(screen, (35, 28, 18), (bx + 30, by, bw, bh))
        pygame.draw.rect(screen, (80, 140, 220), (bx + 30, by, int(bw * pct), bh))
        pygame.draw.rect(screen, UI_BD, (bx + 30, by, bw, bh), 1)

        spd_txt = font.render(f"{int(self.train.speed)} u/s  [↑↓]", True, UI_TXT)
        screen.blit(spd_txt, (bx + 30 + bw + 5, by + 2))

    # ── Key hints ─────────────────────────────────────────
    def _draw_hints(self, screen, font):
        hints = [
            "[TAB] 공장 뷰",
            "[SPACE] 일시정지",
            "[클릭] 자원 채취",
        ]
        y = SCREEN_H - 85
        for h in hints:
            surf = font.render(h, True, (110, 95, 70))
            screen.blit(surf, (SCREEN_W - surf.get_width() - 14, y))
            y += 16

    # ── Worker status ──────────────────────────────────────
    def _draw_worker_status(self, screen, font):
        busy  = len(self.world.workers)
        total = MAX_CREW
        sx, sy = 14, SCREEN_H - 88
        for i in range(total):
            col = GOOD if i < busy else (50, 42, 32)
            pygame.draw.circle(screen, col,         (sx + i * 20, sy), 7)
            pygame.draw.circle(screen, UI_BD,       (sx + i * 20, sy), 7, 1)
        txt = font.render(f"크루 {busy}/{total}", True, UI_TXT)
        screen.blit(txt, (sx + total * 20 + 8, sy - 6))

    # ── Paused overlay ─────────────────────────────────────
    def _draw_paused(self, screen, font):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        screen.blit(overlay, (0, 0))
        txt = font.render("일시 정지", True, UI_ACC)
        screen.blit(txt, (SCREEN_W // 2 - txt.get_width() // 2,
                          SCREEN_H // 2 - txt.get_height() // 2))
