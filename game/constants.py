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
SKY1   = (8,  12,  28)   # 미래 도시 밤하늘
SKY2   = (20, 35,  65)
GND1   = (30, 38,  48)   # 미래 황무지 (콘크리트+먼지)
GND2   = (18, 24,  32)
RAIL_C = (55, 75, 100)   # 자기부상 레일 느낌
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
    SCRAP:   "선체 패널",    # 비행체 갑판 뜯은 것
    IRON:    "정제 합금",
    COAL:    "연료 전지",    # 비행체에서 탈취한 연료 전지
    FUEL:    "플라즈마",     # 가공된 추진 연료
    COPPER:  "나노칩",
    CIRCUIT: "양자 코어",
}
RCOLORS = {
    SCRAP:   (140, 165, 190),  # 은청색 금속 패널
    IRON:    (190, 210, 230),  # 크롬 합금
    COAL:    ( 40, 210, 180),  # 발광하는 연료 전지 (청록)
    FUEL:    (120,  80, 230),  # 플라즈마 보라
    COPPER:  (240, 200,  60),  # 금빛 나노칩
    CIRCUIT: ( 80, 255, 160),  # 양자 코어 형광 녹색
}

# ── Node types ───────────────────────────────────────────
NODES = {
    "ruin": {
        "label": "방치된 비행체",       # 파일럿이 자리 비운 사이 약탈
        "yields": {SCRAP: (5, 12), COAL: (2, 6)},
        "time": 4.0,
        "sprite_pool": "ruins",
    },
    "rock": {
        "label": "추락한 드론",
        "yields": {SCRAP: (2, 6), COPPER: (0, 2)},
        "time": 2.5,
        "sprite_pool": "rocks",
    },
    "coal_seam": {
        "label": "비상 연료 저장소",
        "yields": {COAL: (8, 18)},
        "time": 4.5,
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
        "name": "나노 용융로",   "size": (1, 2),
        "cost": {},
        "inp":  {SCRAP: 3},     "out": {IRON: 1}, "time": 5.0,
        "color": (40, 140, 200),   # 산업용 청색
    },
    M_FUEL: {
        "name": "플라즈마 추출기", "size": (1, 2),
        "cost": {IRON: 3},
        "inp":  {COAL: 2},      "out": {FUEL: 12}, "time": 3.5,
        "color": (100, 50, 200),   # 보라
    },
    M_STORAGE: {
        "name": "화물 컨테이너", "size": (1, 2),
        "cost": {IRON: 2},
        "inp":  None,            "out": None,      "time": 0,
        "color": (50, 75, 100),
    },
    M_BELT: {
        "name": "자기 컨베이어", "size": (1, 1),
        "cost": {IRON: 1},
        "inp":  None,            "out": None,      "time": 0,
        "color": (30, 100, 120),
    },
    M_ASSEMBLER: {
        "name": "양자 조립기",   "size": (2, 2),
        "cost": {IRON: 10, COPPER: 5},
        "inp":  {IRON: 2, COPPER: 1}, "out": {CIRCUIT: 1}, "time": 7.0,
        "color": (60, 200, 140),   # 형광 청록
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
