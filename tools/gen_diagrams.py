"""Block diagram, power tree and system/data-flow diagram of the health watch -> docs/img/*.svg + *.png (rsvg-convert).
Boxes and arrows are declared below; every arrow carries the interface / signal name. Net names match design.py."""
import shutil, tempfile
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
        if shutil.which('rsvg-convert'):
            subprocess.run(['rsvg-convert', '-w', str(s.w * 2), '-o', p + '.png', p + '.svg'], check=True)
        else:   # Chrome: also honours paint-order, which keeps the arrow labels readable (cairosvg does not)
            with tempfile.TemporaryDirectory() as tmp:
                subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--hide-scrollbars', '--user-data-dir=' + tmp, '--force-device-scale-factor=2',
                                '--window-size=%d,%d' % (s.w, s.h), '--default-background-color=FFFFFFFF', '--screenshot=' + os.path.abspath(p + '.png'),
                                'file://' + os.path.abspath(p + '.svg')], check=True, capture_output=True)
        print('->', p + '.png')

# ------------------------------------------------------------------ 1. hardware block diagram
B = '#1f4e9a'; P = '#c55a11'; G = '#2e7d32'; R = '#c00000'; K = '#555555'
S = SVG(1500, 985, 'Sơ đồ khối phần cứng: bo chính và bo cảm biến')
S.frame(15, 45, 1470, 545, 'BO CHÍNH (sau màn hình AMOLED), PCB 4 lớp')
S.frame(15, 625, 1470, 345, 'BO CẢM BIẾN (đáy vỏ, áp vào da)')
S.box('usb', 60, 80, 230, 66, 'USB-C', ['sạc 5 V + USB 2.0 FS', 'ESD: USBLC6-2SC6'], 'conn')
S.box('pmic', 60, 190, 230, 116, 'PMIC AXP2101', ['sạc LiPo, fuel gauge, NTC, nút nguồn', 'DCDC1 3,3 V / 2 A', 'VBUS → buck → L102, R105 → VSYS', 'PWROK → CHIP_PU, IRQ', '(mặc định do OTP)'], 'pwr')
S.box('bat', 60, 345, 230, 52, 'Pin LiPo 1S, 400 mAh', ['shunt 50 mΩ + test point'], 'pwr')
S.box('boost', 60, 440, 230, 80, 'Boost TPS61240', ['VSYS → VLED 5 V', 'EN = GPIO3 (giữ bằng RTC hold)', 'shunt 0,1 Ω'], 'pwr')
S.box('flash', 530, 75, 140, 60, 'Flash 16 MB', ['W25Q128JV (QSPI)'], 'mcu')
S.box('ant', 700, 75, 140, 60, 'Ăng-ten gốm', ['2,4 GHz + mạch π'], 'mcu')
S.box('mcu', 520, 180, 330, 210, 'ESP32-S3R8', ['2 × LX7 240 MHz, lệnh vector', '8 MB PSRAM octal trong chip', 'WiFi 802.11 b/g/n + BLE 5', '', 'Edge AI (TFLite Micro + ESP-NN, int8):', 'té ngã + hoạt động', 'mẫu mạch không đều (thử nghiệm)', '', 'USB Serial/JTAG; GPIO47/48 còn trống'], 'ai')
S.box('disp', 1100, 165, 300, 80, 'AMOLED 1,75" 466×466', ['driver CO5300 (QSPI)', 'cảm ứng CST9217 (I2C)', 'FPC 31 chân 0,3 mm'], 'ui')
S.box('ui', 1100, 275, 300, 80, 'Giao diện', ['motor rung, còi 4 kHz (qua AO3400A)', 'nút SOS, nút nguồn', 'LED trạng thái, LED sạc'], 'ui')
S.box('dbg', 1100, 395, 300, 66, 'Debug và đo', ['UART0, BOOT, RESET', 'test point: nguồn, I2C, SPI, PPG_INT'], 'conn')
S.box('rtc', 360, 455, 160, 60, 'RTC PCF85063A', ['32,768 kHz, INT'], 'sens')
S.box('imu', 560, 455, 160, 60, 'IMU BMI270', ['6 trục, FIFO, INT1/2'], 'sens')
S.box('fpcm', 760, 455, 240, 60, 'FPC 16 chân (J105)', ['3V3, VLED, SPI, INT, I2C'], 'conn')
S.box('fpcs', 760, 655, 240, 60, 'FPC 16 chân (J201)', ['cùng thứ tự chân'], 'conn')
S.box('ldo', 60, 790, 200, 66, 'LDO LP5907 1,8 V', ['nhiễu thấp', 'shunt 0,1 Ω'], 'pwr')
S.box('txs', 340, 790, 200, 66, 'TXS0108E', ['chuyển mức 1,8 ↔ 3,3 V', 'SPI + INT'], 'conn')
S.box('afe', 640, 770, 240, 110, 'AFE MAX86141', ['3 driver LED, 2 ADC 19-bit', 'FIFO 128 mục, SPI 1,8 V', 'PD_GND về GND tại 1 điểm', '(R205 0 Ω)'], 'sens')
S.box('opt', 990, 770, 240, 110, 'Quang học', ['SFH 7016: xanh 530, đỏ 655,', 'hồng ngoại 940 nm', '2 × photodiode VEMD8080', 'vách chắn LED ↔ PD'], 'sens')
S.box('tmp', 1280, 770, 180, 66, 'MAX30208', ['nhiệt độ (xu hướng)', 'I2C 0x52'], 'sens')
S.arrow(S.anchor('usb', 'b'), S.anchor('pmic', 't'), 'VBUS', color=P, lx=205, ly=172)
S.arrow(S.anchor('bat', 't'), S.anchor('pmic', 'b'), 'VBAT', both=True, color=P, lx=210, ly=330)
S.arrow(S.anchor('pmic', 'l', 0.8), S.anchor('boost', 'l', 0.5), 'VSYS', color=P, pts=[(35, 283), (35, 480)], lx=60, ly=420, width=1.8)
S.arrow(S.anchor('usb', 'r'), (520, 215), 'USB D+/D− (GPIO19/20)', color=B, pts=[(405, 113), (405, 215)], lx=405, ly=105)
S.arrow((290, 250), (520, 250), '+3V3 (DCDC1)', color=P)
S.arrow((520, 290), (290, 290), 'I2C, IRQ, PWROK', both=True, color=B)
S.arrow((600, 180), (600, 135), 'QSPI', both=True, color=B, lx=628, ly=162)
S.arrow((770, 180), (770, 135), 'RF', both=True, color=B, lx=790, ly=162)
S.arrow((850, 205), (1100, 205), 'QSPI, CS, TE, RST, I2C, TP_INT', both=True, color=B)
S.arrow((850, 315), (1100, 315), 'PWM GPIO45/46, GPIO8, GPIO18', both=True, color=B)
S.arrow((850, 370), (1100, 428), 'UART0', both=True, color=B, pts=[(960, 370), (960, 428)], lx=985, ly=420)
S.arrow(S.anchor('rtc', 't'), (560, 390), 'I2C + INT', both=True, color=B, pts=[(440, 425), (560, 425)], lx=470, ly=420)
S.arrow(S.anchor('imu', 't', 0.6), (656, 390), 'I2C + INT1/2', both=True, color=B, lx=696, ly=425)
S.arrow(S.anchor('fpcm', 't', 0.15), (796, 390), 'SPI 3,3 V, INT, I2C', both=True, color=B, lx=860, ly=425)
S.arrow(S.anchor('boost', 'r'), S.anchor('fpcm', 'b', 0.2), 'VLED 5 V', color=P, pts=[(320, 480), (320, 555), (808, 555)], lx=560, ly=550)
S.arrow(S.anchor('fpcm', 'b', 0.6), S.anchor('fpcs', 't', 0.6), 'cáp FFC (đo thông mạch trước khi cấp nguồn)', both=True, color=K, lx=1040, ly=610)
S.arrow(S.anchor('fpcs', 'l', 0.35), S.anchor('ldo', 't'), '+3V3', color=P, pts=[(160, 676)], lx=450, ly=671)
S.arrow(S.anchor('fpcs', 'b', 0.1), S.anchor('txs', 't'), 'SPI, INT 3,3 V', both=True, color=B, pts=[(784, 745), (440, 745)], lx=610, ly=740)
S.arrow(S.anchor('fpcs', 'b', 0.6), S.anchor('afe', 't', 0.75), 'VLED', color=P, pts=[(904, 745), (820, 745)], lx=868, ly=740)
S.arrow(S.anchor('fpcs', 'r', 0.3), S.anchor('opt', 't', 0.3), 'VLED 5 V', color=P, pts=[(1062, 673)], lx=1030, ly=668)
S.arrow(S.anchor('fpcs', 'r', 0.7), S.anchor('tmp', 't'), 'I2C + 3V3', both=True, color=B, pts=[(1370, 697)], lx=1200, ly=692)
S.arrow(S.anchor('ldo', 'r'), S.anchor('txs', 'l'), '+1V8', color=P)
S.arrow(S.anchor('txs', 'r'), (640, 823), 'SPI, INT 1,8 V', both=True, color=B, lx=590, ly=815)
S.arrow(S.anchor('ldo', 'b'), S.anchor('afe', 'b', 0.3), '+1V8 (VDD_ANA, VDD_DIG)', color=P, pts=[(160, 925), (712, 925)], lx=430, ly=920)
S.arrow((880, 805), (990, 805), 'LED1/2/3_DRV', color=G)
S.arrow((990, 850), (880, 850), 'PD1, PD2', color=G)
S.save('block_diagram')

# ------------------------------------------------------------------ 2. power tree
S = SVG(1400, 545, 'Cây nguồn và điểm đo dòng (shunt + test point)')
S.box('vbus', 30, 80, 170, 56, 'USB VBUS 5 V', ['TP101'], 'conn')
S.box('bat', 30, 225, 170, 70, 'LiPo 1S 400 mAh', ['R111 50 mΩ', 'TP102 ↔ TP103'], 'pwr')
S.box('pmic', 270, 70, 250, 240, 'AXP2101', ['VBUS → VMID; R126 không lắp', 'buck: VMID → chân SW', 'BATFET: BAT ↔ VSYS', 'DCDC1 3 MHz → 3V3_PMIC', 'VRTC, VREF', 'NTC trên bo → ngắt sạc', 'DCDC2-4, LDO: không dùng', '', 'Mặc định do OTP: phải đọc', 'thanh ghi trên bo thật'], 'pwr')
S.box('l102', 580, 215, 150, 66, 'L102 1 µH', ['R105 0 Ω 0805', 'mang dòng USB vào'], 'pwr')
S.box('v33', 790, 70, 260, 70, '+3V3 (R112 0,1 Ω)', ['TP104 ↔ TP105', 'ESP32, flash, màn hình, IMU, RTC'], 'pwr')
S.box('vsys', 790, 215, 260, 66, 'VSYS (theo pin; đo khi có USB)', ['motor, còi qua MOSFET', 'LED sạc, boost'], 'pwr')
S.box('boost', 790, 345, 260, 56, 'TPS61240 → VLED_5V', ['R114 0,1 Ω: TP108 ↔ TP109'], 'pwr')
S.box('ldo', 1110, 70, 270, 70, 'LP5907 1,8 V (bo cảm biến)', ['R201 0,1 Ω: TP201 ↔ TP202', 'MAX86141 VDD, TXS0108E VCCA, OE'], 'pwr')
S.box('sens33', 1110, 190, 270, 56, '+3V3 bo cảm biến', ['MAX30208, TXS0108E VCCB'], 'sens')
S.box('vled', 1110, 345, 270, 56, 'VLED (bo cảm biến)', ['anode SFH 7016 → MAX86141 LEDx_DRV'], 'sens')
S.arrow(S.anchor('vbus', 'r'), (270, 108), '', color=P)
S.arrow(S.anchor('bat', 'r'), (270, 260), '', both=True, color=P)
S.arrow((520, 105), S.anchor('v33', 'l'), 'DCDC1 (L101, FB1)', color=P, lx=650, ly=99)
S.arrow((520, 248), S.anchor('l102', 'l'), 'SW', color=P)
S.arrow(S.anchor('l102', 'r'), S.anchor('vsys', 'l'), '', color=P)
S.arrow(S.anchor('vsys', 'b'), S.anchor('boost', 't'), 'EN = GPIO3, R113 1 MΩ', color=P, lx=1000, ly=318)
S.arrow(S.anchor('v33', 'r'), S.anchor('ldo', 'l'), 'FPC', color=P)
S.arrow((1080, 105), S.anchor('sens33', 'l'), '', color=P, pts=[(1080, 218)])
S.arrow(S.anchor('boost', 'r'), S.anchor('vled', 'l'), 'FPC', color=P)
S.note(30, 450, 'Đo dòng: đo mV giữa hai test point của shunt, I = V / R_shunt (R111 = 0,05 Ω; R112, R114, R201 = 0,1 Ω). Ví dụ 10 mV trên R112 = 100 mA.\n'
       'Trình tự: AXP2101 khởi động DCDC1 → PWROK nhả CHIP_PU → ESP32 chạy → ESP32 bật boost khi đo PPG.\n'
       'Bảo vệ pin: firmware đặt ngưỡng VOFF (REG24) = 3,3 V và cắt WiFi, độ sáng, rung theo VBAT; UVP của DCDC1 tắt PMIC ở 2,805 V.\n'
       'VCCA (1,8 V) ≤ VCCB (3,3 V) của TXS0108E luôn đúng vì 1,8 V lấy từ 3,3 V; OE nối thẳng VCCA.\n'
       'R112 nằm sau FB1 nên không được bù: ở 0,6 A, +3V3 giảm 60 mV.', 13)
S.save('power_tree')

# ------------------------------------------------------------------ 3. system / data flow
S = SVG(1500, 590, 'Luồng dữ liệu: cảm biến → xử lý trên đồng hồ → web')
S.box('ppg', 30, 80, 190, 66, 'PPG (MAX86141)', ['25 mẫu/s; burst 100 mẫu/s', 'ngắt theo watermark FIFO'], 'sens')
S.box('imu', 30, 230, 190, 66, 'IMU (BMI270)', ['50 Hz, FIFO', 'đếm bước trong chip'], 'sens')
S.box('tmp', 30, 400, 190, 52, 'Nhiệt độ (MAX30208)', ['1 lần/phút, xu hướng'], 'sens')
S.box('dsp', 290, 70, 280, 130, 'Xử lý tín hiệu', ['task ưu tiên cao trên core 1', 'lọc, khử nhiễu bằng gia tốc', 'nhịp tim, IBI/PRV', 'cờ chất lượng, phát hiện tháo tay', 'SpO2 thử nghiệm, không cảnh báo', 'căn đồng hồ PPG với BMI'], 'mcu')
S.box('ai', 290, 245, 280, 125, 'Edge AI (TFLite Micro int8)', ['chạy trong SRAM nội', 'té ngã: va chạm → CNN', 'hoạt động: ít lớp', 'mẫu mạch không đều (thử nghiệm)', 'ngủ/thức, thời lượng'], 'ai')
S.box('evt', 640, 70, 250, 125, 'Quyết định cảnh báo', ['té ngã: nằm yên 5-10 s, hủy 30-60 s', 'SOS: gửi ngay', 'mạch không đều: kéo dài ≥ 30 phút,', 'thông báo không khẩn', 'pin yếu: giữ dự trữ cho SOS'], 'ui')
S.box('buf', 640, 290, 250, 80, 'Log vòng trên flash', ['dữ liệu tổng hợp 1 phút', 'hàng đợi sự kiện chưa có ACK'], 'mcu')
S.box('wifi', 960, 70, 230, 96, 'WiFi HTTPS', ['lô 15 phút, có backoff', 'sự kiện: event ID + ACK, retry', 'OTA có chữ ký, rollback'], 'ext')
S.box('loc', 960, 200, 230, 66, 'Báo tại chỗ', ['rung, còi, màn hình', 'luôn chạy, kể cả khi mất mạng'], 'ui')
S.box('ble', 960, 400, 230, 66, 'BLE (điện thoại)', ['cấu hình WiFi (provisioning)', 'không phải đường gửi khẩn'], 'ext')
S.box('srv', 1260, 70, 215, 180, 'Server + web tự viết', ['đăng nhập, phân quyền', 'hash token thiết bị', 'mã hóa khi lưu, retention', 'consent, xóa dữ liệu', 'đẩy cảnh báo cho người thân', 'dashboard, phát hành OTA'], 'ext')
S.arrow(S.anchor('ppg', 'r'), (290, 113), 'SPI', color=B)
S.arrow((220, 250), (290, 165), 'gia tốc', color=B, pts=[(255, 250), (255, 165)], lx=227, ly=205)
S.arrow((220, 280), (290, 280), 'I2C', color=B)
S.arrow(S.anchor('tmp', 'r'), (640, 345), 'I2C', color=B, pts=[(600, 426), (600, 345)], lx=400, ly=420)
S.arrow((430, 195), (430, 245), 'đặc trưng', color=B, lx=475, ly=224)
S.arrow((570, 110), (640, 110), 'HR', color=B)
S.arrow((570, 270), (640, 170), 'nhãn', color=B, pts=[(605, 270), (605, 170)], lx=605, ly=225)
S.arrow((570, 320), (640, 320), 'tổng hợp', color=B)
S.arrow((890, 100), (960, 100), 'khẩn', color=R)
S.arrow((890, 165), (960, 233), '', color=R, pts=[(925, 165), (925, 233)])
S.arrow((765, 195), (765, 290), 'hàng đợi', color=R, lx=805, ly=248)
S.arrow((890, 345), (1190, 140), 'lô 15 phút', color=B, pts=[(1225, 345), (1225, 140)], lx=1040, ly=340)
S.arrow((1190, 100), (1260, 100), 'TLS', both=True, color=B)
S.note(30, 505, 'Ngoài vùng WiFi: cảnh báo chỉ báo tại chỗ và nằm trong hàng đợi đến khi có mạng. Muốn báo từ xa khi không có WiFi cần app native hoặc LTE-M.\n'
       'Nguyên mẫu nghiên cứu, không phải thiết bị y tế: SpO2 và mẫu mạch không đều là thử nghiệm, không dùng để chẩn đoán.\n'
       'Dữ liệu thô không rời thiết bị trong vận hành thường; chế độ ghi riêng qua USB/BLE để tự thu. HR, SpO2 vẫn là dữ liệu sức khỏe: cần consent và TLS.\n'
       'Bỏ khỏi kế hoạch: phân giai đoạn ngủ, stress, gửi vị trí.', 13)
S.save('data_flow')

# ------------------------------------------------------------------ 4. alert logic
S = SVG(1500, 490, 'Logic cảnh báo: giảm báo động giả trước khi làm phiền người dùng')
S.note(30, 70, 'Té ngã', 15, color='#222')
S.box('f1', 30, 85, 200, 70, 'Va chạm', ['any-motion + độ lớn gia tốc', 'trong firmware'], 'sens')
S.box('f2', 280, 85, 200, 70, 'CNN trên vòng đệm', ['cửa sổ căn quanh va chạm'], 'ai')
S.box('f3', 530, 85, 200, 70, 'Nằm yên 5-10 s?', ['nếu không: bỏ qua'], 'mcu')
S.box('f4', 780, 85, 200, 70, 'Đếm ngược 30-60 s', ['rung, còi; người dùng hủy được'], 'ui')
S.box('f5', 1030, 85, 200, 70, 'Gửi sự kiện', ['event ID, chờ ACK'], 'ext')
S.box('f6', 1280, 85, 190, 70, 'Server', ['đẩy cho người thân'], 'ext')
for a, b in (('f1', 'f2'), ('f2', 'f3'), ('f3', 'f4'), ('f4', 'f5'), ('f5', 'f6')): S.arrow(S.anchor(a, 'r'), S.anchor(b, 'l'), '', color=B)
S.note(30, 205, 'SOS', 15, color='#222')
S.box('s1', 30, 220, 200, 60, 'Nhấn nút SOS', ['GPIO8'], 'ui')
S.arrow(S.anchor('s1', 'r'), (1130, 155), 'bỏ qua bước phân loại: gửi ngay', color=R, pts=[(1130, 250)], lx=620, ly=244)
S.note(30, 325, 'Mẫu mạch không đều (thử nghiệm)', 15, color='#222')
S.box('a1', 30, 340, 200, 70, 'Cửa sổ IBI 100 mẫu/s', ['đứng yên, chất lượng đạt'], 'mcu')
S.box('a2', 280, 340, 200, 70, 'Phân loại', ['loại tín hiệu kém'], 'ai')
S.box('a3', 530, 340, 200, 70, 'Lặp lại ≥ 30 phút?', ['nếu không: bỏ qua'], 'mcu')
S.box('a4', 780, 340, 200, 70, 'Thông báo không khẩn', ['không còi; khuyên đi khám'], 'ui')
S.box('a5', 1030, 340, 200, 70, 'Ghi vào lô', ['không phải sự kiện khẩn'], 'mcu')
for a, b in (('a1', 'a2'), ('a2', 'a3'), ('a3', 'a4'), ('a4', 'a5')): S.arrow(S.anchor(a, 'r'), S.anchor(b, 'l'), '', color=B)
S.note(30, 450, 'Lý do: 43.200 cửa sổ/ngày ở bước 2 s; cảnh báo theo từng cửa sổ thì độ đặc hiệu 99,9 % vẫn cho 43 lần báo giả/ngày. Tham số trên là điểm khởi đầu, phải đánh giá bằng báo giả/ngày khi đeo nhiều ngày.\n'
       'Mất mạng: sự kiện nằm trong hàng đợi flash, thiết bị vẫn báo tại chỗ, gửi lại khi có WiFi.', 12.5)
S.save('alert_flow')
