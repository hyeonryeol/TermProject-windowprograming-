"""
Iron Crawler  /  아이언 크롤러
────────────────────────────────
달리는 기차 공장 게임.
자와족처럼 황무지를 달리며 고철을 터세요!

조작법:
  클릭        - 근처 자원 노드에 크루 파견
  TAB         - 공장 내부 뷰 / 세계 뷰 전환
  SPACE       - 일시정지
  ↑ / ↓      - 속도 조절
  ESC         - 종료
"""
import sys
import pygame

# ── bootstrap ─────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Iron Crawler  –  아이언 크롤러")
clock  = pygame.time.Clock()

from game.constants import FPS, BASE_SPEED, MIN_SPEED, MAX_SPEED
from game.assets    import load_assets
from game.train     import Train
from game.world     import World
from game.factory   import FactoryView
from game.hud       import HUD

assets  = load_assets()
train   = Train(assets)
world   = World(assets)
factory = FactoryView(train, assets)
hud     = HUD(train, world, assets)

VIEW_WORLD   = "world"
VIEW_FACTORY = "factory"
view   = VIEW_WORLD
paused = False

# ── main loop ─────────────────────────────────────────────
while True:
    dt = min(clock.tick(FPS) / 1000.0, 0.05)   # cap at 50 ms

    # ── Events ────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            elif event.key == pygame.K_TAB:
                view = VIEW_FACTORY if view == VIEW_WORLD else VIEW_WORLD

            elif event.key == pygame.K_SPACE:
                paused = not paused

            elif event.key in (pygame.K_UP, pygame.K_w):
                train.set_speed(+20)

            elif event.key in (pygame.K_DOWN, pygame.K_s):
                train.set_speed(-20)

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if view == VIEW_WORLD:
                if event.button == 1:
                    world.try_dispatch_worker(mx, my, train)
            elif view == VIEW_FACTORY:
                factory.handle_click(mx, my, event.button)

    # ── Update ────────────────────────────────────────────
    if not paused:
        train.update(dt)
        world.update(dt, train)
        if view == VIEW_FACTORY:
            factory.update(dt)

    # ── Render ────────────────────────────────────────────
    if view == VIEW_WORLD:
        world.render(screen, train)
        train.render(screen, world.camera_x)
        hud.render(screen, paused)
    else:
        factory.update(dt if paused else 0)   # stop factory when paused
        factory.render(screen)
        # Fuel bar still visible in factory view
        hud._draw_fuel_gauge(screen, assets["font_sm"])
        hud._draw_top_bar(screen, assets["font_sm"], assets["font_md"])
        if paused:
            hud._draw_paused(screen, assets["font_xl"])

    pygame.display.flip()
