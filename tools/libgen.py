"""Project library for the health watch: hardware/HW_Watch.kicad_sym + hardware/HW_Watch.pretty.

Symbols are generated from pin tables typed in from the datasheets (citations next to each table); ESP32-S3R8 (QFN-56 pinout, DS Table 2-1)
and AXP2101 (AXP Table 4-1 p.7-8) are kept from the committed HW_Watch.kicad_sym.  Footprints that KiCad does not ship are drawn from the
package drawings: MAX86141 WLP-20 (MAX p.11 pin map, p.1 "5 x 4, 0.4mm ball pitch"), SFH 7016 (SFH p.13-14),
VEMD8080 (VEMD p.4).  MAX30208 LGA-10 is PRELIMINARY (land pattern 90-100101 not available offline).
usage: python3 tools/libgen.py"""
import os, re, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.join(HERE, '..', 'hardware')
NS = uuid.UUID('6a1f2c3e-0b5d-4c1e-9a7f-a1e0000a7c01')
def U(*k): return str(uuid.uuid5(NS, '/'.join(map(str, k))))
G = 2.54

def eff(hide=False, size=1.27, just=None):
    s = '(effects (font (size %s %s))' % (size, size)
    if just: s += ' (justify %s)' % just
    return s + (' (hide yes)' if hide else '') + ')'

def symbol(name, ref, value, fp, desc, left=(), right=(), top=(), bottom=(), width=None, kw=''):
    """pins: lists of (number, name, etype) per side, top->bottom / left->right; None = gap; extra numbers 'a|b|c' = stacked pins"""
    n = max(len(left), len(right), 1)
    w = width or max(10.16, G * 2 * round((max([len(p[1]) for p in left + right if p] + [4]) * 1.27 * 2 + 5) / (2 * G)))
    w = max(w, G * (max(len(top), len(bottom)) + 1))
    h = G * (n + 1)
    top_y, x0 = h / 2, w / 2
    top_y = G * round(top_y / G); x0 = G * round(x0 / G)
    body = ['\t\t(symbol "%s_0_1"\n\t\t\t(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type default)) (fill (type background)))\n\t\t)'
            % (name, -x0, top_y, x0, -top_y)]
    pins = []
    def pin(num, nm, et, x, y, a, hidden=False):
        pins.append('\t\t\t(pin %s line (at %s %s %d) (length 2.54)%s (name "%s" %s) (number "%s" %s))'
                    % (et, round(x, 2), round(y, 2), a, ' (hide yes)' if hidden else '', nm, eff(size=1.0), num, eff(size=1.0)))
    def side(lst, xy, a):
        for i, p in enumerate(lst):
            if not p: continue
            nums = p[0].split('|')
            x, y = xy(i)
            for k, num in enumerate(nums):
                pin(num, p[1], p[2] if k == 0 else 'passive', x, y, a, hidden=k > 0)
    side(left, lambda i: (-x0 - G, top_y - G * (i + 1)), 0)
    side(right, lambda i: (x0 + G, top_y - G * (i + 1)), 180)
    side(top, lambda i: (-x0 + G * (i + 1), top_y + G), 270)
    side(bottom, lambda i: (-x0 + G * (i + 1), -top_y - G), 90)
    props = [('Reference', ref, (-x0, top_y + 1.5), False, 'left'), ('Value', value, (-x0, -top_y - 1.5), False, 'left'),
             ('Footprint', fp, (0, 0), True, None), ('Datasheet', '~', (0, 0), True, None), ('Description', desc, (0, 0), True, None),
             ('ki_keywords', kw, (0, 0), True, None)]
    P = ''.join('\t\t(property "%s" "%s" (at %s %s 0) %s)\n' % (k, v, round(xy[0], 2), round(xy[1], 2), eff(hid, just=j)) for k, v, xy, hid, j in props)
    return ('\t(symbol "%s" (exclude_from_sim no) (in_bom yes) (on_board yes)\n%s%s\n\t\t(symbol "%s_1_1"\n%s\n\t\t)\n\t)'
            % (name, P, '\n'.join(body), name, '\n'.join(pins)))

def renumber(s, mapping):
    """Renumber the pins of a symbol block; a pin mapped to None is removed."""
    out, i = [], 0
    while True:
        j = s.find('(pin ', i)
        if j < 0: out.append(s[i:]); break
        d = 0
        for e in range(j, len(s)):
            if s[e] == '(': d += 1
            elif s[e] == ')':
                d -= 1
                if d == 0: break
        pin = s[j:e + 1]
        new = mapping[re.search(r'\(number "([^"]+)"', pin).group(1)]
        out.append(s[i:j])
        if new is not None: out.append(re.sub(r'\(number "[^"]+"', '(number "%s"' % new, pin))
        i = e + 1
    return ''.join(out)

def extract(path, name, newname=None, value=None, fp=None):
    t = open(path, encoding='utf-8').read()
    i = t.index('\n\t(symbol "%s"' % name) + 1
    d = 0
    for j in range(i, len(t)):
        if t[j] == '(': d += 1
        elif t[j] == ')':
            d -= 1
            if d == 0: s = t[i:j + 1]; break
    if newname:
        s = s.replace('(symbol "%s"' % name, '(symbol "%s"' % newname).replace('(symbol "%s_' % name, '(symbol "%s_' % newname)
    if value: s = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % value, s, 1)
    if fp: s = re.sub(r'\(property "Footprint" "[^"]*"', '(property "Footprint" "%s"' % fp, s, 1)
    return s

PW, PI, IO, IN, OUT, PS, OC, NC = 'power_in', 'power_out', 'bidirectional', 'input', 'output', 'passive', 'open_collector', 'no_connect'
SYMS = [
 extract(os.path.join(HW, 'HW_Watch.kicad_sym'), 'ESP32-S3R8', 'ESP32-S3R8', 'ESP32-S3R8',
         'Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm_ThermalVias'),
 extract(os.path.join(HW, 'HW_Watch.kicad_sym'), 'AXP2101', 'AXP2101', 'AXP2101',
         'Package_DFN_QFN:QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm_ThermalVias'),
 # MAX86141 pin description MAX p.12, bump map p.11 (MAX86141: D4 = PD2_IN)
 symbol('MAX86141', 'U', 'MAX86141ENP+', 'HW_Watch:MAX86141_WLP-20_2.05x1.85mm_P0.4mm',
        'Optical PPG AFE, 3 LED drivers, 2 x 19-bit PD channels, SPI 1.8 V (MAX86140/MAX86141 datasheet)',
        left=[('A1', 'VLED', PW), None, ('D1', 'LED1_DRV', PS), ('C1', 'LED2_DRV', PS), ('B1', 'LED3_DRV', PS), None,
              ('D5', 'PD1_IN', PS), ('D4', 'PD2_IN', PS), ('C5', 'PD_GND', PS), None, ('B5', 'VREF', PS)],
        right=[('D2', 'VDD_ANA', PW), ('C2', 'VDD_DIG', PW), None, ('A2', 'SCLK', IN), ('A4', 'SDI', IN), ('A3', 'SDO', OUT),
               ('A5', 'CSB', IN), ('B2', 'INT', OC), ('B3', 'GPIO1', IO), ('B4', 'GPIO2', IO)],
        bottom=[('C4', 'GND_ANA', PW), ('C3', 'GND_DIG', PW), ('D3', 'PGND', PW)], width=22.86, kw='PPG SpO2 heart rate AFE'),
 # MAX30208 pin description MAX30208 p.6
 symbol('MAX30208', 'U', 'MAX30208CLB+', 'HW_Watch:MAX30208_LGA-10_2x2mm_PRELIM',
        '0.1 C I2C digital temperature sensor, thin LGA-10 2x2 (MAX30208 datasheet)',
        left=[('1|2|3', 'VDD', PW), None, ('8', 'SDA', IO), ('9', 'SCL', IN)],
        right=[('10', 'GPIO0', IO), ('7', 'GPIO1', IO)], bottom=[('4|5|6', 'GND', PW)], width=15.24, kw='temperature skin'),
 # BMI270 pin-out BMI Table 22 p.135
 symbol('BMI270', 'U', 'BMI270', 'Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm',
        '6-axis IMU, wearable features, I2C/SPI, LGA-14 2.5x3 (BMI270 datasheet)',
        left=[('8', 'VDD', PW), ('5', 'VDDIO', PW), None, ('14', 'SDx', IO), ('13', 'SCx', IN), ('12', 'CSB', IN), ('1', 'SDO', PS)],
        right=[('4', 'INT1', IO), ('9', 'INT2', IO), None, ('2', 'ASDx', IO), ('3', 'ASCx', IO), ('10', 'OCSB', IN), ('11', 'OSDO', OUT)],
        bottom=[('7', 'GND', PW), ('6', 'GNDIO', PW)], width=17.78, kw='IMU accelerometer gyroscope'),
 # TPS61240 pin functions TPS p.3 (WSON: 1 GND, 2 VOUT, 3 FB, 4 EN, 5 L, 6 VIN; thermal pad = GND)
 symbol('TPS61240', 'U', 'TPS61240DRV', 'Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm',
        '5 V fixed boost converter, 450 mA, 3.5 MHz, WSON-6 2x2 (TPS61240 datasheet)',
        left=[('6', 'VIN', PW), ('5', 'L', PS), ('4', 'EN', IN)], right=[('2', 'VOUT', PI), ('3', 'FB', IN)],
        bottom=[('1|7', 'GND', PW)], width=12.7, kw='boost 5V'),
 # VEMD8080 pinning VEMD p.4: pin 5 anode, pins 1-4, 6-8 cathode
 symbol('VEMD8080', 'D', 'VEMD8080', 'HW_Watch:VEMD8080_4.8x2.5mm',
        'Silicon PIN photodiode 4.8 x 2.5 mm, large area, for PPG (VEMD8080 datasheet)',
        left=[('1|2|3|4|6|7|8', 'K', PS)], right=[('5', 'A', PS)], width=7.62, kw='photodiode PPG'),
 # PCF85063ATT TSSOP-8: NXP datasheet Table 3 (no CLKOE, no n.c.); drawn like the frozen PCF85063ATL symbol
 renumber(extract(os.path.join(HERE, 'stock_symbols', 'Timer_RTC.kicad_sym'), 'PCF85063ATL', 'PCF85063ATT', 'PCF85063ATT', 'Package_SO:TSSOP-8_3x3mm_P0.65mm'),
          {'1': '1', '2': '2', '3': None, '4': '3', '5': '4', '6': '5', '7': '6', '8': None, '9': '7', '10': '8'}),
 # 2450AT18D0100 Johanson Ver. 4.4 p.1, function 1: 1 feed, 2-4 ground
 symbol('2450AT18D', 'AE', '2450AT18D0100E', 'HW_Watch:Johanson_2450AT18D_3.2x1.6mm',
        '2.45 GHz edge-mount ceramic antenna, EIA 1206 (Johanson 2450AT18D0100)',
        left=[('1', 'FEED', PS)], right=[('2', 'GND', PS), ('3', 'GND', PS), ('4', 'GND', PS)], width=12.7, kw='antenna'),
 # SFH 7016 SFH p.13: 1 cathode IR, 2 + 5 common anode, 3 cathode green, 4 cathode red, 6 NC
 symbol('SFH7016', 'D', 'SFH 7016', 'HW_Watch:SFH7016_1.85x1.65mm',
        'Multi-chip LED green 530 nm / red 655 nm / IR 940 nm, common anode (OSRAM SFH 7016 datasheet v1.5)',
        left=[('2|5', 'A', PS)], right=[('3', 'K_GREEN', PS), ('4', 'K_RED', PS), ('1', 'K_IR', PS), ('6', 'NC', NC)], width=12.7, kw='LED PPG'),
]
lib = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "libgen.py")\n\t(generator_version "9.0")\n' + '\n'.join(SYMS) + '\n)\n'
open(os.path.join(HW, 'HW_Watch.kicad_sym'), 'w', encoding='utf-8').write(lib)

# ---------------------------------------------------------------- footprints
os.makedirs(os.path.join(HW, 'HW_Watch.pretty'), exist_ok=True)
def fp(name, descr, pads, body, extra='', courtyard=0.25, attr='smd', model=None, paste_margin=None):
    """pads: [(num, shape, x, y, w, h)]; body: (w, h) of the package outline"""
    bw, bh = body
    xs = [p[2] - p[4] / 2 for p in pads] + [p[2] + p[4] / 2 for p in pads] + [-bw / 2, bw / 2]
    ys = [p[3] - p[5] / 2 for p in pads] + [p[3] + p[5] / 2 for p in pads] + [-bh / 2, bh / 2]
    cx0, cx1, cy0, cy1 = min(xs) - courtyard, max(xs) + courtyard, min(ys) - courtyard, max(ys) + courtyard
    r = lambda v: round(v, 3)
    L = ['(footprint "%s"\n\t(version 20241229)\n\t(generator "libgen.py")\n\t(layer "F.Cu")\n\t(descr "%s")\n\t(attr %s)' % (name, descr, attr),
         '\t(property "Reference" "REF**" (at 0 %s 0) (layer "F.SilkS") (uuid "%s") (effects (font (size 0.8 0.8) (thickness 0.12))))' % (r(cy0 - 0.8), U(name, 'ref')),
         '\t(property "Value" "%s" (at 0 %s 0) (layer "F.Fab") (uuid "%s") (effects (font (size 0.8 0.8) (thickness 0.12))))' % (name, r(cy1 + 0.8), U(name, 'val')),
         '\t(fp_rect (start %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "%s"))' % (r(-bw / 2), r(-bh / 2), r(bw / 2), r(bh / 2), U(name, 'fab')),
         '\t(fp_rect (start %s %s) (end %s %s) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "%s"))' % (r(cx0), r(cy0), r(cx1), r(cy1), U(name, 'crt')),
         '\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab") (uuid "%s") (effects (font (size 0.4 0.4) (thickness 0.06))))' % U(name, 'fabref')]
    for i, (num, shape, x, y, w, h) in enumerate(pads):
        extra_pad = (' (roundrect_rratio 0.25)' if shape == 'roundrect' else '') + (' (solder_paste_margin %s)' % paste_margin if paste_margin is not None else '')
        L.append('\t(pad "%s" smd %s (at %s %s) (size %s %s) (layers "F.Cu" "F.Mask" "F.Paste")%s (uuid "%s"))'
                 % (num, shape, r(x), r(y), r(w), r(h), extra_pad, U(name, 'pad', i)))
    L.append(extra)
    L.append(')')
    open(os.path.join(HW, 'HW_Watch.pretty', name + '.kicad_mod'), 'w').write('\n'.join(l for l in L if l) + '\n')

def silk_dot(name, x, y):
    return '\t(fp_circle (center %s %s) (end %s %s) (stroke (width 0.1) (type solid)) (fill yes) (layer "F.SilkS") (uuid "%s"))' % (x, y, round(x + 0.08, 3), y, U(name, 'dot'))

# MAX86141: bump map MAX p.11 (top view, bump side down): rows A-D top->bottom, columns 1-5 left->right, 0.4 mm pitch,
# body 2.048 x 1.848 mm (MAX p.1). NSMD pad 0.25 mm for 0.4 mm pitch WLP: ASSUME (ADI AN1891, not in the offline set).
n = 'MAX86141_WLP-20_2.05x1.85mm_P0.4mm'
fp(n, 'MAX86140/MAX86141 20-bump WLP 2.048x1.848 mm, 0.4 mm pitch (pad size ASSUME per AN1891, check 21-100134)',
   [('%s%d' % (row, col), 'circle', (col - 3) * 0.4, (i - 1.5) * 0.4, 0.25, 0.25) for i, row in enumerate('ABCD') for col in range(1, 6)],
   (2.048, 1.848), silk_dot(n, -1.25, -1.1))
# MAX30208 thin LGA-10 2x2: pad positions read from the pin-configuration drawing MAX30208 p.6 (not dimensioned) - PRELIMINARY
n = 'MAX30208_LGA-10_2x2mm_PRELIM'
big = [(str(k), 'rect', -0.7, y, 0.45, 0.45) for k, y in zip('123', (-0.65, 0, 0.65))] + [(str(k), 'rect', 0.7, y, 0.45, 0.45) for k, y in zip('654', (-0.65, 0, 0.65))]
small = [(str(k), 'rect', 0, y, 0.2, 0.3) for k, y in zip(('7', '8', '9', '10'), (-0.72, -0.24, 0.24, 0.72))]
fp(n, 'MAX30208 thin LGA-10 2x2 mm - PRELIMINARY: replace with ADI land pattern 90-100101 before ordering PCBs', big + small, (2.0, 2.0), silk_dot(n, -1.2, -1.2))
# VEMD8080: footprint VEMD p.4: pads 0.54 x 0.55, x pitch 1.31/1.38/1.31, rows 2.38 apart; top view: bottom row 1-4, top row 8-5
n = 'VEMD8080_4.8x2.5mm'
xs = [-2.0, -0.69, 0.69, 2.0]
fp(n, 'Vishay VEMD8080 PIN photodiode 4.8x2.5 mm (datasheet p.4 footprint)',
   [(str(i + 1), 'rect', x, 1.19, 0.54, 0.55) for i, x in enumerate(xs)] + [(str(8 - i), 'rect', x, -1.19, 0.54, 0.55) for i, x in enumerate(xs)],
   (4.8, 2.5), silk_dot(n, -2.6, 1.6))
# SFH 7016: recommended footprint SFH p.14: 6 pads 0.4 x 0.4, gaps 0.25 (x) / 0.75 (y), stencil 0.3 x 0.3; top view SFH p.13: 5 3 1 / 6 4 2
n = 'SFH7016_1.85x1.65mm'
fp(n, 'OSRAM SFH 7016 multi-chip LED 1.85x1.65 mm (datasheet p.13 pinning, p.14 recommended footprint; stencil 120 um)',
   [('5', 'rect', -0.65, -0.575, 0.4, 0.4), ('3', 'rect', 0, -0.575, 0.4, 0.4), ('1', 'rect', 0.65, -0.575, 0.4, 0.4),
    ('6', 'rect', -0.65, 0.575, 0.4, 0.4), ('4', 'rect', 0, 0.575, 0.4, 0.4), ('2', 'rect', 0.65, 0.575, 0.4, 0.4)],
   (1.85, 1.65), silk_dot(n, 1.2, -1.0), paste_margin=-0.05)
# Johanson 2450AT18D0100 land pattern p.2: pads 1.0 x 0.6, 2.0 gap in x, 0.7 gap in y; terminals p.1, top view 4 3 / 1 2
n = 'Johanson_2450AT18D_3.2x1.6mm'
fp(n, 'Johanson 2450AT18D0100 2.45 GHz ceramic antenna, keep copper out per datasheet p.2',
   [('1', 'rect', -1.5, 0.65, 1.0, 0.6), ('2', 'rect', 1.5, 0.65, 1.0, 0.6), ('3', 'rect', 1.5, -0.65, 1.0, 0.6), ('4', 'rect', -1.5, -0.65, 1.0, 0.6)],
   (3.2, 1.6), silk_dot(n, -2.3, 1.2))
# HDGC 0.3K-HX-31PWB drawing p.1 (recommended layout) and p.2 (n = 31: B 8.40, C 9.00): odd pins bottom row 0.67 long, even pins top row 0.50 long, 2.48 between rows, pads 0.20 wide (dimension in brackets),
# pegs 0.35 x 1.00, 0.80 outside the last pin, 0.10 above the lower edge of the bottom row
n = 'FPC_HDGC_0.3K-HX-31PWB'
fp(n, 'HDGC 0.3K-HX-31PWB, 0.3 mm pitch, 31 pin FPC connector, top contact',
   [(str(i), 'rect', round(-4.5 + 0.3 * (i - 1), 2), (1.49 if i % 2 else -1.575), 0.2, (0.67 if i % 2 else 0.5)) for i in range(1, 32)] + [('MP', 'rect', -5.3, 1.225, 0.35, 1.0), ('MP', 'rect', 5.3, 1.225, 0.35, 1.0)],
   (10.95, 3.3), silk_dot(n, -4.5, 2.5))
# coin vibration motor (10 mm, flying leads soldered to two pads): ASSUME generic
n = 'Motor_Pads_2x1.5mm'
fp(n, 'Two solder pads for a coin vibration motor with wire leads (1027 type)', [('1', 'rect', -1.25, 0, 1.5, 1.5), ('2', 'rect', 1.25, 0, 1.5, 1.5)], (4.0, 1.5))
print('HW_Watch:', len(SYMS), 'symbols,', len(os.listdir(os.path.join(HW, 'HW_Watch.pretty'))), 'footprints')
