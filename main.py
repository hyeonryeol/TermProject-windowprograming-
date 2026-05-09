"""
Iron Crawler 3D  /  아이언 크롤러
탑다운 3D 미래 공장 기차 게임

조작:
  마우스 클릭   - 근처 비행체/드론 약탈
  TAB          - 공장 패널 열기/닫기
  ↑ / ↓       - 기차 속도 조절
  SPACE        - 일시정지
  ESC          - 종료
"""
import random
import math

from ursina import *

from game.constants import (
    SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT,
    RNAMES, RCOLORS, NODES, MDEF,
    M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER,
    MAX_FUEL, MAX_CREW,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = Ursina(title='Iron Crawler - 아이언 크롤러')
window.size          = (1280, 720)
window.fps_counter.enabled  = False
window.exit_button.enabled  = False

# ── 3D 게임 상수 ──────────────────────────────────────────────────────────────
SPD_BASE   = 4.5    # Ursina units/sec
SPD_MAX    = 11.0
SPD_MIN    = 0.8
FUEL_DRAIN = 2.2    # % / sec (base speed)
SCAV_RANGE = 26.0   # 채취 가능 거리 (Ursina units)
NODE_GMIN  = 16
NODE_GMAX  = 48
GEN_AHEAD  = 110.0
W_SPEED    = 6.5    # 워커 이동 속도

CAR_GAP    = 2.7    # 차량 간 간격

# ── 게임 상태 ─────────────────────────────────────────────────────────────────
class GS:
    fuel      = float(MAX_FUEL)
    speed     = SPD_BASE
    paused    = False
    factory   = False

    inventory = {SCRAP: 15, IRON: 0, COAL: 20, FUEL: 0, COPPER: 0, CIRCUIT: 0}

    machines  = [M_FURNACE]   # 시작 기계: 나노 용융로
    workers   = []
    nodes     = []
    m_timers  = {}            # {machine_type: remaining_time}

gs = GS()


# ═══════════════════════════════════════════════════════════════════════════════
# 월드
# ═══════════════════════════════════════════════════════════════════════════════

# 지면 (미래 황무지)
ground = Entity(model='plane', scale=(2000, 1, 80), position=(0, 0, 3),
                color=color.rgb(18, 26, 40))

# 지면 격자 (약하게)
grid = Entity(model='plane', scale=(2000, 1, 80), position=(0, 0.01, 3),
              texture='white_cube', texture_scale=(200, 8),
              color=color.rgba(40, 60, 95, 60))

# 레일 (자기부상 느낌)
rail = Entity(model='cube', scale=(2000, 0.06, 0.65), position=(0, 0.03, 0),
              color=color.rgb(45, 72, 115))

# 레일 발광선
for z_off in (-0.25, 0.25):
    Entity(model='cube', scale=(2000, 0.04, 0.08), position=(0, 0.07, z_off),
           color=color.rgb(80, 140, 240))


# ═══════════════════════════════════════════════════════════════════════════════
# 기차
# ═══════════════════════════════════════════════════════════════════════════════

class TrainBody(Entity):
    # (type, scale, color, x_offset_from_loco)
    CAR_DEFS = [
        ('cargo', Vec3(2.3, 0.6, 1.25), color.rgb(32, 48, 68),  -3 * CAR_GAP),
        ('cargo', Vec3(2.3, 0.6, 1.25), color.rgb(32, 48, 68),  -2 * CAR_GAP),
        ('water', Vec3(1.9, 0.8, 1.25), color.rgb(22, 42, 72),  -1 * CAR_GAP),
        ('loco',  Vec3(2.7, 1.05, 1.4), color.rgb(50, 90, 150),  0),
    ]

    def __init__(self):
        super().__init__()
        self.car_entities = []
        for ctype, sc, col, offset in self.CAR_DEFS:
            body = Entity(model='cube', color=col, scale=sc,
                          position=(offset, sc.y / 2, 0), parent=self)
            # 지붕 패널
            Entity(model='cube',
                   color=color.rgb(min(col.r * 255 + 25, 255),
                                   min(col.g * 255 + 25, 255),
                                   min(col.b * 255 + 25, 255)),
                   scale=(sc.x * 0.85, 0.07, sc.z * 0.75),
                   position=(0, 0.52, 0), parent=body)
            self.car_entities.append((ctype, body, sc))

        # 기관실 엔진 발광
        loco_body = self.car_entities[-1][1]
        self.glow = Entity(model='sphere', color=color.rgb(100, 160, 255),
                           scale=0.45, position=(1.1, 0.65, 0),
                           parent=loco_body, alpha=0.85)

    def update(self):
        t = time.time()
        self.glow.scale = 0.45 + math.sin(t * 3.2) * 0.08
        self.glow.alpha = 0.6  + math.sin(t * 3.2) * 0.2


train = TrainBody()


# ═══════════════════════════════════════════════════════════════════════════════
# 연기 파티클
# ═══════════════════════════════════════════════════════════════════════════════

class Smoke(Entity):
    def __init__(self, pos):
        super().__init__(model='sphere',
                         color=color.rgba(160, 165, 185, 140),
                         scale=0.28, position=pos)
        self.vel  = Vec3(random.uniform(-0.2, 0.1),
                         random.uniform(0.7, 1.3),
                         random.uniform(-0.15, 0.15))
        self.life = 1.4

    def update(self):
        self.life -= time.dt
        self.position += self.vel * time.dt
        self.vel      *= 0.97
        self.scale    += 0.015
        self.alpha     = max(0, self.life / 1.4) * 0.55
        if self.life <= 0:
            destroy(self)

_smoke_t = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# 자원 노드
# ═══════════════════════════════════════════════════════════════════════════════

_NODE_COL = {
    'ruin':      color.rgb(65, 115, 175),
    'rock':      color.rgb(55,  70,  90),
    'coal_seam': color.rgb(28, 175, 145),
}
_NODE_SC = {
    'ruin':      Vec3(2.1, 0.75, 1.9),
    'rock':      Vec3(1.0, 0.55, 1.0),
    'coal_seam': Vec3(1.6, 0.45, 1.6),
}


class ResNode(Entity):
    def __init__(self, x, ntype):
        sc   = _NODE_SC[ntype]
        col  = _NODE_COL[ntype]
        zoff = random.uniform(-5.5, 5.5)
        super().__init__(model='cube', color=col, scale=sc,
                         position=(x, sc.y / 2, zoff),
                         collider='box')
        nd = NODES[ntype]
        self.node_type     = ntype
        self.label         = nd['label']
        self.gather_time   = nd['time']
        self.depleted      = False
        self.in_range      = False
        self.being_gathered = False

        # 수익률 결정
        self.resources = {}
        for res, (lo, hi) in nd['yields'].items():
            amt = random.randint(lo, hi)
            if amt > 0:
                self.resources[res] = amt

        # 지면 발광 링
        self.glow = Entity(model='circle',
                           color=color.rgba(80, 220, 100, 0),
                           scale=(sc.x * 1.7, 1, sc.z * 1.7),
                           rotation_x=90, y=-sc.y / 2 + 0.04,
                           parent=self)

        # 라벨 (항상 카메라를 향하게)
        self.tag = Text(text=nd['label'], scale=1.1,
                        position=(x, sc.y + 0.6, zoff),
                        origin=(0, 0), billboard=True,
                        color=color.rgba(200, 220, 255, 0))

        self.on_click = self._clicked

    def _clicked(self):
        if not self.in_range or self.being_gathered or self.depleted:
            return
        busy = sum(1 for w in gs.workers if not w.done)
        if busy < MAX_CREW:
            w = Worker(Vec3(train.x, 0.3, 0), self)
            gs.workers.append(w)

    def set_range(self, val):
        if val == self.in_range:
            return
        self.in_range     = val
        self.glow.alpha   = 0.38 if val else 0
        self.tag.alpha    = 0.9  if val else 0


_next_node_x = 18.0


def _gen_nodes(up_to_x):
    global _next_node_x
    while _next_node_x < up_to_x + GEN_AHEAD:
        ntype = random.choices(['ruin', 'rock', 'coal_seam'],
                               weights=[50, 35, 15])[0]
        gs.nodes.append(ResNode(_next_node_x, ntype))
        _next_node_x += random.uniform(NODE_GMIN, NODE_GMAX)


_gen_nodes(0)


# ═══════════════════════════════════════════════════════════════════════════════
# 워커 (크루)
# ═══════════════════════════════════════════════════════════════════════════════

class Worker(Entity):
    def __init__(self, start, node):
        super().__init__(model='sphere', color=color.rgb(220, 158, 55),
                         scale=0.32, position=start)
        self.node      = node
        self.state     = 'out'
        self.g_elapsed = 0.0
        self.done      = False
        self._loot     = {}
        node.being_gathered = True

        # 수집물 표시
        self.carry = Entity(model='cube', color=color.yellow,
                            scale=0.28, y=0.38,
                            parent=self, enabled=False)

    def update(self):
        if self.done:
            return
        spd = W_SPEED * time.dt

        if self.state == 'out':
            diff = self.node.position - self.position
            if diff.length() < 0.4:
                self.position = Vec3(*self.node.position)
                self.state = 'gather'
            else:
                self.position += diff.normalized() * spd

        elif self.state == 'gather':
            self.g_elapsed += time.dt
            if self.g_elapsed >= self.node.gather_time:
                self._loot = dict(self.node.resources)
                self.node.resources       = {}
                self.node.depleted        = True
                self.node.glow.alpha      = 0
                self.node.tag.alpha       = 0
                self.node.color           = color.rgb(32, 32, 42)
                self.carry.enabled        = True
                self.state                = 'return'

        elif self.state == 'return':
            target = Vec3(train.x, 0.3, 0)
            diff   = target - self.position
            if diff.length() < 0.5:
                for r, a in self._loot.items():
                    gs.inventory[r] = gs.inventory.get(r, 0) + a
                self.node.being_gathered = False
                self.done = True
                destroy(self)
            else:
                self.position += diff.normalized() * spd


# ═══════════════════════════════════════════════════════════════════════════════
# 기계 처리
# ═══════════════════════════════════════════════════════════════════════════════

def _process_machines(dt):
    for mtype in gs.machines:
        d   = MDEF[mtype]
        inp = d['inp']
        out = d['out']
        t   = d['time']
        if inp is None:
            continue

        gs.m_timers.setdefault(mtype, 0.0)

        if gs.m_timers[mtype] <= 0:
            if all(gs.inventory.get(r, 0) >= a for r, a in inp.items()):
                for r, a in inp.items():
                    gs.inventory[r] -= a
                gs.m_timers[mtype] = t
        else:
            gs.m_timers[mtype] -= dt
            if gs.m_timers[mtype] <= 0:
                for r, a in out.items():
                    gs.inventory[r] = gs.inventory.get(r, 0) + a
                gs.m_timers[mtype] = 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# HUD
# ═══════════════════════════════════════════════════════════════════════════════

# 상단 자원 바
Entity(parent=camera.ui, model='quad', color=color.rgba(8, 6, 4, 210),
       scale=(2.05, 0.068), position=(0, 0.483))

_RES_ORDER = [SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT]
_res_labels = {}
_xs = [-0.87, -0.57, -0.27, 0.03, 0.33, 0.63]

for i, res in enumerate(_RES_ORDER):
    rc = RCOLORS[res]
    Entity(parent=camera.ui, model='quad',
           color=color.rgb(*rc), scale=0.023,
           position=(_xs[i] - 0.022, 0.482))
    t = Text(parent=camera.ui,
             text=f'{RNAMES[res]}: 0',
             position=(_xs[i] + 0.002, 0.465),
             scale=0.68, color=color.rgb(210, 190, 148))
    _res_labels[res] = t

# 연료 게이지
Entity(parent=camera.ui, model='quad', color=color.rgba(12, 9, 6, 200),
       scale=(0.26, 0.042), position=(0.73, -0.452))
_fuel_fill = Entity(parent=camera.ui, model='quad', color=color.rgb(70, 170, 70),
                    scale=(0.245, 0.028), position=(0.73, -0.452))
_fuel_txt  = Text(parent=camera.ui, text='연료 100%',
                  position=(0.605, -0.462), scale=0.68,
                  color=color.rgb(210, 190, 148))

# 속도 / 크루
_spd_txt  = Text(parent=camera.ui, text='속도: 4.5', position=(-0.98, -0.455),
                 scale=0.68, color=color.rgb(210, 190, 148))
_crew_txt = Text(parent=camera.ui, text='크루: 0/5', position=(-0.98, -0.478),
                 scale=0.68, color=color.rgb(210, 190, 148))

# 힌트
Text(parent=camera.ui,
     text='[클릭] 약탈  [TAB] 공장  [↑↓] 속도  [SPACE] 정지  [ESC] 종료',
     position=(0, -0.487), scale=0.52, origin=(0, 0),
     color=color.rgb(90, 80, 58))


def _update_hud():
    for res, lbl in _res_labels.items():
        lbl.text = f'{RNAMES[res]}: {gs.inventory.get(res, 0)}'

    pct = gs.fuel / MAX_FUEL
    fw  = max(0.001, 0.245 * pct)
    _fuel_fill.scale_x = fw
    _fuel_fill.x       = 0.73 - 0.1225 + fw / 2
    _fuel_fill.color   = color.rgb(70, 170, 70) if pct > 0.25 else color.rgb(195, 50, 30)
    _fuel_txt.text     = f'연료 {int(pct * 100)}%'
    _spd_txt.text      = f'속도: {gs.speed:.1f}  [↑↓]'
    busy = sum(1 for w in gs.workers if not w.done)
    _crew_txt.text     = f'크루: {busy}/{MAX_CREW}'


# ═══════════════════════════════════════════════════════════════════════════════
# 공장 패널 (TAB)
# ═══════════════════════════════════════════════════════════════════════════════

_fp_root = Entity(parent=camera.ui, enabled=False)

Entity(parent=_fp_root, model='quad', color=color.rgba(8, 6, 4, 230),
       scale=(1.7, 0.82), position=(0, -0.04))

Text(parent=_fp_root, text='공장 관리  |  [TAB] 닫기',
     position=(-0.83, 0.345), scale=0.82, color=color.rgb(195, 145, 52))

# 기계 목록 (왼쪽)
Text(parent=_fp_root, text='설치된 기계', position=(-0.82, 0.29),
     scale=0.72, color=color.rgb(160, 150, 110))

_m_status_labels = {}

def _rebuild_machine_list():
    for lbl in _m_status_labels.values():
        destroy(lbl)
    _m_status_labels.clear()

    for i, mtype in enumerate(gs.machines):
        d    = MDEF[mtype]
        rem  = gs.m_timers.get(mtype, 0.0)
        total = d['time']
        pct  = (1 - rem / total) * 100 if total > 0 and rem > 0 else 0
        bar  = '█' * int(pct / 10) + '░' * (10 - int(pct / 10))
        status = f'[{bar}] {int(pct)}%' if rem > 0 else '대기 중'
        lbl = Text(parent=_fp_root,
                   text=f'• {d["name"]}  {status}',
                   position=(-0.82, 0.23 - i * 0.07),
                   scale=0.65, color=color.rgb(200, 190, 155))
        _m_status_labels[mtype + str(i)] = lbl

# 구매 가능한 기계 (오른쪽)
Text(parent=_fp_root, text='구매 가능', position=(0.05, 0.29),
     scale=0.72, color=color.rgb(160, 150, 110))

_BUY_MACHINES = [M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER]
_buy_btns = []

def _build_buy_panel():
    for btn in _buy_btns:
        destroy(btn)
    _buy_btns.clear()

    for i, mtype in enumerate(_BUY_MACHINES):
        d    = MDEF[mtype]
        cost = d['cost']
        can  = all(gs.inventory.get(r, 0) >= a for r, a in cost.items())
        already = gs.machines.count(mtype)

        cost_str = '무료' if not cost else '  '.join(
            f'{RNAMES.get(r, r)}×{a}' for r, a in cost.items()
        )
        label = f'{d["name"]}  [{cost_str}]'
        if already:
            label += f'  (×{already})'

        btn = Button(
            parent=_fp_root,
            text=label,
            scale=(0.85, 0.055),
            position=(0.47, 0.23 - i * 0.07),
            color=color.rgb(30, 50, 70) if can else color.rgb(25, 20, 15),
            text_color=color.rgb(200, 190, 155) if can else color.rgb(90, 85, 70),
            highlight_color=color.rgb(50, 80, 110),
            pressed_color=color.rgb(20, 40, 60),
        )

        def _make_handler(mt=mtype, d=d):
            def handler():
                c = d['cost']
                if all(gs.inventory.get(r, 0) >= a for r, a in c.items()):
                    for r, a in c.items():
                        gs.inventory[r] -= a
                    gs.machines.append(mt)
                    _build_buy_panel()
            return handler

        btn.on_click = _make_handler()
        _buy_btns.append(btn)

_build_buy_panel()

# 일시정지 오버레이
_pause_overlay = Entity(parent=camera.ui, model='quad',
                        color=color.rgba(0, 0, 0, 120),
                        scale=(2, 1.1), enabled=False)
_pause_txt = Text(parent=camera.ui, text='일시 정지  [SPACE]',
                  origin=(0, 0), scale=1.4,
                  color=color.rgb(195, 145, 52), enabled=False)


# ═══════════════════════════════════════════════════════════════════════════════
# 카메라
# ═══════════════════════════════════════════════════════════════════════════════

camera.rotation_x = 63
camera.z          = -14
camera.y          = 20


# ═══════════════════════════════════════════════════════════════════════════════
# 메인 업데이트
# ═══════════════════════════════════════════════════════════════════════════════

def update():
    global _smoke_t

    dt = time.dt
    if gs.paused:
        return

    # ── 기차 이동 ───────────────────────────────────────────────────────────
    if gs.fuel > 0:
        gs.fuel = max(0.0, gs.fuel - dt * FUEL_DRAIN * (gs.speed / SPD_BASE))
        train.x += gs.speed * dt
    else:
        gs.speed = max(0.0, gs.speed - 2.0 * dt)
        train.x += gs.speed * dt

    if gs.fuel > 5 and gs.speed < SPD_BASE:
        gs.speed = min(SPD_BASE, gs.speed + 1.5 * dt)

    # 지면/레일 위치를 기차에 따라 이동
    ground.x = train.x
    grid.x   = train.x
    rail.x   = train.x

    # ── 카메라 팔로우 ────────────────────────────────────────────────────────
    camera.x = lerp(camera.x, train.x - 4, dt * 4)

    # ── 노드 생성 및 업데이트 ────────────────────────────────────────────────
    _gen_nodes(train.x)

    stale = []
    for node in gs.nodes:
        if node.x < train.x - 55:
            stale.append(node)
            continue
        dist = abs(node.x - train.x)
        node.set_range(dist < SCAV_RANGE)

    for node in stale:
        gs.nodes.remove(node)
        destroy(node.tag)
        destroy(node)

    # ── 워커 ────────────────────────────────────────────────────────────────
    gs.workers = [w for w in gs.workers if not w.done]

    # ── 기계 처리 ────────────────────────────────────────────────────────────
    _process_machines(dt)

    # ── 연기 파티클 ──────────────────────────────────────────────────────────
    global _smoke_t
    _smoke_t += dt
    if _smoke_t > 0.22:
        _smoke_t = 0
        Smoke(Vec3(train.x + 1.4, 1.6, 0))

    # ── HUD 업데이트 ─────────────────────────────────────────────────────────
    _update_hud()
    if gs.factory:
        _rebuild_machine_list()


# ═══════════════════════════════════════════════════════════════════════════════
# 입력
# ═══════════════════════════════════════════════════════════════════════════════

def input(key):
    if key == 'escape':
        application.quit()

    elif key == 'tab':
        gs.factory = not gs.factory
        _fp_root.enabled = gs.factory
        if gs.factory:
            _build_buy_panel()

    elif key == 'space':
        gs.paused = not gs.paused
        _pause_overlay.enabled = gs.paused
        _pause_txt.enabled     = gs.paused

    elif key in ('up arrow', 'w'):
        gs.speed = min(SPD_MAX, gs.speed + 1.0)

    elif key in ('down arrow', 's'):
        gs.speed = max(SPD_MIN, gs.speed - 1.0)


# ── 시작 ──────────────────────────────────────────────────────────────────────
app.run()
