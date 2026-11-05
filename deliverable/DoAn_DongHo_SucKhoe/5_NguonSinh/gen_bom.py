"""BOM for JLCPCB PCBA -> outputs/bom/health_watch_<board>_jlc_bom.csv + outputs/bom/health_watch_bom.xlsx.
Prices and stock are read live from JLCPCB and LCSC. Needs openpyxl.  usage: python3 tools/gen_bom.py"""
import collections, csv, datetime, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as CL
import design as D
import jlc_api as A
OUT = os.path.join(HERE, '..', 'outputs', 'bom')
SETS_MAX = 5
SKIP = {'TP'}                    # test points are copper only
HAND = {'MOTOR', 'HDR3'}         # soldered by hand, not in the SMT order
LEADLESS = {'ESP32', 'AXP', 'BOOST', 'IMU', 'AFE', 'TEMP', 'LED3', 'PD'}    # X-ray per component
# parts bought loose: (item, qty per set, code, note)
LOOSE = [('Pin LiPo 390 mAh, 28×27×5 mm (FLY.502728.390)', 1, 'C5154896', 'Cần xác nhận đầu nối, NTC và điều kiện giao pin về Việt Nam'),
         ('Cáp FFC 16P 0,5 mm, 50 mm, ngược mặt', 1, 'C5242797', 'Độ dài và loại cáp chốt theo vỏ')]
# fees of JLCPCB Standard PCBA, https://jlcpcb.com/help/article/pcb-assembly-price, read 05/11/2026
FEES = {'Setup 2 mặt': 51.12, 'Stencil 2 mặt': 16.42, 'Nạp feeder mỗi mã': 1.53, 'Mỗi mối hàn (0,016 + 0,0016)': 0.0176, 'Đóng gói + xác nhận vị trí': 0.95}
XRAY = [(1, 1.64), (11, 0.82), (51, 0.49), (201, 0.33)]
HEAD = PatternFill('solid', fgColor='305496'); WHITE = Font(name='Arial', bold=True, color='FFFFFF'); BASE = Font(name='Arial'); BOLD = Font(name='Arial', bold=True)
BLUE = Font(name='Arial', color='0000FF'); BAD = PatternFill('solid', fgColor='F8CBAD')

def price(j, l):
    p = sorted(j.get('componentPrices') or [], key=lambda e: e['startNumber'])
    if p: return p[0]['productPrice']
    p = l.get('productPriceList') or []
    return p[0]['usdPrice'] if p else None

def lines(board):
    groups = collections.OrderedDict()
    for p in D.BOARDS[board]:
        if p['dnp'] or p['typ'] in SKIP: continue
        groups.setdefault(p['typ'], []).append(p)
    out = []
    for typ, ps in groups.items():
        lib, value, fp, code, _ = D.P[typ]
        m = re.match(r'C\d+', code or '')
        c = m.group(0) if m else ''
        j, l = (A.jlc(c), A.lcsc(c)) if c else ({}, {})
        need = len(ps) * SETS_MAX + (j.get('lossNumber') or 0)
        stock = j.get('stockCount') or 0
        if typ in HAND: status = 'Mua rời, hàn tay'
        elif not c: status = 'KHÔNG CÓ trên JLCPCB/LCSC'
        elif j.get('noBuyReason') or stock < need: status = 'HẾT HÀNG trên JLCPCB' + (' và LCSC' if not l.get('stockNumber') else '')
        else: status = 'Đặt PCBA được'
        pads = sum(len(p['pins']) for p in ps) // len(ps)
        out.append(dict(typ=typ, refs=','.join(p['ref'] for p in ps), qty=len(ps), value=value, fp=fp, code=c or code, lib=j.get('componentLibraryType') or '', jlc=stock, lcsc=l.get('stockNumber'),
                        least=j.get('leastPatchNumber') or 0, loss=j.get('lossNumber') or 0, price=price(j, l), status=status, pads=pads, leadless=typ in LEADLESS))
    return out

def header(ws, row, names, widths=None):
    for i, n in enumerate(names, 1):
        c = ws.cell(row, i, n); c.fill = HEAD; c.font = WHITE; c.alignment = Alignment(wrap_text=True, vertical='center')
        if widths: ws.column_dimensions[CL(i)].width = widths[i - 1]

def board_sheet(wb, title, rows):
    ws = wb.create_sheet(title)
    header(ws, 1, ['Tham chiếu', 'SL/bộ', 'Giá trị', 'Footprint', 'Mã LCSC', 'Thư viện JLC', 'Tồn JLCPCB', 'Tồn LCSC', 'Mua tối thiểu', 'Hao hụt', 'Đơn giá bậc 1 ($)', 'SL mua', 'Thành tiền ($)', 'Chân/linh kiện', 'Mối hàn/bộ', 'Tính X-ray', 'Trạng thái'],
           [30, 7, 24, 42, 12, 10, 11, 10, 9, 8, 10, 8, 10, 9, 9, 8, 30])
    for i, r in enumerate(rows, 2):
        smt = r['typ'] not in HAND
        vals = [r['refs'], r['qty'], r['value'], r['fp'], r['code'], r['lib'], r['jlc'], r['lcsc'], r['least'], r['loss'], r['price'],
                "=MAX(B%d*'Chi phí'!$B$3+J%d,I%d)" % (i, i, i), '=L%d*K%d' % (i, i) if r['price'] is not None else 0, r['pads'], '=B%d*N%d' % (i, i) if smt else 0, r['qty'] if r['leadless'] else 0, r['status']]
        for k, v in enumerate(vals, 1):
            c = ws.cell(i, k, v); c.font = BASE
            if k == 13: c.number_format = '0.00'
        if 'Đặt PCBA' not in r['status'] and 'Mua rời' not in r['status']:
            for k in range(1, 18): ws.cell(i, k).fill = BAD
    last = len(rows) + 1
    t = last + 1
    ws.cell(t, 1, 'Tổng').font = BOLD
    for col in ('M', 'O', 'P'):
        c = ws['%s%d' % (col, t)]; c.value = '=SUM(%s2:%s%d)' % (col, col, last); c.font = BOLD; c.number_format = '0.00' if col == 'M' else '0'
    ws.freeze_panes = 'A2'
    return t, sum(1 for r in rows if r['typ'] not in HAND and r['code'] and re.match(r'C\d', r['code']))

def main():
    os.makedirs(OUT, exist_ok=True)
    wb = Workbook(); cost = wb.active; cost.title = 'Chi phí'
    data = {b: lines(b) for b in D.BOARDS}
    for b, rows in data.items():
        with open(os.path.join(OUT, 'health_watch_%s_jlc_bom.csv' % b), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
            for r in rows:
                if r['typ'] not in HAND: w.writerow([r['value'], r['refs'], r['fp'].split(':')[-1], r['code'] if re.match(r'C\d', r['code']) else ''])
    tm, fm = board_sheet(wb, 'Bo chính', data['main'])
    ts, fs = board_sheet(wb, 'Bo cảm biến', data['sensor'])
    lo = wb.create_sheet('Mua rời')
    header(lo, 1, ['Hạng mục', 'SL/bộ', 'Mã LCSC', 'Tồn JLCPCB', 'Tồn LCSC', 'Đơn giá ($)', 'SL mua', 'Thành tiền ($)', 'Ghi chú'], [48, 7, 12, 11, 10, 10, 8, 10, 60])
    items = [(n, q, c, x) for n, q, c, x in LOOSE] + [(D.P[r['typ']][1], r['qty'], r['code'], 'Không nằm trong đơn SMT') for r in data['main'] if r['typ'] in HAND]
    row = 2
    for n, q, c, x in items:
        j, l = A.jlc(c), A.lcsc(c)
        for k, v in enumerate([n, q, c, j.get('stockCount'), l.get('stockNumber'), price(j, l), "=B%d*'Chi phí'!$B$3" % row, '=G%d*F%d' % (row, row), x], 1):
            lo.cell(row, k, v).font = BASE
        row += 1
    for k, v in enumerate(['Màn AMOLED 1,75" CO5300 + cảm ứng', 1, '', '', '', '', "=B%d*'Chi phí'!$B$3" % row, '', 'KHÔNG CÓ trên JLCPCB/LCSC. Chưa tính giá; cần chốt nhà cung cấp, chân FPC và IC cảm ứng'], 1):
        c = lo.cell(row, k, v); c.font = BASE; c.fill = BAD
    lt = row + 1
    lo.cell(lt, 1, 'Tổng (chưa gồm màn hình)').font = BOLD
    c = lo['H%d' % lt]; c.value = '=SUM(H2:H%d)' % row; c.font = BOLD; c.number_format = '0.00'
    # cost sheet
    cost.column_dimensions['A'].width = 46
    for col in 'BCD': cost.column_dimensions[col].width = 14
    cost['A1'] = 'Dự toán PCBA JLCPCB (Standard, 2 mặt, mỗi bo một đơn)'; cost['A1'].font = BOLD
    cost['A2'] = 'Giá đọc ngày %s; đổi theo thời điểm' % datetime.date.today().strftime('%d/%m/%Y'); cost['A2'].font = BASE
    cost['A3'] = 'Số bộ (nhập tại đây)'; cost['A3'].font = BOLD
    cost['B3'] = 2; cost['B3'].font = BLUE
    r = 5
    fee_row = {}
    for k, v in FEES.items():
        cost.cell(r, 1, k).font = BASE; c = cost.cell(r, 2, v); c.font = BLUE; fee_row[k] = r; r += 1
    cost.cell(r, 1, 'Nguồn phí: jlcpcb.com/help/article/pcb-assembly-price').font = BASE
    r += 2
    header(cost, r, ['Hạng mục ($)', 'Bo chính', 'Bo cảm biến', 'Tổng'])
    f = lambda k: '$B$%d' % fee_row[k]
    xr = lambda n: 'IF(%s<=10,1.64,IF(%s<=50,0.82,IF(%s<=200,0.49,0.33)))' % (n, n, n)
    rows = [('Linh kiện', "='Bo chính'!M%d" % tm, "='Bo cảm biến'!M%d" % ts),
            ('Setup + stencil', '=%s+%s' % (f('Setup 2 mặt'), f('Stencil 2 mặt')), '=%s+%s' % (f('Setup 2 mặt'), f('Stencil 2 mặt'))),
            ('Nạp feeder', '=%d*%s' % (fm, f('Nạp feeder mỗi mã')), '=%d*%s' % (fs, f('Nạp feeder mỗi mã'))),
            ('Mối hàn', "='Bo chính'!O%d*$B$3*%s" % (tm, f('Mỗi mối hàn (0,016 + 0,0016)')), "='Bo cảm biến'!O%d*$B$3*%s" % (ts, f('Mỗi mối hàn (0,016 + 0,0016)'))),
            ('X-ray', "='Bo chính'!P%d*$B$3*%s" % (tm, xr("('Bo chính'!P%d*$B$3)" % tm)), "='Bo cảm biến'!P%d*$B$3*%s" % (ts, xr("('Bo cảm biến'!P%d*$B$3)" % ts))),
            ('Đóng gói + xác nhận vị trí', '=' + f('Đóng gói + xác nhận vị trí'), '=' + f('Đóng gói + xác nhận vị trí'))]
    s = r + 1
    for n, a, b in rows:
        r += 1
        cost.cell(r, 1, n).font = BASE; cost.cell(r, 2, a).font = BASE; cost.cell(r, 3, b).font = BASE; cost.cell(r, 4, '=B%d+C%d' % (r, r)).font = BASE
    r += 1
    cost.cell(r, 1, 'Tổng PCBA').font = BOLD
    for col in 'BCD':
        cost['%s%d' % (col, r)] = '=SUM(%s%d:%s%d)' % (col, s, col, r - 1); cost['%s%d' % (col, r)].font = BOLD
    for rr in range(s, r + 1):
        for col in 'BCD': cost['%s%d' % (col, rr)].number_format = '0.00'
    t = r
    r += 1
    cost.cell(r, 1, 'Mua rời, chưa gồm màn hình').font = BASE; cost['D%d' % r] = "='Mua rời'!H%d" % lt; cost['D%d' % r].number_format = '0.00'; cost['D%d' % r].font = BASE
    r += 1
    cost.cell(r, 1, 'Tổng đã có giá').font = BOLD; cost['D%d' % r] = '=D%d+D%d' % (t, r - 1); cost['D%d' % r].font = BOLD; cost['D%d' % r].number_format = '0.00'
    r += 2
    for n in ('Chưa gồm: SFH 7016 và màn hình (chưa có giá), MAX86141 tính theo giá niêm yết khi hết hàng, PCB, vận chuyển, thuế, vỏ, phí fixture và handling nếu phát sinh.',
              'Đơn giá dùng bậc 1 nên có thể cao hơn báo giá thật. Bo chưa có layout, nên số mối hàn lấy từ số chân trong design.py.'):
        cost.cell(r, 1, n).font = BASE; r += 1
    wb.save(os.path.join(OUT, 'health_watch_bom.xlsx'))
    res = {b: [(x['typ'], x['code'], x['qty'], x['jlc'], x['lcsc'], x['price'], x['status']) for x in rows_] for b, rows_ in data.items()}
    json.dump(res, sys.stdout, ensure_ascii=False); print()

if __name__ == '__main__':
    main()
