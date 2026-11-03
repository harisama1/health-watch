"""Design-analysis report of the health watch -> docs/health_watch_design_report.md (then tools/md2pdf.py -> outputs/*.pdf).
All per-part tables come from design.py, all datasheet numbers from facts.py (page-checked), the power budget is computed here."""
import os, sys, re, collections, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D
import facts as F
OUT = os.path.join(HERE, '..', 'docs', 'health_watch_design_report.md')
v, c = F.val, F.cite
L = []
def w(s=''): L.append(s)
def table(head, rows):
    w('| ' + ' | '.join(head) + ' |'); w('|' + '---|' * len(head))
    for r in rows: w('| ' + ' | '.join(str(x).replace('|', '/').replace('\n', ' ') for x in r) + ' |')
    w()

# ------------------------------------------------------------------ power budget (named inputs)
VBAT_NOM, EFF_DCDC, EFF_BOOST, CAP_MAH, USABLE = 3.7, 0.90, 0.85, 400, 0.85
def from3v3(i): return i * 3.3 / (VBAT_NOM * EFF_DCDC)          # mA at the battery for a load on +3V3
def from5v(i): return i * 5.0 / (VBAT_NOM * EFF_BOOST)           # mA at the battery for a load on VLED 5 V
A = 'ASSUME'
LOADS = [  # (name, battery mA average, how it is computed, source)
 ('ESP32-S3 light-sleep nền', from3v3(v('esp_light')), '%.3f mA × 100 %% thời gian' % v('esp_light'), c('esp_light')),
 ('Màn hình AMOLED sáng (5 % thời gian)', from3v3(40 * 0.05), '40 mA × 5 % (giơ tay xem ~72 phút/ngày)', A + ': chưa có datasheet panel; đo bằng R112'),
 ('ESP32 chạy giao diện khi màn sáng', from3v3(v('esp_160') * 0.05), '%.1f mA × 5 %%' % v('esp_160'), c('esp_160')),
 ('AI té ngã/hoạt động (mỗi 2 s, 20 ms @240 MHz)', from3v3(v('esp_240') * 0.020 / 2), '%.1f mA × 1 %%' % v('esp_240'), c('esp_240') + '; thời gian suy luận ' + A),
 ('Xử lý PPG + HR mỗi 1 s (5 ms @160 MHz)', from3v3(v('esp_160') * 0.005), '%.1f mA × 0.5 %%' % v('esp_160'), c('esp_160') + '; ' + A),
 ('WiFi HTTPS: 96 lần/ngày × 3 s × 120 mA', from3v3(120 * 96 * 3 / 86400), 'kết nối + TLS + POST; TB giữa RX %d mA / TX đỉnh %d mA' % (v('wifi_rx'), v('wifi_tx')), c('wifi_tx') + '; 120 mA TB và 3 s là ' + A),
 ('LED PPG xanh, 25 sps liên tục (ngày)', from5v(v('afe_led25')) * 16 / 24, '%.3f mA ở VLED × 16 h' % v('afe_led25'), c('afe_led25')),
 ('LED PPG 100 sps ban đêm (HRV giấc ngủ)', from5v(v('afe_led100')) * 8 / 24, '%.3f mA ở VLED × 8 h' % v('afe_led100'), c('afe_led100')),
 ('SpO2 đo nhanh 30 s mỗi 10 phút (đỏ + IR)', from5v(2 * v('afe_led100')) * 0.05, '2 LED × %.3f mA × 5 %%' % v('afe_led100'), c('afe_led100')),
 ('MAX86141 VDD (1.8 V)', from3v3(v('afe_vdd25') + v('lp_iq')), 'AFE %.3f + LDO Iq %.3f mA' % (v('afe_vdd25'), v('lp_iq')), c('afe_vdd25') + ', ' + c('lp_iq')),
 ('Boost TPS61240 Iq khi bật (24 h)', v('tps_iq'), '%.3f mA từ VSYS' % v('tps_iq'), c('tps_iq')),
 ('BMI270 acc + gyro normal', from3v3(v('imu_ag')), '%.3f mA (gyro cần cho té ngã)' % v('imu_ag'), c('imu_ag')),
 ('AXP2101 tĩnh khi chạy', 0.10, '~0.1 mA', A + ' (datasheet chỉ ghi %.0f µA khi tắt, %s)' % (v('axp_off') * 1000, c('axp_off'))),
 ('MAX30208, RTC, TXS0108E, pull-up', from3v3(v('m30_stby') + 0.01), '~0.01 mA', c('m30_stby') + '; còn lại ' + A),
 ('Motor/còi: 10 cảnh báo × 2 s × 80 mA', 80 * 20 / 86400, 'từ VSYS', A),
]
TOTAL = sum(x[1] for x in LOADS)
HOURS = CAP_MAH * USABLE / TOTAL
NAIVE = [('Màn hình luôn sáng', from3v3(40)), ('CPU luôn chạy 160 MHz, không ngủ', from3v3(v('esp_160'))), ('WiFi luôn kết nối (modem ~20 mA TB)', from3v3(20)),
         ('PPG 100 sps liên tục', from5v(v('afe_led100'))), ('IMU + các IC khác', from3v3(v('imu_ag')) + 0.1)]
NAIVE_T = sum(x[1] for x in NAIVE)

# ------------------------------------------------------------------ report
today = datetime.date(2026, 11, 4).isoformat()
nm = len(D.MAIN); ns = len(D.SENSOR)
w('# Báo cáo phân tích thiết kế - Đồng hồ đeo tay theo dõi sức khỏe (edge AI + web)')
w()
w('Phiên bản 1.0 - %s. Thiết kế đã chốt sau 7 vòng audit hỏi-đáp với người làm đồ án. Báo cáo sinh tự động bởi `tools/gen_report.py` từ `tools/design.py` '
  '(linh kiện, net, lý do, trích dẫn) và `tools/facts.py` (số liệu datasheet đã đối chiếu trang).' % today)
w()
w('## 1. Tóm tắt')
w()
w('Đồng hồ đo **nhịp tim, SpO2, nhiệt độ da, chuyển động**, chạy **3 nhóm model AI ngay trên đồng hồ** (té ngã + hoạt động, nhịp tim bất thường/rung nhĩ, giấc ngủ/stress) '
  'và gửi kết quả lên **web tự viết** qua WiFi HTTPS (lô 15 phút, sự kiện khẩn gửi ngay, dự phòng BLE → điện thoại).')
w()
table(['Hạng mục', 'Kết quả'], [
 ('Phần cứng', '2 PCB: bo chính (%d linh kiện) + bo cảm biến (%d linh kiện) nối FPC 16 chân' % (nm, ns)),
 ('Bộ xử lý', 'ESP32-S3R8 (2 × LX7 240 MHz, 8 MB PSRAM, WiFi + BLE 5) + flash 16 MB'),
 ('Cảm biến', 'MAX86141 + SFH 7013 + 2 × VEMD8080 (PPG), BMI270 (IMU), MAX30208 (nhiệt độ da)'),
 ('Nguồn', 'AXP2101 + LiPo ~400 mAh, USB-C; boost 5 V riêng cho LED PPG'),
 ('Ngân sách pin (ước tính)', '**%.1f mA trung bình → ~%.0f giờ (%.1f ngày)** với %d mAh × %d %% dùng được; đạt mục tiêu ≥ 1 ngày' % (TOTAL, HOURS, HOURS / 24, CAP_MAH, USABLE * 100)),
 ('Schematic', 'KiCad 9, phân cấp, **đi dây như vẽ tay** (tụ, thạch anh, RF, USB, LED, MOSFET, LDO/boost nối dây thật; nhãn chỉ cho tín hiệu giữa khối/trang): bo chính 4 trang, bo cảm biến 1 trang. **ERC 0 lỗi / 0 cảnh báo**, kết nối khớp `design.py` 100 %% (%d + %d chân)'
  % (sum(len(p['pins']) for p in D.MAIN), sum(len(p['pins']) for p in D.SENSOR))),
 ('Trích dẫn', '%d số liệu datasheet đã mở lại đúng trang PDF và khớp (script `tools/facts.py`)' % len(F.F)),
 ('Chưa làm', 'Layout PCB, đặt hàng, đo trên phần cứng, firmware, model AI, web'),
])
w('File: `outputs/health_watch_main_schematic.pdf`, `outputs/health_watch_sensor_schematic.pdf`, `docs/img/block_diagram.png`, `docs/img/power_tree.png`, `docs/img/data_flow.png`; '
  'project KiCad trong `hardware/main`, `hardware/sensor`.')
w()
w('## 2. Quyết định thiết kế (kết quả audit)')
w()
table(['Câu hỏi', 'Quyết định', 'Lý do / hệ quả', 'Phương án không chọn'], [
 ('Mức độ hoàn thiện', 'PCB tự thiết kế, cỡ đồng hồ nhưng được phép to hơn (demo)', 'Có chỗ cho test point, shunt đo dòng, header debug', 'ghép module có sẵn'),
 ('Đưa dữ liệu lên web', 'WiFi trực tiếp (ESP32-S3) + BLE', 'Không cần điện thoại để đồng bộ; tốn pin hơn BLE-only → giới hạn số lần bật WiFi', 'nRF52 BLE-only; 2 chip'),
 ('Dạng chip', 'ESP32-S3R8 chip trần + anten gốm', 'Giống bo Waveshare 1.75C → dùng lại mạch RF/thạch anh/flash đã chạy; cần tune mạch π bằng VNA', 'module ESP32-S3-MINI-1'),
 ('Cảm biến', 'PPG + IMU + nhiệt độ da (không ECG)', 'Rung nhĩ phát hiện từ khoảng nhịp PPG → chỉ là sàng lọc', 'ECG MAX30003'),
 ('AFE PPG', 'MAX86141 + LED/PD rời (người làm chọn)', 'Tín hiệu tốt nhất, 2 PD chống nhiễu cử động; **WLP 0.4 mm bắt buộc PCBA**', 'MAXM86161, MAXM86146'),
 ('Edge AI', 'Cả 3: té ngã + hoạt động, nhịp bất thường, giấc ngủ/stress', 'Train trên Google Colab, int8, TFLite Micro + ESP-NN', 'chỉ 1 model'),
 ('Màn hình', 'AMOLED 1.75" CO5300 QSPI + touch (như bản clone)', 'Dùng lại FPC, GPIO, code mẫu Waveshare', '1.43" tròn, LCD GC9A01'),
 ('Pin', '≥ 1 ngày, LiPo ~400 mAh', 'Ước tính %.1f ngày (mục 7)' % (HOURS / 24), '≥ 3 ngày'),
 ('Nguồn', 'PMIC AXP2101', 'Sạc + DCDC + fuel gauge + nút nguồn trong 1 IC, có bo tham chiếu', 'BQ25180 + TPS62840 + MAX17048'),
 ('Sạc/nạp', 'USB-C (sạc + nạp + USB-JTAG)', 'Không cần chip USB-UART', 'pogo + đế sạc'),
 ('Giao diện', 'Motor rung, 2 nút (nguồn, SOS), còi từ, RTC ngoài, LED trạng thái', 'Báo động không cần nhìn màn hình', 'loa I2S, codec + mic'),
 ('IMU', 'BMI270 trên bo chính', 'Tính năng cổ tay, FIFO 2 KB; hai bo gắn cứng nên chuyển động giống nhau', 'QMI8658, LSM6DSOX'),
 ('PCB', '4 lớp, 2 bo nối FPC', 'RF cần mặt GND liền; bo cảm biến riêng ở đáy vỏ áp da', '1 bo 2 mặt'),
 ('Giao thức', 'HTTPS POST theo lô 15 phút; sự kiện khẩn gửi ngay; BLE → điện thoại khi mất WiFi', 'Đơn giản, web tự viết REST API', 'MQTT, WebSocket'),
 ('Firmware', 'ESP-IDF + FreeRTOS', 'Quản lý nguồn tốt (auto light-sleep, tickless idle); cần cài lại ESP-IDF', 'Arduino core'),
])
w('Bổ sung sau khi đọc datasheet (không đổi kiến trúc đã chốt):')
w()
w('- **Boost 5 V cho LED (TPS61240)**: LED xanh lá có VF tối đa %.2f V (%s); cộng phần áp cho bộ lái dòng thì cần VLED ≥ ~3.85 V, nhưng pin LiPo về cuối chỉ còn ~3.4 V. '
  'MAX86141 cho VLED %.1f-5.5 V (%s) và đặc tả đo ở 5.0 V.' % (v('sfh_vf_g'), c('sfh_vf_g'), v('afe_vled'), c('afe_vled')))
w('- **LDO 1.8 V + chuyển mức TXS0108E**: MAX86141 chạy 1.7-2.0 V (%s), chân SPI chịu tối đa %.1f V (%s), không nối thẳng với ESP32 3.3 V được. '
  'Ngược lại, ESP32 cần VIH ≥ 0.75·VDD = 2.5 V (DS Table 5-4 p.65), nên mức 1.8 V của MAX86141 không đủ.' % (c('afe_vdd'), v('afe_absmax'), c('afe_absmax')))
w('- **Địa chỉ I2C MAX30208 = 0x52**: mặc định 0x50 + 2 bit GPIO dễ trùng RTC 0x51 → nối cứng GPIO1 = 1, GPIO0 = 0 (M30 Table 3 p.10), đọc nhiệt độ theo chu kỳ, không dùng INT.')
w()
w('## 3. Kiến trúc')
w()
w('<img src="img/block_diagram.png" width="700">')
w()
w('Hình 1. Sơ đồ khối phần cứng. Mũi tên xanh = tín hiệu (ghi giao tiếp), cam = nguồn, xanh lá = tín hiệu quang/analog.')
w()
w('<img src="img/power_tree.png" width="700">')
w()
w('Hình 2. Cây nguồn và điểm đo dòng.')
w()
w('<img src="img/data_flow.png" width="700">')
w()
w('Hình 3. Luồng dữ liệu từ cảm biến qua edge AI tới web.')
w()
w('## 4. Phân tích từng khối')
w()
w('### 4.1 Nguồn - AXP2101, pin, USB-C')
w()
w('- Mạch theo hình 7-1 của datasheet (AXP Fig 7-1 p.57) và bo Waveshare 1.75C (cùng chip): VSYS 2 × 22 µF (%s), BAT 1 µF, VBUS/VMID 10 µF, DCDC1 1 µH + 22 µF. '
  'DCDC2-4, ALDO/BLDO/DLDO không dùng: để trống như bo tham chiếu (WS p.1). Chân SW (DCDC5) giữ cấu trúc của Waveshare (L 1 µH về VSYS).' % c('axp_vsys'))
w('- **PWROK → CHIP_PU**: ESP32 chỉ chạy khi PMIC báo nguồn ổn định, kết hợp RC 10 kΩ/1 µF theo HDG §1.3.3 p.8.')
w('- Dòng sạc đặt bằng thanh ghi ICHG của AXP2101; firmware đặt **200 mA ≈ 0.5C** cho pin 400 mAh (AXP p.23). NTC 10 kΩ trên chân TS ngắt sạc khi pin nóng.')
w('- I2C hệ thống kéo lên 2.2 kΩ (yêu cầu của AXP2101, %s). Thời gian lên t_r = 0.8473·R·C = 0.8473 × 2.2 kΩ × 100 pF ≈ %.0f ns < 300 ns (Fast-mode 400 kHz) với 5 thiết bị + FPC (C bus 100 pF: **ASSUME**).'
  % (c('axp_sda'), 0.8473 * 2200 * 100e-12 * 1e9))
w('- Shunt đo dòng: R111 50 mΩ (pin), R112 0.1 Ω (3V3), R114 0.1 Ω (VLED), R201 0.1 Ω (1V8). Sụt áp lớn nhất: 3V3 ở 400 mA → 40 mV (1.2 %), chấp nhận được; đo ngủ sâu thì tháo shunt, nối đồng hồ µA.')
w()
w('### 4.2 ESP32-S3R8, flash, RF')
w()
w('- Theo sơ đồ tham chiếu HDG Fig.1 p.5: VDD3P3 lọc LC 2.0 nH + 10 µF/1 µF/100 nF; VDDA 1 µF + 10 nF; thạch anh 40 MHz với 24 nH nối tiếp XTAL_P và tụ tải 22 pF '
  '(CL = 22·22/44 + ~4 pF ký sinh ≈ 15 pF, HDG §1.3.5 p.10-11).')
w('- S3R8 không có flash trong chip → W25Q128JV 16 MB qua SPI0 (chân 30-35), VDD_SPI = 3.3 V vì GPIO45 = 0 khi reset (DS Table 3-4 p.34). Dùng cho OTA 2 phân vùng, model TFLite (~100-300 KB mỗi model, ASSUME) và bộ đệm dữ liệu offline.')
w('- RF: mạch CLC phía chip (1.5 pF / 2.4 nH / 1.5 pF, HDG §1.3.6 Table 6 p.13) + mạch π phía ăng-ten (DNP / 0 Ω / DNP) để tune bằng VNA. Ăng-ten gốm Johanson 2450AT18A100 ở góc bo, cần vùng cấm đồng.')
w('- USB D+/D− nối tiếp 22 Ω (HDG §1.3.13 p.18), ESD USBLC6-2SC6 sát cổng.')
w()
w('Bảng gán GPIO (giữ nguyên các chân màn hình/cảm ứng/I2C của Waveshare 1.75C):')
w()
NOTE = {'BOOT': 'strapping, nút BOOT', 'VLED_EN': 'strapping (JTAG src), kéo xuống 100k', 'BUZZER': 'strapping VDD_SPI → phải 0 lúc reset (R123)',
        'MOTOR': 'strapping boot mode → phải 0 lúc reset (R121)', 'BTN_SOS': 'RTC GPIO: đánh thức deep-sleep', 'IMU_INT1': 'RTC GPIO: wake (giơ tay, va chạm)',
        'IMU_INT2': 'RTC GPIO', 'PPG_INT': 'RTC GPIO: FIFO đầy', 'AXP_IRQ': 'RTC GPIO: nút nguồn, sạc', 'RTC_INT': 'RTC GPIO: hẹn giờ',
        'PPG_SCLK': 'SPI2 qua GPIO matrix, ≤ %d MHz (%s)' % (v('afe_spi'), c('afe_spi')), 'QSPI_CLK': 'QSPI màn hình (SPI2/3)', 'SYS_SDA': 'I2C0 400 kHz', 'SYS_SCL': 'I2C0'}
rows = []
for pin, net in sorted(D.ESP_GPIO.items(), key=lambda kv: int(D.GPIO_NAME[kv[0]][4:])):
    rows.append((D.GPIO_NAME[pin], pin, net, NOTE.get(net, '')))
rows += [('GPIO19/20', '25/26', 'USB_DN/DP', 'USB Serial/JTAG'), ('U0TXD/RXD', '49/50', 'U0TXD/U0RXD', 'header J103'), ('GPIO33-37', '38-42', '-', 'PSRAM octal trong chip: không dùng'),
         ('GPIO47/48', '36/37', '-', 'miền VDD_SPI: để trống')]
table(['GPIO', 'Chân QFN', 'Net', 'Ghi chú'], rows)
w('Bus I2C (7 bit): ' + ', '.join('%s 0x%02X' % (k, a) for k, a in D.I2C.items()) + ' - không trùng (kiểm trong `design.check()`).')
w()
w('### 4.3 Màn hình, IMU, RTC, giao diện')
w()
w('- FPC 31 chân 0.3 mm giống hệt J3 của Waveshare (WS p.1): QSPI GPIO4-7 + GPIO38, CS GPIO12, TE GPIO13, RST GPIO1; cảm ứng I2C + TP_INT GPIO11 + TP_RST GPIO2. Thêm 10 µF + 100 nF cạnh FPC.')
w('- BMI270 ở chế độ I2C: CSB = VDDIO, SDO = GND → 0x68 (BMI Table 22 p.135, %s); ASDx/ASCx/OCSB/OSDO để trống (cho phép khi không dùng giao tiếp phụ). INT1/INT2 về RTC GPIO.' % c('imu_addr'))
w('- Motor rung và còi từ đóng ngắt phía thấp bằng AO3400A, diode dập BAT54WS, cổng 100 Ω + kéo xuống 100 kΩ. Motor 3 V cấp từ VSYS (≤ 4.4 V): duty PWM D ≤ 3.0/4.2 ≈ %.0f %% khi pin đầy.' % (300 / 4.2))
w('- Nút SOS GPIO8 (kéo lên 10 kΩ + 100 nF ≈ 1 ms chống dội), nút nguồn vào PWRON của AXP2101 (510 Ω + 1 nF như Waveshare). LED đỏ sạc do AXP2101 lái (CHGLED), LED xanh trạng thái GPIO18.')
w()
w('### 4.4 Bo cảm biến - chuỗi PPG')
w()
w('- **Quang học**: SFH 7013 (xanh 530 nm cho nhịp tim ở cổ tay, đỏ 655 + IR 940 nm cho SpO2) ở giữa, 2 photodiode VEMD8080 hai bên; cần vách chắn sáng giữa LED và PD và cửa sổ kính/acrylic mỏng. '
  'LED1_DRV = xanh, LED2 = đỏ, LED3 = IR; PD1/PD2 đọc đồng thời (MAX p.12).')
w('- **Nguồn AFE**: LP5907 1.8 V nhiễu thấp từ 3V3 (Iq %.0f µA, %s); VDD_ANA 0.1 µF + 10 µF, VDD_DIG 0.1 µF, VREF 1 µF, VLED 10 µF (MAX p.12).' % (v('lp_iq') * 1000, c('lp_iq')))
w('- **Chuyển mức**: TXS0108E VCCA 1.8 V / VCCB 3.3 V, kênh 1-5 = SCLK, SDI, SDO, CSB, INT. Điện trở kéo lên nội 4 k/40 k (%s) nên INT cực máng hở vẫn hoạt động; '
  'OE nối VCCA qua RC 100 kΩ × 100 nF = 10 ms để chỉ bật sau khi hai nguồn ổn định (%s). SPI 4 MHz nằm trong khả năng của TXS0108E (110 Mbps push-pull, 1.2 Mbps open-drain - đủ cho INT; TXS p.1).' % (c('txs_pu'), c('txs_vcca')))
w('- **MAX30208**: cấp từ +3V3 luôn bật (không cấp từ nguồn bị cắt, tránh I2C cấp ngược vào IC không có nguồn), địa chỉ 0x52, đặt sát tấm tiếp xúc da và xa LDO/LED.')
w('- **FPC 16 chân**: GND ở chân 1, 4, 7, 13, 16 tách nhóm VLED / SPI / I2C; dùng cáp FFC loại B (tiếp điểm hai đầu ngược mặt) để chân 1 ↔ chân 1 khi hai đầu nối cùng nằm mặt trên.')
w()
w('## 5. Edge AI và firmware')
w()
table(['Model', 'Đầu vào', 'Kiến trúc (đề xuất)', 'Dữ liệu train', 'Chạy khi nào'], [
 ('Té ngã + hoạt động (đi, chạy, ngồi, nằm, cầu thang)', 'acc + gyro 50 Hz, cửa sổ 2.56 s', '1D-CNN 3 lớp, int8, ~20-50 KB', 'UMAFall / WEDA-FALL (cổ tay) + tự thu (ngã lên nệm)', 'mỗi 2 s khi FIFO đầy; INT va chạm đánh thức'),
 ('Nhịp tim bất thường / rung nhĩ', 'chuỗi IBI từ PPG 30-60 s + đặc trưng HRV', 'MLP/1D-CNN nhỏ trên IBI', 'MIMIC PERform AF, MIT-BIH AF (chuyển R-R → IBI)', 'mỗi 5 phút khi đứng yên (IMU)'),
 ('Giấc ngủ / stress', 'HRV (RMSSD, LF/HF) + mức vận động 30 s', 'cây quyết định / MLP', 'WESAD (stress), tự ghi nhật ký ngủ', 'ban đêm, mỗi epoch 30 s'),
])
w('- Quy trình: thu dữ liệu → Google Colab (Keras) → lượng tử hóa int8 → TFLite Micro + ESP-NN trên ESP32-S3 → đánh giá trên tập kiểm tra và trên đồng hồ thật. 8 MB PSRAM chứa tensor arena và bộ đệm cửa sổ.')
w('- Task FreeRTOS: `sensor_task` (đọc FIFO theo INT), `dsp_task` (lọc, HR, SpO2, IBI), `ai_task` (3 model), `event_task` (rung/còi/màn hình), `net_task` (HTTPS/BLE, chỉ bật khi cần), `ui_task` (LVGL). '
  'Phần còn lại ở auto light-sleep (ESP-IDF power management).')
w('- Web: REST API `POST /api/batch` (JSON 15 phút: HR, SpO2, bước, nhiệt độ, nhãn hoạt động) và `POST /api/event` (té ngã/AF/SOS, kèm vị trí thời gian); token thiết bị trong NVS, TLS.')
w('- **Giới hạn y khoa**: cảnh báo rung nhĩ từ PPG chỉ là sàng lọc, không phải chẩn đoán; giao diện phải ghi khuyến cáo đi khám.')
w()
w('## 6. Phân tích tín hiệu PPG - biên áp LED')
w()
vf, head = v('sfh_vf_g'), 0.5
w('VLED_min = VF_max + V_headroom = %.2f V + %.1f V (**ASSUME**, đồ thị "suggested LED driver headroom" MAX p.10) = %.2f V. Pin LiPo 3.4-4.2 V không đảm bảo → boost 5 V. '
  'Công suất LED: I_LED,TB × 5 V / (η %.0f %% × %.1f V) quy về pin (đã tính trong mục 7).' % (vf, head, vf + head, EFF_BOOST * 100, VBAT_NOM))
w()
w('## 7. Ngân sách pin')
w()
w('Giả thiết: pin %.1f V danh định, hiệu suất DCDC1 %.0f %%, boost %.0f %%, dung lượng %d mAh × %.0f %% dùng được. Dòng ở 3V3 quy về pin: I_bat = I × 3.3 / (%.1f × %.2f).'
  % (VBAT_NOM, EFF_DCDC * 100, EFF_BOOST * 100, CAP_MAH, USABLE * 100, VBAT_NOM, EFF_DCDC))
w()
table(['Tải', 'mA TB ở pin', 'Cách tính', 'Nguồn số liệu'], [(n, '%.3f' % i, how, src) for n, i, how, src in LOADS] + [('**Tổng**', '**%.2f**' % TOTAL, '', '')])
w('**Thời gian chạy ≈ %d × %.2f / %.2f ≈ %.0f giờ ≈ %.1f ngày.** So sánh thiết kế "ngây thơ" (không ngủ): %.0f mA → %.1f giờ, tức tiết kiệm %.0f lần nhờ light-sleep, màn hình tắt, WiFi theo lô.'
  % (CAP_MAH, USABLE, TOTAL, HOURS, HOURS / 24, NAIVE_T, CAP_MAH * USABLE / NAIVE_T, NAIVE_T / TOTAL))
w()
table(['Thiết kế ngây thơ', 'mA ở pin'], [(n, '%.1f' % i) for n, i in NAIVE])
w('Ba mục lớn nhất cần đo sớm bằng shunt: màn hình (R112), LED PPG (R114), IMU. Nếu màn hình > 60 mA khi sáng thì giảm độ sáng/thời gian sáng trước.')
w()
w('## 8. Kiểm tra đã làm')
w()
table(['Kiểm tra', 'Kết quả'], [
 ('ERC KiCad 9 (lỗi + cảnh báo), cả 2 bo', '0 vi phạm'),
 ('Netlist KiCad so với design.py: mỗi net thiết kế = đúng một net KiCad, cùng tập chân', '0 sai khác (`tools/check_net.py`); vài net nối dây ngắn giữ tên tự động của KiCad'),
 ('Chân mỗi symbol mới so với bảng chân datasheet', 'MAX86141 (MAX p.11-12), MAX30208 (M30 p.6), BMI270 (BMI p.135), TPS61240 (TPS p.3), VEMD8080 (VEMD p.4), SFH 7013 (SFH p.9); AXP2101 so với Table 4-1 p.7-9'),
 ('Số liệu trích dẫn', '%d/%d khớp đúng trang PDF (`tools/facts.py`)' % (F.verify()[0], len(F.F))),
 ('Địa chỉ I2C, sơ đồ chân FPC hai bo', 'không trùng / giống nhau (`design.check()`)'),
 ('Chưa kiểm', 'layout PCB, DRC, chạy thật, firmware, đo dòng'),
])
w('## 9. Rủi ro và việc còn mở')
w()
table(['#', 'Rủi ro / việc', 'Mức', 'Xử lý'], [
 (1, 'MAX86141 WLP 0.4 mm: không hàn tay; LCSC chỉ còn ~30 con, SFH 7013 hết hàng ở LCSC (4/11/2026)', 'Cao', 'Đặt PCBA 2 mặt có via-in-pad; mua sớm hoặc qua DigiKey/Mouser; LED thay thế: 1 LED xanh + 1 LED đỏ/IR rời'),
 (2, 'Datasheet PCF85063A (NXP) chưa tải được - pinout lấy từ thư viện KiCad', 'TB', 'Tải PDF NXP thủ công vào docs/datasheets rồi đối chiếu chân, tụ tải 7 pF, địa chỉ 0x51'),
 (3, 'Footprint MAX30208 LGA-10 là bản sơ bộ; pad MAX86141 0.25 mm theo AN1891 (ASSUME)', 'Cao', 'Lấy land pattern ADI 90-100101 và outline 21-100134 trước khi đặt PCB'),
 (4, 'Ăng-ten gốm trên bo nhỏ, cạnh pin và màn hình', 'TB', 'Vùng cấm đồng theo datasheet ăng-ten, đo S11 bằng VNA, chỉnh mạch π C130/R117/C131'),
 (5, 'Dòng màn hình AMOLED chưa có số liệu (giả định 40 mA)', 'TB', 'Đo bằng shunt R112 trên bo Waveshare có sẵn'),
 (6, 'Cáp FFC giữa 2 bo: sai loại A/B sẽ đảo chân', 'TB', 'Ghi rõ loại B trên silkscreen, kiểm thông mạch trước khi cấp nguồn'),
 (7, 'Phát hiện rung nhĩ từ PPG chỉ là sàng lọc; dataset ECG ≠ PPG', 'TB', 'Báo cáo độ nhạy/độ đặc hiệu trên tập kiểm tra, ghi rõ giới hạn'),
 (8, 'Chân SW/DCDC5 của AXP2101 nối theo Waveshare, chưa có giải thích trong datasheet', 'Thấp', 'Giữ như bo đã chạy; kiểm DCDC5 tắt bằng thanh ghi'),
 (9, 'ESP-IDF đã gỡ khỏi máy (25/10)', 'Thấp', 'Cài lại khi bắt đầu firmware'),
])
w('## 10. Danh sách linh kiện theo khối (từ design.py)')
w()
for board, parts in D.BOARDS.items():
    w('### %s' % D.TITLE[board])
    w()
    byb = collections.OrderedDict()
    for p in parts: byb.setdefault(p['block'], []).append(p)
    for b, ps in byb.items():
        w('**%s**' % D.BLOCK_NAME[b])
        w()
        table(['Ref', 'Giá trị', 'Vai trò', 'Tài liệu'], [(p['ref'], D.P[p['typ']][1] + (' (DNP)' if p['dnp'] else ''), p['why'], p['cite']) for p in ps])
w('## 11. Tài liệu tham khảo')
w()
table(['Khóa', 'Tài liệu', 'File (docs/datasheets/)'], [(k, d[1], d[0]) for k, d in D.DOCS.items()])
w('Số trang = số trang PDF (trùng số in trên trang, trừ HDG: số in = PDF − 3).')
open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('->', OUT, '| total %.2f mA -> %.0f h' % (TOTAL, HOURS))
