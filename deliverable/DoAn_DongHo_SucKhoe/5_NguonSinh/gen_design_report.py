"""Overall design report -> outputs/health_watch_design_report.docx + docs/img/budget_*.png.
Needs python-docx, matplotlib, pdftoppm.  usage: python3 tools/gen_design_report.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import design as D
from report_docx import Report, ROOT
from design_report_content import CONTENT, BUDGET, LIFE
IMG = os.path.join(ROOT, 'docs', 'img')
BAR, INK, MUTED, GRID = '#305496', '#1f1f1f', '#6b6b6b', '#e4e4e4'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.edgecolor': GRID, 'text.color': INK, 'axes.labelcolor': MUTED, 'xtick.color': MUTED, 'ytick.color': INK})
def base(ax):
    for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
    ax.tick_params(length=0); ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True); ax.invert_yaxis()
# battery life per scenario, against the >= 24 h target
fig, ax = plt.subplots(figsize=(7, 2.7), dpi=220)
names, hours = zip(*LIFE); ax.barh(names, hours, color=BAR, height=0.55); base(ax)
for y, h in enumerate(hours): ax.text(h + 1, y, ('%g h' % h).replace('.', ','), va='center', color=INK, bbox=dict(facecolor='white', edgecolor='none', pad=1.2), zorder=5)
ax.axvline(24, color=INK, lw=1, ls=(0, (4, 3))); ax.text(24.8, -0.75, 'mục tiêu 24 h', color=INK, va='bottom', fontsize=8.5)
ax.set_xlabel('Thời lượng pin (giờ)'); ax.set_xlim(0, 100); fig.tight_layout(); fig.savefig(os.path.join(IMG, 'budget_life.png')); plt.close(fig)
# nominal average battery current per load, largest first
rows = sorted(((r[0], r[3]) for r in BUDGET if r[3] > 0), key=lambda r: -r[1])
fig, ax = plt.subplots(figsize=(7, 4.3), dpi=220)
ax.barh([r[0] for r in rows], [r[1] for r in rows], color=BAR, height=0.6); base(ax)
for y, r in enumerate(rows[:6]): ax.text(r[1] + 0.03, y, ('%.2f' % r[1]).replace('.', ','), va='center', color=INK)
ax.set_xlabel('Dòng trung bình tại pin, kịch bản danh định (mA)'); ax.set_xlim(0, 2.75); fig.tight_layout(); fig.savefig(os.path.join(IMG, 'budget_loads.png')); plt.close(fig)
def budget(rep):
    t = [['Tải', 'Báo cáo cũ', 'Tốt nhất', 'Danh định', 'Xấu nhất', 'Cơ sở']]
    for r in BUDGET: t.append([r[0]] + [('%.2f' % v).replace('.', ',') if v is not None else 'gộp' for v in (r[1], r[2], r[3], r[4])] + [r[5]])
    tot = [sum(r[k] or 0 for r in BUDGET) for k in (1, 2, 3, 4)]
    t.append(['**Tổng (mA)**'] + ['**%s**' % ('%.2f' % v).replace('.', ',') for v in tot] + [''])
    t.append(['Dung lượng dùng được (mAh)', '340', '360', '320', '190', 'Giả định: 85 %; 90 %; 80 %; 80 %×70 %×85 %'])
    t.append(['**Thời lượng (giờ)**', '**40**', '**90**', '**27,6**', '**4,6**', 'Tính từ hai dòng trên'])
    rep.table(t)
def gpio(rep):
    t = [['GPIO', 'Chân', 'Net']]
    u = next(p for p in D.MAIN if p['short'] == 'U4')
    for pin, net in sorted(D.ESP_GPIO.items(), key=lambda e: int(D.GPIO_NAME[e[0]][4:])): t.append([D.GPIO_NAME[pin], pin, net])
    t += [['GPIO19 / GPIO20', '25 / 26', 'USB_DN_MCU / USB_DP_MCU'], ['U0TXD / U0RXD', '49 / 50', 'U0TXD_MCU / U0RXD'], ['GPIO33-37', '38-42', 'PSRAM octal trong chip: không dùng'], ['GPIO48 / GPIO47', '36 / 37', '**Còn trống**, dùng được ở 3,3 V (DS ghi chú 4 chỉ áp dụng cho R8V, R16V)']]
    rep.table(t)
def parts(rep):
    for board, title in (('main', 'Bo chính'), ('sensor', 'Bo cảm biến')):
        rep.doc.add_heading(title, 3)
        t = [['Ref', 'Giá trị', 'Mã đặt', 'Vai trò', 'Tài liệu']]
        for p in D.BOARDS[board]: t.append([p['ref'], D.P[p['typ']][1] + (' (DNP)' if p['dnp'] else ''), (D.P[p['typ']][3] or '-').replace('|', '/'), p['why'].replace('|', '/'), (p['cite'] or '-').replace('|', '/')])
        rep.table(t)
Report('Đồng hồ theo dõi sức khỏe: báo cáo phân tích thiết kế', 'Báo cáo phân tích thiết kế: đồng hồ theo dõi sức khỏe').render(
    CONTENT, os.path.join(ROOT, 'outputs', 'health_watch_design_report.docx'), {'budget': budget, 'gpio': gpio, 'parts': parts})
