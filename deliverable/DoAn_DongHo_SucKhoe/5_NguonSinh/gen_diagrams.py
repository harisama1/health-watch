"""Block diagram, power tree and system/data-flow diagram of the health watch -> docs/img/*.svg + *.png (rsvg-convert).
Boxes and arrows are declared below; every arrow carries the interface / signal name. Net names match design.py."""
import os, subprocess, html
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, '..', 'docs', 'img')
os.makedirs(IMG, exist_ok=True)
COL = {'mcu': '#dbe8f7', 'pwr': '#fde9d0', 'sens': '#e2f2dc', 'ui': '#efe3f6', 'conn': '#eeeeee', 'ext': '#fff7c2', 'ai': '#ffd9d9'}

class SVG:
    def __init__(s, w, h, title):
        s.w, s.h, s.el = w, h, []
        s.el.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (w, h))
        s.el.append('<text x="%d" y="28" font-size="20" font-weight="bold" text-anchor="middle">%s</text>' % (w / 2, html.escape(title)))
        s.box_at = {}
    def frame(s, x, y, w, h, label):
        s.el.append('<rect x="%d" y="%d" width="%d" height="%d" rx="10" fill="none" stroke="#555" stroke-width="2" stroke-dasharray="8 5"/>' % (x, y, w, h))
        s.el.append('<text x="%d" y="%d" font-size="15" font-weight="bold" fill="#444">%s</text>' % (x + 10, y + 20, html.escape(label)))
    def box(s, key, x, y, w, h, title, lines=(), kind='mcu'):
        s.box_at[key] = (x, y, w, h)
        s.el.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="#333" stroke-width="1.5"/>' % (x, y, w, h, COL[kind]))
        s.el.append('<text x="%d" y="%d" font-size="14" font-weight="bold" text-anchor="middle">%s</text>' % (x + w / 2, y + 19, html.escape(title)))
        for i, l in enumerate(lines):
            s.el.append('<text x="%d" y="%d" font-size="11.5" text-anchor="middle" fill="#222">%s</text>' % (x + w / 2, y + 36 + 14.5 * i, html.escape(l)))
    def anchor(s, key, side, f=0.5):
        x, y, w, h = s.box_at[key]
        return {'l': (x, y + h * f), 'r': (x + w, y + h * f), 't': (x + w * f, y), 'b': (x + w * f, y + h)}[side]
    def arrow(s, a, b, label='', both=False, color='#1f4e9a', dy=-5, pts=None, lx=None, ly=None, width=1.8):
        path = [a] + (pts or []) + [b]
        d = 'M %s' % ' L '.join('%.1f %.1f' % p for p in path)
        s.el.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" marker-end="url(#ah%s)"%s/>'
                    % (d, color, width, color[1:], ' marker-start="url(#as%s)"' % color[1:] if both else ''))
        s.colors = getattr(s, 'colors', set()) | {color}
        if label:
            if lx is None:
                (x0, y0), (x1, y1) = path[len(path) // 2 - 1], path[len(path) // 2]
                lx, ly = (x0 + x1) / 2, (y0 + y1) / 2 + dy
            s.el.append('<text x="%.1f" y="%.1f" font-size="11" text-anchor="middle" fill="%s" stroke="#fff" stroke-width="3" paint-order="stroke">%s</text>'
                        % (lx, ly, color, html.escape(label)))
    def note(s, x, y, text, size=12, anchor='start', color='#333'):
        for i, l in enumerate(text.split('\n')):
            s.el.append('<text x="%d" y="%d" font-size="%s" text-anchor="%s" fill="%s">%s</text>' % (x, y + i * (size + 4), size, anchor, color, html.escape(l)))
    def save(s, name):
        defs = ''.join('<marker id="ah%s" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="%s"/></marker>'
                       '<marker id="as%s" markerWidth="10" markerHeight="8" refX="1" refY="4" orient="auto"><path d="M10,0 L0,4 L10,8 z" fill="%s"/></marker>'
                       % (c[1:], c, c[1:], c) for c in getattr(s, 'colors', set()))
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" font-family="DejaVu Sans, Arial, sans-serif">'
               '<defs>%s</defs>%s</svg>' % (s.w, s.h, s.w, s.h, defs, ''.join(s.el)))
        p = os.path.join(IMG, name)
        open(p + '.svg', 'w', encoding='utf-8').write(svg)
        subprocess.run(['rsvg-convert', '-w', str(s.w * 2), '-o', p + '.png', p + '.svg'], check=True)
        print('->', p + '.png')

# ------------------------------------------------------------------ 1. hardware block diagram
S = SVG(1500, 1010, 'Sơ đồ khối phần cứng - đồng hồ theo dõi sức khỏe (bo chính + bo cảm biến)')
S.frame(20, 45, 1460, 640, 'BO CHÍNH (sau màn hình AMOLED) - PCB 4 lớp')
S.frame(20, 720, 1460, 270, 'BO CẢM BIẾN (đáy vỏ, áp vào da) - nối bo chính bằng FPC 16 chân 0.5 mm')
S.box('usb', 50, 90, 170, 80, 'USB-C', ['5 V sạc + USB 2.0 FS', 'ESD USBLC6-2SC6'], 'conn')
S.box('pmic', 50, 230, 210, 150, 'PMIC AXP2101', ['sạc LiPo tuyến tính ≤1 A', 'DCDC1 3.3 V / 2 A', 'fuel gauge, NTC, nút nguồn', 'PWROK → CHIP_PU, IRQ'], 'pwr')
S.box('bat', 50, 440, 210, 70, 'Pin LiPo 1S ~400 mAh', ['shunt 50 mΩ + test point'], 'pwr')
S.box('boost', 50, 560, 210, 90, 'Boost TPS61240', ['VSYS → VLED 5 V', 'EN = GPIO3 (tắt khi ngủ)', 'shunt 0.1 Ω'], 'pwr')
S.box('mcu', 520, 200, 300, 260, 'ESP32-S3R8', ['2× Xtensa LX7 240 MHz + lệnh vector', '8 MB PSRAM octal (trong chip)', 'WiFi 802.11 b/g/n + BLE 5',
      '', 'Edge AI (TFLite Micro + ESP-NN, int8):', '• té ngã + nhận dạng hoạt động', '• nhịp tim bất thường / rung nhĩ', '• giấc ngủ / stress (HRV)', '', 'USB Serial/JTAG, light/deep sleep'], 'ai')
S.box('flash', 520, 90, 140, 70, 'Flash 16 MB', ['W25Q128JV (QSPI)'], 'mcu')
S.box('ant', 690, 90, 130, 70, 'Ăng-ten gốm', ['2.4 GHz + mạch π'], 'mcu')
S.box('rtc', 330, 470, 150, 70, 'RTC PCF85063A', ['32.768 kHz, INT'], 'sens')
S.box('imu', 330, 560, 150, 80, 'IMU BMI270', ['acc + gyro 6 trục', 'INT1/INT2 (wake)'], 'sens')
S.box('disp', 1000, 90, 230, 110, 'AMOLED 1.75" 466×466', ['driver CO5300 (QSPI)', 'cảm ứng CST9217 (I2C)', 'FPC 31 chân 0.3 mm'], 'ui')
S.box('ui', 1000, 250, 230, 140, 'Giao diện', ['motor rung 1027 (AO3400A)', 'còi từ 8.5 mm (AO3400A)', 'nút SOS, nút nguồn', 'LED trạng thái + LED sạc'], 'ui')
S.box('dbg', 1000, 430, 230, 80, 'Debug / đo', ['UART0 header, BOOT, RESET', 'test point VBAT/3V3/1V8/VLED'], 'conn')
S.box('fpcm', 600, 600, 220, 60, 'FPC 16P (J105)', ['3V3, VLED, SPI, INT, I2C'], 'conn')
S.box('fpcs', 600, 750, 220, 60, 'FPC 16P (J201)', ['cùng thứ tự chân'], 'conn')
S.box('ldo', 60, 840, 200, 80, 'LDO LP5907 1.8 V', ['nhiễu thấp, PSRR cao', 'shunt 0.1 Ω'], 'pwr')
S.box('txs', 380, 850, 210, 80, 'TXS0108E', ['chuyển mức 1.8 ↔ 3.3 V', 'SPI + INT'], 'conn')
S.box('afe', 680, 850, 230, 110, 'AFE MAX86141', ['3 driver LED, 2 ADC 19-bit', 'khử ánh sáng nền', 'FIFO 128 mẫu, SPI 1.8 V'], 'sens')
S.box('opt', 1010, 830, 230, 140, 'Quang học (cửa sổ đáy)', ['SFH 7013: xanh 530 / đỏ 655', '/ hồng ngoại 940 nm', '2× photodiode VEMD8080', 'vách chắn sáng LED ↔ PD'], 'sens')
S.box('tmp', 1290, 830, 170, 90, 'MAX30208', ['nhiệt độ da ±0.1 °C', 'I2C 0x52'], 'sens')
B = '#1f4e9a'; P = '#c55a11'; G = '#2e7d32'
S.arrow(S.anchor('usb', 'b'), S.anchor('pmic', 't'), 'VBUS 5 V', color=P, dy=0, lx=170, ly=205)
S.arrow(S.anchor('usb', 'r'), S.anchor('mcu', 'l', 0.15), 'USB D+/D− (GPIO19/20)', color=B, pts=[(400, 130), (400, 239)], lx=400, ly=125)
S.arrow(S.anchor('bat', 't'), S.anchor('pmic', 'b'), 'VBAT', both=True, color=P, lx=190, ly=415)
S.arrow(S.anchor('pmic', 'r', 0.25), S.anchor('mcu', 'l', 0.35), '+3V3 (DCDC1)', color=P, lx=390, ly=266)
S.arrow(S.anchor('mcu', 'l', 0.55), S.anchor('pmic', 'r', 0.65), 'I2C + IRQ, PWROK→CHIP_PU', both=True, color=B, lx=390, ly=360)
S.arrow((155, 380), S.anchor('boost', 't'), '', color=P, pts=[(30, 380), (30, 545), (155, 545)])
S.note(34, 470, 'VSYS', 11, color=P)
S.arrow(S.anchor('mcu', 't', 0.2), S.anchor('flash', 'b'), 'QSPI', both=True, color=B, dy=0)
S.arrow(S.anchor('mcu', 't', 0.8), S.anchor('ant', 'b'), 'RF', both=True, color=B, dy=0)
S.arrow(S.anchor('mcu', 'r', 0.1), S.anchor('disp', 'l', 0.6), 'QSPI + CS/TE/RST, I2C + TP_INT', both=True, color=B, lx=905, ly=212)
S.arrow(S.anchor('mcu', 'r', 0.4), S.anchor('ui', 'l', 0.4), 'PWM GPIO45/46, GPIO8, GPIO18', both=True, color=B, lx=905, ly=298)
S.arrow(S.anchor('mcu', 'r', 0.75), S.anchor('dbg', 'l', 0.4), 'UART0', both=True, color=B, lx=905, ly=390)
S.arrow(S.anchor('rtc', 'r'), S.anchor('mcu', 'b', 0.12), 'I2C + INT', both=True, color=B, pts=[(556, 505)], lx=510, ly=500)
S.arrow(S.anchor('imu', 'r'), S.anchor('mcu', 'b', 0.05), 'I2C + INT1/2', both=True, color=B, pts=[(535, 600)], lx=500, ly=625)
S.arrow(S.anchor('mcu', 'b', 0.5), S.anchor('fpcm', 't', 0.5), 'SPI 3.3 V + PPG_INT, I2C', both=True, color=B, dy=0, lx=760, ly=530)
S.arrow(S.anchor('boost', 'r'), S.anchor('fpcm', 'l', 0.5), 'VLED 5 V', color=P, pts=[(300, 605), (300, 670), (570, 670), (570, 630)], lx=440, ly=665)
S.arrow(S.anchor('fpcm', 'b'), S.anchor('fpcs', 't'), 'cáp FFC loại B', both=True, color='#555555', dy=0, lx=770, ly=705)
S.arrow(S.anchor('fpcs', 'l', 0.5), S.anchor('ldo', 't'), '+3V3', color=P, pts=[(160, 780)], lx=300, ly=775)
S.arrow(S.anchor('fpcs', 'b', 0.2), S.anchor('txs', 't', 0.7), 'SPI/INT 3.3 V', both=True, color=B, pts=[(644, 830), (527, 830)], lx=575, ly=845)
S.arrow(S.anchor('ldo', 'r'), S.anchor('txs', 'l'), '+1V8', color=P, lx=320, ly=876)
S.arrow(S.anchor('txs', 'r'), S.anchor('afe', 'l', 0.4), 'SPI/INT 1.8 V', both=True, color=B, lx=635, ly=888)
S.arrow((260, 900), S.anchor('afe', 'b', 0.3), '+1V8 (VDD_ANA/DIG)', color=P, pts=[(300, 900), (300, 980), (749, 980)], lx=520, ly=975)
S.arrow(S.anchor('fpcs', 'r'), S.anchor('opt', 't', 0.2), 'VLED 5 V', color=P, pts=[(1056, 780)], lx=960, ly=775)
S.arrow(S.anchor('afe', 'r', 0.3), S.anchor('opt', 'l', 0.4), 'LED1/2/3_DRV', color=G, lx=960, ly=878)
S.arrow(S.anchor('opt', 'l', 0.75), S.anchor('afe', 'r', 0.75), 'PD1/PD2 (dòng)', color=G, lx=960, ly=940)
S.arrow(S.anchor('fpcs', 'r', 0.8), S.anchor('tmp', 't'), 'I2C + 3V3', both=True, color=B, pts=[(1375, 798)], lx=1250, ly=794)
S.save('block_diagram')

# ------------------------------------------------------------------ 2. power tree
S = SVG(1300, 660, 'Cây nguồn và điểm đo dòng (shunt + test point)')
S.box('vbus', 30, 80, 170, 70, 'USB VBUS 5 V', ['TP101'], 'conn')
S.box('pmic', 280, 70, 230, 230, 'AXP2101', ['VBUS → VMID → sạc tuyến tính', 'BATFET: BAT ↔ VSYS', 'DCDC1 3 MHz → 3V3_PMIC', 'VRTC, VREF', 'NTC → ngắt sạc khi nóng',
      'DCDC2-4, LDO khác: không dùng'], 'pwr')
S.box('bat', 30, 220, 170, 80, 'LiPo 1S 400 mAh', ['R111 50 mΩ', 'TP102 ↔ TP103'], 'pwr')
S.box('v33', 620, 70, 230, 80, '+3V3 (R112 0.1 Ω)', ['TP104 ↔ TP105', 'ESP32, flash, màn hình, IMU, RTC'], 'pwr')
S.box('vsys', 620, 200, 230, 80, 'VSYS 3.4-4.4 V', ['motor, còi (qua MOSFET)', 'LED sạc'], 'pwr')
S.box('boost', 620, 330, 230, 80, 'TPS61240 → VLED_5V', ['R114 0.1 Ω: TP108 ↔ TP109'], 'pwr')
S.box('ldo', 940, 70, 300, 80, 'LP5907 1.8 V (bo cảm biến)', ['R201 0.1 Ω: TP201 ↔ TP202', 'MAX86141 VDD, TXS0108E VCCA'], 'pwr')
S.box('sens33', 940, 200, 300, 80, '+3V3 bo cảm biến', ['MAX30208, TXS0108E VCCB'], 'sens')
S.box('vled', 940, 330, 300, 80, 'VLED (bo cảm biến)', ['anode SFH 7013 → MAX86141 LEDx_DRV'], 'sens')
S.arrow(S.anchor('vbus', 'r'), S.anchor('pmic', 'l', 0.12), '', color=P)
S.arrow(S.anchor('bat', 'r'), S.anchor('pmic', 'l', 0.8), '', both=True, color=P)
S.arrow(S.anchor('pmic', 'r', 0.12), S.anchor('v33', 'l'), 'DCDC1', color=P)
S.arrow(S.anchor('pmic', 'r', 0.6), S.anchor('vsys', 'l'), 'VSYS', color=P)
S.arrow((560, 240), S.anchor('boost', 'l'), 'EN = GPIO3', color=P, pts=[(560, 370)], lx=600, ly=300)
S.arrow(S.anchor('v33', 'r'), S.anchor('ldo', 'l'), 'FPC', color=P)
S.arrow((880, 110), S.anchor('sens33', 'l'), '', color=P, pts=[(880, 240)])
S.arrow(S.anchor('boost', 'r'), S.anchor('vled', 'l'), 'FPC', color=P)
S.note(30, 470, 'Đo dòng: đặt đồng hồ đo mV giữa hai test point của shunt, I = V / R_shunt (R111 = 0.05 Ω, R112/R114/R201 = 0.1 Ω).\n'
       'Ví dụ 10 mV trên R112 = 100 mA trên đường 3V3. Đo ngủ sâu (µA) thì tháo shunt, nối đồng hồ µA nối tiếp hai pad.\n'
       'Trình tự: AXP2101 khởi động DCDC1 → PWROK nhả CHIP_PU → ESP32 chạy → ESP32 bật boost VLED khi cần đo PPG.\n'
       'VCCA (1.8 V) ≤ VCCB (3.3 V) của TXS0108E luôn đúng vì 1.8 V lấy từ 3.3 V; OE chỉ lên sau RC ~10 ms.', 13)
S.save('power_tree')

# ------------------------------------------------------------------ 3. system / data flow
S = SVG(1500, 560, 'Luồng dữ liệu: cảm biến → edge AI trên đồng hồ → web')
S.box('ppg', 30, 80, 200, 80, 'PPG (MAX86141)', ['25-100 mẫu/s, FIFO'], 'sens')
S.box('imu', 30, 200, 200, 80, 'IMU (BMI270)', ['50 Hz, FIFO, INT'], 'sens')
S.box('tmp', 30, 320, 200, 80, 'Nhiệt độ da', ['1 lần/phút'], 'sens')
S.box('dsp', 310, 80, 250, 120, 'Tiền xử lý (FreeRTOS task)', ['lọc thông dải, phát hiện đỉnh', 'HR, SpO2 (tỉ số R), IBI/HRV', 'đặc trưng cửa sổ 2-30 s'], 'mcu')
S.box('ai', 310, 240, 250, 160, 'Edge AI (TFLite Micro int8)', ['1D-CNN té ngã + hoạt động', 'phân loại nhịp (IBI) → AF?', 'giấc ngủ / stress (HRV+motion)', 'train trên Google Colab', '(dataset công khai + tự thu)'], 'ai')
S.box('evt', 640, 80, 230, 120, 'Bộ quyết định sự kiện', ['té ngã / nhịp bất thường / SOS', '→ rung + còi + màn hình', '→ gửi NGAY'], 'ui')
S.box('buf', 640, 260, 230, 120, 'Bộ đệm flash 16 MB', ['dữ liệu tổng hợp 1 phút', 'giữ lại khi mất mạng'], 'mcu')
S.box('wifi', 950, 80, 230, 100, 'WiFi HTTPS', ['lô 15 phút: POST /api/batch', 'sự kiện: POST /api/event'], 'ext')
S.box('ble', 950, 240, 230, 100, 'BLE → điện thoại', ['dự phòng khi không có WiFi', '(Web Bluetooth / app)'], 'ext')
S.box('srv', 1260, 80, 210, 260, 'Server + web tự viết', ['REST API (HTTPS)', 'cơ sở dữ liệu chuỗi thời gian', 'dashboard: biểu đồ HR,', 'SpO2, bước, nhiệt độ, ngủ', 'cảnh báo cho người thân', 'OTA firmware / model'], 'ext')
for a, b, l in [('ppg', 'dsp', 'SPI'), ('tmp', 'dsp', 'I2C')]:
    S.arrow(S.anchor(a, 'r'), S.anchor(b, 'l', 0.5 if a == 'ppg' else 0.9), l, color=B)
S.arrow(S.anchor('imu', 'r'), S.anchor('ai', 'l', 0.2), 'I2C FIFO', color=B)
S.arrow(S.anchor('dsp', 'b'), S.anchor('ai', 't'), 'đặc trưng', color=B, dy=0, lx=480, ly=225)
S.arrow(S.anchor('ai', 'r', 0.2), S.anchor('evt', 'l', 0.7), 'nhãn + độ tin cậy', color=B)
S.arrow(S.anchor('dsp', 'r', 0.3), S.anchor('evt', 'l', 0.3), 'HR, SpO2', color=B)
S.arrow(S.anchor('ai', 'r', 0.7), S.anchor('buf', 'l', 0.5), 'tổng hợp', color=B)
S.arrow(S.anchor('evt', 'r', 0.5), S.anchor('wifi', 'l', 0.5), 'khẩn', color='#c00000')
S.arrow(S.anchor('buf', 'b', 0.5), S.anchor('wifi', 'b', 0.87), 'lô 15 phút', color=B, pts=[(755, 420), (1210, 420), (1210, 205), (1150, 205)], lx=980, ly=414)
S.arrow(S.anchor('evt', 'b', 0.8), S.anchor('ble', 'l', 0.4), 'không WiFi', color='#c00000', pts=[(824, 230), (900, 230), (900, 280)], lx=880, ly=226)
S.arrow(S.anchor('wifi', 'r'), S.anchor('srv', 'l', 0.2), 'TLS', color=B)
S.arrow(S.anchor('ble', 'r'), S.anchor('srv', 'l', 0.75), 'điện thoại chuyển tiếp', color=B, lx=1220, ly=272)
S.note(30, 450, 'Cảnh báo AF/nhịp bất thường chỉ là SÀNG LỌC (screening), không phải chẩn đoán y khoa - hiển thị khuyến cáo đi khám.\n'
       'Mọi model chạy trên đồng hồ: dữ liệu thô không cần rời thiết bị, chỉ gửi kết quả + tổng hợp → tiết kiệm pin và riêng tư.', 13)
S.save('data_flow')
