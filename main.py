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
import os, shutil, random, math, traceback

from ursina import *

from game.constants import (
    SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT,
    RNAMES, RCOLORS, NODES, MDEF,
    M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER,
    MAX_FUEL, MAX_CREW,
)

# ── App ───────────────────────────────────────────────────────────────────────
app = Ursina(title='Iron Crawler - 아이언 크롤러')
window.size                = (1280, 720)
window.fps_counter.enabled = True
window.exit_button.enabled = False
# Panda3D 직접 배경색 설정 (window.color / Sky() 대신 확실한 방법)
base.setBackgroundColor(0.02, 0.03, 0.08, 1)

# ── 한국어 폰트 ───────────────────────────────────────────────────────────────
_LOCAL_FONT = 'korean_font.ttf'
if not os.path.exists(_LOCAL_FONT):
    for _wf in [r'C:\Windows\Fonts\malgun.ttf', r'C:\Windows\Fonts\malgunbd.ttf']:
        if os.path.exists(_wf):
            shutil.copy(_wf, _LOCAL_FONT)
            break
if os.path.exists(_LOCAL_FONT):
    Text.default_font = _LOCAL_FONT

# ── 3D 게임 상수 ──────────────────────────────────────────────────────────────
SPD_BASE   = 4.5
SPD_MAX    = 11.0
SPD_MIN    = 0.8
FUEL_DRAIN = 2.2
SCAV_RANGE = 26.0
NODE_GMIN  = 16
NODE_GMAX  = 48
GEN_AHEAD  = 110.0
W_SPEED    = 6.5
CAR_GAP    = 2.7

# ── 게임 상태 ─────────────────────────────────────────────────────────────────
class GS:
    fuel      = float(MAX_FUEL)
    speed     = SPD_BASE
    paused    = False
    factory   = False
    inventory = {SCRAP: 15, IRON: 0, COAL: 20, FUEL: 0, COPPER: 0, CIRCUIT: 0}
    machines  = [M_FURNACE]
    workers   = []
    nodes     = []
    m_timers  = {}

gs = GS()

# ── 월드 ─────────────────────────────────────────────────────────────────────
ground = Entity(
    model='plane',
    scale=500,
    color=color.rgb(18, 26, 40),
    texture='white_cube',
    texture_scale=(50, 50),
)

rail = Entity(
    model='cube',
    scale=(500, 0.06, 0.65),
    color=color.rgb(45, 72, 115),
)

# 레일 발광선
for _z in (-0.26, 0.26):
    Entity(model='cube', scale=(500, 0.04, 0.07),
           position=(0, 0.06, _z), color=color.rgb(80, 140, 240))

# ── 기차 ─────────────────────────────────────────────────────────────────────
_CAR_DEFS = [
    # (w, h, d,  r,  g,  b, x_offset)
    (2.3, 0.60, 1.25,  32, 48, 68, -3 * CAR_GAP),
    (2.3, 0.60, 1.25,  32, 48, 68, -2 * CAR_GAP),
    (1.9, 0.80, 1.25,  22, 42, 72, -1 * CAR_GAP),
    (2.7, 1.05, 1.40,  50, 90,150,  0.0),          # 기관차 (맨 앞)
]

train = Entity()   # 빈 부모 엔티티
_car_entities = []

for _w, _h, _d, _r, _g, _b, _ox in _CAR_DEFS:
    _body = Entity(
        model='cube',
        color=color.rgb(_r, _g, _b),
        scale=Vec3(_w, _h, _d),
        position=Vec3(_ox, _h / 2, 0),
        parent=train,
    )
    # 지붕
    Entity(
        model='cube',
        color=color.rgb(min(_r+22, 255), min(_g+22, 255), min(_b+22, 255)),
        scale=Vec3(_w * 0.85, 0.07, _d * 0.75),
        position=Vec3(0, 0.52, 0),
        parent=_body,
    )
    _car_entities.append(_body)

# 기관차 엔진 발광구
_loco_glow = Entity(
    model='sphere',
    color=color.rgb(100, 160, 255),
    scale=Vec3(0.5, 0.5, 0.5),
    position=Vec3(1.1, 0.65, 0),
    parent=_car_entities[-1],
)

# ── 연기 파티클 ───────────────────────────────────────────────────────────────
class Smoke(Entity):
    def __init__(self, pos):
        super().__init__(model='sphere', color=color.rgb(155, 160, 175),
                         scale=Vec3(0.28, 0.28, 0.28), position=pos)
        self.vel  = Vec3(random.uniform(-0.2, 0.1),
                         random.uniform(0.7, 1.3),
                         random.uniform(-0.15, 0.15))
        self.life = 1.4

    def update(self):
        self.life -= time.dt
        self.position += self.vel * time.dt
        self.vel      *= 0.97
        s = max(0.01, 0.28 + (1.4 - self.life) * 0.18)
        self.scale    = Vec3(s, s, s)
        self.alpha    = max(0.0, self.life / 1.4) * 0.5
        if self.life <= 0:
            destroy(self)

_smoke_t = 0.0

# ── 자원 노드 ─────────────────────────────────────────────────────────────────
_NODE_RGB = {
    'ruin':      (65, 115, 175),
    'rock':      (55,  70,  90),
    'coal_seam': (28, 175, 145),
}
_NODE_DIM = {
    'ruin':      (2.1, 0.75, 1.9),
    'rock':      (1.0, 0.55, 1.0),
    'coal_seam': (1.6, 0.45, 1.6),
}

class ResNode(Entity):
    def __init__(self, x, ntype):
        w, h, d   = _NODE_DIM[ntype]
        r, g, b   = _NODE_RGB[ntype]
        zoff      = random.uniform(-5.0, 5.0)

        super().__init__(
            model='cube',
            color=color.rgb(r, g, b),
            scale=Vec3(w, h, d),
            position=Vec3(x, h / 2, zoff),
            collider='box',
        )
        nd = NODES[ntype]
        self.node_type      = ntype
        self.gather_time    = nd['time']
        self.depleted       = False
        self.in_range       = False
        self.being_gathered = False

        self.resources = {}
        for res, (lo, hi) in nd['yields'].items():
            amt = random.randint(lo, hi)
            if amt > 0:
                self.resources[res] = amt

        # 발광 표시 (납작한 quad를 눕혀서 원형 대신 사용)
        self.glow = Entity(
            model='quad',
            color=color.rgb(80, 220, 100),
            scale=Vec3(w * 2.0, d * 2.0, 1),
            rotation_x=90,
            y=-h / 2 + 0.05,
            parent=self,
            alpha=0,
        )
        self.on_click = self._clicked

    def _clicked(self):
        if not self.in_range or self.being_gathered or self.depleted:
            return
        busy = sum(1 for w in gs.workers if not w.done)
        if busy < MAX_CREW:
            gs.workers.append(Worker(Vec3(train.x, 0.3, 0), self))

    def set_range(self, val):
        if val == self.in_range:
            return
        self.in_range  = val
        self.glow.alpha = 0.35 if val else 0.0

_next_node_x = 18.0

def _gen_nodes(up_to_x):
    global _next_node_x
    while _next_node_x < up_to_x + GEN_AHEAD:
        ntype = random.choices(['ruin','rock','coal_seam'], weights=[50,35,15])[0]
        gs.nodes.append(ResNode(_next_node_x, ntype))
        _next_node_x += random.uniform(NODE_GMIN, NODE_GMAX)

_gen_nodes(0)

# ── 워커 ─────────────────────────────────────────────────────────────────────
class Worker(Entity):
    def __init__(self, start, node):
        super().__init__(model='sphere', color=color.rgb(220, 158, 55),
                         scale=Vec3(0.32, 0.32, 0.32), position=start)
        self.node      = node
        self.state     = 'out'
        self.g_elapsed = 0.0
        self.done      = False
        self._loot     = {}
        node.being_gathered = True

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
                self._loot             = dict(self.node.resources)
                self.node.resources    = {}
                self.node.depleted     = True
                self.node.glow.alpha   = 0.0
                self.node.color        = color.rgb(32, 32, 42)
                self.state             = 'return'
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

# ── 기계 처리 ─────────────────────────────────────────────────────────────────
def _process_machines(dt):
    for mtype in gs.machines:
        d = MDEF[mtype]
        if d['inp'] is None:
            continue
        gs.m_timers.setdefault(mtype, 0.0)
        if gs.m_timers[mtype] <= 0:
            if all(gs.inventory.get(r, 0) >= a for r, a in d['inp'].items()):
                for r, a in d['inp'].items():
                    gs.inventory[r] -= a
                gs.m_timers[mtype] = d['time']
        else:
            gs.m_timers[mtype] = max(0.0, gs.m_timers[mtype] - dt)
            if gs.m_timers[mtype] == 0.0:
                for r, a in d['out'].items():
                    gs.inventory[r] = gs.inventory.get(r, 0) + a

# ── HUD ───────────────────────────────────────────────────────────────────────
_RES_ORDER = [SCRAP, IRON, COAL, FUEL, COPPER, CIRCUIT]
_res_labels = {}

# 상단 바 배경
Entity(parent=camera.ui, model='quad', color=color.rgba(8, 6, 4, 200),
       scale=(2.05, 0.07), position=(0, 0.483))

_xs = [-0.87, -0.57, -0.27, 0.03, 0.33, 0.63]
for _i, _res in enumerate(_RES_ORDER):
    _rc = RCOLORS[_res]
    Entity(parent=camera.ui, model='quad',
           color=color.rgb(_rc[0], _rc[1], _rc[2]),
           scale=(0.025, 0.025), position=(_xs[_i] - 0.022, 0.482))
    _lbl = Text(parent=camera.ui, text=f'{RNAMES[_res]}: 0',
                position=(_xs[_i] + 0.002, 0.465),
                scale=0.68, color=color.rgb(210, 190, 148))
    _res_labels[_res] = _lbl

# 연료 게이지
Entity(parent=camera.ui, model='quad', color=color.rgba(12, 9, 6, 200),
       scale=(0.26, 0.042), position=(0.73, -0.452))
_fuel_fill = Entity(parent=camera.ui, model='quad', color=color.rgb(70, 170, 70),
                    scale=(0.245, 0.028), position=(0.73, -0.452))
_fuel_txt  = Text(parent=camera.ui, text='연료 100%',
                  position=(0.608, -0.462), scale=0.68,
                  color=color.rgb(210, 190, 148))
_spd_txt   = Text(parent=camera.ui, text='속도: 4.5',
                  position=(-0.98, -0.455), scale=0.68,
                  color=color.rgb(210, 190, 148))
_crew_txt  = Text(parent=camera.ui, text='크루: 0/5',
                  position=(-0.98, -0.478), scale=0.68,
                  color=color.rgb(210, 190, 148))
Text(parent=camera.ui,
     text='[클릭] 약탈  [TAB] 공장  [↑↓] 속도  [SPACE] 정지  [ESC] 종료',
     position=(0, -0.487), scale=0.52, origin=(0, 0),
     color=color.rgb(90, 80, 58))

def _update_hud():
    for res, lbl in _res_labels.items():
        lbl.text = f'{RNAMES[res]}: {gs.inventory.get(res, 0)}'
    pct = gs.fuel / MAX_FUEL
    fw  = max(0.002, 0.245 * pct)
    _fuel_fill.scale_x = fw
    _fuel_fill.x       = 0.73 - 0.1225 + fw / 2
    _fuel_fill.color   = color.rgb(70, 170, 70) if pct > 0.25 else color.rgb(195, 50, 30)
    _fuel_txt.text     = f'연료 {int(pct * 100)}%'
    _spd_txt.text      = f'속도: {gs.speed:.1f}  [↑↓]'
    busy = sum(1 for w in gs.workers if not w.done)
    _crew_txt.text     = f'크루: {busy}/{MAX_CREW}'

# ── 공장 패널 ─────────────────────────────────────────────────────────────────
_fp = Entity(parent=camera.ui, enabled=False)
Entity(parent=_fp, model='quad', color=color.rgba(8, 6, 4, 230),
       scale=(1.7, 0.82), position=(0, -0.04))
Text(parent=_fp, text='공장 관리  |  [TAB] 닫기',
     position=(-0.83, 0.345), scale=0.82, color=color.rgb(195, 145, 52))
Text(parent=_fp, text='설치된 기계', position=(-0.82, 0.29),
     scale=0.72, color=color.rgb(160, 150, 110))
Text(parent=_fp, text='구매 가능',   position=(0.05,  0.29),
     scale=0.72, color=color.rgb(160, 150, 110))

_m_rows = [Text(parent=_fp, text='', position=(-0.82, 0.23 - i * 0.07),
                scale=0.65, color=color.rgb(200, 190, 155)) for i in range(8)]

def _refresh_machine_rows():
    for i, lbl in enumerate(_m_rows):
        if i < len(gs.machines):
            mtype = gs.machines[i]
            d     = MDEF[mtype]
            rem   = gs.m_timers.get(mtype, 0.0)
            if d['time'] > 0 and rem > 0:
                filled = int((1 - rem / d['time']) * 10)
                lbl.text = f'• {d["name"]}  [{"█"*filled}{"░"*(10-filled)}]'
            else:
                lbl.text = f'• {d["name"]}  [대기중]'
        else:
            lbl.text = ''

_BUY_LIST = [M_FURNACE, M_FUEL, M_STORAGE, M_BELT, M_ASSEMBLER]
_buy_btns = []

def _build_buy_panel():
    for btn in _buy_btns:
        destroy(btn)
    _buy_btns.clear()
    for i, mtype in enumerate(_BUY_LIST):
        d    = MDEF[mtype]
        cost = d['cost']
        can  = all(gs.inventory.get(r, 0) >= a for r, a in cost.items())
        cnt  = gs.machines.count(mtype)
        cs   = '무료' if not cost else ' '.join(f'{RNAMES.get(r,r)}x{a}' for r, a in cost.items())
        label = f'{d["name"]} [{cs}]' + (f' x{cnt}' if cnt else '')
        btn = Button(parent=_fp, text=label,
                     scale=(0.85, 0.055), position=(0.47, 0.23 - i * 0.075),
                     color=color.rgb(30, 50, 70) if can else color.rgb(22, 18, 12),
                     highlight_color=color.rgb(50, 80, 110),
                     pressed_color=color.rgb(20, 40, 60))
        btn.text_entity.color = color.rgb(200, 190, 155) if can else color.rgb(80, 75, 60)
        def _make(mt=mtype, d=d):
            def _h():
                if all(gs.inventory.get(r, 0) >= a for r, a in d['cost'].items()):
                    for r, a in d['cost'].items():
                        gs.inventory[r] -= a
                    gs.machines.append(mt)
                    _build_buy_panel()
            return _h
        btn.on_click = _make()
        _buy_btns.append(btn)

_build_buy_panel()

_pause_bg  = Entity(parent=camera.ui, model='quad', color=color.rgba(0, 0, 0, 120),
                    scale=(2.1, 1.1), enabled=False)
_pause_lbl = Text(parent=camera.ui, text='일시 정지  [SPACE]',
                  origin=(0, 0), scale=1.4,
                  color=color.rgb(195, 145, 52), enabled=False)

# ── 카메라 ────────────────────────────────────────────────────────────────────
camera.position   = Vec3(0, 20, 0)
camera.rotation_x = 85    # 거의 수직 탑다운, 약간의 원근감
camera.fov        = 90

# ── 메인 업데이트 ─────────────────────────────────────────────────────────────
def update():
    global _smoke_t
    try:
        dt = min(time.dt, 0.05)
        if gs.paused:
            return

        # 기차 이동
        if gs.fuel > 0:
            gs.fuel  = max(0.0, gs.fuel - dt * FUEL_DRAIN * (gs.speed / SPD_BASE))
            train.x += gs.speed * dt
        else:
            gs.speed = max(0.0, gs.speed - 2.0 * dt)
            train.x += gs.speed * dt
        if gs.fuel > 5 and gs.speed < SPD_BASE:
            gs.speed = min(SPD_BASE, gs.speed + 1.5 * dt)

        # 월드 지면 따라가기
        ground.x = train.x
        rail.x   = train.x

        # 카메라 기차 팔로우
        camera.x += (train.x - camera.x) * min(dt * 4, 1.0)

        # 기관차 발광 애니메이션
        g = 0.45 + math.sin(time.time() * 3) * 0.08
        _loco_glow.scale = Vec3(g, g, g)

        # 노드 생성 및 업데이트
        _gen_nodes(train.x)
        stale = []
        for node in gs.nodes:
            if node.x < train.x - 55:
                stale.append(node)
                continue
            node.set_range(abs(node.x - train.x) < SCAV_RANGE)
        for node in stale:
            gs.nodes.remove(node)
            destroy(node)

        # 워커
        gs.workers = [w for w in gs.workers if not w.done]

        # 기계
        _process_machines(dt)

        # 연기
        _smoke_t += dt
        if _smoke_t > 0.25:
            _smoke_t = 0.0
            Smoke(Vec3(train.x + 1.4, 1.6, 0))

        # HUD
        _update_hud()
        if gs.factory:
            _refresh_machine_rows()

    except Exception as e:
        print(f'[update 오류] {e}')
        traceback.print_exc()

# ── 입력 ─────────────────────────────────────────────────────────────────────
def input(key):
    if key == 'escape':
        application.quit()
    elif key == 'tab':
        gs.factory  = not gs.factory
        _fp.enabled = gs.factory
        if gs.factory:
            _build_buy_panel()
    elif key == 'space':
        gs.paused          = not gs.paused
        _pause_bg.enabled  = gs.paused
        _pause_lbl.enabled = gs.paused
    elif key in ('up arrow', 'w'):
        gs.speed = min(SPD_MAX, gs.speed + 1.0)
    elif key in ('down arrow', 's'):
        gs.speed = max(SPD_MIN, gs.speed - 1.0)

app.run()
