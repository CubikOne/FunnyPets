#!/usr/bin/env python3
"""FunnyPets — пиксельный питомец для Windows 10/11.

Порт macOS-версии: кот/хомяк, окрасы, глаза за курсором, месит лапками
при печати, перегрев, мурчание, сон, охота за курсором, рулон бумаги
при скролле, прогулки, помодоро, разминка, интеграция с Claude Code.

Запуск: python funnypets_win.py  (нужен только стандартный Python 3.9+)
Сборка exe: pyinstaller --onefile --noconsole --name FunnyPets
            --add-data "linux/sprites.json;." windows/funnypets_win.py
"""
import ctypes
import ctypes.wintypes as wt
import json
import math
import os
import random
import sys
import time
import tkinter as tk

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
try:
    import winsound
except ImportError:
    winsound = None

TRANSPARENT = '#010203'   # colorkey для прозрачности окна


def find_sprites():
    cands = []
    if hasattr(sys, '_MEIPASS'):
        cands.append(os.path.join(sys._MEIPASS, 'sprites.json'))
    here = os.path.dirname(os.path.abspath(__file__))
    cands += [os.path.join(here, 'sprites.json'),
              os.path.join(here, '..', 'linux', 'sprites.json')]
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit('sprites.json не найден — положи его рядом со скриптом')


SPRITES = json.load(open(find_sprites(), encoding='utf-8'))
GRID_W, GRID_H = SPRITES['grid']
EYES = SPRITES['eyes']

CONF_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'FunnyPets')
CONF_PATH = os.path.join(CONF_DIR, 'config.json')
AGENT_FILE = os.path.expanduser('~/.comnyan/agent')

SOLIDS = [
    ('Рыжий', (240, 148, 54), (198, 104, 26)),
    ('Серый', (154, 158, 170), (110, 114, 126)),
    ('Чёрный', (66, 60, 68), (44, 40, 48)),
    ('Белый', (246, 242, 234), (216, 208, 198)),
    ('Кремовый', (238, 208, 156), (206, 162, 106)),
]
PATTERN_TITLES = {'SIAMESE': 'Сиамский', 'MACKEREL': 'Полосатый', 'CALICO': 'Калико', 'TUXEDO': 'Смокинг'}
PATTERN_PAL = {
    'c': (242, 232, 210), 'd': (88, 60, 48),
    'e': (168, 172, 182), 'f': (106, 110, 122),
    'g': (246, 242, 234), 'h': (238, 146, 52), 'i': (70, 64, 72),
    'j': (52, 48, 56),
}
OUTLINE = (43, 29, 24)
WHITE = (252, 244, 232)
PINK = (247, 143, 158)
BLUSH = (250, 178, 162)
HOT = (236, 96, 72)
HOT_S = (198, 58, 42)
HEART = (244, 110, 130)
PAPER = (250, 248, 240)
PAPER_L = (200, 196, 186)

ROLL_SPRITE = ['.ooo.', 'oWWWo', 'oWhWo', 'oWWWo', 'oWWWo', '.ooo.']
STRIP_ROW, STRIP_LINE, STRIP_TEAR = 'oWWWo', 'oWlWo', '.W.W.'
PAW_SPRITE = ['.ooo.', 'oBBBo', '.ooo.']


def hx(c):
    return f'#{c[0]:02x}{c[1]:02x}{c[2]:02x}'


# ---------- win32 helpers ----------
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [('cbSize', wt.UINT), ('dwTime', wt.DWORD)]


def idle_ms():
    li = LASTINPUTINFO()
    li.cbSize = ctypes.sizeof(li)
    if user32.GetLastInputInfo(ctypes.byref(li)):
        return kernel32.GetTickCount() - li.dwTime
    return 0


def cursor_pos():
    pt = wt.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def keys_down():
    """Множество нажатых сейчас клавиш клавиатуры (мышь 0x01-0x06 не считаем)."""
    down = set()
    for vk in range(0x08, 0xFF):
        if user32.GetAsyncKeyState(vk) & 0x8000:
            down.add(vk)
    return down


def load_conf():
    try:
        return json.load(open(CONF_PATH, encoding='utf-8'))
    except Exception:
        return {}


class Pet:
    def __init__(self):
        self.conf = load_conf()
        self.S = self.conf.get('scale', 6)
        self.margin_x = 20
        self.margin_bottom = 20
        self.top_space = 90

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', TRANSPARENT)
        self.root.title('FunnyPets')
        self.canvas = tk.Canvas(self.root, highlightthickness=0, bg=TRANSPARENT)
        self.canvas.pack(fill='both', expand=True)
        self.resize_to_grid()

        x = self.conf.get('x', user32.GetSystemMetrics(0) - self.win_w() - 60)
        y = self.conf.get('y', user32.GetSystemMetrics(1) - self.win_h() - 60)
        self.root.geometry(f'+{x}+{y}')

        self.canvas.bind('<Button-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Button-3>', self.on_menu)
        self.canvas.bind('<Motion>', self.on_motion)

        # state
        self.state = 'idle'
        self.gaze = (0, 0)
        self.blink_until = 0
        self.next_blink = time.time() + 3
        self.tail_up_until = 0
        self.next_flick = time.time() + 4
        self.knead_flip = False
        self.knead_at = 0
        self.jelly = 0.0
        self.jphase = 0.0
        self.stretch = 0.0
        self.hearts = []
        self.last_heart = 0
        self.zzz = 0.0
        self.think_phase = 0.0
        self.cheek = 0.0
        self.paper = 0.0
        self.paper_phase = 0.0
        self.hop_started = time.time()
        self.dragging = False
        self.drag_off = (0, 0)
        self.pressed_at = 0
        self.moved = False
        self.pet_until = 0
        self.pet_dir = 0
        self.pet_x = 0
        self.pet_turns = []
        self.message = ''
        self.message_until = 0
        self.pomo_end = None
        self.pomo_break = False
        self.pomo_w, self.pomo_b = 25, 5
        self.last_stretch = time.time()
        self.stretch_active_until = 0
        self.agent_thinking = False
        self.last_agent_check = 0

        # input tracking
        self.prev_keys = set()
        self.key_times = []
        self.last_key = 0
        self.last_scroll = 0
        self.prev_cursor = cursor_pos()
        self.dir_x = 0
        self.reversals = []
        self.stalk_until = 0
        self.hunt_cd_until = 0
        self.pounce = None
        self.pounce_n = 0
        self.next_walk = time.time() + random.uniform(240, 480)
        self.walk_hops = 0
        self.walk_step = 0
        self.walk_hop = None
        self.peeking = False

        self.install_scroll_hook()

        h = time.localtime().tm_hour
        hello = ('мяу… не пора ли спать? 🌙' if h >= 23 or h < 5 else
                 'доброе утро! ☀️' if h < 11 else 'мяу! Я тут :3')
        self.say(self.named(hello), 5)

        self.tick()
        self.root.mainloop()

    # ---------- geometry / conf ----------
    def win_w(self):
        return GRID_W * self.S + 2 * self.margin_x

    def win_h(self):
        return GRID_H * self.S + self.margin_bottom + self.top_space

    def resize_to_grid(self):
        self.root.geometry(f'{self.win_w()}x{self.win_h()}')

    def species(self):
        return self.conf.get('species', 'cat')

    def frames(self):
        return SPRITES[self.species()]

    def save(self):
        os.makedirs(CONF_DIR, exist_ok=True)
        json.dump(self.conf, open(CONF_PATH, 'w', encoding='utf-8'))

    def named(self, text):
        un = self.conf.get('user_name', '')
        return (un + ', ' + text) if un else text

    def say(self, text, secs):
        self.message = text
        self.message_until = time.time() + secs

    def beep(self):
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

    # ---------- scroll hook (для рулона бумаги) ----------
    def install_scroll_hook(self):
        try:
            WH_MOUSE_LL, WM_MOUSEWHEEL = 14, 0x020A
            proto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wt.WPARAM, wt.LPARAM)

            def proc(n, w, l):
                if w == WM_MOUSEWHEEL:
                    self.last_scroll = time.time()
                return user32.CallNextHookEx(None, n, w, l)

            self._hook_proc = proto(proc)   # держим ссылку от GC
            self._hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._hook_proc, None, 0)
        except Exception:
            self._hook = None

    # ---------- colors ----------
    def cell_color(self, x, y, ch, hot):
        if ch == 'o':
            return OUTLINE
        if ch not in 'bswp':
            return None
        if hot:
            return {'b': HOT, 's': HOT_S, 'w': WHITE, 'p': PINK}[ch]
        ctype = self.conf.get('coat_type', 'solid')
        idx = self.conf.get('coat_idx', 0)
        if ctype == 'pattern' and ch != 'p':
            name = list(PATTERN_TITLES)[min(idx, 3)]
            pc = SPRITES['patterns'][self.species()][name][y][x]
            if pc != '.' and pc in PATTERN_PAL:
                return PATTERN_PAL[pc]
        solid = SOLIDS[min(idx, len(SOLIDS) - 1)] if ctype == 'solid' else SOLIDS[0]
        return {'b': solid[1], 's': solid[2], 'w': WHITE, 'p': PINK}[ch]

    def dark_body(self):
        c = self.cell_color(EYES[0][0], EYES[0][1], 'b', False)
        return c and sum(c) / 3 < 90

    # ---------- main tick ----------
    def tick(self):
        now = time.time()

        # keyboard: новые нажатия за тик
        keys = keys_down()
        presses = len(keys - self.prev_keys)
        self.prev_keys = keys
        if presses:
            self.last_key = now
            self.key_times += [now] * presses
        self.key_times = [t for t in self.key_times if now - t < 2]
        kps = len(self.key_times) / 2
        typing = now - self.last_key < 1.2
        overheated = kps >= 5

        idle_s = idle_ms() / 1000
        scrolling = now - self.last_scroll < 1.2

        self.track_hunt(now)
        self.do_walk(now)

        # state
        if self.dragging:
            self.state = 'drag'
        elif self.stretch_active_until > now:
            self.state = 'stretch'
        elif self.stalk_until > now or self.pounce:
            self.state = 'hunt'
        elif self.pet_until > now:
            self.state = 'pet'
        elif typing:
            self.state = 'overheat' if overheated else 'knead'
        elif scrolling and self.paper > 2:
            self.state = 'knead'
        elif self.agent_thinking:
            self.state = 'think'
        elif idle_s > (90 if self.is_night() else 240):
            self.state = 'sleep'
        else:
            self.state = 'idle'

        self.stretch += ((1.0 if self.state == 'stretch' else 0.0) - self.stretch) * 0.18

        # paper
        S = self.S
        if now - self.last_scroll < 0.25:
            self.paper = min(S * 7, self.paper + S * 1.1)
            self.paper_phase += S * 0.45
        elif now - self.last_scroll > 2.5:
            self.paper = max(0, self.paper - S * 0.35)

        # gaze
        px, py = cursor_pos()
        if self.state == 'think':
            self.gaze = (1, -1)
        else:
            wx, wy = self.root.winfo_x(), self.root.winfo_y()
            cx = wx + self.margin_x + GRID_W * S / 2
            cy = wy + self.top_space + GRID_H * S * 0.45
            dx, dy = px - cx, py - cy
            self.gaze = (-1 if dx < -30 else (1 if dx > 30 else 0),
                         -1 if dy < -60 else (1 if dy > 60 else 0))

        if self.state != 'hunt' and now > self.next_blink:
            self.blink_until = now + 0.15
            self.next_blink = now + random.uniform(2.5, 6)
        if self.state == 'idle' and self.species() == 'cat' and now > self.next_flick:
            self.tail_up_until = now + 0.6
            self.next_flick = now + random.uniform(3, 8)
        if self.state in ('knead', 'overheat') and now - self.knead_at > (0.16 if self.state == 'overheat' else 0.26):
            self.knead_flip = not self.knead_flip
            self.knead_at = now

        # cheeks
        if self.species() == 'hamster':
            if self.state in ('knead', 'overheat'):
                self.cheek = min(1, self.cheek + 0.012)
            else:
                self.cheek = max(0, self.cheek - 0.004)
        else:
            self.cheek = 0

        # hearts
        if self.state == 'pet' and now - self.last_heart > 0.35:
            self.hearts.append([GRID_W * S / 2 + random.uniform(-30, 30), GRID_H * S * 0.9, 0])
            self.last_heart = now
        for hh in self.hearts:
            hh[1] += 0.8
            hh[2] += 0.04
        self.hearts = [hh for hh in self.hearts if hh[2] < 1.6]

        self.zzz += 0.02
        self.think_phase += 0.05
        self.jphase += 0.18
        if not self.dragging:
            self.jelly *= 0.95

        # stretch reminder
        sm = self.conf.get('stretch_min', 45)
        if sm and self.stretch_active_until < now and now - self.last_stretch > sm * 60:
            self.stretch_active_until = now + 20
            self.last_stretch = now
            self.say(self.named('потянись со мной! 🧘'), 20)
            self.beep()

        # pomodoro
        if self.pomo_end and now >= self.pomo_end:
            if self.pomo_break:
                self.pomo_end = now + self.pomo_w * 60
                self.pomo_break = False
                self.say(self.named('перерыв окончен — за работу!'), 5)
            else:
                self.pomo_end = now + self.pomo_b * 60
                self.pomo_break = True
                self.say(self.named(f'{self.pomo_w} минут готово! Перерыв 🐾'), 6)
                self.hop_started = now
            self.beep()

        # agent
        if now - self.last_agent_check > 0.5:
            self.last_agent_check = now
            self.check_agent(now)

        self.draw(now)
        self.root.after(40, self.tick)   # 25 fps

    def is_night(self):
        h = time.localtime().tm_hour
        return h >= 23 or h < 5

    def check_agent(self, now):
        try:
            st = os.stat(AGENT_FILE)
            word = open(AGENT_FILE).read().strip()
            age = now - st.st_mtime
        except Exception:
            self.agent_thinking = False
            return
        was = self.agent_thinking
        self.agent_thinking = word == 'thinking' and age < 1800
        if was and not self.agent_thinking and word == 'done' and age < 120:
            self.say(self.named('агент закончил! Мяу!'), 6)
            self.hop_started = now
            self.beep()

    # ---------- hunt (потряси мышкой на месте) ----------
    def track_hunt(self, now):
        px, py = cursor_pos()
        dx = px - self.prev_cursor[0]
        self.prev_cursor = (px, py)
        if not self.conf.get('hunt', True) or self.dragging:
            return
        if abs(dx) > 4:
            d = 1 if dx > 0 else -1
            if self.dir_x and d != self.dir_x:
                self.reversals.append(now)
            self.dir_x = d
        self.reversals = [t for t in self.reversals if now - t < 0.8]

        wx, wy = self.root.winfo_x(), self.root.winfo_y()
        cx, cy = wx + self.win_w() / 2, wy + self.win_h() / 2
        if (self.pounce is None and self.stalk_until <= now and now > self.hunt_cd_until
                and len(self.reversals) >= 4 and math.hypot(px - cx, py - cy) > 120):
            self.stalk_until = now + 0.6
            self.pounce_n = 0
            self.reversals = []

        if self.pounce is None and self.stalk_until and now >= self.stalk_until:
            self.stalk_until = 0
            self.start_pounce(now, px, py)

        if self.pounce:
            fx, fy, tx, ty, t0 = self.pounce
            t = (now - t0) / 0.35
            if t >= 1:
                self.root.geometry(f'+{int(tx)}+{int(ty)}')
                self.pounce = None
                self.jelly = 0.12
                px, py = cursor_pos()
                wx, wy = self.root.winfo_x(), self.root.winfo_y()
                d = math.hypot(px - wx - self.win_w() / 2, py - wy - self.win_h() / 2)
                if self.pounce_n < 3 and d > 150:
                    self.start_pounce(now, px, py)
                else:
                    self.conf['x'], self.conf['y'] = self.root.winfo_x(), self.root.winfo_y()
                    self.save()
                    self.hunt_cd_until = now + 8
                    self.hop_started = now
            else:
                e = t * t * (3 - 2 * t)
                x = fx + (tx - fx) * e
                y = fy + (ty - fy) * e - math.sin(t * math.pi) * 42
                self.root.geometry(f'+{int(x)}+{int(y)}')

    def start_pounce(self, now, px, py):
        fx, fy = self.root.winfo_x(), self.root.winfo_y()
        tx = px - self.win_w() / 2
        ty = py - self.top_space - GRID_H * self.S * 0.7
        d = math.hypot(tx - fx, ty - fy)
        if d > 320:
            tx = fx + (tx - fx) / d * 320
            ty = fy + (ty - fy) / d * 320
        sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        tx = max(-20, min(tx, sw - self.win_w() + 20))
        ty = max(-10, min(ty, sh - self.win_h() + 10))
        self.pounce = (fx, fy, tx, ty, now)
        self.pounce_n += 1

    # ---------- walks ----------
    def do_walk(self, now):
        if now >= self.next_walk:
            self.next_walk = now + random.uniform(240, 600)
            if self.state == 'idle' and not self.dragging and self.pounce is None and self.walk_hops == 0:
                sw = user32.GetSystemMetrics(0)
                target = self.root.winfo_x() + random.uniform(90, 240) * random.choice([-1, 1])
                target = max(-10, min(target, sw - self.win_w() + 10))
                total = target - self.root.winfo_x()
                if abs(total) > 50:
                    self.walk_hops = 3
                    self.walk_step = total / 3
                    self.tail_up_until = now + 2
        if self.walk_hop is None and self.walk_hops > 0:
            if self.dragging or self.pounce:
                self.walk_hops = 0
                return
            fx, fy = self.root.winfo_x(), self.root.winfo_y()
            self.walk_hop = (fx, fy, now)
        if self.walk_hop:
            fx, fy, t0 = self.walk_hop
            t = (now - t0) / 0.38
            if self.dragging:
                self.walk_hop = None
                self.walk_hops = 0
            elif t >= 1:
                self.root.geometry(f'+{int(fx + self.walk_step)}+{fy}')
                self.walk_hop = None
                self.walk_hops -= 1
                if self.walk_hops == 0:
                    self.conf['x'], self.conf['y'] = self.root.winfo_x(), self.root.winfo_y()
                    self.save()
            else:
                e = t * t * (3 - 2 * t)
                self.root.geometry(f'+{int(fx + self.walk_step * e)}+{int(fy - math.sin(t * math.pi) * 13)}')

    # ---------- input ----------
    def on_press(self, ev):
        self.pressed_at = time.time()
        self.moved = False
        self.dragging = True
        self.drag_off = (ev.x_root - self.root.winfo_x(), ev.y_root - self.root.winfo_y())

    def on_drag(self, ev):
        nx, ny = ev.x_root - self.drag_off[0], ev.y_root - self.drag_off[1]
        if abs(nx - self.root.winfo_x()) + abs(ny - self.root.winfo_y()) > 3:
            self.moved = True
            self.jelly = min(0.16, self.jelly + 0.02)
        self.root.geometry(f'+{nx}+{ny}')

    def on_release(self, _ev):
        self.dragging = False
        now = time.time()
        if not self.moved and now - self.pressed_at < 0.35:
            if self.peeking:
                self.unpeek()
                return
            if self.stretch_active_until > now:
                self.stretch_active_until = 0
            else:
                self.say(random.choice(['Мяу!', 'Мррр~', 'Ня!', ':3'] if self.species() == 'cat'
                                       else ['Пип!', 'Хрум-хрум', ':3']), 2)
                self.beep()
            return
        self.settle_after_drag()

    def settle_after_drag(self):
        sw = user32.GetSystemMetrics(0)
        S = self.S
        cat_l = self.root.winfo_x() + self.margin_x
        cat_r = self.root.winfo_x() + self.win_w() - self.margin_x
        cw = GRID_W * S
        if cat_r - sw > cw * 0.22:
            self.peek(right=True)
        elif -cat_l > cw * 0.22:
            self.peek(right=False)
        else:
            self.peeking = False
            self.conf['x'], self.conf['y'] = self.root.winfo_x(), self.root.winfo_y()
            self.save()

    def peek(self, right):
        self.peeking = True
        sw = user32.GetSystemMetrics(0)
        vis = GRID_W * self.S * 0.38
        x = sw - self.margin_x - vis if right else -(self.win_w() - self.margin_x - vis)
        self.root.geometry(f'+{int(x)}+{self.root.winfo_y()}')
        self.conf['x'], self.conf['y'] = self.root.winfo_x(), self.root.winfo_y()
        self.save()

    def unpeek(self):
        self.peeking = False
        sw = user32.GetSystemMetrics(0)
        mid = self.root.winfo_x() + self.win_w() / 2
        x = sw - self.win_w() + self.margin_x - 8 if mid > sw / 2 else 8 - self.margin_x
        self.root.geometry(f'+{int(x)}+{self.root.winfo_y()}')
        self.conf['x'], self.conf['y'] = self.root.winfo_x(), self.root.winfo_y()
        self.save()
        self.hop_started = time.time()

    def on_motion(self, ev):
        if self.dragging:
            return
        S = self.S
        if (self.margin_x + GRID_W * S * 0.1 < ev.x < self.margin_x + GRID_W * S * 0.9
                and self.top_space < ev.y < self.top_space + GRID_H * S * 0.75):
            dx = ev.x - self.pet_x
            self.pet_x = ev.x
            if abs(dx) > 1.5:
                d = 1 if dx > 0 else -1
                now = time.time()
                if d != self.pet_dir and self.pet_dir != 0:
                    self.pet_turns.append(now)
                    self.pet_turns = [t for t in self.pet_turns if now - t < 1.5]
                    if len(self.pet_turns) >= 3:
                        self.pet_until = now + 1.2
                self.pet_dir = d

    # ---------- menu ----------
    def on_menu(self, ev):
        m = tk.Menu(self.root, tearoff=0)

        pets = tk.Menu(m, tearoff=0)
        for t, s in [('Кот 🐈', 'cat'), ('Хомяк 🐹', 'hamster')]:
            pets.add_checkbutton(label=t, onvalue=1, offvalue=0,
                                 variable=tk.IntVar(value=int(self.species() == s)),
                                 command=lambda s=s: self.set_conf('species', s))
        m.add_cascade(label='Питомец', menu=pets)

        coats = tk.Menu(m, tearoff=0)
        for i, (t, _, _) in enumerate(SOLIDS):
            coats.add_command(label=('✓ ' if self.conf.get('coat_type', 'solid') == 'solid'
                                     and self.conf.get('coat_idx', 0) == i else '  ') + t,
                              command=lambda i=i: self.set_coat('solid', i))
        for i, name in enumerate(PATTERN_TITLES.values()):
            coats.add_command(label=('✓ ' if self.conf.get('coat_type') == 'pattern'
                                     and self.conf.get('coat_idx') == i else '  ') + name,
                              command=lambda i=i: self.set_coat('pattern', i))
        m.add_cascade(label='Окрас', menu=coats)

        sizes = tk.Menu(m, tearoff=0)
        for t, s in [('Маленький', 4), ('Средний', 6), ('Большой', 8)]:
            sizes.add_command(label=('✓ ' if self.S == s else '  ') + t,
                              command=lambda s=s: self.set_scale(s))
        m.add_cascade(label='Размер', menu=sizes)

        pomo = tk.Menu(m, tearoff=0)
        if self.pomo_end is None:
            pomo.add_command(label='Старт 25+5', command=lambda: self.pomo_start(25, 5))
            pomo.add_command(label='Старт 50+10', command=lambda: self.pomo_start(50, 10))
        else:
            pomo.add_command(label='Стоп', command=self.pomo_stop)
        m.add_cascade(label='🍅 Помодоро', menu=pomo)

        st = tk.Menu(m, tearoff=0)
        for t, mins in [('Выкл', 0), ('Каждые 30 мин', 30), ('Каждые 45 мин', 45), ('Каждый час', 60)]:
            st.add_command(label=('✓ ' if self.conf.get('stretch_min', 45) == mins else '  ') + t,
                           command=lambda mins=mins: self.set_conf('stretch_min', mins))
        m.add_cascade(label='🧘 Разминка', menu=st)

        m.add_command(label='Моё имя…', command=lambda: self.ask_name('user_name', 'Как тебя зовут?'))
        m.add_command(label='Имя питомца…', command=lambda: self.ask_name('cat_name', 'Как зовут питомца?'))
        m.add_command(label=('✓ ' if self.conf.get('show_name') else '  ') + 'Показывать имя',
                      command=lambda: self.set_conf('show_name', not self.conf.get('show_name', False)))
        m.add_command(label=('✓ ' if self.conf.get('hunt', True) else '  ') + 'Охота за курсором',
                      command=lambda: self.set_conf('hunt', not self.conf.get('hunt', True)))
        m.add_command(label='Спрятаться за край' if not self.peeking else 'Выглянуть',
                      command=(lambda: self.peek(right=True)) if not self.peeking else self.unpeek)
        m.add_separator()
        m.add_command(label='Выход', command=self.root.destroy)
        m.tk_popup(ev.x_root, ev.y_root)

    def set_conf(self, key, val):
        self.conf[key] = val
        self.save()

    def set_coat(self, t, i):
        self.conf['coat_type'] = t
        self.conf['coat_idx'] = i
        self.save()

    def set_scale(self, s):
        self.S = s
        self.conf['scale'] = s
        self.save()
        self.resize_to_grid()

    def pomo_start(self, w, b):
        self.pomo_w, self.pomo_b = w, b
        self.pomo_end = time.time() + w * 60
        self.pomo_break = False
        self.say(self.named(f'фокус {w} минут. Погнали!'), 4)

    def pomo_stop(self):
        self.pomo_end = None
        self.say('Помодоро выключен', 3)

    def ask_name(self, key, title):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.attributes('-topmost', True)
        tk.Label(win, text=title).pack(padx=12, pady=6)
        e = tk.Entry(win, width=24)
        e.insert(0, self.conf.get(key, ''))
        e.pack(padx=12)
        e.focus_set()

        def ok(*_a):
            self.conf[key] = e.get().strip()
            if key == 'cat_name' and self.conf[key]:
                self.conf['show_name'] = True
            self.save()
            win.destroy()

        tk.Button(win, text='OK', command=ok).pack(pady=6)
        e.bind('<Return>', ok)

    # ---------- drawing ----------
    def draw(self, now):
        c = self.canvas
        c.delete('all')
        S = self.S
        hot = self.state == 'overheat'
        f = self.frames()
        if self.state in ('knead', 'overheat'):
            grid = f['knead0'] if self.knead_flip else f['knead1']
        elif self.tail_up_until > now:
            grid = f['tail_up']
        else:
            grid = f['base']

        wob = self.jelly * math.sin(self.jphase)
        grow = 1 + self.stretch * 0.45
        sx = (1 + wob) * grow
        sy = (1 - wob) * grow
        if self.state == 'hunt':
            sy *= 0.88
            sx *= 1.06
        hop = 0
        ht = now - self.hop_started
        if ht < 0.9:
            hop = abs(math.sin(ht * math.pi * 2.2)) * 26 * (1 - ht / 0.9)

        ax = self.margin_x + GRID_W * S / 2
        ay = self.top_space + GRID_H * S - hop

        def cell(x, y, col):
            # клетка (x, y) сетки с желейной трансформацией вокруг нижнего центра
            x0 = ax + (x * S - GRID_W * S / 2) * sx
            y0 = ay - (GRID_H - y) * S * sy
            c.create_rectangle(x0, y0, x0 + S * sx + 0.5, y0 + S * sy + 0.5,
                               fill=hx(col), width=0)

        if self.paper > 3:
            self.draw_paper(c, S)

        for y, row in enumerate(grid):
            for x, ch in enumerate(row):
                col = self.cell_color(x, y, ch, hot)
                if col:
                    cell(x, y, col)

        # cheeks
        if self.species() == 'hamster' and self.cheek > 0.25:
            lvl2 = self.cheek > 0.7
            fillc = BLUSH if hot else WHITE
            white = [(2, 10), (3, 10), (2, 11), (3, 11)] + ([(4, 10), (4, 11), (2, 12), (3, 12)] if lvl2 else [])
            ring = ([(2, 9), (3, 9), (4, 9), (5, 10), (5, 11), (4, 12), (2, 13), (3, 13)] if lvl2
                    else [(2, 9), (3, 9), (4, 10), (4, 11), (2, 12), (3, 12)])
            for x, y in ring:
                cell(x, y, OUTLINE)
                cell(21 - x, y, OUTLINE)
            for x, y in white:
                cell(x, y, fillc)
                cell(21 - x, y, fillc)
            if lvl2:
                cell(3, 11, PINK)
                cell(18, 11, PINK)

        # eyes
        closed = (self.state == 'sleep' or self.blink_until > now) and self.state not in ('pet', 'hunt')
        happy = self.state in ('pet', 'stretch')
        dark = self.dark_body()
        ink = WHITE if dark else OUTLINE
        for ex, ey in EYES:
            if happy:
                cell(ex - 1, ey + 1, ink); cell(ex, ey, ink); cell(ex + 1, ey + 1, ink)
            elif closed:
                cell(ex, ey + 1, ink); cell(ex + 1, ey + 1, ink)
            elif dark:
                for xx in range(2):
                    for yy in range(2):
                        cell(ex + xx, ey + yy, WHITE)
                cell(ex + (1 if self.gaze[0] > 0 else 0), ey + (1 if self.gaze[1] > 0 else 0), OUTLINE)
            else:
                gx, gy = ex + self.gaze[0], ey + self.gaze[1]
                for xx in range(2):
                    for yy in range(2):
                        cell(gx + xx, gy + yy, OUTLINE)
                if self.state != 'hunt':
                    cell(gx, gy, (255, 255, 255))

        if self.state == 'pet':
            for x in (3, 17):
                cell(x, 11, BLUSH)
                cell(x + 1, 11, BLUSH)

        # overlays
        if hot:
            self.draw_steam(c, S)
        if self.state == 'sleep':
            self.draw_zzz(c, S)
        if self.state == 'think':
            self.draw_dots(c, S)
        for hh in self.hearts:
            self.draw_heart(c, hh)
        self.draw_bubble(c, now)
        if self.conf.get('show_name') and self.conf.get('cat_name'):
            w = 10 + 6 * len(self.conf['cat_name'])
            x = self.margin_x + GRID_W * S / 2
            y = self.top_space + GRID_H * S + 10
            c.create_rectangle(x - w / 2, y - 7, x + w / 2, y + 7, fill='#1a1517', width=0)
            c.create_text(x, y, text=self.conf['cat_name'], fill='white', font=('Consolas', 8))

    def draw_pixel_grid(self, c, grid, x0, top, S, paw):
        colmap = {'o': OUTLINE, 'W': PAPER, 'l': PAPER_L, 'h': (150, 146, 136), 'B': paw}
        for r, line in enumerate(grid):
            for cc, ch in enumerate(line):
                col = colmap.get(ch)
                if col:
                    c.create_rectangle(x0 + cc * S, top + r * S, x0 + (cc + 1) * S, top + (r + 1) * S,
                                       fill=hx(col), width=0)

    def draw_paper(self, c, S):
        paw = self.cell_color(3, 14, 'b', False)
        ground = self.top_space + GRID_H * S
        roll_top = ground - 13 * S
        self.draw_pixel_grid(c, ROLL_SPRITE, S * 0.5, roll_top, S, paw)
        strip_top = roll_top + 6 * S
        rows = min(7, int(self.paper / S))
        ph = int(self.paper_phase / S)
        for i in range(rows):
            row = STRIP_TEAR if i == rows - 1 else (STRIP_LINE if ((i - ph) % 3 + 3) % 3 == 1 else STRIP_ROW)
            self.draw_pixel_grid(c, [row], S * 0.5, strip_top + i * S, S, paw)
        self.draw_pixel_grid(c, PAW_SPRITE, S * 3.5, roll_top - S, S, paw)

    def draw_steam(self, c, S):
        for i in range(3):
            ph = self.think_phase * 1.2 + i * 2.1
            rise = ph % 6 / 6
            x = self.margin_x + GRID_W * S / 2 + (i - 1) * S * 3.2 + math.sin(ph) * 3
            y = self.top_space - rise * S * 5
            r = S * (0.8 + rise * 0.8)
            c.create_oval(x - r, y - r, x + r, y + r, fill='#b8b8c2', width=0)

    def draw_zzz(self, c, S):
        for i in range(3):
            ph = (self.zzz + i * 0.9) % 2.7
            t = ph / 2.7
            c.create_text(self.margin_x + GRID_W * S * 0.72 + t * 22 + i * 6,
                          self.top_space + GRID_H * S * 0.1 - t * 26 - i * 4,
                          text='z', fill='#7382a6', font=('Consolas', 9 + i * 3, 'bold'))

    def draw_dots(self, c, S):
        for i in range(3):
            x = self.margin_x + GRID_W * S * 0.8 + i * S * 1.6
            y = self.top_space - S - i * S * 0.9
            r = S * 0.55
            c.create_oval(x - r, y - r, x + r, y + r, fill='#8a92b8', width=0)

    def draw_heart(self, c, hh):
        u = 3
        pattern = ['.#.#.', '#####', '.###.', '..#..']
        x0 = self.margin_x + hh[0] - u * 2.5
        y0 = self.top_space + GRID_H * self.S - hh[1]
        for r, line in enumerate(pattern):
            for cc, ch in enumerate(line):
                if ch == '#':
                    c.create_rectangle(x0 + cc * u, y0 + r * u, x0 + (cc + 1) * u, y0 + (r + 1) * u,
                                       fill=hx(HEART), width=0)

    def draw_bubble(self, c, now):
        text = None
        if self.message_until > now:
            text = self.message
        elif self.pomo_end:
            left = max(0, int(self.pomo_end - now))
            text = ('☕' if self.pomo_break else '🍅') + f' {left // 60:02d}:{left % 60:02d}'
        if not text or (self.peeking and self.message_until <= now):
            return
        w = 24 + 7 * len(text)
        x = max(2, self.margin_x + GRID_W * self.S / 2 - w / 2)
        y = self.top_space - 42
        c.create_rectangle(x, y, x + w, y + 26, fill='#fffcf5', outline=hx(OUTLINE), width=2)
        c.create_text(x + w / 2, y + 13, text=text, fill=hx(OUTLINE), font=('Consolas', 10, 'bold'))


if __name__ == '__main__':
    Pet()
