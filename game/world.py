import math
import random
import pygame
from .constants import (
    SCREEN_W, SCREEN_H, GROUND_Y, HORIZON_Y, RAIL_Y, TRAIN_SCREEN_X,
    SKY1, SKY2, GND1, GND2, RAIL_C,
    NODES, NODE_MIN_GAP, NODE_MAX_GAP, GEN_AHEAD, SCAVENGE_DIST,
)
from .node import ResourceNode
from .worker import Worker


# Pre-bake a sky gradient into a Surface for speed
def _build_sky() -> pygame.Surface:
    surf = pygame.Surface((SCREEN_W, GROUND_Y))
    for y in range(GROUND_Y):
        t = y / GROUND_Y
        r = int(SKY1[0] + (SKY2[0] - SKY1[0]) * t)
        g = int(SKY1[1] + (SKY2[1] - SKY1[1]) * t)
        b = int(SKY1[2] + (SKY2[2] - SKY1[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))
    return surf


class World:
    def __init__(self, assets: dict):
        self.assets  = assets
        self.camera_x = 0.0      # world x of screen left edge

        self.nodes   = []
        self.workers = []
        self._next_node_x = 700.0   # next node spawn position

        # Background helpers
        self.sky_surf = _build_sky()
        self._tile_offset = 0

        # Pre-generate a bunch of nodes
        for _ in range(12):
            self._gen_node()

    # ── Node generation ────────────────────────────────────
    def _sprite_pool(self, pool_name: str) -> list:
        return self.assets.get(pool_name, [])

    def _gen_node(self) -> None:
        ntype = random.choices(
            ["ruin", "rock", "coal_seam"],
            weights=[50, 35, 15],
        )[0]
        pool_name = NODES[ntype]["sprite_pool"]
        pool = self._sprite_pool(pool_name)
        sprite = random.choice(pool) if pool else None

        node = ResourceNode(self._next_node_x, ntype, sprite)
        self.nodes.append(node)
        self._next_node_x += random.randint(NODE_MIN_GAP, NODE_MAX_GAP)

    # ── Coordinate helpers ─────────────────────────────────
    def to_screen_x(self, world_x: float) -> int:
        return int(world_x - self.camera_x)

    def to_world_x(self, screen_x: int) -> float:
        return float(screen_x) + self.camera_x

    # ── Update ─────────────────────────────────────────────
    def update(self, dt: float, train) -> None:
        self.camera_x = train.world_x - TRAIN_SCREEN_X

        # Generate nodes ahead
        while self._next_node_x < train.world_x + GEN_AHEAD:
            self._gen_node()

        # Cull nodes that are too far behind
        self.nodes = [
            n for n in self.nodes
            if n.world_x > train.world_x - 800
        ]

        # Mark nodes in scavenge range
        for node in self.nodes:
            dist = abs(node.world_x - train.center_world_x)
            node.in_range = dist < SCAVENGE_DIST and not node.depleted
            node.update(dt)

        # Update workers
        for w in self.workers:
            w.update(dt, train)
        self.workers = [w for w in self.workers if not w.done]

        # Tile scroll offset for ground texture
        self._tile_offset = int(self.camera_x) % 32

    # ── Interaction ────────────────────────────────────────
    def try_dispatch_worker(self, screen_x: int, screen_y: int, train) -> bool:
        """Click handler: dispatch a worker to the nearest in-range node."""
        # Count busy workers
        busy = len(self.workers)
        from .constants import MAX_CREW
        if busy >= MAX_CREW:
            return False

        wx = self.to_world_x(screen_x)
        best, best_dist = None, 999999.0
        for node in self.nodes:
            if not node.in_range or node.being_gathered:
                continue
            d = abs(node.world_x - wx)
            if d < best_dist and d < 200:
                best, best_dist = node, d

        if best is None:
            # Accept any in-range node within 300 screen px
            for node in self.nodes:
                if node.in_range and not node.being_gathered:
                    sx = self.to_screen_x(node.world_x)
                    if abs(sx - screen_x) < 300:
                        best = node
                        break

        if best:
            start_wx = train.world_x + 10
            self.workers.append(Worker(start_wx, best))
            return True
        return False

    # ── Render ─────────────────────────────────────────────
    def render(self, screen: pygame.Surface, train) -> None:
        # Sky
        screen.blit(self.sky_surf, (0, 0))

        # Distant hills (parallax)
        self._draw_hills(screen)

        # Ground strip
        pygame.draw.rect(screen, GND1, (0, GROUND_Y, SCREEN_W, SCREEN_H - GROUND_Y))
        pygame.draw.rect(screen, GND2, (0, GROUND_Y + 2, SCREEN_W, SCREEN_H - GROUND_Y - 2))

        # Rail track
        self._draw_rail(screen)

        # Resource nodes
        for node in self.nodes:
            sx = self.to_screen_x(node.world_x)
            if -100 < sx < SCREEN_W + 100:
                node.render(screen, sx)

        # Workers
        for w in self.workers:
            w.render(screen, self.camera_x)

    def _draw_hills(self, screen: pygame.Surface) -> None:
        """Simple parallax mountain silhouette."""
        offset = self.camera_x * 0.15   # slow parallax
        pts = [(0, HORIZON_Y + 40)]
        for i in range(0, SCREEN_W + 80, 60):
            hx = i
            hy = HORIZON_Y + int(
                28 * math.sin((i + offset) * 0.018)
                + 14 * math.sin((i + offset) * 0.035 + 1.2)
            )
            pts.append((hx, hy))
        pts += [(SCREEN_W, HORIZON_Y + 40), (SCREEN_W, GROUND_Y), (0, GROUND_Y)]
        pygame.draw.polygon(screen, (55, 43, 28), pts)

        # Second layer (closer, darker)
        offset2 = self.camera_x * 0.32
        pts2 = [(0, HORIZON_Y + 90)]
        for i in range(0, SCREEN_W + 60, 50):
            hy = HORIZON_Y + 60 + int(
                20 * math.sin((i + offset2) * 0.025 + 0.7)
                + 10 * math.sin((i + offset2) * 0.05 + 2.1)
            )
            pts2.append((i, hy))
        pts2 += [(SCREEN_W, HORIZON_Y + 90), (SCREEN_W, GROUND_Y), (0, GROUND_Y)]
        pygame.draw.polygon(screen, (48, 38, 24), pts2)

    def _draw_rail(self, screen: pygame.Surface) -> None:
        ry = RAIL_Y
        # Rail bed
        pygame.draw.rect(screen, RAIL_C,       (0, ry - 2, SCREEN_W, 16))
        pygame.draw.rect(screen, (70, 55, 35), (0, ry,     SCREEN_W, 12))

        # Rail lines
        pygame.draw.rect(screen, (110, 95, 65), (0, ry,     SCREEN_W, 3))
        pygame.draw.rect(screen, (110, 95, 65), (0, ry + 8, SCREEN_W, 3))

        # Ties (sleepers) – scroll with world
        tie_gap = 42
        off = int(self.camera_x) % tie_gap
        for x in range(-off, SCREEN_W, tie_gap):
            pygame.draw.rect(screen, (60, 48, 30), (x - 2, ry - 5, 10, 22))
