#!/usr/bin/env python3
"""FunnyPets — пиксельный питомец для Linux (Debian 13+).

Порт macOS-версии ComNyan: кот/хомяк, окрасы, глаза за курсором, месит
лапками при печати, мурчит от поглаживания, спит, помодоро, разминка,
интеграция с Claude Code (~/.comnyan/agent).

Требует X11 (или XWayland-сессию «GNOME on Xorg»):
  sudo apt install python3-gi gir1.2-gtk-3.0 libxss1
Запуск: python3 funnypets.py
"""
import json, os, math, random, time, ctypes, sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib

HERE = os.path.dirname(os.path.abspath(__file__))
SPRITES = json.load(open(os.path.join(HERE, 'sprites.json')))
GRID_W, GRID_H = SPRITES['grid']
EYES = SPRITES['eyes']

CONF_DIR = os.path.expanduser('~/.config/funnypets')
CONF_PATH = os.path.join(CONF_DIR, 'config.json')
AGENT_FILE = os.path.expanduser('~/.comnyan/agent')

SOLIDS = [
    ('Рыжий',    (240, 148, 54),  (198, 104, 26)),
    ('Серый',    (154, 158, 170), (110, 114, 126)),
    ('Чёрный',   (66, 60, 68),    (44, 40, 48)),
    ('Белый',    (246, 242, 234), (216, 208, 198)),
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


def load_conf():
    try:
        return json.load(open(CONF_PATH))
    except Exception:
        return {}


def save_conf(c):
    os.makedirs(CONF_DIR, exist_ok=True)
    json.dump(c, open(CONF_PATH, 'w'))


class XIdle:
    """Глобальный простой ввода через XScreenSaver (X11)."""
    def __init__(self):
        self.ok = False
        try:
            xlib = ctypes.cdll.LoadLibrary('libX11.so.6')
            xss = ctypes.cdll.LoadLibrary('libXss.so.1')
            dpy = xlib.XOpenDisplay(None)
            if not dpy:
                return

            class Info(ctypes.Structure):
                _fields_ = [('window', ctypes.c_ulong), ('state', ctypes.c_int),
                            ('kind', ctypes.c_int), ('since', ctypes.c_ulong),
                            ('idle', ctypes.c_ulong), ('event_mask', ctypes.c_ulong)]

            xss.XScreenSaverAllocInfo.restype = ctypes.POINTER(Info)
            self.info = xss.XScreenSaverAllocInfo()
            self.dpy, self.root, self.xss = dpy, xlib.XDefaultRootWindow(dpy), xss
            self.ok = True
        except Exception:
            pass

    def idle_ms(self):
        if not self.ok:
            return None
        self.xss.XScreenSaverQueryInfo(self.dpy, self.root, self.info)
        return self.info.contents.idle


class Pet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.conf = load_conf()
        self.S = self.conf.get('scale', 6)
        self.margin_x = 20
        self.margin_bottom = 20
        self.top_space = 90   # место под пузырь и шапку

        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_app_paintable(True)
        self.set_accept_focus(False)
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.resize_to_grid()

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK |
                        Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('draw', self.on_draw)
        self.connect('button-press-event', self.on_press)
        self.connect('button-release-event', self.on_release)
        self.connect('motion-notify-event', self.on_motion)
        self.connect('destroy', Gtk.main_quit)

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
        self.hop_started = 0
        self.dragging = False
        self.drag_off = (0, 0)
        self.pressed_at = 0
        self.moved = False
        self.pet_until = 0
        self.pet_dir = 0
        self.pet_x = 0
        self.pet_turns = []
        self.typing = 0
        self.prev_pointer = (0, 0)
        self.message = ''
        self.message_until = 0
        self.pomo_end = None
        self.pomo_break = False
        self.pomo_w, self.pomo_b = 25, 5
        self.last_stretch = time.time()
        self.stretch_active_until = 0
        self.agent_thinking = False
        self.agent_last = ''
        self.idle_src = XIdle()

        x, y = self.conf.get('x'), self.conf.get('y')
        if x is not None and y is not None:
            self.move(x, y)
        self.show_all()

        h = time.localtime().tm_hour
        hello = ('мяу… не пора ли спать? 🌙' if h >= 23 or h < 5 else
                 'доброе утро! ☀️' if h < 11 else 'мяу! Я тут :3')
        un = self.conf.get('user_name', '')
        self.say((un + ', ' + hello) if un else hello, 5)
        self.hop_started = time.time()

        GLib.timeout_add(33, self.tick)

    # ---------- geometry / conf ----------
    def resize_to_grid(self):
        self.resize(GRID_W * self.S + 2 * self.margin_x,
                    GRID_H * self.S + self.margin_bottom + self.top_space)

    def species(self):
        return self.conf.get('species', 'cat')

    def frames(self):
        return SPRITES[self.species()]

    def save(self):
        save_conf(self.conf)

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

    # ---------- behavior ----------
    def say(self, text, secs):
        self.message = text
        self.message_until = time.time() + secs

    def named(self, text):
        un = self.conf.get('user_name', '')
        return (un + ', ' + text) if un else text

    def tick(self):
        now = time.time()
        S = self.S

        # pointer & typing heuristic
        try:
            seat = Gdk.Display.get_default().get_default_seat()
            _, px, py = seat.get_pointer().get_position()
        except Exception:
            px, py = 0, 0
        pointer_moved = abs(px - self.prev_pointer[0]) + abs(py - self.prev_pointer[1]) > 2
        self.prev_pointer = (px, py)
        idle = self.idle_src.idle_ms()
        if idle is not None and idle < 250 and not pointer_moved:
            self.typing = min(600, self.typing + 1)
        else:
            self.typing = max(0, self.typing - 3)
        idle_s = (idle / 1000) if idle is not None else 0

        # state
        if self.dragging:
            self.state = 'drag'
        elif self.stretch_active_until > now:
            self.state = 'stretch'
        elif self.pet_until > now:
            self.state = 'pet'
        elif self.typing > 3:
            self.state = 'overheat' if self.typing > 450 else 'knead'
        elif self.agent_thinking:
            self.state = 'think'
        elif idle is not None and idle_s > (90 if self.is_night() else 240):
            self.state = 'sleep'
        else:
            self.state = 'idle'

        self.stretch += ((1.0 if self.state == 'stretch' else 0.0) - self.stretch) * 0.18

        # gaze
        if self.state == 'think':
            self.gaze = (1, -1)
        else:
            wx, wy = self.get_position()
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

        # hamster cheeks
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
            hh[2] += 0.033
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

        # agent file
        if int(now * 2) != int((now - 0.033) * 2):
            self.check_agent(now)

        self.queue_draw()
        return True

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
        self.agent_last = word

    # ---------- input ----------
    def on_press(self, _w, ev):
        if ev.button == 3:
            self.build_menu().popup_at_pointer(ev)
            return True
        if ev.button == 1:
            self.pressed_at = time.time()
            self.moved = False
            self.dragging = True
            self.drag_off = (ev.x_root - self.get_position()[0], ev.y_root - self.get_position()[1])
        return True

    def on_release(self, _w, ev):
        if ev.button != 1:
            return True
        self.dragging = False
        if not self.moved and time.time() - self.pressed_at < 0.35:
            if self.stretch_active_until > time.time():
                self.stretch_active_until = 0
            else:
                self.say(random.choice(['Мяу!', 'Мррр~', 'Ня!', ':3'] if self.species() == 'cat'
                                       else ['Пип!', 'Хрум-хрум', ':3']), 2)
        x, y = self.get_position()
        self.conf['x'], self.conf['y'] = x, y
        self.save()
        return True

    def on_motion(self, _w, ev):
        if self.dragging:
            nx, ny = int(ev.x_root - self.drag_off[0]), int(ev.y_root - self.drag_off[1])
            ox, oy = self.get_position()
            if abs(nx - ox) + abs(ny - oy) > 3:
                self.moved = True
                self.jelly = min(0.16, self.jelly + 0.02)
            self.move(nx, ny)
            return True
        # petting: strokes over the head
        S = self.S
        hx0 = self.margin_x + GRID_W * S * 0.1
        hy0 = self.top_space
        if hx0 < ev.x < hx0 + GRID_W * S * 0.8 and hy0 < ev.y < hy0 + GRID_H * S * 0.75:
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
        return True

    # ---------- menu ----------
    def build_menu(self):
        menu = Gtk.Menu()

        def add(parent, title, cb=None, check=False, on=False):
            it = Gtk.CheckMenuItem(label=title) if check else Gtk.MenuItem(label=title)
            if check:
                it.set_active(on)
            if cb:
                it.connect('activate', cb)
            parent.append(it)
            return it

        def sub(title):
            it = Gtk.MenuItem(label=title)
            m = Gtk.Menu()
            it.set_submenu(m)
            menu.append(it)
            return m

        pets = sub('Питомец')
        for t, s in [('Кот 🐈', 'cat'), ('Хомяк 🐹', 'hamster')]:
            add(pets, t, lambda _w, s=s: self.set_conf('species', s),
                check=True, on=self.species() == s)

        coats = sub('Окрас')
        for i, (t, _, _) in enumerate(SOLIDS):
            add(coats, t, lambda _w, i=i: self.set_coat('solid', i),
                check=True, on=self.conf.get('coat_type', 'solid') == 'solid' and self.conf.get('coat_idx', 0) == i)
        for i, name in enumerate(PATTERN_TITLES.values()):
            add(coats, name, lambda _w, i=i: self.set_coat('pattern', i),
                check=True, on=self.conf.get('coat_type') == 'pattern' and self.conf.get('coat_idx') == i)

        sizes = sub('Размер')
        for t, s in [('Маленький', 4), ('Средний', 6), ('Большой', 8)]:
            add(sizes, t, lambda _w, s=s: self.set_scale(s), check=True, on=self.S == s)

        pomo = sub('🍅 Помодоро')
        if self.pomo_end is None:
            add(pomo, 'Старт 25+5', lambda _w: self.pomo_start(25, 5))
            add(pomo, 'Старт 50+10', lambda _w: self.pomo_start(50, 10))
        else:
            add(pomo, 'Стоп', lambda _w: self.pomo_stop())

        st = sub('🧘 Разминка')
        for t, m in [('Выкл', 0), ('Каждые 30 мин', 30), ('Каждые 45 мин', 45), ('Каждый час', 60)]:
            add(st, t, lambda _w, m=m: self.set_conf('stretch_min', m),
                check=True, on=self.conf.get('stretch_min', 45) == m)

        add(menu, 'Моё имя…', lambda _w: self.ask_name('user_name', 'Как тебя зовут?'))
        add(menu, 'Имя питомца…', lambda _w: self.ask_name('cat_name', 'Как зовут питомца?'))
        add(menu, 'Показывать имя', lambda _w: self.set_conf('show_name', not self.conf.get('show_name', False)),
            check=True, on=self.conf.get('show_name', False))
        menu.append(Gtk.SeparatorMenuItem())
        add(menu, 'Выход', lambda _w: Gtk.main_quit())
        menu.show_all()
        return menu

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
        d = Gtk.Dialog(title=title, transient_for=self, flags=0)
        d.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        e = Gtk.Entry()
        e.set_text(self.conf.get(key, ''))
        d.get_content_area().add(e)
        d.show_all()
        if d.run() == Gtk.ResponseType.OK:
            self.conf[key] = e.get_text().strip()
            if key == 'cat_name' and self.conf[key]:
                self.conf['show_name'] = True
            self.save()
        d.destroy()

    # ---------- drawing ----------
    def on_draw(self, _w, cr):
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(1)  # SOURCE
        cr.paint()
        cr.set_operator(2)  # OVER

        now = time.time()
        S = self.S
        hot = self.state == 'overheat'
        f = self.frames()
        if self.state in ('knead', 'overheat'):
            grid = f['knead0'] if self.knead_flip else f['knead1']
        elif self.tail_up_until > now:
            grid = f['tail_up']
        else:
            grid = f['base']

        ox = self.margin_x
        oy = self.top_space
        wob = self.jelly * math.sin(self.jphase)
        grow = 1 + self.stretch * 0.45
        sx = (1 + wob) * grow
        sy = (1 - wob) * grow
        hop = 0
        ht = now - self.hop_started
        if ht < 0.9:
            hop = abs(math.sin(ht * math.pi * 2.2)) * 26 * (1 - ht / 0.9)

        cr.save()
        cr.translate(ox + GRID_W * S / 2, oy + GRID_H * S - hop)
        cr.scale(sx, sy)
        cr.translate(-GRID_W * S / 2, -GRID_H * S)

        def cell(x, y, col):
            cr.set_source_rgb(col[0] / 255, col[1] / 255, col[2] / 255)
            cr.rectangle(x * S, y * S, S, S)
            cr.fill()

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
        ex_l, ex_r = EYES
        closed = (self.state == 'sleep' or self.blink_until > now) and self.state != 'pet'
        happy = self.state in ('pet', 'stretch')
        dark = self.dark_body()
        ink = WHITE if dark else OUTLINE
        for ex, ey in (ex_l, ex_r):
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
                cell(gx, gy, (255, 255, 255))

        if self.state == 'pet':
            for x in (3, 17):
                cell(x, 11, BLUSH); cell(x + 1, 11, BLUSH)
        cr.restore()

        # overlays (unscaled)
        if hot:
            self.draw_steam(cr, now)
        if self.state == 'sleep':
            self.draw_zzz(cr)
        if self.state == 'think':
            self.draw_dots(cr)
        for hx, hy, age in [(h[0], h[1], h[2]) for h in self.hearts]:
            self.draw_heart(cr, hx, hy, age)
        self.draw_bubble(cr, now)
        if self.conf.get('show_name') and self.conf.get('cat_name'):
            self.draw_nameplate(cr)
        return True

    def draw_steam(self, cr, now):
        S = self.S
        for i in range(3):
            ph = self.think_phase * 1.2 + i * 2.1
            rise = ph % 6 / 6
            x = self.margin_x + GRID_W * S / 2 + (i - 1) * S * 3.2 + math.sin(ph) * 3
            y = self.top_space + GRID_H * S * 0.05 - rise * S * 5
            r = S * (0.8 + rise * 0.8)
            cr.set_source_rgba(0.72, 0.72, 0.76, (1 - rise) * 0.85)
            cr.arc(x, y, r, 0, 6.283)
            cr.fill()

    def draw_zzz(self, cr):
        S = self.S
        cr.select_font_face('monospace')
        for i in range(3):
            ph = (self.zzz + i * 0.9) % 2.7
            t = ph / 2.7
            cr.set_font_size(9 + i * 3)
            cr.set_source_rgba(0.45, 0.5, 0.65, 1 - t * 0.8)
            cr.move_to(self.margin_x + GRID_W * S * 0.72 + t * 22 + i * 6,
                       self.top_space + GRID_H * S * 0.1 - t * 26 - i * 4)
            cr.show_text('z')

    def draw_dots(self, cr):
        S = self.S
        for i in range(3):
            a = 0.25 + 0.75 * (math.sin(self.think_phase * 3 - i * 0.9) + 1) / 2
            cr.set_source_rgba(0.5, 0.55, 0.7, a)
            cr.arc(self.margin_x + GRID_W * S * 0.8 + i * S * 1.6,
                   self.top_space - S - i * S * 0.9, S * 0.55, 0, 6.283)
            cr.fill()

    def draw_heart(self, cr, hx, hy, age):
        u = 3
        cr.set_source_rgba(HEART[0] / 255, HEART[1] / 255, HEART[2] / 255, max(0, 1 - age / 1.6))
        pattern = ['.#.#.', '#####', '.###.', '..#..']
        x0 = self.margin_x + hx - u * 2.5
        y0 = self.top_space + GRID_H * self.S - hy
        for r, line in enumerate(pattern):
            for c, ch in enumerate(line):
                if ch == '#':
                    cr.rectangle(x0 + c * u, y0 + r * u, u, u)
        cr.fill()

    def draw_bubble(self, cr, now):
        text = None
        if self.message_until > now:
            text = self.message
        else:
            parts = []
            if self.pomo_end:
                left = max(0, int(self.pomo_end - now))
                parts.append(('☕' if self.pomo_break else '🍅') + f' {left // 60:02d}:{left % 60:02d}')
            if parts:
                text = ' · '.join(parts)
        if not text:
            return
        cr.select_font_face('monospace')
        cr.set_font_size(12)
        ext = cr.text_extents(text)
        w = ext.width + 24
        h = 26
        x = max(2, self.margin_x + GRID_W * self.S / 2 - w / 2)
        y = self.top_space - 42
        cr.set_source_rgba(1, 0.99, 0.96, 0.97)
        cr.rectangle(x, y, w, h)
        cr.fill()
        cr.set_source_rgb(OUTLINE[0] / 255, OUTLINE[1] / 255, OUTLINE[2] / 255)
        cr.set_line_width(1.5)
        cr.rectangle(x, y, w, h)
        cr.stroke()
        cr.move_to(x + 12, y + h - 8)
        cr.show_text(text)

    def draw_nameplate(self, cr):
        name = self.conf['cat_name']
        cr.select_font_face('monospace')
        cr.set_font_size(9)
        ext = cr.text_extents(name)
        w = ext.width + 10
        x = self.margin_x + GRID_W * self.S / 2 - w / 2
        y = self.top_space + GRID_H * self.S + 4
        cr.set_source_rgba(0.1, 0.08, 0.09, 0.62)
        cr.rectangle(x, y, w, 13)
        cr.fill()
        cr.set_source_rgb(1, 1, 1)
        cr.move_to(x + 5, y + 10)
        cr.show_text(name)


if __name__ == '__main__':
    Pet()
    Gtk.main()
