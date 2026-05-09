import math
import random
import pygame
from .constants import (
    NODES, RNAMES, RCOLORS, GROUND_Y,
    WHITE, BLACK, UI_TXT, UI_ACC, GOOD,
)

_GLOW_RADIUS = 44


class ResourceNode:
    """A scavengeable resource deposit sitting in the world."""

    def __init__(self, world_x: float, node_type: str, sprite):
        self.world_x  = world_x
        # Sit just above ground with slight variation
        self.world_y  = GROUND_Y - random.randint(15, 55)
        self.type     = node_type
        self.sprite   = sprite
        self.depleted = False
        self.in_range = False
        self.being_gathered = False

        nd = NODES[node_type]
        self.label = nd["label"]
        self.gather_time = nd["time"]

        # Roll yields
        self.resources = {}
        for res, (lo, hi) in nd["yields"].items():
            amt = random.randint(lo, hi)
            if amt > 0:
                self.resources[res] = amt

        # Animation
        self.timer = random.uniform(0, math.pi * 2)

    # ── Update ─────────────────────────────────────────────
    def update(self, dt: float):
        self.timer += dt

    # ── Render ─────────────────────────────────────────────
    def render(self, screen: pygame.Surface, sx: int):
        sy = int(self.world_y)

        if self.depleted:
            if self.sprite:
                dark = self.sprite.copy()
                dark.fill((0, 0, 0, 160), special_flags=pygame.BLEND_RGBA_MULT)
                w, h = dark.get_size()
                screen.blit(dark, (sx - w // 2, sy - h))
            return

        # Glow ring when in range
        if self.in_range and not self.being_gathered:
            alpha = int(90 + 55 * abs(math.sin(self.timer * 2.2)))
            gsurf = pygame.Surface((_GLOW_RADIUS * 2, _GLOW_RADIUS * 2), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (80, 220, 100, alpha),
                               (_GLOW_RADIUS, _GLOW_RADIUS), _GLOW_RADIUS)
            screen.blit(gsurf, (sx - _GLOW_RADIUS, sy - _GLOW_RADIUS))

        # Sprite or fallback shape
        if self.sprite:
            w, h = self.sprite.get_size()
            screen.blit(self.sprite, (sx - w // 2, sy - h))
        else:
            pygame.draw.circle(screen, (115, 105, 85), (sx, sy), 22)
            pygame.draw.circle(screen, (145, 135, 110), (sx, sy), 22, 2)

        # Label and resource hint (only when in range)
        if self.in_range and not self.being_gathered:
            self._draw_tooltip(screen, sx, sy)

    def _draw_tooltip(self, screen, sx, sy):
        lines = [self.label] + [
            f"{RNAMES.get(r, r)}: {amt}"
            for r, amt in self.resources.items()
        ]
        font = pygame.font.Font(None, 16)
        line_h = 14
        box_w  = max(font.size(l)[0] for l in lines) + 10
        box_h  = len(lines) * line_h + 6
        bx = sx - box_w // 2
        by = sy - 80 - box_h

        bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg.fill((10, 8, 5, 200))
        screen.blit(bg, (bx, by))
        pygame.draw.rect(screen, UI_ACC, (bx, by, box_w, box_h), 1)

        for i, ln in enumerate(lines):
            col = UI_ACC if i == 0 else UI_TXT
            surf = font.render(ln, True, col)
            screen.blit(surf, (bx + 5, by + 3 + i * line_h))
