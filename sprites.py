#!/usr/bin/env python3
"""Pixel pet sprite designer — renders frames to a PNG sheet for preview."""
import struct, zlib, json, os

PAL = {
    '.': None,             # transparent
    'o': (43, 29, 24),     # outline
    'b': (240, 148, 54),   # body orange
    's': (198, 104, 26),   # stripe darker
    'w': (252, 244, 232),  # white muzzle/paws
    'p': (247, 143, 158),  # pink nose/inner ear
    'e': (43, 29, 24),     # eye dark
    'W': (255, 255, 255),  # eye shine
    'q': (250, 178, 162),  # blush
    'g': (170, 170, 180),  # steam gray
    'r': (236, 96, 72),    # overheat body tint (preview only)
}

W_, H_ = 24, 19

# base sitting loaf, no eyes (eyes drawn as overlay)
BASE = [
"........................",
"...oo...........oo......",
"...obo.........obo......",
"...obbo.......obbo......",
"...obpbo.....obpbo......",
"..obbbbboooooobbbbo.....",
"..obbbbbbsbsbsbbbbo.....",
".obbbbbbbbbbbbbbbbbo....",
".obbbbbbbbbbbbbbbbbo....",
".obbbbbbbwwwbbbbbbbo....",
".obbbbbbwwpwwbbbbbbo....",
".obbbbbbwwwwwbbbbbbo....",
"..obbbbbbwwwbbbbbbo.....",
"..obbbbbbbbbbbbbbbo.....",
".obbbbbbbwwwwbbbbboo....",
".obsbbbbbwwwwbbbsbbbo...",
".obbbbbbbwwwwbbbbbbsbo..",
".obbbbwwbwwwwbwwbbbsbo..",
"..oooooooooooooooooooo..",
]

# hamster: round body, small ears, no tail; paws/belly aligned with the cat so knead() works
HAM_BASE = [
"........................",
".....oo.......oo........",
"....obpo.....obpo.......",
"...oobbbooooobbboo......",
"..obbbbbbbbbbbbbbbbo....",
".obbbbbbbbbbbbbbbbbbo...",
".obbbbbbbbbbbbbbbbbbbo..",
".obbbbbbbbbbbbbbbbbbbo..",
".obbbbbbbbbbbbbbbbbbbo..",
".obbbbbbbbwwwbbbbbbbbo..",
".obbbbbbbwwpwwbbbbbbbo..",
".obbbbbbbwwwwwbbbbbbbo..",
".obbbbbbbbwwwbbbbbbbbo..",
".obbbbbbbbbbbbbbbbbbbo..",
".obbbbbbbbwwwwbbbbbbbo..",
".obbbbbbbbwwwwbbbbbbbo..",
".obbbbbbbbwwwwbbbbbbo...",
".obbbbwwbwwwwbwwbbbbo...",
"..oooooooooooooooooo....",
]

EYE_L = (4, 8)   # top-left of left 2x2 eye
EYE_R = (15, 8)

def put(f, x, y, c):
    if 0 <= y < len(f) and 0 <= x < len(f[0]):
        f[y] = f[y][:x] + c + f[y][x+1:]

def eyes_open(f, dx=0, dy=0):
    for ex, ey in (EYE_L, EYE_R):
        x, y = ex+dx, ey+dy
        for yy in range(2):
            for xx in range(2):
                put(f, x+xx, y+yy, 'e')
        put(f, x, y, 'W')

def eyes_closed(f):
    for ex, ey in (EYE_L, EYE_R):
        put(f, ex, ey+1, 'e'); put(f, ex+1, ey+1, 'e')

def eyes_happy(f):
    # ^ ^ shape, 3px wide
    for ex, ey in (EYE_L, EYE_R):
        put(f, ex-1, ey+1, 'e'); put(f, ex, ey, 'e'); put(f, ex+1, ey+1, 'e')

def frame(mods=(), gaze=(0,0), eye='open', base=None):
    f = list(base if base is not None else BASE)
    for m in mods: m(f)
    if eye == 'open': eyes_open(f, *gaze)
    elif eye == 'closed': eyes_closed(f)
    elif eye == 'happy': eyes_happy(f)
    return f

def blush(f):
    for x in (3, 17):
        put(f, x, 11, 'q'); put(f, x+1, 11, 'q')

def tail_up(f):
    # erase curled tail, draw raised flicking tail
    for y, xs in ((15,(19,20)), (16,(18,19,20,21)), (17,(18,19,20,21)), (18,(17,18,19,20,21))):
        for x in xs: put(f, x, y, '.')
    put(f, 18, 17, 'o'); put(f, 17, 18, 'o'); put(f, 18, 18, 'o')
    for y in range(12, 17):
        put(f, 19, y, 'o'); put(f, 20, y, 'b' if y > 13 else 's'); put(f, 21, y, 'o')
    put(f, 20, 11, 'o'); put(f, 20, 17, 'o'); put(f, 19, 17, 'b'); put(f, 19, 18, 'o'); put(f, 20, 18, 'o')

def knead(side):
    # lift one front paw: white paw block rises 1px
    def m(f):
        xs = (6, 7) if side == 0 else (14, 15)
        for x in xs:
            put(f, x, 17, 'b')          # old paw spot -> body
            put(f, x, 16, 'w')          # raised paw
    return m

def render(frames, path, scale=8, gap=2):
    h = len(frames[0]); w = len(frames[0][0])
    Wp = (w*scale+gap)*len(frames)+gap; Hp = h*scale+2*gap
    px = [[(70,70,80,255)]*Wp for _ in range(Hp)]
    for fi, f in enumerate(frames):
        ox = gap+fi*(w*scale+gap)
        for y, row in enumerate(f):
            for x, c in enumerate(row):
                col = PAL.get(c)
                if col is None: continue
                for dy in range(scale):
                    for dx in range(scale):
                        px[gap+y*scale+dy][ox+x*scale+dx] = (*col, 255)
    raw = b''.join(b'\x00'+b''.join(struct.pack('4B',*p) for p in r) for r in px)
    def chunk(t, d):
        c = struct.pack('>I', len(d))+t+d
        return c+struct.pack('>I', zlib.crc32(t+d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', Wp, Hp, 8, 6, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b'')
    open(path, 'wb').write(png)
    print(f'{path}: {len(frames)} frames {w}x{h}')

# ---- coat patterns: override grids over body cells (b/s/w) ----
# pattern palettes (letter -> rgb), also merged into PAL for preview
PATTERN_PAL = {
    'c': (242, 232, 210),  # siamese cream
    'd': (88, 60, 48),     # siamese points (dark brown)
    'e': (168, 172, 182),  # mackerel gray
    'f': (106, 110, 122),  # mackerel stripe
    'g': (246, 242, 234),  # calico white
    'h': (238, 146, 52),   # calico orange
    'i': (70, 64, 72),     # calico black
    'j': (52, 48, 56),     # tuxedo black
}
PAL.update(PATTERN_PAL)

def cat_frames():
    return [frame(eye='none'), frame(mods=[tail_up], eye='none'),
            frame(mods=[knead(0)], eye='none'), frame(mods=[knead(1)], eye='none')]

def ham_frames():
    return [frame(base=HAM_BASE, eye='none'),
            frame(base=HAM_BASE, mods=[knead(0)], eye='none'),
            frame(base=HAM_BASE, mods=[knead(1)], eye='none')]

def pattern_grid(rule, fs):
    # union over ALL frames so animated pixels (raised paw, flicked tail) are covered too
    g = [['.'] * W_ for _ in range(H_)]
    for f in fs:
        for y, row in enumerate(f):
            for x, ch in enumerate(row):
                if ch in 'bsw' and g[y][x] == '.':
                    r = rule(x, y, ch)
                    if r: g[y][x] = r
    return [''.join(r) for r in g]

def siamese(x, y, ch):
    if y <= 4: return 'd'                                  # ears
    if 7 <= x <= 13 and 8 <= y <= 12 and ch == 'w': return 'd'   # face mask on muzzle
    if y >= 16 and ch == 'w' and (x <= 7 or x >= 14): return 'd' # paws
    if x >= 18 and y >= 12: return 'd'                     # tail
    return 'c'

def mackerel(x, y, ch):
    if ch == 'w': return None
    if ch == 's': return 'f'
    if (x == 4 or x == 15) and 13 <= y <= 16: return 'f'   # body stripes
    if (x == 2 or x == 18) and 8 <= y <= 10: return 'f'    # cheek stripes
    return 'e'

def calico(x, y, ch):
    if ch == 'w': return None
    if x >= 18 and y >= 12: return 'h'                     # tail orange
    if y <= 6 and x <= 9: return 'h'                       # left ear/head patch
    if y >= 12 and 12 <= x <= 17: return 'i'               # right body patch
    return 'g'

def tuxedo(x, y, ch):
    if ch == 'w': return None
    return 'j'

PATTERNS = [('SIAMESE', siamese), ('MACKEREL', mackerel), ('CALICO', calico), ('TUXEDO', tuxedo)]

# hamster variants: no tail zone, wider face
def siamese_h(x, y, ch):
    if y <= 4: return 'd'
    if 8 <= x <= 14 and 9 <= y <= 12 and ch == 'w': return 'd'
    if y >= 16 and ch == 'w' and (x <= 7 or x >= 14): return 'd'
    return 'c'

def mackerel_h(x, y, ch):
    if ch == 'w': return None
    if ch == 's': return 'f'
    if (x == 4 or x == 17) and 13 <= y <= 16: return 'f'
    if (x == 2 or x == 19) and 7 <= y <= 10: return 'f'
    return 'e'

def calico_h(x, y, ch):
    if ch == 'w': return None
    if y <= 6 and x <= 9: return 'h'
    if y >= 12 and 14 <= x <= 19: return 'i'
    return 'g'

def tuxedo_h(x, y, ch):
    if ch == 'w': return None
    return 'j'

PATTERNS_HAM = [('SIAMESE', siamese_h), ('MACKEREL', mackerel_h), ('CALICO', calico_h), ('TUXEDO', tuxedo_h)]

def apply_pattern(f, grid):
    out = []
    for y, row in enumerate(f):
        line = ''
        for x, ch in enumerate(row):
            p = grid[y][x]
            line += p if (p != '.' and ch in 'bsw') else ch
        out.append(line)
    return out

def emit_swift(path):
    def sw(name, f):
        rows = ',\n'.join(f'    "{r}"' for r in f)
        return f'let {name}: [String] = [\n{rows},\n]\n'
    body = '// Generated by sprites.py — do not edit by hand\n'
    body += sw('FRAME_TAIL_DOWN', frame(eye='none'))
    body += sw('FRAME_TAIL_UP', frame(mods=[tail_up], eye='none'))
    body += sw('FRAME_KNEAD_0', frame(mods=[knead(0)], eye='none'))
    body += sw('FRAME_KNEAD_1', frame(mods=[knead(1)], eye='none'))
    body += sw('HAM_BASE_F', frame(base=HAM_BASE, eye='none'))
    body += sw('HAM_KNEAD_0', frame(base=HAM_BASE, mods=[knead(0)], eye='none'))
    body += sw('HAM_KNEAD_1', frame(base=HAM_BASE, mods=[knead(1)], eye='none'))
    for name, rule in PATTERNS:
        body += sw(f'PATTERN_{name}', pattern_grid(rule, cat_frames()))
    for name, rule in PATTERNS_HAM:
        body += sw(f'PATTERN_{name}_HAM', pattern_grid(rule, ham_frames()))
    body += 'let EYE_LX = 4, EYE_LY = 8, EYE_RX = 15, EYE_RY = 8\n'
    body += f'let GRID_W = {W_}, GRID_H = {H_}\n'
    open(path, 'w').write(body)
    print(f'wrote {path}')

def emit_linux(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        'grid': [W_, H_],
        'eyes': [list(EYE_L), list(EYE_R)],
        'palette': {k: list(v) for k, v in PAL.items() if v is not None},
        'cat': {
            'base': frame(eye='none'),
            'tail_up': frame(mods=[tail_up], eye='none'),
            'knead0': frame(mods=[knead(0)], eye='none'),
            'knead1': frame(mods=[knead(1)], eye='none'),
        },
        'hamster': {
            'base': frame(base=HAM_BASE, eye='none'),
            'tail_up': frame(base=HAM_BASE, eye='none'),
            'knead0': frame(base=HAM_BASE, mods=[knead(0)], eye='none'),
            'knead1': frame(base=HAM_BASE, mods=[knead(1)], eye='none'),
        },
        'patterns': {
            'cat': {n: pattern_grid(r, cat_frames()) for n, r in PATTERNS},
            'hamster': {n: pattern_grid(r, ham_frames()) for n, r in PATTERNS_HAM},
        },
    }
    json.dump(data, open(path, 'w'))
    print(f'wrote {path}')

def render_icon(path, scale=42):
    f = frame(mods=[blush], eye='happy')
    h, w = len(f), len(f[0])
    # crop transparent margins loosely: use cols 0..22, rows 0..19 as-is
    Wp, Hp = 1024, 1024
    ox = (Wp - w*scale)//2; oy = (Hp - h*scale)//2
    px = [[(0,0,0,0)]*Wp for _ in range(Hp)]
    for y, row in enumerate(f):
        for x, c in enumerate(row):
            col = PAL.get(c)
            if col is None: continue
            for dy in range(scale):
                for dx in range(scale):
                    px[oy+y*scale+dy][ox+x*scale+dx] = (*col, 255)
    raw = b''.join(b'\x00'+b''.join(struct.pack('4B',*p) for p in r) for r in px)
    def chunk(t, d):
        c = struct.pack('>I', len(d))+t+d
        return c+struct.pack('>I', zlib.crc32(t+d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', Wp, Hp, 8, 6, 0, 0, 0))+chunk(b'IDAT', zlib.compress(raw))+chunk(b'IEND', b'')
    open(path, 'wb').write(png)
    print(f'wrote {path}')

if __name__ == '__main__':
    frames = [
        frame(),                       # idle, tail down
        frame(mods=[tail_up]),         # idle, tail up
        frame(eye='closed'),           # blink
        frame(mods=[blush], eye='happy'),  # petted
        frame(mods=[knead(0)], gaze=(0,1)),  # knead left paw
        frame(mods=[knead(1)], gaze=(0,1)),  # knead right paw
    ]
    render(frames, 'preview.png')
    pats = [apply_pattern(frame(), pattern_grid(rule, cat_frames())) for _, rule in PATTERNS]
    render(pats, 'preview_patterns.png')
    hams = [frame(base=HAM_BASE), frame(base=HAM_BASE, mods=[knead(0)], gaze=(0,1)),
            frame(base=HAM_BASE, mods=[knead(1)], gaze=(0,1)), frame(base=HAM_BASE, mods=[blush], eye='happy')]
    hams += [apply_pattern(frame(base=HAM_BASE), pattern_grid(rule, ham_frames())) for _, rule in PATTERNS_HAM]
    render(hams, 'preview_hamster.png')
    emit_swift('Sources/CatFrames.swift')
    emit_linux('linux/sprites.json')
    render_icon('icon_1024.png')
