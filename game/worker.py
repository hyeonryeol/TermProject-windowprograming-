import math
import pygame
from .constants import GROUND_Y, RCOLORS, WORKER_SPD


class Worker:
    """A crew member that runs to a node, gathers resources, and returns."""

    IDLE     = "idle"
    OUTBOUND = "outbound"
    GATHER   = "gather"
    RETURN   = "return"
    DONE     = "done"

    def __init__(self, start_world_x: float, node):
        self.world_x  = float(start_world_x)
        self.node     = node
        self.state    = self.OUTBOUND
        self.gathered = {}
        self.anim_timer = 0.0
        self.gather_timer = 0.0
        node.being_gathered = True

    # ── State ──────────────────────────────────────────────
    @property
    def done(self) -> bool:
        return self.state == self.DONE

    # ── Update ─────────────────────────────────────────────
    def update(self, dt: float, train) -> None:
        self.anim_timer += dt

        if self.state == self.OUTBOUND:
            self._move_toward(self.node.world_x, dt)
            if abs(self.world_x - self.node.world_x) < 8:
                self.state = self.GATHER
                self.gather_timer = 0.0

        elif self.state == self.GATHER:
            self.gather_timer += dt
            if self.gather_timer >= self.node.gather_time:
                self._take_from_node()
                self.state = self.RETURN

        elif self.state == self.RETURN:
            target = train.world_x + 20   # near the rear of loco
            self._move_toward(target, dt)
            if abs(self.world_x - target) < 10:
                self._deposit(train)
                self.state = self.DONE
                self.node.being_gathered = False

    # ── Helpers ────────────────────────────────────────────
    def _move_toward(self, target_x: float, dt: float) -> None:
        dist = target_x - self.world_x
        step = WORKER_SPD * dt
        if abs(dist) <= step:
            self.world_x = target_x
        else:
            self.world_x += math.copysign(step, dist)

    def _take_from_node(self) -> None:
        node = self.node
        self.gathered = dict(node.resources)
        node.resources = {}
        node.depleted  = True

    def _deposit(self, train) -> None:
        for res, amt in self.gathered.items():
            train.add(res, amt)
        self.gathered = {}

    # ── Render ─────────────────────────────────────────────
    def render(self, screen: pygame.Surface, camera_x: float) -> None:
        sx = int(self.world_x - camera_x)
        sy = GROUND_Y - 4   # stand on ground

        # Walking animation: legs swing
        t   = self.anim_timer * 6
        leg = math.sin(t) * 5
        dir_sign = 1 if self.state == self.OUTBOUND else -1

        skin  = (200, 178, 138)
        cloth = (80, 100, 130)
        boot  = (55, 42, 28)

        # Legs
        pygame.draw.line(screen, boot,
                         (sx, sy - 6), (sx + int(leg),      sy + 5), 2)
        pygame.draw.line(screen, boot,
                         (sx, sy - 6), (sx - int(leg),      sy + 5), 2)
        # Body
        pygame.draw.rect(screen, cloth,  (sx - 4, sy - 18, 8, 12))
        # Head
        pygame.draw.circle(screen, skin,  (sx, sy - 22), 5)
        # Arms (swing opposite legs)
        arm = math.sin(t + math.pi) * 4
        pygame.draw.line(screen, cloth,
                         (sx, sy - 14), (sx + int(arm) - 3, sy - 9), 2)
        pygame.draw.line(screen, cloth,
                         (sx, sy - 14), (sx - int(arm) + 3, sy - 9), 2)

        # Carry icon while returning
        if self.state == self.RETURN and self.gathered:
            res = next(iter(self.gathered))
            col = RCOLORS.get(res, (180, 180, 180))
            pygame.draw.rect(screen, col, (sx - 4, sy - 30, 8, 7))
            pygame.draw.rect(screen, (220, 210, 190), (sx - 4, sy - 30, 8, 7), 1)

        # Gathering animation
        if self.state == self.GATHER:
            prog = self.gather_timer / max(self.node.gather_time, 0.001)
            bar_w = 30
            pygame.draw.rect(screen, (40, 40, 40),   (sx - 15, sy - 40, bar_w, 5))
            pygame.draw.rect(screen, (80, 220, 100), (sx - 15, sy - 40, int(bar_w * prog), 5))
