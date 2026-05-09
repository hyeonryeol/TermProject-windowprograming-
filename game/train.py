import pygame
from .constants import (
    TRAIN_SCREEN_X, GROUND_Y,
    BASE_SPEED, MAX_SPEED, MIN_SPEED, FUEL_RATE, MAX_FUEL,
    SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT,
    WHITE, UI_ACC, DANGER, GOOD, UI_TXT,
)


class Train:
    """The player's mobile factory."""

    def __init__(self, assets: dict):
        self.assets    = assets
        self.world_x   = 600.0   # front of locomotive in world space
        self.speed     = BASE_SPEED
        self.fuel      = MAX_FUEL

        self.inventory = {
            SCRAP: 15, IRON: 0, COAL: 20,
            FUEL: 0,   COPPER: 0, CIRCUIT: 0,
        }

        # Car order: ["loco", "water", "cargo", "cargo"]
        self._build_sprites()

    # ── Geometry ───────────────────────────────────────────
    def _build_sprites(self):
        """Pre-scale and cache sprite rects for each car."""
        a = self.assets
        self._cars = []
        cursor = TRAIN_SCREEN_X   # left edge of current car

        for key in ("loco", "water", "cargo", "cargo"):
            img = a.get(key)
            if img is None:
                w, h = 120, 80
            else:
                w, h = img.get_size()
            # Bottom of car sits on ground
            rect = pygame.Rect(cursor, GROUND_Y - h, w, h)
            self._cars.append((key, img, rect))
            cursor += w - 2   # slight overlap to look connected

        self.train_width   = cursor - TRAIN_SCREEN_X
        self.center_offset = self.train_width // 2   # from world_x to centre

    @property
    def center_world_x(self) -> float:
        return self.world_x + self.center_offset

    @property
    def rear_world_x(self) -> float:
        return self.world_x + self.train_width

    # ── Inventory helpers ──────────────────────────────────
    def add(self, resource: str, amount: int) -> None:
        self.inventory[resource] = self.inventory.get(resource, 0) + amount

    def take(self, resource: str, amount: int) -> bool:
        if self.inventory.get(resource, 0) >= amount:
            self.inventory[resource] -= amount
            return True
        return False

    def has(self, resource: str, amount: int = 1) -> bool:
        return self.inventory.get(resource, 0) >= amount

    # ── Update ─────────────────────────────────────────────
    def update(self, dt: float) -> None:
        if self.fuel > 0:
            spend = FUEL_RATE * dt * (self.speed / BASE_SPEED)
            self.fuel = max(0.0, self.fuel - spend)
            self.world_x += self.speed * dt
        else:
            # Coast to a stop
            self.speed = max(0.0, self.speed - 40 * dt)
            self.world_x += self.speed * dt

        # Ramp back up once fuel is available
        if self.fuel > 5 and self.speed < BASE_SPEED:
            self.speed = min(BASE_SPEED, self.speed + 25 * dt)

    def set_speed(self, delta: float) -> None:
        self.speed = max(MIN_SPEED, min(MAX_SPEED, self.speed + delta))

    # ── Render ─────────────────────────────────────────────
    def render(self, screen: pygame.Surface, camera_x: float) -> None:
        # Smoke puffs from locomotive (simple circles)
        self._draw_smoke(screen, camera_x)

        for key, img, template_rect in self._cars:
            # Shift rect by (world_x - camera_x) to account for world scroll
            # Train world_x maps to TRAIN_SCREEN_X, so offset is 0 for camera following
            rect = template_rect.copy()
            if img:
                screen.blit(img, rect.topleft)
            else:
                col = (80, 70, 55) if key == "loco" else (65, 58, 45)
                pygame.draw.rect(screen, col, rect)
                pygame.draw.rect(screen, (100, 90, 70), rect, 2)

    def _draw_smoke(self, screen: pygame.Surface, camera_x: float) -> None:
        import math, time
        t = time.time()
        # Smoke from chimney at ~30px from left of loco, near top
        loco_rect = self._cars[0][2]
        cx = loco_rect.x + 30
        cy = loco_rect.y + 8
        for i in range(3):
            phase = t * 1.5 + i * 0.6
            ox = int(math.sin(phase) * 4)
            oy = int(i * 12 + (phase % 1) * 10)
            alpha = max(0, 180 - oy * 4)
            r = 5 + i * 3
            psurf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(psurf, (180, 170, 155, alpha), (r, r), r)
            screen.blit(psurf, (cx + ox - r, cy - oy - r))
