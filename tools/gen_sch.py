"""Draw the hierarchical schematic of one health-watch board from design.py (KiCad 9).

Root sheet = sheet symbols; one sub-sheet per group of blocks (design.SHEETS). Inside a sheet every block gets a dashed
frame with its title. Layout rules (readable without hand placement):
  * ICs / connectors / multi-pin parts in a row at the top of the block; every pin gets a short stub and then
    a power symbol (rails), a label (signals) or a no-connect flag;
  * two-pin parts (caps, resistors, inductors, LEDs ...) in rows under the ICs, drawn vertically: decoupling caps show
    "rail - C - GND", series parts show their two nets;
  * text notes (design.NOTES) printed inside the frame.
Rails are KiCad power symbols (net name = symbol value), so a decoupling cap is visibly tied to the rail it serves.
usage: gen_sch.py <main|sensor> <out_root.kicad_sch>"""
import sys, os, re, math, uuid, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
BOARD, OUT = sys.argv[1], sys.argv[2]
OUTDIR = os.path.dirname(os.path.abspath(OUT))
PROJ = os.path.join(HERE, '..')
LIBS = {'HW_Watch': os.path.join(PROJ, 'hardware', 'HW_Watch.kicad_sym'),
        'HW_IC': os.path.expanduser('~/workspace/PCB_design_learning/kicad_lib/HW_IC.kicad_sym')}
STOCK = '/usr/share/kicad/symbols'
NS = uuid.UUID('6a1f2c3e-0b5d-4c1e-9a7f-a1e0000a7c02')
def U(*k): return str(uuid.uuid5(NS, BOARD + '/' + '/'.join(map(str, k))))
G = 2.54
def r2(v): return round(v + 0.0, 2)
def snap(v): return r2(G * round(v / G))
PROJECT = 'health_watch_' + BOARD
BROOT = U('root')

# ---------------- symbol library access (flattening 'extends')
_cache = {}
def libtext(lib):
    if lib not in _cache:
        t = open(LIBS.get(lib, os.path.join(STOCK, lib + '.kicad_sym')), encoding='utf-8').read()
        blocks = {}
        for m in re.finditer(r'\n\t\(symbol "([^"]+)"', t):
            s = m.start() + 1; depth = 0
            for i in range(s, len(t)):
                if t[i] == '(': depth += 1
                elif t[i] == ')':
                    depth -= 1
                    if depth == 0: blocks[m.group(1)] = t[s:i + 1]; break
        _cache[lib] = blocks
    return _cache[lib]
PROP = re.compile(r'\n\t\t\(property "([^"]+)".*?\n\t\t\)', re.S)
def flat(lib, name):
    raw = libtext(lib)[name]
    m = re.search(r'\(extends "([^"]+)"\)', raw)
    if not m: return raw
    pname = m.group(1); parent = flat(lib, pname)
    i = parent.index('\n\t\t(property')
    head = parent[:i].replace('(symbol "%s"' % pname, '(symbol "%s"' % name, 1)
    props = collections.OrderedDict((pm.group(1), pm.group(0)) for pm in PROP.finditer(parent))
    for pm in PROP.finditer(raw): props[pm.group(1)] = pm.group(0)
    body = parent[parent.index('\n\t\t(symbol "'):]
    body = re.sub(r'\(symbol "%s_(\d+_\d+)"' % re.escape(pname), lambda q: '(symbol "%s_%s"' % (name, q.group(1)), body)
    return head + ''.join(props.values()) + body
_syms = {}
def sym(libid):
    if libid not in _syms:
        lib, name = libid.split(':'); t = flat(lib, name)
        pins = [dict(et=et, num=n, name=nm, x=float(x), y=float(y), a=int(float(a)), l=float(l), hide='(hide yes)' in blk)
                for blk, et, x, y, a, l, nm, n in
                [(m.group(0),) + m.groups() for m in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length ([\d.]+)\)(?:(?!\(pin ).)*?\(name "([^"]*)".*?\(number "([^"]*)"', t, re.S)]]
        xs = [p['x'] for p in pins] + [float(v) for v in re.findall(r'\((?:start|end|xy) ([-\d.]+) [-\d.]+\)', t)]
        ys = [p['y'] for p in pins] + [float(v) for v in re.findall(r'\((?:start|end|xy) [-\d.]+ ([-\d.]+)\)', t)]
        props = {k: v for k, v in re.findall(r'\(property "([^"]+)" "([^"]*)"', t)}
        _syms[libid] = dict(text=t, pins=pins, bb=(min(xs), min(ys), max(xs), max(ys)), props=props)
    return _syms[libid]
libsyms = {}
def want(libid):
    if libid not in libsyms:
        libsyms[libid] = sym(libid)['text'].replace('(symbol "%s"' % libid.split(':')[1], '(symbol "%s"' % libid, 1)
def fnt(hide=False, just=None, size=1.27):
    s = '(effects (font (size %s %s))' % (size, size)
    if just: s += ' (justify %s)' % just
    if hide: s += ' (hide yes)'
    return s + ')'
def esc(s): return str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

PARTS = D.BOARDS[BOARD]
BYREF = {p['ref']: p for p in PARTS}
# rails drawn as power symbols: every net that feeds decoupling, plus the stock ones
STOCKPWR = {'GND': 'power:GND', '+3V3': 'power:+3V3', 'VBUS': 'power:VBUS'}
RAILS = {'GND', '+3V3', 'VBUS', 'VSYS', 'VBAT', 'VBAT_CELL', '3V3_PMIC', 'VMID', 'VRTC', 'VBACKUP', 'VDD3P3', 'VDD_SPI', 'VLED', 'VLED_5V',
         '+1V8', '1V8_LDO', 'AXP_VREF', 'AFE_VREF'}
def ptype(net):
    return STOCKPWR.get(net, 'power:VCC')
# nets driven only by passives / connectors need a PWR_FLAG for ERC: rails without a power_out pin on this board
def drivers():
    d = collections.defaultdict(list)
    for p in PARTS:
        s = sym(D.P[p['typ']][0])
        types = {q['num']: q['et'] for q in s['pins']}
        for k, n in p['pins'].items():
            if n: d[n].append(types.get(k, '?'))
    return d
DRV = drivers()
NEED_FLAG = {n for n in RAILS if n in DRV and 'power_out' not in DRV[n]}

SHEET_OF = {}
for key, title, paper, blocks in D.SHEETS[BOARD]:
    for p in PARTS:
        if p['block'] in blocks: SHEET_OF[p['ref']] = key
missing = [p['ref'] for p in PARTS if p['ref'] not in SHEET_OF]
assert not missing, missing
NET_SHEETS = collections.defaultdict(set)
for p in PARTS:
    for n in p['pins'].values():
        if n: NET_SHEETS[n].add(SHEET_OF[p['ref']])
DIR = {'left': (-1, 0), 'right': (1, 0), 'up': (0, -1), 'down': (0, 1)}
cnt = collections.Counter()
flagged = set()

class Sheet:
    def __init__(self, key, title, paper):
        self.key, self.title, self.paper = key, title, paper
        self.uuid = U('sheet', key); self.screen = U('screen', key)
        self.items, self.segs, self.points, self.placed, self.done = [], [], [], {}, set()
        self.small = True; self.named = set()
        self.path = '/%s/%s' % (BROOT, self.uuid)
    def inst(self, ref):
        return '(instances (project "%s" (path "%s" (reference "%s") (unit 1))))' % (PROJECT, self.path, ref)
    def _tf(self, ref, px, py):
        X, Y, rot, mir = self.placed[ref]
        if mir: px = -px
        c, s = round(math.cos(math.radians(rot))), round(math.sin(math.radians(rot)))
        x, y = px * c - py * s, px * s + py * c
        return (r2(X + x), r2(Y - y))
    def _dir(self, ref, a):
        rot, mir = self.placed[ref][2], self.placed[ref][3]
        if mir: a = (180 - a) % 360
        ang = math.radians(a + rot)
        return (-round(math.cos(ang)), round(math.sin(ang)))
    def pin(self, ref, num):
        q = next(q for q in sym(D.P[BYREF[ref]['typ']][0])['pins'] if q['num'] == num)
        return self._tf(ref, q['x'], q['y'])
    def P(self, ref, num):
        self.done.add((ref, num)); return self.pin(ref, num)
    def place(self, ref, at, rot=0, pin=None, mirror=False, text=None):
        p = BYREF[ref]; libid, value, fp, code, dsk = D.P[p['typ']]
        s = sym(libid); want(libid)
        X, Y = at
        if pin is not None:
            self.placed[ref] = (0, 0, rot, mirror)
            ox, oy = self.pin(ref, pin)
            X, Y = r2(at[0] - ox), r2(at[1] - oy)
        self.placed[ref] = (X, Y, rot, mirror)
        lcsc = code if re.fullmatch(r'C\d+', code or '') else ''
        mpn = '' if lcsc else (code or '')
        dnp = p['dnp'] or value == 'DNP'
        x0, y0, x1, y1 = s['bb']
        corners = [self._tf(ref, a, b) for a in (x0, x1) for b in (y0, y1)]
        top, bot = min(c[1] for c in corners), max(c[1] for c in corners)
        left, right = min(c[0] for c in corners), max(c[0] for c in corners)
        npins = len({q['num'] for q in s['pins']})
        cx = (left + right) / 2
        if npins == 2 and (right - left) > (bot - top) + 0.1:     # horizontal 2-pin part: text above (or below)
            if text == 'below': rp, vp, just = (cx, bot + 1.6), (cx, bot + 3.2), None
            else: rp, vp, just = (cx, top - 2.6), (cx, top - 1.0), None
        elif npins == 2:                                          # vertical 2-pin part: text right (or left) of the body
            if text == 'left': rp, vp, just = (left - 0.6, Y - 1.0), (left - 0.6, Y + 1.0), 'right'
            else: rp, vp, just = (right + 0.6, Y - 1.0), (right + 0.6, Y + 1.0), 'left'
        elif npins == 1:
            rp, vp, just = (X + 1.6, Y - 2.6), (X + 1.6, Y - 0.9), 'left'
        elif text == 'below':
            rp, vp, just = (left, bot + 1.8), (left, bot + 3.4), 'left'
        elif text == 'right':
            rp, vp, just = (right + 1.0, top + 1.0), (right + 1.0, top + 2.6), 'left'
        else:
            rp, vp, just = (left, top - 2.8), (left, top - 1.0), 'left'
        L = ['\t(symbol (lib_id "%s") (at %s %s %d)%s (unit 1) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp %s) (uuid "%s")'
             % (libid, X, Y, rot, ' (mirror y)' if mirror else '', 'yes' if dnp else 'no', U('sym', ref))]
        fa = 90 if rot in (90, 270) else 0
        L.append('\t\t(property "Reference" "%s" (at %s %s %d) %s)' % (ref, r2(rp[0]), r2(rp[1]), fa, fnt(just=just)))
        L.append('\t\t(property "Value" "%s" (at %s %s %d) %s)' % (esc(value), r2(vp[0]), r2(vp[1]), fa, fnt(just=just, size=1.0)))
        for k, v in (('Footprint', fp), ('Datasheet', D.DOCS[dsk][0] if dsk else '~'), ('LCSC', lcsc), ('MPN', mpn), ('Purpose', p['why']), ('Reference_doc', p['cite'])):
            L.append('\t\t(property "%s" "%s" (at %s %s 0) %s)' % (k, esc(v), X, Y, fnt(True)))
        for q in s['pins']: L.append('\t\t(pin "%s" (uuid "%s"))' % (q['num'], U('pin', ref, q['num'])))
        L.append('\t\t%s\n\t)' % self.inst(ref))
        self.items.append('\n'.join(L))
    def wire(self, a, b):
        if a != b:
            assert a[0] == b[0] or a[1] == b[1], ('diagonal', self.key, a, b)
            self.segs.append((a, b))
    def _pt(self, a):
        if isinstance(a[0], str): return self.P(*a)
        return (r2(a[0]), r2(a[1]))
    def W(self, *pts):
        pts = [self._pt(a) for a in pts]
        for a, b in zip(pts, pts[1:]): self.wire(a, b)
        return pts[-1]
    def pwr(self, net, at, dv):
        libid = ptype(net); want(libid); cnt['pwr'] += 1
        gnd = net == 'GND'
        if not gnd and dv[1] > 0: dv = dv          # rails pointing down (bottom pins) are still drawn as arrows
        r = {(0, 1): 0 if gnd else 180, (0, -1): 180 if gnd else 0, (-1, 0): 270 if gnd else 90, (1, 0): 90 if gnd else 270}[dv]
        ref = '#PWR%03d' % cnt['pwr']
        vx, vy = at[0] + dv[0] * 3.8, at[1] + dv[1] * (4.6 if gnd else 3.8)
        just = None; vang = 90 if r in (90, 270) else 0
        if dv[1] and not self.small:            # IC top/bottom pins are 2.54 mm apart: vertical text avoids overlaps
            vang = 90; vx = at[0]; vy = at[1] + dv[1] * (5.6 if gnd else 3.4); just = 'left' if (dv[1] < 0) == (r == 0) else 'right'
        if dv[0]: just = 'left' if (dv[0] > 0) == (r in (0, 270)) else 'right'; vx = at[0] + dv[0] * (2.2 if gnd else 3.4); vy = at[1]
        self.items.append('\t(symbol (lib_id "%s") (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "%s")\n'
                          '\t\t(property "Reference" "%s" (at %s %s 0) %s)\n\t\t(property "Value" "%s" (at %s %s %d) %s)\n'
                          '\t\t(property "Footprint" "" (at %s %s 0) %s)\n\t\t(property "Datasheet" "" (at %s %s 0) %s)\n'
                          '\t\t(pin "1" (uuid "%s"))\n\t\t%s\n\t)'
                          % (libid, at[0], at[1], r, U('pwr', self.key, ref), ref, at[0], at[1], fnt(True), esc(net), r2(vx), r2(vy), vang, fnt(size=1.0, just=just),
                             at[0], at[1], fnt(True), at[0], at[1], fnt(True), U('pp', self.key, ref), self.inst(ref)))
        self.points.append(at); self.named.add(at)
        if net in NEED_FLAG and net not in flagged and dv[0] == 0 and self.small:
            flagged.add(net); self.flag(at, dv)
    def flag(self, at, dv):
        want('power:PWR_FLAG'); cnt['flg'] += 1
        ref = '#FLG%03d' % cnt['flg']
        # flag sits on a short side wire so it does not cover the power symbol
        side = (1, 0) if dv[1] else (0, -1)
        q = (r2(at[0] + side[0] * G), r2(at[1] + side[1] * G))
        self.wire(at, q)
        r = {(1, 0): 270, (0, -1): 0}[side]
        self.items.append('\t(symbol (lib_id "power:PWR_FLAG") (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom no) (on_board yes) (dnp no) (uuid "%s")\n'
                          '\t\t(property "Reference" "%s" (at %s %s 0) %s)\n\t\t(property "Value" "PWR_FLAG" (at %s %s 0) %s)\n'
                          '\t\t(property "Footprint" "" (at %s %s 0) %s)\n\t\t(property "Datasheet" "" (at %s %s 0) %s)\n'
                          '\t\t(pin "1" (uuid "%s"))\n\t\t%s\n\t)'
                          % (q[0], q[1], r, U('flg', self.key, ref), ref, q[0], q[1], fnt(True), q[0], q[1], fnt(True),
                             q[0], q[1], fnt(True), q[0], q[1], fnt(True), U('flgp', self.key, ref), self.inst(ref)))
        self.points.append(q)
    def lab(self, net, at, dv, local=False):
        self.named.add(at)
        ang = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[dv]
        just = 'right' if dv in ((-1, 0), (0, 1)) else 'left'
        if len(NET_SHEETS[net]) > 1 and not local:
            self.items.append('\t(global_label "%s" (shape bidirectional) (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s")\n'
                              '\t\t(property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))\n\t)'
                              % (esc(net), at[0], at[1], ang, just, U('gl', self.key, net, at), at[0], at[1]))
        else:
            self.items.append('\t(label "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid "%s"))'
                              % (esc(net), at[0], at[1], ang, just, U('lab', self.key, net, at)))
        self.points.append(at)
    def text(self, s, at, size=1.3, bold=False):
        self.items.append('\t(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) (justify left top)) (uuid "%s"))'
                          % (esc(s), r2(at[0]), r2(at[1]), size, size, ' (bold yes)' if bold else '', U('txt', self.key, s[:40], at)))
    def frame(self, title, x0, y0, x1, y1):
        self.items.append('\t(rectangle (start %s %s) (end %s %s) (stroke (width 0.25) (type dash)) (fill (type none)) (uuid "%s"))' % (r2(x0), r2(y0), r2(x1), r2(y1), U('frm', self.key, title)))
        self.items.append('\t(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size 1.8 1.8) (bold yes)) (justify left bottom)) (uuid "%s"))'
                          % (esc(title), r2(x0 + 1), r2(y0 - 1), U('frmt', self.key, title)))
    def finish(self):
        for ref in list(self.placed):
            p = BYREF[ref]; s = sym(D.P[p['typ']][0])
            seen = {self._tf(ref, q['x'], q['y']) for q in s['pins'] if (ref, q['num']) in self.done}
            for q in s['pins']:
                net = p['pins'].get(q['num'], 'UNLISTED')
                e = self._tf(ref, q['x'], q['y'])
                if e in seen: continue
                seen.add(e)
                if net == 'UNLISTED': print('WARN pin not in design:', ref, q['num'], q['name'])
                if (ref, q['num']) in self.done: continue
                if any(e in s_ or (s_[0][0] == s_[1][0] == e[0] and min(s_[0][1], s_[1][1]) < e[1] < max(s_[0][1], s_[1][1]))
                       or (s_[0][1] == s_[1][1] == e[1] and min(s_[0][0], s_[1][0]) < e[0] < max(s_[0][0], s_[1][0])) for s_ in self.segs):
                    continue                                   # pin sits on a drawn wire
                if net is None or net == 'UNLISTED':
                    self.items.append('\t(no_connect (at %s %s) (uuid "%s"))' % (e[0], e[1], U('nc', ref, q['num']))); continue
                d = self._dir(ref, q['a'])
                self.small = len({k for k in p['pins']}) <= 2
                st = (r2(e[0] + d[0] * G), r2(e[1] + d[1] * G))
                self.wire(e, st)
                if net in RAILS: self.pwr(net, st, d)
                else: self.lab(net, st, d)
            for k in p['pins']:
                if k not in {q['num'] for q in s['pins']}: print('WARN design pin missing in symbol:', ref, k)
        pins = [self._tf(r, q['x'], q['y']) for r in self.placed for q in sym(D.P[BYREF[r]['typ']][0])['pins']]
        pts = set(pins) | set(self.points) | {a for s_ in self.segs for a in s_}
        def on(p_, s_):
            (ax, ay), (bx, by) = s_
            if ax == bx == p_[0]: return min(ay, by) < p_[1] < max(ay, by)
            if ay == by == p_[1]: return min(ax, bx) < p_[0] < max(ax, bx)
            return False
        segs = list(dict.fromkeys(self.segs))
        changed = True
        while changed:
            changed = False
            for i, s_ in enumerate(segs):
                for p_ in pts:
                    if on(p_, s_):
                        segs[i:i + 1] = [(s_[0], p_), (p_, s_[1])]; changed = True; break
                if changed: break
        # name every wired net that has no label / power symbol yet (so the netlist keeps the design net names)
        par = {}
        def fnd(a):
            par.setdefault(a, a)
            while par[a] != a: par[a] = par[par[a]]; a = par[a]
            return a
        for a, b in segs: par[fnd(a)] = fnd(b)
        comp = collections.defaultdict(set)
        for r in self.placed:
            for q in sym(D.P[BYREF[r]['typ']][0])['pins']:
                n = BYREF[r]['pins'].get(q['num'])
                e = self._tf(r, q['x'], q['y'])
                if n and e in par: comp[fnd(e)].add(n)
        named = {fnd(p_) for p_ in self.named if p_ in par}
        for root, nets in comp.items():
            if root in named: continue
            if len(nets) > 1: print('WARN short on sheet', self.key, sorted(nets)); continue
            net = next(iter(nets))
            cand = [s_ for s_ in segs if fnd(s_[0]) == root]
            s_ = max(cand, key=lambda s_: abs(s_[0][0] - s_[1][0]) + abs(s_[0][1] - s_[1][1]))
            (ax, ay), (bx, by) = s_
            if abs(ax - bx) + abs(ay - by) < 4 * G - 0.05: continue      # too short to carry a readable name
            mx, my = snap((ax + bx) / 2), snap((ay + by) / 2)
            if (mx, my) in (s_[0], s_[1]) and abs(ax - bx) + abs(ay - by) > G: mx, my = snap(min(ax, bx) + (G if ax != bx else 0)), snap(min(ay, by) + (G if ay != by else 0))
            self.lab(net, (r2(mx), r2(my)), (1, 0) if ay == by else (0, -1), local=True)
        for root, nets in comp.items():
            if len(nets) > 1 and root in named: print('WARN short on sheet', self.key, sorted(nets))
        deg = collections.Counter()
        for a, b in segs: deg[a] += 1; deg[b] += 1
        pinc = collections.Counter(pins)
        for p_, n in deg.items():
            if n + pinc[p_] >= 3:
                self.items.append('\t(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))' % (p_[0], p_[1], U('j', self.key, p_)))
        for a, b in segs:
            self.items.append('\t(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))' % (a[0], a[1], b[0], b[1], U('w', self.key, a, b)))
    def write(self, path):
        libs = sorted({re.search(r'lib_id "([^"]+)"', it).group(1) for it in self.items if it.startswith('\t(symbol (lib_id')})
        hdr = '(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n\t(uuid "%s")\n\t(paper "%s")\n' % (self.screen, self.paper)
        hdr += ('\t(title_block\n\t\t(title "%s")\n\t\t(date "2026-11-04")\n\t\t(rev "1.0")\n\t\t(company "harisama1 - đồ án đồng hồ sức khỏe")\n'
                '\t\t(comment 1 "Generated by tools/gen_sch.py from tools/design.py - edit the design file, not this sheet")\n\t)\n\t(lib_symbols\n'
                % esc(D.TITLE[BOARD] + ' - ' + self.title))
        lib = ''.join('\n'.join(('\t' + l) if l.strip() else l for l in libsyms[k].split('\n')) + '\n' for k in libs)
        open(path, 'w', encoding='utf-8').write(hdr + lib + '\t)\n' + '\n'.join(self.items) + '\n\t(embedded_fonts no)\n)\n')

# ============================================================== automatic block layout
def label_len(net): return 2.0 + 1.05 * len(net)
def side_extent(ref):
    """space needed left/right/top/bottom of the symbol body for stubs + labels / power symbols"""
    p = BYREF[ref]; s = sym(D.P[p['typ']][0]); ext = {'l': 0, 'r': 0, 't': 0, 'b': 0}
    for q in s['pins']:
        net = p['pins'].get(q['num'])
        n = 4.0 if net is None else (G + (6.0 if net in RAILS else label_len(net)))
        side = {0: 'l', 180: 'r', 270: 't', 90: 'b'}[q['a']]
        ext[side] = max(ext[side], n)
    return ext
def layout_block(S, block, x0, y0, xmax, refs=None):
    """place a block's parts starting at (x0, y0); returns (x1, y1) of the used area"""
    if refs is None: refs = [p['ref'] for p in PARTS if p['block'] == block]
    big = [r for r in refs if len({q['num'] for q in sym(D.P[BYREF[r]['typ']][0])['pins']}) > 2]
    small = [r for r in refs if r not in big]
    x, y, rowh, used_x = x0 + 2, y0 + 6, 0, x0
    for r in big:
        s = sym(D.P[BYREF[r]['typ']][0]); e = side_extent(r)
        bx0, by0, bx1, by1 = s['bb']
        w = (bx1 - bx0) + e['l'] + e['r']
        h = (by1 - by0) + e['t'] + e['b'] + 6
        if x + w > xmax and x > x0 + 2: x, y, rowh = x0 + 2, y + rowh + 4, 0
        X = snap(x + e['l'] - bx0); Y = snap(y + 4 + e['t'] + by1)          # symbol y axis points up
        S.place(r, (X, Y))
        x += w + 6; rowh = max(rowh, h); used_x = max(used_x, x)
    if big: y += rowh + 4
    # two-pin parts: rows, vertical
    x = x0 + 4; rowh = 0
    for r in small:
        p = BYREF[r]; s = sym(D.P[p['typ']][0]); pins = s['pins']
        bx0, by0, bx1, by1 = s['bb']
        vert = (by1 - by0) >= (bx1 - bx0)
        rot = 0
        if not vert:     # horizontal 2-pin symbol: turn it so GND (else pin 1) ends up at the top/bottom sensibly
            def ytop(rr, num):
                q = next(q for q in pins if q['num'] == num); c, s_ = round(math.cos(math.radians(rr))), round(math.sin(math.radians(rr)))
                return -(q['x'] * s_ + q['y'] * c)
            gpin = next((q['num'] for q in pins if p['pins'].get(q['num']) == 'GND'), None)
            rot = 90
            if gpin: rot = 90 if ytop(90, gpin) > ytop(270, gpin) else 270
            elif len(pins) == 2: rot = 90 if ytop(90, pins[0]['num']) < ytop(270, pins[0]['num']) else 270
        nets = [p['pins'].get(q['num']) for q in pins]
        top = max(6.0 if (n in RAILS) else label_len(n or ''), 4) + G
        bot = top
        if len(pins) == 1: bot = 0
        h = (max(by1 - by0, bx1 - bx0)) + top + bot + 2
        w = max(12.7, snap(6 + 0.8 * max(len(r), len(D.P[p['typ']][1]))))
        if x + w > xmax: x, y, rowh = x0 + 4, y + rowh + 2, 0
        X = snap(x + 2); Y = snap(y + top + (max(by1 - by0, bx1 - bx0)) / 2)
        S.place(r, (X, Y), rot)
        x += w; rowh = max(rowh, h); used_x = max(used_x, x)
    y += rowh
    return used_x + 2, y + 2

exec(open(os.path.join(HERE, 'sch_layouts.py'), encoding='utf-8').read())
PAPER = {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420)}
sheets = []
for page, (key, title, paper, blocks) in enumerate(D.SHEETS[BOARD], 2):
    S = Sheet(key, title, paper); S.page = page
    PW_, PH_ = PAPER[paper]
    S.text(title, (12, 8), 2.2, True)
    if key not in LAYOUT: S.text('Mỗi khung = một khối chức năng. Ký hiệu nguồn (+3V3, VSYS, VLED, +1V8 ...) nối theo tên; nhãn tín hiệu cùng tên là cùng một dây. '
           'Lý do chọn và trang datasheet của từng linh kiện: trường Purpose / Reference_doc và báo cáo docs/health_watch_design_report.md', (12, 12), 1.2)
    if key in LAYOUT:
        LAYOUT[key](S)
        left = [p['ref'] for p in PARTS if SHEET_OF[p['ref']] == key and p['ref'] not in S.placed]
        if left:
            fx, fy = FALLBACK.get(key, (12, PH_ - 70))
            x1, y1 = layout_block(S, None, fx, fy, PW_ - 12, refs=left)
            S.frame('Điểm đo / linh kiện phụ', fx, fy, x1, y1)
    else:
      x, y, bandh = 12, 22, 0
      for b in blocks:
        S0 = len(S.items)
        x1, y1 = layout_block(S, b, x, y, PW_ - 12)
        if x1 > PW_ - 10 and x > 12:
            for r in [p['ref'] for p in PARTS if p['block'] == b]: S.placed.pop(r, None)
            del S.items[S0:]
            x, y, bandh = 12, y + bandh + 8, 0
            x1, y1 = layout_block(S, b, x, y, PW_ - 12)
        x1 = max(x1, x + 1.25 * len(D.BLOCK_NAME[b]) + 6)
        S.frame(D.BLOCK_NAME[b], x, y, x1, y1)
        bandh = max(bandh, y1 - y)
        x = x1 + 8
    lost = [p['ref'] for p in PARTS if SHEET_OF[p['ref']] == key and p['ref'] not in S.placed]
    assert not lost, (key, lost)
    S.finish()
    S.file = '%s_%s.kicad_sch' % (os.path.splitext(os.path.basename(OUT))[0], key)
    sheets.append(S)

# root sheet
R = Sheet('root', 'root', 'A4'); R.path = '/' + BROOT
R.text(D.TITLE[BOARD], (20, 16), 2.4, True)
R.text('Sơ đồ phân cấp: mỗi ô là một trang con. Nhãn toàn cục (global label) nối tín hiệu giữa các trang; ký hiệu nguồn nối theo tên.', (20, 22), 1.4)
R.text('Ref %d-%d. Sinh tự động bởi tools/gen_sch.py từ tools/design.py.' % (D.BASE[BOARD] + 1, D.BASE[BOARD] + 99), (20, 26), 1.3)
x, y = 20.32, 40.64
for S in sheets:
    w, h = 50.8, 20.32
    R.items.append('\t(sheet (at %s %s) (size %s %s) (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced yes)\n'
                   '\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000)) (uuid "%s")\n'
                   '\t\t(property "Sheetname" "%s" (at %s %s 0) (effects (font (size 1.5 1.5)) (justify left bottom)))\n'
                   '\t\t(property "Sheetfile" "%s" (at %s %s 0) (effects (font (size 1.1 1.1)) (justify left top)))\n'
                   '\t\t(instances (project "%s" (path "/%s" (page "%d"))))\n\t)'
                   % (x, y, w, h, S.uuid, esc(S.title), x, r2(y - 0.71), S.file, x, r2(y + h + 0.59), PROJECT, BROOT, S.page))
    x += 66.04
    if x > 230: x, y = 20.32, y + 35.56
R.screen = BROOT
for S in sheets: S.write(os.path.join(OUTDIR, S.file))
R.items.append('\t(sheet_instances (path "/" (page "1")))')
R.write(OUT)
print('written', OUT, '+', ', '.join(S.file for S in sheets), '| parts', len(PARTS), '| PWR_FLAG on', sorted(flagged))
