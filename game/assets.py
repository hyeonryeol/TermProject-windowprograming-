import pygame
import subprocess
from .constants import TRAIN_DIR, RUINS_DIR, ROCKS_DIR, TILES_DIR

# ─────────────────────────────────────────────────────────
def _find_korean_font():
    """Return a pygame Font that can render Korean, or None."""
    candidates = [
        "malgungothic", "malgun gothic",
        "nanumgothic", "nanum gothic",
        "dotumche", "gulim",
        "unifont",
    ]
    for name in candidates:
        try:
            f = pygame.font.SysFont(name, 14)
            # Quick check: does it render a Korean glyph correctly?
            surf = f.render("고", True, (255, 255, 255))
            if surf.get_width() > 4:
                return name
        except Exception:
            pass

    # Try finding a .ttf via fc-list (Linux)
    try:
        result = subprocess.run(
            ["fc-list", ":lang=ko", "--format=%{file}\n"],
            capture_output=True, text=True, timeout=2,
        )
        for line in result.stdout.splitlines():
            path = line.strip()
            if path.endswith(".ttf") or path.endswith(".otf"):
                return path          # pygame.font.Font accepts a file path too
    except Exception:
        pass

    return None


def _make_font(name_or_path, size):
    if name_or_path is None:
        return pygame.font.Font(None, size)
    if name_or_path.startswith("/"):          # file path
        try:
            return pygame.font.Font(name_or_path, size)
        except Exception:
            return pygame.font.Font(None, size)
    return pygame.font.SysFont(name_or_path, size)


def _scale(img, factor=2):
    w, h = img.get_size()
    return pygame.transform.scale(img, (w * factor, h * factor))


def load_assets():
    assets = {}

    # ── Train sprites (scale 2×) ──────────────────────────
    try:
        assets["loco"]  = _scale(pygame.image.load(str(TRAIN_DIR / "기관차.png")).convert_alpha())
        assets["cargo"] = _scale(pygame.image.load(str(TRAIN_DIR / "짐칸.png")).convert_alpha())
        assets["water"] = _scale(pygame.image.load(str(TRAIN_DIR / "물칸.png")).convert_alpha())
    except Exception as e:
        print(f"[assets] Could not load train sprites: {e}")
        assets["loco"]  = None
        assets["cargo"] = None
        assets["water"] = None

    # ── Resource-node sprites ─────────────────────────────
    ruins, rocks = [], []
    for i in range(1, 6):
        p = RUINS_DIR / f"{i}.png"
        if p.exists():
            img = pygame.image.load(str(p)).convert_alpha()
            ruins.append(pygame.transform.scale(img, (72, 60)))
    for i in range(1, 7):
        p = ROCKS_DIR / f"{i}.png"
        if p.exists():
            img = pygame.image.load(str(p)).convert_alpha()
            rocks.append(pygame.transform.scale(img, (56, 50)))
    assets["ruins"] = ruins
    assets["rocks"] = rocks

    # ── Ground tiles (first 6) ────────────────────────────
    tiles = []
    for i in range(1, 7):
        p = TILES_DIR / f"Map_tile_0{i}.png"
        if p.exists():
            tiles.append(pygame.image.load(str(p)).convert_alpha())
    assets["tiles"] = tiles

    # ── Fonts ─────────────────────────────────────────────
    korean = _find_korean_font()
    assets["font_sm"] = _make_font(korean, 15)
    assets["font_md"] = _make_font(korean, 19)
    assets["font_lg"] = _make_font(korean, 25)
    assets["font_xl"] = _make_font(korean, 32)

    return assets
