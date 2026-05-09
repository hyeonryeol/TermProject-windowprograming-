from pathlib import Path

# ── Screen ──────────────────────────────────────────────
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

GROUND_Y   = 555   # top surface of the ground strip
RAIL_Y     = 560   # centre of rail band
HORIZON_Y  = 280
TRAIN_SCREEN_X = 160   # left edge of locomotive on screen

# ── Paths ────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent
TRAIN_DIR  = ROOT / "train"
CRAFTPIX   = ROOT / "craftpix-net-280167-free-level-map-pixel-art-assets-pack"
TILES_DIR  = CRAFTPIX / "1 Tiles"
RUINS_DIR  = CRAFTPIX / "2 Objects" / "Ruins"
ROCKS_DIR  = CRAFTPIX / "2 Objects" / "Rocks"

# ── Colours ──────────────────────────────────────────────
SKY1   = (42, 33, 22)
SKY2   = (98, 76, 50)
GND1   = (62, 50, 32)
GND2   = (40, 32, 18)
RAIL_C = (88, 70, 46)
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
UI_BG  = (16,  12,   8)
UI_BD  = (75,  58,  38)
UI_TXT = (212, 192, 150)
UI_ACC = (195, 145,  52)
DANGER = (195,  52,  32)
GOOD   = (72,  172,  72)

# ── Resources ────────────────────────────────────────────
SCRAP   = "scrap"
IRON    = "iron"
COAL    = "coal"
FUEL    = "fuel"
COPPER  = "copper"
CIRCUIT = "circuit"

RNAMES = {
    SCRAP: "고철", IRON: "철판", COAL: "석탄",
    FUEL: "연료",  COPPER: "구리판", CIRCUIT: "회로",
}
RCOLORS = {
    SCRAP:   (155, 135, 100),
    IRON:    (180, 190, 200),
    COAL:    ( 50,  50,  60),
    FUEL:    (220, 162,  42),
    COPPER:  (210, 140,  58),
    CIRCUIT: ( 62, 200, 122),
}

# ── Node types ───────────────────────────────────────────
NODES = {
    "ruin": {
        "label": "폐허",
        "yields": {SCRAP: (4, 10), COAL: (0, 3)},
        "time": 3.5,
        "sprite_pool": "ruins",
    },
    "rock": {
        "label": "바위",
        "yields": {SCRAP: (2, 5)},
        "time": 2.0,
        "sprite_pool": "rocks",
    },
    "coal_seam": {
        "label": "석탄층",
        "yields": {COAL: (6, 14)},
        "time": 4.0,
        "sprite_pool": "rocks",
    },
}

# ── Machine definitions ──────────────────────────────────
M_FURNACE   = "furnace"
M_FUEL      = "fuel_gen"
M_STORAGE   = "storage"
M_BELT      = "belt"
M_ASSEMBLER = "assembler"

MDEF = {
    M_FURNACE: {
        "name": "용광로",     "size": (1, 2),
        "cost": {},
        "inp":  {SCRAP: 3},  "out": {IRON: 1}, "time": 5.0,
        "color": (175, 72, 32),
    },
    M_FUEL: {
        "name": "연료 변환기", "size": (1, 2),
        "cost": {IRON: 3},
        "inp":  {COAL: 2},   "out": {FUEL: 12}, "time": 3.5,
        "color": (205, 155, 38),
    },
    M_STORAGE: {
        "name": "저장고",     "size": (1, 2),
        "cost": {IRON: 2},
        "inp":  None,         "out": None,      "time": 0,
        "color": (72, 92, 112),
    },
    M_BELT: {
        "name": "컨베이어",   "size": (1, 1),
        "cost": {IRON: 1},
        "inp":  None,         "out": None,      "time": 0,
        "color": (95, 95, 72),
    },
    M_ASSEMBLER: {
        "name": "조립기",     "size": (2, 2),
        "cost": {IRON: 10, COPPER: 5},
        "inp":  {IRON: 2, COPPER: 1}, "out": {CIRCUIT: 1}, "time": 7.0,
        "color": (52, 112, 175),
    },
}

# ── Train physics ────────────────────────────────────────
BASE_SPEED  = 85.0    # world units / sec
MAX_SPEED   = 230.0
MIN_SPEED   = 22.0
FUEL_RATE   = 2.2     # % / sec at base speed
MAX_FUEL    = 100.0

# ── Workers ──────────────────────────────────────────────
WORKER_SPD  = 175.0   # world units / sec
MAX_CREW    = 5

# ── World generation ─────────────────────────────────────
SCAVENGE_DIST = 440
NODE_MIN_GAP  = 290
NODE_MAX_GAP  = 660
GEN_AHEAD     = 1600

# ── Factory interior grid ────────────────────────────────
CELL      = 48
FGRID_W   = 22
FGRID_H   = 5
FGRID_X   = 10
FGRID_Y   = 110
