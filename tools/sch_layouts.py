# Hand layouts of every schematic sheet (exec'd inside gen_sch.py: uses Sheet, sym, D, BYREF, RAILS, DIR, G, r2 ...).
# Coordinates are in grid units (1 = 2.54 mm). Local connections are real wires: decoupling caps on the pin they serve,
# crystal / RF / USB chains, LED + resistor, MOSFET drivers, regulators with their in/out parts. Labels only carry
# signals between blocks or sheets. Parts not placed here are put in a fallback frame by gen_sch.py.
import math as _m

def g(v): return r2(v * G)
OFF = [0, 0]
def gp(x, y): return (g(x + OFF[0]), g(y + OFF[1]))
def _p(a): return a if isinstance(a[0], str) else gp(*a)
def W(S, *pts): return S.W(*[_p(a) for a in pts])
def pw(S, net, x, y, d='up'): S.small = True; S.pwr(net, gp(x, y), DIR[d])
def lb(S, net, x, y, d='right'): S.lab(net, gp(x, y), DIR[d])
def T(S, s, x, y, size=1.25, bold=False): S.text(s, gp(x, y), size, bold)
def F(S, title, x0, y0, x1, y1): S.frame(title, g(x0 + OFF[0]), g(y0 + OFF[1]), g(x1 + OFF[0]), g(y1 + OFF[1]))
def gpin(S, ref, num):
    x, y = S.pin(ref, num); return (round(x / G - OFF[0], 2), round(y / G - OFF[1], 2))

def orient(ref, inpin, d):
    """rotation (0/90/180/270) of a 2-pin symbol so that the other pin lies in direction d from inpin"""
    s = sym(D.P[BYREF[ref]['typ']][0])
    pins = {q['num']: q for q in s['pins']}
    a = pins[inpin]
    other = next(k for k, q in pins.items() if (q['x'], q['y']) != (a['x'], a['y']))
    b = pins[other]
    dx, dy = b['x'] - a['x'], b['y'] - a['y']
    want = DIR[d]
    for rot in (0, 90, 180, 270):
        c, s_ = round(_m.cos(_m.radians(rot))), round(_m.sin(_m.radians(rot)))
        x, y = dx * c - dy * s_, -(dx * s_ + dy * c)
        if (x > 0) - (x < 0) == want[0] and (y > 0) - (y < 0) == want[1]: return rot, other
    raise ValueError((ref, inpin, d))

def part2(S, ref, x, y, inpin='1', d='right', text=None):
    """2-pin part with pin `inpin` at (x, y), body towards d; returns the other pin (grid units)"""
    rot, other = orient(ref, inpin, d)
    S.place(ref, gp(x, y), rot, pin=inpin, text=text)
    S.done.add((ref, inpin))
    return gpin(S, ref, other)

def cap(S, ref, x, y, text=None):
    """hanging part: pin 1 at (x, y), body below; the free pin is finished by gen_sch (GND symbol / label)"""
    return part2(S, ref, x, y, '1', 'down', text)

def stair(S, ref, side, rows):
    """pins of one side of an IC: rows {pin: [items]} drawn outwards as a staircase so hanging parts never cross the
    wires of the pins below. items: ('C', ref) hanging cap | ('S', ref, inpin) inline part | ('P', net) power symbol |
    ('L', net) label | ('G',) wire down to GND | ('X', extent) pin drawn elsewhere"""
    sgn = -1 if side == 'l' else 1
    out = 'left' if sgn < 0 else 'right'
    s = sym(D.P[BYREF[ref]['typ']][0])
    a_side = 0 if side == 'l' else 180
    pins = []
    for q in s['pins']:
        if q['hide']: continue
        if S._dir(ref, q['a']) != DIR[out]: continue
        pins.append((q['num'], gpin(S, ref, q['num'])))
    ext = {}
    def lw(net): return 2.0 + 0.55 * len(net)
    for num, (px, py) in sorted(pins, key=lambda e: -e[1][1]):
        y = int(round(py)); net = BYREF[ref]['pins'].get(num)
        items = rows.get(num)
        if not items:
            ext[y] = 0.5 if net is None else 1 + (4.5 if net in RAILS else lw(net)); continue
        if items[0][0] == 'X': ext[y] = items[0][1]; continue
        # measure with stub 0
        cur, hang = 0, []
        for it in items:
            if it[0] == 'C': hang.append(cur); cur += 4
            elif it[0] == 'S':
                rot, other = orient(it[1], it[2], out); sp = sym(D.P[BYREF[it[1]]['typ']][0])
                pa = next(q for q in sp['pins'] if q['num'] == it[2]); pb = next(q for q in sp['pins'] if q['num'] == other)
                cur += round(abs(pa['x'] - pb['x']) + abs(pa['y'] - pb['y'])) / G + 1
            elif it[0] == 'G': hang.append(cur); cur += 1
        below = max([ext.get(y + k, 0) for k in range(1, 7)] + [0])
        s0 = 1
        for o in hang: s0 = max(s0, below + 2 - o)
        s0 = _m.ceil(s0)
        last = (px, py); cur = s0
        for it in items:
            x = px + sgn * cur
            if it[0] == 'C':
                W(S, last, (x, py)); cap(S, it[1], x, py, text='left' if sgn < 0 else None); last = (x, py); cur += 4
            elif it[0] == 'S':
                W(S, last, (x, py)); o = part2(S, it[1], x, py, it[2], out); last = o; cur = abs(o[0] - px) + 1
            elif it[0] == 'P':
                W(S, last, (x, py)); pw(S, it[1], x, py, out); cur += 1 + lw(it[1])
            elif it[0] == 'L':
                W(S, last, (x, py)); lb(S, it[1], x, py, out); cur += lw(it[1])
            elif it[0] == 'G':
                W(S, last, (x, py), (x, py + 2)); pw(S, 'GND', x, py + 2, 'down'); cur += 2
        ext[y] = cur

# ============================================================== main board
def sheet_main_power(S):
    T(S, 'USB-C → ESD → AXP2101 (sạc LiPo + DCDC1 3.3 V). Shunt + test point để đo dòng: pin (R111) và 3V3 (R112).', 5, 4.6)
    # ---------------- USB-C + ESD
    F(S, 'USB-C + ESD', 4, 9, 50, 40)
    S.place('J101', gp(18, 18), pin='A4')
    W(S, ('J101', 'A4'), (24, 18)); W(S, (24, 18), (24, 14))
    S.place('TP101', gp(21, 18), pin='1')
    W(S, ('J101', 'A7'), (19, 23), (19, 24), ('J101', 'B7'))
    W(S, (19, 23), (24, 23), (24, 29))
    S.place('U101', gp(26, 29), pin='1')
    W(S, (24, 29), ('U101', '1'))
    W(S, ('J101', 'A6'), (20, 25), (20, 26), ('J101', 'B6'))
    W(S, (20, 26), (22, 26), (22, 30), ('U101', '3'))
    W(S, ('U101', '5'), (28, 26)); pw(S, 'VBUS', 28, 26, 'up')
    W(S, ('U101', '6'), (34, 29)); o = part2(S, 'R103', 34, 29, '1', 'right'); W(S, o, (39, 29)); lb(S, 'USB_DN_MCU', 39, 29)
    W(S, ('U101', '4'), (31, 30), (31, 32), (35, 32)); o = part2(S, 'R104', 35, 32, '1', 'right'); W(S, o, (39, 32)); lb(S, 'USB_DP_MCU', 39, 32)
    W(S, ('J101', 'A5'), (46, 20)); cap(S, 'R101', 46, 20)
    W(S, ('J101', 'B5'), (44, 21)); cap(S, 'R102', 44, 21, text='left')
    T(S, 'Rd 5.1k: thiết bị sink (USB-C)', 36, 36)
    # ---------------- AXP2101
    F(S, 'PMIC AXP2101 + pin + shunt đo dòng', 52, 9, 146, 78)
    S.place('U102', gp(112, 36), text='below')
    # VBUS from the connector: one wire along the top of the sheet
    W(S, (24, 14), (104, 14), (104, 25), ('U102', '37')); cap(S, 'C101', 80, 14); pw(S, 'VBUS', 60, 14, 'up')
    W(S, ('U102', '36'), (102, 26), (102, 17), (85, 17)); cap(S, 'C102', 85, 17); pw(S, 'VMID', 94, 17, 'up')
    W(S, ('U102', '34'), (100, 27), (100, 21), (88, 21)); cap(S, 'C103', 97, 21); cap(S, 'C104', 92, 21); pw(S, 'VSYS', 88, 21, 'up')
    stair(S, 'U102', 'l', {
        '37': [('X', 1)], '36': [('X', 3)], '34': [('X', 5)],
        '33': [('C', 'C105'), ('P', 'VBAT')],
        '31': [('C', 'RT101')],
        '2': [('C', 'C106')],
        '17': [('C', 'C110'), ('P', 'VSYS')],
    })
    # right side: DCDC1 -> L101 -> 3V3_PMIC -> shunt R112 -> +3V3
    W(S, ('U102', '23'), (120, 25), (120, 16), (123, 16)); cap(S, 'C109', 123, 16); pw(S, 'VSYS', 120, 16, 'up')
    W(S, ('U102', '22'), (121, 26)); o = part2(S, 'L101', 121, 26, '1', 'right')
    W(S, o, (127, 26)); W(S, ('U102', '21'), (125, 27), (125, 26))
    S.place('TP104', gp(126, 26), pin='1'); cap(S, 'C111', 127, 26)
    W(S, (127, 26), (129, 26)); o = part2(S, 'R112', 129, 26, '1', 'right')
    W(S, o, (136, 26)); S.place('TP105', gp(134, 26), pin='1'); pw(S, '+3V3', 136, 26, 'right')
    T(S, 'DCDC1 3.3 V / 2 A, FB1 lấy sau cuộn', 123, 31)
    # chains of the dense left pins, drawn where there is room (connected by local labels)
    W(S, (58, 40), (60, 40)); lb(S, 'AXP_SW', 58, 40, 'left'); o = part2(S, 'L102', 60, 40, '1', 'right'); W(S, o, (65, 40))
    o = part2(S, 'R105', 65, 40, '1', 'right'); W(S, o, (70, 40)); pw(S, 'VSYS', 70, 40, 'right')
    pw(S, 'VMID', 81, 44, 'up'); cap(S, 'R126', 81, 44); T(S, 'R126: VMID-VSYS, không lắp', 84, 45)
    T(S, 'SW (DCDC5) nối như bo Waveshare', 56, 37)
    W(S, (58, 45), (60, 45)); lb(S, 'CHGLED', 58, 45, 'left'); o = part2(S, 'D101', 60, 45, '1', 'right'); W(S, o, (65, 45))
    o = part2(S, 'R110', 65, 45, '2', 'right'); W(S, o, (70, 45)); pw(S, 'VSYS', 70, 45, 'right')
    T(S, 'LED sạc (AXP lái CHGLED)', 56, 42.5)
    W(S, (58, 53), (62, 53)); lb(S, 'PWRON', 58, 53, 'left'); cap(S, 'C112', 60, 53); o = part2(S, 'R109', 62, 53, '1', 'right'); W(S, o, (66, 53))
    o = part2(S, 'SW101', 66, 53, '1', 'right'); W(S, o, (71, 53), (71, 55)); pw(S, 'GND', 71, 55, 'down')
    T(S, 'Nút nguồn: nhấn = bật, giữ = tắt', 56, 49)
    T(S, 'I = V(TP104-TP105) / 0.1 Ω', 126, 22)
    W(S, ('U102', '28'), (126, 40)); cap(S, 'C107', 126, 40)
    W(S, ('U102', '27'), (123, 41)); cap(S, 'C108', 123, 41)
    W(S, ('U102', '3'), (120, 42), (120, 43), ('U102', '41')); W(S, (120, 43), (120, 46)); pw(S, 'GND', 120, 46, 'down')
    # battery connector + shunt
    S.place('J102', gp(62, 68), pin='1', mirror=True)
    W(S, ('J102', '1'), (65, 68)); S.place('TP102', gp(63, 68), pin='1')
    o = part2(S, 'R111', 65, 68, '1', 'right'); W(S, o, (75, 68)); S.place('TP103', gp(71, 68), pin='1'); pw(S, 'VBAT', 75, 68, 'up')
    W(S, ('J102', '2'), (63, 69), (63, 71)); pw(S, 'GND', 63, 71, 'down')
    T(S, 'Pin LiPo 1S (có mạch bảo vệ), chân 1 = +', 55, 61)
    T(S, 'I_pin = V(TP102-TP103) / 0.05 Ω', 55, 62.6)
    S.place('TP106', gp(104, 64)); S.place('TP107', gp(110, 64))
    T(S, 'Đo VSYS / GND', 102, 60)
    # I2C / IRQ pull-ups
    pw(S, '+3V3', 80, 66, 'up'); W(S, (80, 66), (92, 66))
    cap(S, 'R107', 84, 66); cap(S, 'R108', 88, 66); cap(S, 'R106', 92, 66)
    T(S, 'Kéo lên I2C 2.2k (AXP p.9) + IRQ 4.7k', 78, 61)
    T(S, 'PWROK → CHIP_PU: ESP32 chờ nguồn ổn định', 96, 54)
FALLBACK = {}
FALLBACK['power'] = (g(100), g(82))

def sheet_main_mcu(S):
    T(S, 'ESP32-S3R8: decoupling theo HDG Fig.1 p.5, thạch anh 40 MHz, flash QSPI 16 MB, mạch phối hợp RF + ăng-ten gốm, UART0.', 5, 4.6)
    F(S, 'ESP32-S3R8 + flash + thạch anh + RF + UART0', 4, 26, 130, 84)
    S.place('U104', gp(70, 58), text='right')
    # top supply pins: left-going rails (VDDA, VDD3P3), right-going rails (RTC, VDD_SPI, CPU)
    W(S, ('U104', '55'), (68, 40), (50, 40)); cap(S, 'C119', 56, 40); cap(S, 'C118', 52, 40); pw(S, '+3V3', 50, 40, 'left')
    W(S, ('U104', '2'), (69, 37), (34, 37)); cap(S, 'C117', 45, 37); cap(S, 'C116', 41, 37); cap(S, 'C115', 37, 37)
    o = part2(S, 'L104', 34, 37, '2', 'left'); W(S, o, (29, 37)); pw(S, '+3V3', 29, 37, 'left')
    T(S, 'VDD3P3 (PA RF): lọc LC 2.0 nH', 30, 33); S.flag(gp(56, 37), (1, 0)); flagged.add('VDD3P3')
    W(S, ('U104', '46'), (72, 40), (77, 40)); cap(S, 'C120', 75, 40); pw(S, '+3V3', 77, 40, 'right')
    W(S, ('U104', '29'), (71, 38), (90, 38)); cap(S, 'C122', 83, 38); cap(S, 'C123', 87, 38); pw(S, 'VDD_SPI', 90, 38, 'right')
    W(S, ('U104', '20'), (70, 35), (100, 35)); cap(S, 'C121', 98, 35); pw(S, '+3V3', 100, 35, 'right')
    T(S, 'VDD_SPI = 3.3 V (GPIO45 = 0 lúc reset) cấp flash + PSRAM', 80, 31)
    # crystal
    W(S, ('U104', '54'), (57, 69)); o = part2(S, 'L105', 57, 69, '1', 'down'); W(S, o, (57, 75))
    S.place('Y101', gp(57, 75), pin='1')
    W(S, ('U104', '53'), (60, 70), ('Y101', '3'))
    W(S, (57, 75), (55, 75)); cap(S, 'C125', 55, 75, text='left')
    W(S, ('Y101', '3'), (62, 75)); cap(S, 'C126', 62, 75)
    T(S, '40 MHz, CL 15 pF ≈ 22·22/44 + 4 pF', 44, 81)
    # flash (SPI0 pins by label, power wired)
    S.place('U105', gp(116, 52), text='below')
    W(S, ('U105', '8'), (116, 45), (120, 45)); cap(S, 'C127', 120, 45); pw(S, 'VDD_SPI', 116, 45, 'up')
    # RF chain
    W(S, ('U104', '1'), (80, 70), (80, 73), (82, 73)); cap(S, 'C128', 82, 73)
    o = part2(S, 'L106', 83, 73, '1', 'right'); W(S, (82, 73), (83, 73))
    W(S, o, (95, 73)); cap(S, 'C129', 88, 73); cap(S, 'C130', 92, 73)
    o = part2(S, 'R117', 95, 73, '1', 'right'); W(S, o, (104, 73)); cap(S, 'C131', 100, 73)
    S.place('AE101', gp(104, 73), pin='1')
    T(S, 'Phối hợp phía chip (HDG Table 6) | mạch π phía ăng-ten (DNP, tune bằng VNA)', 80, 78)
    # UART0 header
    W(S, ('U104', '49'), (89, 65)); o = part2(S, 'R118', 89, 65, '1', 'right', text='below'); W(S, o, (96, 65))
    S.place('J103', gp(96, 65), pin='2')
    W(S, ('U104', '50'), ('J103', '3'))
    W(S, ('J103', '1'), (95, 64)); pw(S, 'GND', 95, 64, 'left')
    # reset / boot
    F(S, 'Reset (CHIP_PU) + Boot (GPIO0)', 4, 89, 70, 108)
    pw(S, '+3V3', 14, 93, 'up'); cap(S, 'R116', 14, 93); W(S, (14, 96), (20, 96)); W(S, (14, 96), (10, 96)); lb(S, 'BOOT', 10, 96, 'left')
    o = part2(S, 'SW103', 20, 96, '1', 'right'); W(S, o, (24, 96), (24, 98)); pw(S, 'GND', 24, 98, 'down')
    pw(S, '+3V3', 40, 93, 'up'); cap(S, 'R115', 40, 93); W(S, (40, 96), (48, 96)); W(S, (40, 96), (36, 96)); lb(S, 'CHIP_PU', 36, 96, 'left')
    cap(S, 'C124', 44, 96)
    o = part2(S, 'SW102', 48, 96, '1', 'right'); W(S, o, (52, 96), (52, 98)); pw(S, 'GND', 52, 98, 'down')
    T(S, 'RC 10k/1µF: CHIP_PU lên sau nguồn ≥ 50 µs (HDG §1.3.3)', 30, 103)
    T(S, 'Giữ BOOT + nhấn RESET = chế độ nạp', 6, 103)
FALLBACK['mcu'] = (g(80), g(90))

def sheet_main_periph(S):
    T(S, 'Màn hình AMOLED (FPC 31P như Waveshare 1.75C), IMU BMI270, RTC PCF85063A, boost 5 V cho LED PPG, FPC 16P sang bo cảm biến.', 5, 4.6)
    # ---------------- display FPC
    F(S, 'FPC màn hình AMOLED + cảm ứng', 4, 9, 38, 56)
    S.place('J104', gp(30, 15), pin='1')
    for n, y in (('21', 35), ('22', 36), ('23', 37), ('24', 38)): W(S, ('J104', n), (27, y))
    W(S, (27, 35), (27, 38)); W(S, (27, 36), (14, 36)); cap(S, 'C132', 22, 36); cap(S, 'C133', 18, 36); pw(S, '+3V3', 14, 36, 'up')
    T(S, 'QSPI + I2C chung', 6, 52)
    F(S, 'Điểm đo bus (bring-up)', 82, 60, 112, 76)
    for i, r_ in enumerate(('TP110', 'TP111', 'TP112', 'TP113', 'TP114')): S.place(r_, gp(86 + 5 * i, 64), pin='1')
    # ---------------- BMI270
    F(S, 'IMU BMI270 + RTC PCF85063A', 40, 12, 80, 56)
    S.place('U106', gp(60, 25))
    W(S, ('U106', '8'), (54, 22), (54, 23), ('U106', '5')); W(S, (54, 22), (54, 19), (46, 19))
    cap(S, 'C134', 50, 19); cap(S, 'C135', 46, 19); pw(S, '+3V3', 54, 19, 'up')
    T(S, 'I2C 0x68: CSB = VDDIO, SDO = GND', 42, 35)
    # ---------------- RTC
    S.place('U107', gp(60, 45))
    W(S, ('U107', '1'), (50, 46)); S.place('Y102', gp(50, 46), rot=orient('Y102', '1', 'down')[0], pin='1')
    W(S, ('U107', '2'), (52, 47), (52, 49), ('Y102', '2'))
    W(S, ('U107', '10'), (60, 37), (66, 37)); cap(S, 'C136', 66, 37); pw(S, '+3V3', 60, 37, 'up')
    W(S, ('U107', '4'), (72, 44))
    S.place('R119', gp(70, 44), pin='2'); S.done.add(('R119', '1')); pw(S, '+3V3', 70, 41, 'up')
    lb(S, 'RTC_INT', 72, 44)
    # ---------------- boost
    F(S, 'Boost 5 V cho LED PPG (TPS61240)', 82, 14, 125, 36)
    S.place('U103', gp(100, 25))
    pw(S, 'VSYS', 83, 24, 'up'); W(S, (83, 24), ('U103', '6')); cap(S, 'C113', 85, 24)
    W(S, (91, 24), (91, 25)); o = part2(S, 'L103', 91, 25, '1', 'right'); W(S, o, ('U103', '5'))
    W(S, ('U103', '4'), (95, 26)); cap(S, 'R113', 95, 26); W(S, (95, 26), (93, 26)); lb(S, 'VLED_EN', 93, 26, 'left')
    W(S, ('U103', '3'), (104, 25), (104, 24)); W(S, ('U103', '2'), (110, 24)); cap(S, 'C114', 106, 24)
    S.place('TP108', gp(108, 24), pin='1')
    o = part2(S, 'R114', 110, 24, '1', 'right'); W(S, o, (120, 24)); S.place('TP109', gp(116, 24), pin='1'); pw(S, 'VLED', 120, 24, 'up')
    T(S, 'EN = GPIO3, kéo xuống 1 MΩ; giữ bằng RTC hold khi ngủ', 84, 31)
    T(S, 'I_LED = V(TP108-TP109) / 0.1 Ω', 104, 31)
    # ---------------- FPC to the sensor board
    F(S, 'FPC 16P sang bo cảm biến', 128, 9, 160, 46)
    S.place('J105', gp(150, 15), pin='1')
    T(S, 'Cáp đảo đưa 5 V vào chân tín hiệu: đo thông mạch trước khi cấp nguồn', 129, 42)
FALLBACK['periph'] = (g(82), g(60))

def sheet_main_ui(S):
    OFF[1] = -16
    OFF[1] = 0
    T(S, 'Motor rung + còi từ: MOSFET phía thấp, diode dập, cổng kéo xuống (GPIO45/46 là chân strapping). Nút SOS, LED trạng thái.', 5, 4.6)
    OFF[1] = -16
    F(S, 'Motor rung (GPIO46)', 6, 24, 42, 50)
    S.place('Q101', gp(28, 40), pin='1')
    W(S, ('Q101', '3'), (31, 36)); S.place('M101', gp(31, 36), pin='2'); W(S, ('M101', '1'), (31, 28)); pw(S, 'VSYS', 31, 28, 'up')
    W(S, (31, 29), (35, 29), (35, 30)); o = part2(S, 'D102', 35, 30, '1', 'down'); W(S, o, (35, 37), (31, 37))
    W(S, ('Q101', '1'), (24, 40)); cap(S, 'R121', 26, 40)
    o = part2(S, 'R120', 24, 40, '2', 'left'); W(S, o, (17, 40)); lb(S, 'MOTOR', 17, 40, 'left')
    F(S, 'Còi từ (GPIO45, PWM ~2.7 kHz)', 48, 24, 90, 50)
    S.place('Q102', gp(68, 40), pin='1')
    S.place('BZ101', gp(75, 34), pin='2')
    W(S, ('Q102', '3'), (71, 34), ('BZ101', '2'))
    W(S, ('BZ101', '1'), (69, 32), (69, 29)); pw(S, 'VSYS', 69, 29, 'up')
    W(S, (69, 32), (65, 32)); o = part2(S, 'D103', 65, 32, '1', 'down'); W(S, o, (65, 36), (71, 36))
    W(S, ('Q102', '1'), (64, 40)); cap(S, 'R123', 66, 40)
    o = part2(S, 'R122', 64, 40, '2', 'left'); W(S, o, (59, 40)); lb(S, 'BUZZER', 59, 40, 'left')
    F(S, 'Nút SOS (GPIO8, đánh thức deep-sleep)', 6, 54, 42, 72)
    pw(S, '+3V3', 20, 57, 'up'); cap(S, 'R124', 20, 57); W(S, (20, 60), (26, 60)); cap(S, 'C137', 23, 60)
    o = part2(S, 'SW104', 26, 60, '1', 'right'); W(S, o, (31, 60), (31, 62)); pw(S, 'GND', 31, 62, 'down')
    W(S, (20, 60), (16, 60)); lb(S, 'BTN_SOS', 16, 60, 'left')
    F(S, 'LED trạng thái (GPIO18)', 48, 54, 90, 72)
    o = part2(S, 'R125', 56, 60, '1', 'right'); W(S, (56, 60), (54, 60)); lb(S, 'LED_STAT', 54, 60, 'left')
    o = part2(S, 'D104', o[0] + 1, o[1], '2', 'right'); W(S, (59, 60), (60, 60)); W(S, o, (65, 60), (65, 62)); pw(S, 'GND', 65, 62, 'down')
    OFF[1] = 0

# ============================================================== sensor board
def sheet_sensor(S):
    T(S, 'Bo cảm biến: LDO 1.8 V nhiễu thấp → MAX86141; LED SFH 7016 (xanh/đỏ/IR) và 2 photodiode nối thẳng vào AFE; SPI 1.8 V ↔ 3.3 V qua TXS0108E; MAX30208 nhiệt độ da.', 5, 4.6)
    F(S, 'FPC 16P nối bo chính', 4, 9, 36, 48)
    S.place('J201', gp(26, 15), pin='1')
    pw(S, '+3V3', 8, 38, 'up'); cap(S, 'C201', 8, 38)
    pw(S, 'VLED', 16, 38, 'up'); W(S, (16, 38), (20, 38)); cap(S, 'C202', 16, 38); cap(S, 'C203', 20, 38)
    T(S, 'C202 10 µF sát VLED (MAX p.12)', 6, 45)
    # LDO + shunt
    F(S, 'LDO 1.8 V + shunt đo dòng', 40, 9, 92, 30)
    pw(S, '+3V3', 44, 19, 'up')
    S.place('U201', gp(54, 19), pin='1')
    W(S, (44, 19), (54, 19)); cap(S, 'C204', 47, 19); W(S, ('U201', '3'), (52, 20), (52, 19))
    W(S, ('U201', '5'), (70, 19)); cap(S, 'C205', 62, 19); S.place('TP201', gp(65, 19), pin='1')
    o = part2(S, 'R201', 70, 19, '1', 'right'); W(S, o, (80, 19)); S.place('TP202', gp(76, 19), pin='1'); pw(S, '+1V8', 80, 19, 'up')
    T(S, 'I_1V8 = V(TP201-TP202) / 0.1 Ω', 62, 26)
    # AFE + optics
    F(S, 'MAX86141 + LED + photodiode', 40, 36, 96, 72)
    S.place('U202', gp(74, 55))
    S.place('D201', gp(60, 52), pin='3')
    for a, b in (('3', 'D1'), ('4', 'C1'), ('1', 'B1')): W(S, ('D201', a), ('U202', b))
    W(S, ('U202', 'A1'), (52, 50)); W(S, ('D201', '2'), (53, 52), (53, 50)); pw(S, 'VLED', 52, 50, 'up')
    W(S, ('U202', 'D5'), (56, 56), (56, 58)); part2(S, 'D202', 56, 58, '1', 'down', text='left')
    W(S, ('U202', 'D4'), (59, 57), (59, 58)); part2(S, 'D203', 59, 58, '1', 'down')
    W(S, ('U202', 'B5'), (66, 60)); cap(S, 'C206', 66, 60)
    W(S, ('U202', 'C2'), (80, 51), (80, 50)); W(S, ('U202', 'D2'), (80, 50), (80, 44), (91, 44))
    cap(S, 'C207', 83, 44); cap(S, 'C208', 87, 44); cap(S, 'C209', 91, 44); pw(S, '+1V8', 80, 44, 'up')
    a = gpin(S, 'D202', '5'); b = gpin(S, 'D203', '5'); y = a[1] + 1
    W(S, ('D202', '5'), (a[0], y), (b[0], y), ('D203', '5')); W(S, (a[0], y), (46, y)); cap(S, 'R205', 46, y); lb(S, 'PD_GND', 50, y, 'up')
    T(S, 'LED1 xanh (nhịp tim), LED2 đỏ, LED3 IR (SpO2); PD1/PD2 đọc đồng thời', 50, 69)
    T(S, 'R205 0 Ω: PD_GND về GND tại 1 điểm (MAX p.88)', 50, 70.5)
    # level shifter, A side wired straight to the AFE
    F(S, 'Chuyển mức TXS0108E (1.8 ↔ 3.3 V)', 98, 36, 132, 72)
    S.place('U203', gp(100, 56), text='right')
    for a, b, n in (('A2', '1', 'SCLK_1V8'), ('A4', '3', 'SDI_1V8'), ('A3', '4', 'SDO_1V8'), ('A5', '5', 'CSB_1V8'), ('B2', '6', 'INT_1V8')):
        pa = gpin(S, 'U202', a); W(S, ('U202', a), ('U203', b)); lb(S, n, pa[0] + 3, pa[1])
    T(S, 'OE nối thẳng VCCA (TXS p.6: OE Δt/Δv ≤ 10 ns/V)', 106, 70)
    pw(S, '+1V8', 122, 62, 'up'); cap(S, 'C211', 122, 62)
    pw(S, '+3V3', 127, 62, 'up'); cap(S, 'C212', 127, 62)
    # skin temperature
    F(S, 'MAX30208 nhiệt độ da (I2C 0x52)', 4, 76, 60, 98)
    S.place('U204', gp(40, 86))
    W(S, ('U204', '1'), (34, 85), (34, 82), (26, 82)); cap(S, 'C213', 26, 82); pw(S, '+3V3', 34, 82, 'up')
    W(S, ('U204', '10'), (57, 85)); cap(S, 'R204', 57, 85)
    W(S, ('U204', '7'), (47, 86)); o = part2(S, 'R203', 47, 86, '2', 'right', text='below'); W(S, o, (51, 86)); pw(S, '+3V3', 51, 86, 'right')
    T(S, 'GPIO1 = 1, GPIO0 = 0 → địa chỉ 0x52', 30, 95)
FALLBACK['sensor'] = (g(100), g(80))

LAYOUT = {'power': sheet_main_power, 'mcu': sheet_main_mcu, 'periph': sheet_main_periph, 'ui': sheet_main_ui, 'sensor': sheet_sensor}
