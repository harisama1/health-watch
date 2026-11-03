"""Health watch (đồ án): single source of truth for both boards - parts, pin->net, values, design reasons, citations.
gen_sch.py draws the schematics from it, gen_report.py writes the design report, gen_bom.py the BOM.

Boards (design frozen with the user 2026-11-04, see docs/health_watch_design_report.md):
  main   : ESP32-S3R8 + 16 MB flash + ceramic antenna, AXP2101 PMIC + LiPo ~400 mAh + USB-C, AMOLED 1.75" (CO5300 QSPI,
           CST9217 touch) on a 31-pin FPC, BMI270 IMU, PCF85063A RTC, vibration motor, buzzer, SOS + power buttons,
           status LEDs, UART0 header, BOOT/RESET, current shunts + test points, TPS61240 5 V boost for the PPG LEDs,
           16-pin FPC to the sensor board.
  sensor : MAX86141 PPG AFE + SFH 7013 (green/red/IR) + 2 x VEMD8080, LP5907 1.8 V LDO, TXS0108E 1.8 <-> 3.3 V level
           shifter, MAX30208 skin temperature, 16-pin FPC.

Citation keys -> files in docs/datasheets/ (page = printed page number; for all these documents printed = PDF page,
except HDG where printed = PDF - 3):
"""
import collections, re

DOCS = {
 'DS':   ('ESP32-S3_Datasheet.pdf', 'Espressif ESP32-S3 Series Datasheet v2.2'),
 'HDG':  ('ESP32-S3_Hardware_Design_Guidelines.pdf', 'Espressif ESP32-S3 Hardware Design Guidelines'),
 'AXP':  ('LCSC_C3036461_AXP2101.pdf', 'X-Powers AXP2101 datasheet'),
 'MAX':  ('LCSC_C5328762_MAX86141.pdf', 'Analog Devices MAX86140/MAX86141 datasheet'),
 'M30':  ('LCSC_C2874216_MAX30208.pdf', 'Maxim MAX30208 datasheet'),
 'BMI':  ('Bosch_BMI270_datasheet.pdf', 'Bosch BMI270 datasheet BST-BMI270-DS000-08'),
 'TPS':  ('LCSC_C133991_TPS61240.pdf', 'TI TPS61240/TPS61241 datasheet SLVS806D'),
 'TXS':  ('LCSC_C17206_TXS0108E.pdf', 'TI TXS0108E datasheet SCES642L'),
 'LP':   ('LCSC_C92498_LP5907-1.8.pdf', 'TI LP5907 datasheet'),
 'W25':  ('LCSC_C97521_W25Q128JVSIQ.pdf', 'Winbond W25Q128JV datasheet'),
 'SFH':  ('OSRAM_SFH7013.pdf', 'OSRAM SFH 7013 datasheet (Chinese edition) v1.3'),
 'VEMD': ('LCSC_C511402_VEMD8080.pdf', 'Vishay VEMD8080 datasheet rev 1.0'),
 'LC6':  ('LCSC_C7519_USBLC6-2SC6.pdf', 'ST USBLC6-2 datasheet'),
 'TYC':  ('LCSC_C165948_TYPE-C-31-M-12.pdf', 'USB-C receptacle TYPE-C-31-M-12 drawing'),
 'XT':   ('LCSC_C9010_X322540MPB4SI_40MHz.pdf', '40 MHz crystal X322540MPB4SI'),
 'TS':   ('LCSC_C720477_TS-1088_tact_switch.pdf', 'tact switch TS-1088'),
 'AO':   ('LCSC_C15127_AO3401A.pdf', 'AO3401A (P-FET, reference only)'),
 'WS':   ('Waveshare_ESP32-S3-Touch-AMOLED-1.75C_schematic.pdf', 'Waveshare ESP32-S3-Touch-AMOLED-1.75C schematic (reference design)'),
}

# ---------------------------------------------------------------- part types
# key: (symbol lib id, value, footprint, LCSC / MPN, datasheet key)
P = {
 'ESP32':  ('HW_Watch:ESP32-S3R8', 'ESP32-S3R8', 'Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP4x4mm_ThermalVias', 'C2913194', 'DS'),
 'FLASH':  ('Memory_Flash:W25Q128JVS', 'W25Q128JVSIQ', 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm', 'C97521', 'W25'),
 'AXP':    ('HW_Watch:AXP2101', 'AXP2101', 'Package_DFN_QFN:QFN-40-1EP_5x5mm_P0.4mm_EP3.6x3.6mm_ThermalVias', 'C3036461', 'AXP'),
 'BOOST':  ('HW_Watch:TPS61240', 'TPS61240DRVT', 'Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm', 'C133991', 'TPS'),
 'IMU':    ('HW_Watch:BMI270', 'BMI270', 'Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm', 'C2836813', 'BMI'),
 'RTC':    ('Timer_RTC:PCF85063ATL', 'PCF85063ATL/1', 'Package_DFN_QFN:DFN-10-1EP_2.6x2.6mm_P0.5mm_EP1.3x2.2mm', 'C404360', ''),
 'AFE':    ('HW_Watch:MAX86141', 'MAX86141ENP+', 'HW_Watch:MAX86141_WLP-20_2.05x1.85mm_P0.4mm', 'C5328762', 'MAX'),
 'TEMP':   ('HW_Watch:MAX30208', 'MAX30208CLB+', 'HW_Watch:MAX30208_LGA-10_2x2mm_PRELIM', 'C2874216', 'M30'),
 'LDO18':  ('Regulator_Linear:LP5907MFX-1.8', 'LP5907MFX-1.8', 'Package_TO_SOT_SMD:SOT-23-5', 'C92498', 'LP'),
 'TXS':    ('Logic_LevelTranslator:TXS0108EPW', 'TXS0108EPWR', 'Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm', 'C17206', 'TXS'),
 'LED3':   ('HW_Watch:SFH7013', 'SFH 7013', 'HW_Watch:SFH7013_2.5x1.6mm', 'C2900450', 'SFH'),
 'PD':     ('HW_Watch:VEMD8080', 'VEMD8080', 'HW_Watch:VEMD8080_4.8x2.5mm', 'C511402', 'VEMD'),
 'ESD':    ('HW_IC:USBLC6-2SC6', 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6', 'C7519', 'LC6'),
 'USBC':   ('HW_IC:USB_C_Receptacle_USB2.0_16P', 'TYPE-C-31-M-12', 'HW_IC:USB_C_Receptacle_16P_MidMount_TYPE-C-31-M-12', 'C165948', 'TYC'),
 'XTAL40': ('Device:Crystal_GND24', '40MHz 10ppm CL15pF', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', 'C9010', 'XT'),
 'XTAL32': ('Device:Crystal', '32.768kHz CL7pF', 'Crystal:Crystal_SMD_2012-2Pin_2.0x1.2mm', 'C2838510 (chọn mã CL 7 pF)', ''),
 'ANT':    ('Device:Antenna_Chip', '2450AT18A100E', 'RF_Antenna:Johanson_2450AT18x100', 'C2917717 (kiểm tra mã)', ''),
 'NFET':   ('Transistor_FET:AO3400A', 'AO3400A', 'Package_TO_SOT_SMD:SOT-23', 'C20917', ''),
 'DFLY':   ('Device:D_Schottky', 'BAT54WS', 'Diode_SMD:D_SOD-323', 'C191023', ''),
 'MOTOR':  ('Motor:Motor_DC', 'Coin motor 1027 3V', 'HW_Watch:Motor_Pads_2x1.5mm', '(Shopee: motor rung đồng xu 1027)', ''),
 'BUZZ':   ('Device:Buzzer', 'CMT-8504-100-SMT', 'Buzzer_Beeper:MagneticBuzzer_CUI_CMT-8504-100-SMT', 'CMT-8504-100-SMT (CUI)', ''),
 'BTN':    ('Switch:SW_Push', 'TS-1088 4x3mm', 'HW_IC:SW_SPST_TS-1088-xR020', 'C720477', 'TS'),
 'NTC':    ('Device:Thermistor_NTC', 'NTC 10k B3950', 'Resistor_SMD:R_0402_1005Metric', 'C25563', ''),
 'BAT':    ('Connector_Generic_MountingPin:Conn_01x02_MountingPin', 'LiPo 1S ~400mAh', 'Connector_Molex:Molex_PicoBlade_53261-0271_1x02-1MP_P1.25mm_Horizontal', '53261-0271', ''),
 'FPC31':  ('Connector_Generic_MountingPin:Conn_01x31_MountingPin', 'FPC 0.3mm 31P back-flip', 'HW_Watch:FPC_P0.30mm_1x31-1MP_BackFlip_Staggered', '(như bo Waveshare)', 'WS'),
 'FPC16':  ('Connector_Generic_MountingPin:Conn_01x16_MountingPin', 'FH12-16S-0.5SH', 'Connector_FFC-FPC:Hirose_FH12-16S-0.5SH_1x16-1MP_P0.50mm_Horizontal', 'C506807 (kiểm tra mã)', ''),
 'HDR3':   ('Connector_Generic:Conn_01x03', 'UART0 1x03 2.54', 'Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical', '', ''),
 'TP':     ('Connector:TestPoint', 'TP', 'TestPoint:TestPoint_Pad_D1.0mm', '', ''),
 'LED_R':  ('Device:LED', 'Red 0603', 'LED_SMD:LED_0603_1608Metric', 'C2286', ''),
 'LED_G':  ('Device:LED', 'Green 0603', 'LED_SMD:LED_0603_1608Metric', 'C72043', ''),
}
def R(v, lcsc='', pkg='0402'): return ('Device:R', v, 'Resistor_SMD:R_%s_%sMetric' % (pkg, {'0402': '1005', '0603': '1608', '0805': '2012'}[pkg]), lcsc, '')
def C(v, lcsc='', pkg='0402'): return ('Device:C', v, 'Capacitor_SMD:C_%s_%sMetric' % (pkg, {'0402': '1005', '0603': '1608', '0805': '2012'}[pkg]), lcsc, '')
def L(v, lcsc='', fp='Inductor_SMD:L_0402_1005Metric'): return ('Device:L', v, fp, lcsc, '')
P.update({
 'R0': R('0R', 'C17168'), 'R5k1': R('5.1k', 'C25905'), 'R10k': R('10k', 'C25744'), 'R100k': R('100k', 'C25741'), 'R1k': R('1k', 'C11702'),
 'R510': R('510', 'C25123'), 'R2k2': R('2.2k', 'C25879'), 'R4k7': R('4.7k', 'C25900'), 'R22': R('22', 'C25092'), 'R499': R('499', 'C25100'),
 'R100': R('100', 'C25076'),
 'RS50m': R('0.05R 1% 0805', 'C129937 (kiểm tra mã)', '0805'), 'RS100m': R('0.1R 1% 0603', 'C22381 (kiểm tra mã)', '0603'),
 'C100n': C('100nF', 'C1525'), 'C1u': C('1uF', 'C52923'), 'C10n': C('10nF', 'C15195'), 'C2u2': C('2.2uF', 'C12530'),
 'C4u7': C('4.7uF', 'C23733', '0603'), 'C10u': C('10uF 10V', 'C19702', '0603'), 'C22u': C('22uF 6.3V', 'C59461', '0603'),
 'C22p': C('22pF C0G', 'C1555'), 'C8p': C('8.2pF C0G', 'C1546 (kiểm tra mã)'), 'C1n': C('1nF', 'C1523'),
 'C1p5': C('1.5pF C0G', 'C1546 (chọn mã ±0.1pF)'), 'CDNP': C('DNP', ''),
 'L2n0': L('2.0nH', 'LQG15 2.0nH (chọn mã)'), 'L2n4': L('2.4nH', 'LQG15 2.4nH (chọn mã)'), 'L24n': L('24nH', 'LQG15 24nH (chọn mã)'),
 'L1u_2A': L('1uH 2.5A', '1uH 2520 Isat ≥2.5A (chọn mã)', 'Inductor_SMD:L_1008_2520Metric'),
 'L1u_1A': L('1uH 1A', '1uH 0805 Isat ≥1A (chọn mã)', 'Inductor_SMD:L_0805_2012Metric'),
})

def part(ref, typ, pins, block, why, cite='', dnp=False): return dict(ref=ref, typ=typ, pins=pins, block=block, why=why, cite=cite, dnp=dnp)
def cap(ref, typ, net, block, why, cite=''): return part(ref, typ, {'1': net, '2': 'GND'}, block, why, cite)
def res(ref, typ, a, b, block, why, cite=''): return part(ref, typ, {'1': a, '2': b}, block, why, cite)
def tp(ref, net, block, why): return part(ref, 'TP', {'1': net}, block, why)

# ================================================================ MAIN BOARD
ESP_GPIO = {   # QFN-56 pin -> net (DS Table 2-1 pin list; display/touch pins kept as on the Waveshare 1.75C board, WS p.1 GPIO table)
 '5': 'BOOT', '6': 'LCD_RST', '7': 'TP_RST', '8': 'VLED_EN', '9': 'QSPI_D0', '10': 'QSPI_D1', '11': 'QSPI_D2', '12': 'QSPI_D3',
 '13': 'BTN_SOS', '14': 'IMU_INT1', '15': 'PPG_INT', '16': 'TP_INT', '17': 'LCD_CS', '18': 'LCD_TE', '19': 'SYS_SCL', '21': 'SYS_SDA',
 '22': 'AXP_IRQ', '23': 'RTC_INT', '24': 'LED_STAT', '27': 'IMU_INT2', '43': 'QSPI_CLK', '44': 'PPG_SCLK', '45': 'PPG_MOSI',
 '47': 'PPG_MISO', '48': 'PPG_CS', '51': 'BUZZER', '52': 'MOTOR'}
GPIO_NAME = {'5': 'GPIO0', '6': 'GPIO1', '7': 'GPIO2', '8': 'GPIO3', '9': 'GPIO4', '10': 'GPIO5', '11': 'GPIO6', '12': 'GPIO7', '13': 'GPIO8',
             '14': 'GPIO9', '15': 'GPIO10', '16': 'GPIO11', '17': 'GPIO12', '18': 'GPIO13', '19': 'GPIO14', '21': 'GPIO15', '22': 'GPIO16',
             '23': 'GPIO17', '24': 'GPIO18', '27': 'GPIO21', '43': 'GPIO38', '44': 'GPIO39', '45': 'GPIO40', '47': 'GPIO41', '48': 'GPIO42',
             '51': 'GPIO45', '52': 'GPIO46'}
esp_pins = {'1': 'LNA_IN', '2': 'VDD3P3', '3': 'VDD3P3', '4': 'CHIP_PU', '20': '+3V3', '46': '+3V3', '55': '+3V3', '56': '+3V3', '57': 'GND',
            '29': 'VDD_SPI', '30': 'SPIHD', '31': 'SPIWP', '32': 'SPICS0', '33': 'SPICLK', '34': 'SPIQ', '35': 'SPID',
            '53': 'XTAL_N', '54': 'XTAL_P_IC', '25': 'USB_DN_MCU', '26': 'USB_DP_MCU', '49': 'U0TXD_MCU', '50': 'U0RXD',
            '28': None, '36': None, '37': None, '38': None, '39': None, '40': None, '41': None, '42': None}
esp_pins.update(ESP_GPIO)

MAIN = [
 # ---------------- USB-C + ESD
 part('J1', 'USBC', {'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS', 'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'S1': 'GND',
                     'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DN', 'B7': 'USB_DN', 'A8': None, 'B8': None},
      'USB', 'USB-C duy nhất: sạc pin (VBUS → AXP2101) + nạp/debug firmware qua USB Serial/JTAG của ESP32-S3.', 'TYC; HDG §1.3.13'),
 res('R1', 'R5k1', 'CC1', 'GND', 'USB', 'Rd 5.1 kΩ trên CC1: thiết bị là sink, sạc USB-C mới cấp 5 V.', 'USB Type-C spec (Rd = 5.1 kΩ)'),
 res('R2', 'R5k1', 'CC2', 'GND', 'USB', 'Rd 5.1 kΩ trên CC2 (cắm ngược).', 'USB Type-C spec'),
 part('U1', 'ESD', {'1': 'USB_DN', '6': 'USB_DN', '3': 'USB_DP', '4': 'USB_DP', '5': 'VBUS', '2': 'GND'}, 'USB',
      'Chống ESD cho D+/D− và VBUS ngay sau cổng (1-6, 3-4 là hai đầu của cùng một đường).', 'LC6 p.1; HDG §1.3.13'),
 res('R3', 'R22', 'USB_DN', 'USB_DN_MCU', 'USB', 'Điện trở nối tiếp D− 22 Ω sát chip.', 'HDG §1.3.13; WS p.1 (R13)'),
 res('R4', 'R22', 'USB_DP', 'USB_DP_MCU', 'USB', 'Điện trở nối tiếp D+ 22 Ω.', 'HDG §1.3.13; WS p.1 (R14)'),
 tp('TP1', 'VBUS', 'USB', 'Đo VBUS.'),
 # ---------------- PMIC AXP2101 (AXP Fig 7-1 p.57, pin table 4-1 p.7-8; Waveshare 1.75C uses the same chip - WS p.1)
 part('U2', 'AXP', {'1': 'CHGLED', '2': 'AXP_VREF', '3': 'GND', '41': 'GND', '17': 'VSYS', '23': 'VSYS', '34': 'VSYS', '22': 'LX1', '21': '3V3_PMIC',
                    '27': 'VBACKUP', '28': 'VRTC', '29': 'CHIP_PU', '30': 'PWRON', '31': 'TS', '33': 'VBAT', '35': 'AXP_SW', '36': 'VMID',
                    '37': 'VBUS', '38': 'AXP_IRQ', '39': 'SYS_SDA', '40': 'SYS_SCL',
                    '4': None, '5': None, '6': None, '7': None, '8': None, '9': None, '10': None, '11': None, '12': None, '13': None, '14': None,
                    '15': None, '16': None, '18': None, '19': None, '20': None, '24': None, '25': None, '26': None, '32': None},
      'PMIC', 'PMIC: sạc tuyến tính 100 mA–1 A cho LiPo, DCDC1 3.3 V (2 A) cho toàn hệ thống, đo % pin (fuel gauge), nút nguồn, IRQ; '
      'PWROK giữ ESP32 ở reset tới khi nguồn ổn định (giống bo Waveshare). DCDC2-4, các LDO không dùng: để trống như bo tham chiếu.',
      'AXP p.1 (features), Table 4-1 p.7-9 (chân), Fig 7-1 p.57 (mạch ứng dụng); WS p.1'),
 cap('C1', 'C10u', 'VBUS', 'PMIC', 'Tụ VBUS 10 µF/10 V.', 'AXP Fig 7-1 p.57'),
 cap('C2', 'C10u', 'VMID', 'PMIC', 'Tụ VMID (sau RBFET) 10 µF/10 V, như bo Waveshare.', 'AXP Fig 7-1 p.57; WS p.1 (CP2)'),
 cap('C3', 'C22u', 'VSYS', 'PMIC', 'VSYS: hai tụ 22 µF sát chân SYS.', 'AXP Table 4-1 p.8 (pin 34)'),
 cap('C4', 'C22u', 'VSYS', 'PMIC', 'Tụ 22 µF thứ hai trên VSYS.', 'AXP Table 4-1 p.8 (pin 34)'),
 cap('C5', 'C1u', 'VBAT', 'PMIC', 'Tụ 1 µF sát chân BAT.', 'AXP Table 4-1 p.8 (pin 33)'),
 cap('C6', 'C1u', 'AXP_VREF', 'PMIC', 'Tụ VREF 1 µF.', 'AXP Fig 7-1 p.57'),
 cap('C7', 'C1u', 'VRTC', 'PMIC', 'Tụ VRTC 1 µF.', 'AXP Fig 7-1 p.57'),
 cap('C8', 'C2u2', 'VBACKUP', 'PMIC', 'VBackup: không dùng pin dự phòng, chỉ tụ 2.2 µF như bo Waveshare.', 'WS p.1 (CP13); AXP Fig 7-1 p.57'),
 cap('C9', 'C1u', 'VSYS', 'PMIC', 'Tụ vào VIN1 (DCDC1) 1 µF.', 'AXP Fig 7-1 p.57'),
 cap('C10', 'C1u', 'VSYS', 'PMIC', 'Tụ vào ALDOIN 1 µF.', 'AXP Fig 7-1 p.57'),
 part('L1', 'L1u_2A', {'1': 'LX1', '2': '3V3_PMIC'}, 'PMIC', 'Cuộn DCDC1 1 µH (3 MHz); Isat ≥ 2.5 A cho tải đỉnh WiFi + màn hình.', 'AXP Fig 7-1 p.57, §6.6 p.22 (3 MHz)'),
 cap('C11', 'C22u', '3V3_PMIC', 'PMIC', 'Tụ ra DCDC1 22 µF, FB1 lấy tại đây.', 'AXP Fig 7-1 p.57'),
 part('L2', 'L1u_2A', {'1': 'AXP_SW', '2': 'VSYS_D5'}, 'PMIC', 'Chân SW (DCDC5) nối như bo Waveshare đã chạy thực tế (cuộn 1 µH về VSYS); DCDC5 không dùng làm nguồn.', 'WS p.1 (LP2, RP2); AXP Fig 7-1 p.57'),
 res('R5', 'R0', 'VSYS_D5', 'VSYS', 'PMIC', '0 Ω (Waveshare dùng 0.01 Ω ở vị trí này) - giữ nguyên cấu trúc bo tham chiếu.', 'WS p.1 (RP2)'),
 part('RT1', 'NTC', {'1': 'TS', '2': 'GND'}, 'PMIC', 'NTC 10 kΩ đặt sát pin: AXP2101 ngắt sạc khi pin quá nóng/lạnh.', 'AXP Table 4-1 p.8 (pin 31 TS); WS p.1 (RP4)'),
 res('R6', 'R4k7', '+3V3', 'AXP_IRQ', 'PMIC', 'Kéo lên IRQ (cực máng hở) 4.7 kΩ.', 'AXP Table 4-1 p.8 (pin 38)'),
 res('R7', 'R2k2', '+3V3', 'SYS_SDA', 'PMIC', 'Kéo lên I2C SDA 2.2 kΩ (bus chung: AXP2101, touch, BMI270, RTC, MAX30208).', 'AXP Table 4-1 p.9 (pin 39 "needs a 2.2kΩ pull high")'),
 res('R8', 'R2k2', '+3V3', 'SYS_SCL', 'PMIC', 'Kéo lên I2C SCL 2.2 kΩ.', 'AXP Table 4-1 p.9 (pin 40)'),
 res('R9', 'R510', 'PWRON', 'PWR_KEY', 'PMIC', 'Nối tiếp nút nguồn 510 Ω như bo Waveshare.', 'WS p.1 (RP6)'),
 cap('C12', 'C1n', 'PWRON', 'PMIC', 'Lọc nhiễu nút nguồn 1 nF.', 'WS p.1 (CP14)'),
 part('SW1', 'BTN', {'1': 'PWR_KEY', '2': 'GND'}, 'PMIC', 'Nút nguồn: nhấn ngắn = bật/đánh thức (IRQ), giữ lâu = tắt (AXP2101 xử lý).', 'AXP Table 4-1 p.8 (pin 30 PWRON, kéo lên 100k nội)'),
 res('R10', 'R1k', 'VSYS', 'CHGLED_A', 'PMIC', 'Hạn dòng LED sạc ≈ (4.0−2.0)/1k ≈ 2 mA.', 'AXP Fig 7-1 p.57 (LED từ VSYS về CHGLED)'),
 part('D1', 'LED_R', {'2': 'CHGLED_A', '1': 'CHGLED'}, 'PMIC', 'LED đỏ báo sạc (AXP2101 điều khiển chân CHGLED cực máng hở; firmware có thể tự điều khiển).', 'AXP Table 4-1 p.7 (pin 1)'),
 # battery + shunts
 part('J2', 'BAT', {'1': 'VBAT_CELL', '2': 'GND', 'MP': 'GND'}, 'PMIC', 'Đầu nối pin LiPo 1S (Molex PicoBlade 1.25 mm); pin có sẵn mạch bảo vệ. Chân 1 = +.', ''),
 res('R11', 'RS50m', 'VBAT_CELL', 'VBAT', 'PMIC', 'Shunt 50 mΩ đo dòng pin: I = V(TP2−TP3)/0.05; 0.3 A chỉ sụt 15 mV.', 'yêu cầu đo dòng (user)'),
 tp('TP2', 'VBAT_CELL', 'PMIC', 'Đo dòng pin: đầu pin của shunt.'),
 tp('TP3', 'VBAT', 'PMIC', 'Đo dòng pin: đầu AXP của shunt.'),
 res('R12', 'RS100m', '3V3_PMIC', '+3V3', 'PMIC', 'Shunt 0.1 Ω đo dòng 3V3 toàn hệ thống (ESP32 + màn hình + cảm biến).', 'yêu cầu đo dòng (user)'),
 tp('TP4', '3V3_PMIC', 'PMIC', 'Đo dòng 3V3: phía DCDC1.'),
 tp('TP5', '+3V3', 'PMIC', 'Đo dòng 3V3: phía tải.'),
 tp('TP6', 'VSYS', 'PMIC', 'Đo VSYS.'),
 tp('TP7', 'GND', 'PMIC', 'GND cho que đo.'),
 # ---------------- 5 V boost for the PPG LEDs
 part('U3', 'BOOST', {'6': 'VSYS', '5': 'BST_L', '4': 'VLED_EN', '2': 'VLED_5V', '3': 'VLED_5V', '1': 'GND', '7': 'GND'}, 'BOOST',
      'Boost 5 V cấp VLED cho LED PPG: LED xanh lá có VF tới 3.35 V + áp cần cho driver, pin LiPo xuống 3.4 V thì không đủ. '
      'Datasheet MAX86141 đo ở VLED = 5.0 V. EN do ESP32 bật chỉ khi đo PPG.', 'TPS p.1, p.3 (chân), §10.2.2 p.12 (CIN 2.2 µF, COUT 4.7 µF, L 1 µH); MAX p.6 (VLED 3.1-5.5 V); SFH p.3 (VF green max 3.35 V)'),
 part('L3', 'L1u_1A', {'1': 'VSYS', '2': 'BST_L'}, 'BOOST', 'Cuộn boost 1 µH.', 'TPS §10.2.2 p.12 (L = 1 µH)'),
 cap('C13', 'C2u2', 'VSYS', 'BOOST', 'Tụ vào boost 2.2 µF.', 'TPS §10.2.2 p.12'),
 cap('C14', 'C4u7', 'VLED_5V', 'BOOST', 'Tụ ra boost 4.7 µF.', 'TPS §10.2.2 p.12'),
 res('R13', 'R100k', 'VLED_EN', 'GND', 'BOOST', 'Kéo xuống EN: boost tắt khi ESP32 reset/ngủ. GPIO3 là chân strapping (nguồn tín hiệu JTAG) - mức thấp không ảnh hưởng khi eFuse mặc định.', 'DS §3 Table 3-1 p.32 (GPIO3 strapping)'),
 res('R14', 'RS100m', 'VLED_5V', 'VLED', 'BOOST', 'Shunt 0.1 Ω đo dòng LED PPG.', 'yêu cầu đo dòng (user)'),
 tp('TP8', 'VLED_5V', 'BOOST', 'Đo dòng VLED: phía boost.'),
 tp('TP9', 'VLED', 'BOOST', 'Đo dòng VLED: phía tải.'),
 # ---------------- ESP32-S3R8 core (HDG Fig 1 p.5 reference schematic; Waveshare 1.75C uses the same chip)
 part('U4', 'ESP32', esp_pins, 'MCU', 'SoC 2 nhân Xtensa LX7 240 MHz, lệnh vector cho AI (ESP-NN), 8 MB PSRAM octal trong chip, WiFi 2.4 GHz + BLE 5. '
      'Flash ngoài 16 MB (U5) chứa firmware, model AI và bộ đệm dữ liệu khi mất mạng.', 'DS p.2 (features), Table 1-1 (R8 = 8 MB PSRAM), Table 2-1 (chân)'),
 cap('C15', 'C10u', 'VDD3P3', 'MCU', 'VDD3P3 (PA RF): 10 µF.', 'HDG §1.3.2 p.8'),
 cap('C16', 'C1u', 'VDD3P3', 'MCU', 'VDD3P3 1 µF.', 'HDG Fig.1 p.5'),
 cap('C17', 'C100n', 'VDD3P3', 'MCU', 'VDD3P3 100 nF sát chân 2/3.', 'HDG Fig.1 p.5'),
 part('L4', 'L2n0', {'1': '+3V3', '2': 'VDD3P3'}, 'MCU', 'Lọc LC VDD3P3 2.0 nH (≥500 mA).', 'HDG §1.3.2 p.8; WS p.1 (IND1 2.0nH)'),
 cap('C18', 'C1u', '+3V3', 'MCU', 'VDDA 1 µF.', 'HDG Fig.1 p.5'),
 cap('C19', 'C10n', '+3V3', 'MCU', 'VDDA 10 nF.', 'HDG Fig.1 p.5'),
 cap('C20', 'C100n', '+3V3', 'MCU', 'VDD3P3_CPU 100 nF.', 'HDG §1.3.2'),
 cap('C21', 'C100n', '+3V3', 'MCU', 'VDD3P3_RTC 100 nF.', 'HDG §1.3.2'),
 cap('C22', 'C100n', 'VDD_SPI', 'MCU', 'VDD_SPI (cấp flash + PSRAM) 100 nF.', 'HDG §1.3.2 p.7'),
 cap('C23', 'C1u', 'VDD_SPI', 'MCU', 'VDD_SPI 1 µF.', 'HDG §1.3.2 p.7'),
 res('R15', 'R10k', '+3V3', 'CHIP_PU', 'MCU', 'RC trễ CHIP_PU (10 kΩ). AXP2101 PWROK cũng kéo CHIP_PU xuống tới khi nguồn ổn định.', 'HDG §1.3.3 Table 2 p.8; WS p.1 (R8)'),
 cap('C24', 'C1u', 'CHIP_PU', 'MCU', 'RC trễ CHIP_PU (1 µF).', 'HDG §1.3.3 p.8'),
 part('SW2', 'BTN', {'1': 'CHIP_PU', '2': 'GND'}, 'MCU', 'Nút RESET.', 'HDG §1.3.3'),
 res('R16', 'R10k', '+3V3', 'BOOT', 'MCU', 'Kéo lên GPIO0 (strapping): nhả = chạy firmware.', 'DS §3 Table 3-1 p.32; HDG §1.3.9'),
 part('SW3', 'BTN', {'1': 'BOOT', '2': 'GND'}, 'MCU', 'Nút BOOT: giữ khi reset = chế độ nạp (USB/UART).', 'DS Table 3-3 p.33; HDG §1.3.9'),
 part('Y1', 'XTAL40', {'1': 'XTAL_P', '3': 'XTAL_N', '2': 'GND', '4': 'GND'}, 'MCU', 'Thạch anh 40 MHz ±10 ppm.', 'HDG §1.3.5 p.10; XT'),
 part('L5', 'L24n', {'1': 'XTAL_P_IC', '2': 'XTAL_P'}, 'MCU', 'Cuộn 24 nH nối tiếp XTAL_P (giảm hài lên RF).', 'HDG §1.3.5 p.10; WS p.1 (R10 24nH)'),
 cap('C25', 'C22p', 'XTAL_P', 'MCU', 'Tụ tải thạch anh (CL 15 pF ≈ 22·22/44 + ~4 pF ký sinh; chỉnh theo đo tần số).', 'HDG §1.3.5 p.11'),
 cap('C26', 'C22p', 'XTAL_N', 'MCU', 'Tụ tải thạch anh thứ hai.', 'HDG §1.3.5 p.11'),
 part('U5', 'FLASH', {'1': 'SPICS0', '2': 'SPIQ', '3': 'SPIWP', '4': 'GND', '5': 'SPID', '6': 'SPICLK', '7': 'SPIHD', '8': 'VDD_SPI'}, 'MCU',
      'Flash QSPI 16 MB (S3R8 không có flash trong chip): firmware OTA 2 phân vùng, model TFLite, bộ đệm dữ liệu offline. VDD_SPI = 3.3 V vì GPIO45 = 0 lúc reset.',
      'W25 p.1, §3 (chân SOIC-8 208 mil); DS §3.3 Table 3-4 p.34 (VDD_SPI theo GPIO45); WS p.1 (U2)'),
 cap('C27', 'C100n', 'VDD_SPI', 'MCU', 'Decoupling flash 100 nF.', 'W25'),
 # RF: chip-side CLC + antenna-side pi + chip antenna
 cap('C28', 'C1p5', 'LNA_IN', 'RF', 'Phối hợp phía chip: tụ song song 1.2-1.8 pF sát LNA_IN.', 'HDG §1.3.6 Table 6 p.13'),
 part('L6', 'L2n4', {'1': 'LNA_IN', '2': 'RF1'}, 'RF', 'Phối hợp phía chip: cuộn nối tiếp 2.0-3.0 nH.', 'HDG §1.3.6 Table 6 p.13'),
 cap('C29', 'C1p5', 'RF1', 'RF', 'Phối hợp phía chip: tụ song song 1.2-1.8 pF.', 'HDG §1.3.6 p.12-13'),
 part('C30', 'CDNP', {'1': 'RF1', '2': 'GND'}, 'RF', 'Mạch π phía ăng-ten (để trống, dùng khi đo VNA).', 'HDG §1.3.6 p.12', dnp=True),
 res('R17', 'R0', 'RF1', 'RF_ANT', 'RF', 'Phần tử nối tiếp mạch π: 0 Ω mặc định.', 'HDG §1.3.6 p.12'),
 part('C31', 'CDNP', {'1': 'RF_ANT', '2': 'GND'}, 'RF', 'Mạch π phía ăng-ten (để trống).', 'HDG §1.3.6 p.12', dnp=True),
 part('AE1', 'ANT', {'1': 'RF_ANT', '2': None}, 'RF', 'Ăng-ten gốm 2.4 GHz 3.2×1.6 mm (Johanson 2450AT18A100). Đặt ở góc bo, vùng cấm đồng theo datasheet ăng-ten; cần tune mạch π bằng VNA.',
      'HDG §1.3.6; datasheet Johanson (chưa tải - ASSUME)'),
 # debug
 res('R18', 'R499', 'U0TXD_MCU', 'U0TXD', 'DEBUG', '499 Ω nối tiếp U0TXD.', 'HDG §1.3.7 p.13'),
 part('J3', 'HDR3', {'1': 'GND', '2': 'U0TXD', '3': 'U0RXD'}, 'DEBUG', 'Header UART0 (GND/TX/RX): xem log và cứu nạp khi USB treo.', 'yêu cầu user'),
 # ---------------- display FPC (pin map identical to the Waveshare 1.75C J3, WS p.1)
 part('J4', 'FPC31', {'1': 'GND', '4': 'GND', '7': 'GND', '10': 'GND', '20': 'GND', '25': 'GND', '31': 'GND', 'MP': 'GND',
                      '2': None, '3': None, '5': None, '6': None, '8': None, '9': None, '19': None,
                      '11': 'LCD_TE', '12': 'QSPI_D2', '13': 'QSPI_D3', '14': 'QSPI_CLK', '15': 'QSPI_D1', '16': 'QSPI_D0', '17': 'LCD_CS',
                      '18': 'LCD_RST', '21': '+3V3', '22': '+3V3', '23': '+3V3', '24': '+3V3', '26': '+3V3',
                      '27': 'SYS_SCL', '28': 'SYS_SDA', '29': 'TP_RST', '30': 'TP_INT'},
      'DISPLAY', 'Màn AMOLED 1.75" 466×466 (driver CO5300, QSPI) + cảm ứng CST9217 (I2C 0x5A) trên một FPC 31 chân 0.3 mm. '
      'Thứ tự chân và GPIO giữ đúng như bo Waveshare 1.75C để dùng lại code mẫu.', 'WS p.1 (J3, bảng GPIO)'),
 cap('C32', 'C10u', '+3V3', 'DISPLAY', 'Tụ bulk 10 µF cạnh FPC màn hình (dòng xung khi màn sáng).', 'ASSUME (thực hành chung)'),
 cap('C33', 'C100n', '+3V3', 'DISPLAY', 'Decoupling 100 nF cạnh FPC.', ''),
 # ---------------- sensors on the main board
 part('U6', 'IMU', {'8': '+3V3', '5': '+3V3', '7': 'GND', '6': 'GND', '14': 'SYS_SDA', '13': 'SYS_SCL', '12': '+3V3', '1': 'GND',
                    '4': 'IMU_INT1', '9': 'IMU_INT2', '2': None, '3': None, '10': None, '11': None},
      'SENSORS', 'IMU 6 trục cho đếm bước, giơ tay bật màn hình, dữ liệu té ngã/hoạt động cho AI. I2C: CSB = VDDIO, SDO = GND → địa chỉ 0x68. '
      'INT1/INT2 về GPIO RTC để đánh thức ESP32. ASDx/ASCx, OCSB/OSDO để trống (cho phép khi không dùng giao tiếp phụ).',
      'BMI Table 22 p.135 (chân, cách nối I2C), §5 p.128 (địa chỉ 0x68)'),
 cap('C34', 'C100n', '+3V3', 'SENSORS', 'Decoupling VDD BMI270.', 'BMI §7 (sơ đồ nối) - ASSUME giá trị 100 nF'),
 cap('C35', 'C100n', '+3V3', 'SENSORS', 'Decoupling VDDIO BMI270.', 'BMI §7'),
 part('U7', 'RTC', {'10': '+3V3', '5': 'GND', '1': 'OSCI', '2': 'OSCO', '3': 'GND', '4': 'RTC_INT', '6': 'SYS_SDA', '7': 'SYS_SCL',
                    '8': None, '9': None},
      'SENSORS', 'RTC 32.768 kHz rất ít dòng: giữ giờ và hẹn giờ đánh thức (INT) khi ESP32 ngủ sâu. CLKOE = GND tắt CLKOUT. I2C 0x51.',
      'ASSUME: datasheet NXP PCF85063A chưa tải được; pinout lấy từ symbol KiCad Timer_RTC:PCF85063ATL'),
 part('Y2', 'XTAL32', {'1': 'OSCI', '2': 'OSCO'}, 'SENSORS', 'Thạch anh 32.768 kHz CL 7 pF (PCF85063A có tụ tải trong, chọn 7 pF bằng thanh ghi).', 'ASSUME (datasheet PCF85063A)'),
 cap('C36', 'C100n', '+3V3', 'SENSORS', 'Decoupling PCF85063A.', ''),
 res('R19', 'R10k', '+3V3', 'RTC_INT', 'SENSORS', 'Kéo lên INT (cực máng hở) của RTC.', ''),
 # ---------------- user interface
 part('Q1', 'NFET', {'1': 'MOT_G', '2': 'GND', '3': 'MOT_D'}, 'UI', 'MOSFET kênh N mức logic (VGS(th) thấp) đóng ngắt motor rung, PWM từ GPIO46.', 'AO3400A datasheet (ASSUME, chưa tải)'),
 res('R20', 'R100', 'MOTOR', 'MOT_G', 'UI', 'Điện trở cổng 100 Ω.', ''),
 res('R21', 'R100k', 'MOT_G', 'GND', 'UI', 'Kéo xuống cổng: motor tắt khi reset. GPIO46 là chân strapping, phải ở mức 0 lúc khởi động (SPI boot).', 'DS §3 Table 3-1 p.32, Table 3-3 p.33 (GPIO46)'),
 part('M1', 'MOTOR', {'1': 'VSYS', '2': 'MOT_D'}, 'UI', 'Motor rung đồng xu 1027 (3 V): báo té ngã / nhịp bất thường / thông báo. Cấp từ VSYS, firmware giới hạn duty ≤ 75 % khi VSYS 4.2 V.', ''),
 part('D2', 'DFLY', {'1': 'VSYS', '2': 'MOT_D'}, 'UI', 'Diode dập xung ngược của motor.', ''),
 part('Q2', 'NFET', {'1': 'BZ_G', '2': 'GND', '3': 'BZ_D'}, 'UI', 'MOSFET kênh N đóng ngắt còi, PWM ~2.7 kHz (tần số cộng hưởng) từ GPIO45.', ''),
 res('R22', 'R100', 'BUZZER', 'BZ_G', 'UI', 'Điện trở cổng 100 Ω.', ''),
 res('R23', 'R100k', 'BZ_G', 'GND', 'UI', 'Kéo xuống cổng. GPIO45 là chân strapping VDD_SPI: phải 0 lúc reset để flash chạy 3.3 V.', 'DS §3 Table 3-1 p.32, Table 3-4 p.34 (GPIO45)'),
 part('BZ1', 'BUZZ', {'1': 'VSYS', '2': 'BZ_D'}, 'UI', 'Còi từ 8.5 mm SMD: báo động té ngã để người xung quanh nghe.', 'CUI CMT-8504 (ASSUME, chưa tải)'),
 part('D3', 'DFLY', {'1': 'VSYS', '2': 'BZ_D'}, 'UI', 'Diode dập xung ngược của còi từ (cuộn dây).', ''),
 part('SW4', 'BTN', {'1': 'BTN_SOS', '2': 'GND'}, 'UI', 'Nút SOS: gửi cảnh báo khẩn ngay; nối GPIO8 (RTC GPIO) để đánh thức từ deep sleep.', 'DS §2.3 p.23-24 (RTC GPIO)'),
 res('R24', 'R10k', '+3V3', 'BTN_SOS', 'UI', 'Kéo lên nút SOS (không phụ thuộc pull-up nội khi ngủ).', ''),
 cap('C37', 'C100n', 'BTN_SOS', 'UI', 'Chống dội nút SOS (RC 1 ms).', ''),
 res('R25', 'R1k', 'LED_STAT', 'LED_STAT_A', 'UI', 'Hạn dòng LED trạng thái ≈ (3.3−2.9)/1k... chọn 1 kΩ (~0.5-1 mA đủ sáng).', ''),
 part('D4', 'LED_G', {'2': 'LED_STAT_A', '1': 'GND'}, 'UI', 'LED xanh trạng thái (đã kết nối / lỗi / đang đo) - nhìn được khi màn hình tắt.', 'yêu cầu user'),
 # ---------------- FPC to the sensor board
 part('J5', 'FPC16', {'1': 'GND', '2': '+3V3', '3': '+3V3', '4': 'GND', '5': 'VLED', '6': 'VLED', '7': 'GND', '8': 'PPG_SCLK', '9': 'PPG_MOSI',
                      '10': 'PPG_MISO', '11': 'PPG_CS', '12': 'PPG_INT', '13': 'GND', '14': 'SYS_SDA', '15': 'SYS_SCL', '16': 'GND', 'MP': 'GND'},
      'FPC', 'FPC 16 chân 0.5 mm sang bo cảm biến: 3V3, VLED 5 V, SPI 3.3 V (đã chuyển mức trên bo cảm biến), INT, I2C. GND xen giữa nhóm nguồn LED / SPI / I2C. '
      'Cáp FFC loại B (hai đầu tiếp điểm ngược mặt) để chân 1 ↔ chân 1.', 'Hirose FH12 (footprint KiCad)'),
]

# ================================================================ SENSOR BOARD
SENSOR = [
 part('J1', 'FPC16', {'1': 'GND', '2': '+3V3', '3': '+3V3', '4': 'GND', '5': 'VLED', '6': 'VLED', '7': 'GND', '8': 'PPG_SCLK', '9': 'PPG_MOSI',
                      '10': 'PPG_MISO', '11': 'PPG_CS', '12': 'PPG_INT', '13': 'GND', '14': 'SYS_SDA', '15': 'SYS_SCL', '16': 'GND', 'MP': 'GND'},
      'FPC', 'FPC 16 chân nối bo chính (cùng thứ tự chân).', ''),
 cap('C1', 'C10u', '+3V3', 'FPC', 'Tụ bulk 3V3 ở đầu bo cảm biến.', ''),
 cap('C2', 'C10u', 'VLED', 'FPC', 'Tụ 10 µF cho VLED sát MAX86141 (yêu cầu của datasheet).', 'MAX p.12 (VLED: bypass 10 µF to PGND)'),
 cap('C3', 'C100n', 'VLED', 'FPC', 'Tụ 100 nF cho VLED (xung LED tần số cao).', 'ASSUME'),
 # 1.8 V LDO + shunt
 part('U1', 'LDO18', {'1': '+3V3', '3': '+3V3', '2': 'GND', '4': None, '5': '1V8_LDO'}, 'LDO',
      'LDO 1.8 V nhiễu thấp (6.5 µVrms) riêng cho AFE: MAX86141 chỉ chịu 1.7-2.0 V, PSRR tốt chặn nhiễu DC-DC. EN = IN (luôn bật; AFE tự shutdown 0.6 µA).',
      'LP p.1 (noise, PSRR); MAX p.6 (VDD 1.7-2.0 V), p.7 (shutdown 0.6 µA)'),
 cap('C4', 'C1u', '+3V3', 'LDO', 'Tụ vào LDO 1 µF.', 'LP p.6 (điều kiện đo CIN = COUT = 1 µF)'),
 cap('C5', 'C1u', '1V8_LDO', 'LDO', 'Tụ ra LDO 1 µF.', 'LP p.6 (COUT 1 µF)'),
 res('R1', 'RS100m', '1V8_LDO', '+1V8', 'LDO', 'Shunt 0.1 Ω đo dòng 1V8 của AFE + phía A của TXS0108E.', 'yêu cầu đo dòng (user)'),
 tp('TP1', '1V8_LDO', 'LDO', 'Đo dòng 1V8: phía LDO.'),
 tp('TP2', '+1V8', 'LDO', 'Đo dòng 1V8: phía tải.'),
 tp('TP3', 'GND', 'LDO', 'GND cho que đo.'),
 # PPG AFE
 part('U2', 'AFE', {'A1': 'VLED', 'D1': 'LED_G_K', 'C1': 'LED_R_K', 'B1': 'LED_IR_K', 'D5': 'PD1_K', 'D4': 'PD2_K', 'C5': 'GND', 'B5': 'AFE_VREF',
                    'D2': '+1V8', 'C2': '+1V8', 'A2': 'SCLK_1V8', 'A4': 'SDI_1V8', 'A3': 'SDO_1V8', 'A5': 'CSB_1V8', 'B2': 'INT_1V8',
                    'B3': None, 'B4': None, 'C4': 'GND', 'C3': 'GND', 'D3': 'GND'},
      'AFE', 'AFE quang PPG: 3 bộ lái LED (tới 124 mA), 2 kênh ADC dòng 19-bit cho 2 photodiode chạy đồng thời, khử ánh sáng môi trường, FIFO 128 mẫu. '
      'SPI tối đa 4 MHz ở mức 1.8 V. LED1 = xanh lá (nhịp tim), LED2 = đỏ, LED3 = hồng ngoại (SpO2). GPIO1/2 không dùng (để trống được).',
      'MAX p.1, p.6 (VLED, VDD), p.8 (SPI 4 MHz, VIH 1.4 V), p.11 (bump map), p.12 (chân)'),
 cap('C6', 'C1u', 'AFE_VREF', 'AFE', 'VREF: tụ 1 µF.', 'MAX p.12 (VREF)'),
 cap('C7', 'C100n', '+1V8', 'AFE', 'VDD_ANA: 0.1 µF sát bump.', 'MAX p.12 (VDD_ANA)'),
 cap('C8', 'C10u', '+1V8', 'AFE', 'VDD_ANA: 10 µF.', 'MAX p.12 (VDD_ANA)'),
 cap('C9', 'C100n', '+1V8', 'AFE', 'VDD_DIG: bypass 0.1 µF.', 'MAX p.12 (VDD_DIG); sơ đồ khối MAX p.40'),
 part('D1', 'LED3', {'3': 'VLED', '1': 'LED_G_K', '4': 'LED_R_K', '2': 'LED_IR_K'}, 'AFE',
      'LED 3 màu trong 1 vỏ: xanh lá 530 nm (nhịp tim ở cổ tay), đỏ 655 nm + hồng ngoại 940 nm (SpO2). Anode chung lên VLED, cathode về LEDx_DRV.',
      'SFH p.1, p.3 (VF), p.9 (chân); MAX p.12 (nối LED)'),
 part('D2', 'PD', {'1': 'PD1_K', '2': 'PD1_K', '3': 'PD1_K', '4': 'PD1_K', '6': 'PD1_K', '7': 'PD1_K', '8': 'PD1_K', '5': 'GND'}, 'AFE',
      'Photodiode diện tích lớn #1 (phía trái LED). Cathode → PD1_IN, anode → PD_GND.', 'VEMD p.1, p.4 (chân); MAX p.12 (PD1_IN)'),
 part('D3', 'PD', {'1': 'PD2_K', '2': 'PD2_K', '3': 'PD2_K', '4': 'PD2_K', '6': 'PD2_K', '7': 'PD2_K', '8': 'PD2_K', '5': 'GND'}, 'AFE',
      'Photodiode #2 (phía phải LED): 2 kênh giúp chọn kênh tốt / trung bình khi cử động.', 'VEMD p.4; MAX p.12 (PD2_IN, chỉ MAX86141)'),
 # level shifter 1.8 <-> 3.3 V
 part('U3', 'TXS', {'2': '+1V8', '19': '+3V3', '11': 'GND', '10': 'TXS_OE',
                    '1': 'SCLK_1V8', '3': 'SDI_1V8', '4': 'SDO_1V8', '5': 'CSB_1V8', '6': 'INT_1V8', '7': None, '8': None, '9': None,
                    '20': 'PPG_SCLK', '18': 'PPG_MOSI', '17': 'PPG_MISO', '16': 'PPG_CS', '15': 'PPG_INT', '14': None, '13': None, '12': None},
      'SHIFT', 'Chuyển mức 2 chiều tự động 1.8 V ↔ 3.3 V cho SPI + INT: chân MAX86141 tối đa 2.2 V, còn ESP32 cần VIH ≥ 0.75·3.3 V. '
      'VCCA = 1.8 V ≤ VCCB = 3.3 V luôn đúng vì 1V8 lấy từ 3V3. Kênh 6-8 để trống (có điện trở kéo lên nội).',
      'TXS p.1, p.4 (chân), §7.3.5 p.18 (pull-up 4k/40k nội), §8.3 p.20 (OE, VCCA ≤ VCCB); MAX p.4 (abs max 2.2 V), DS Table 5-4 p.65 (VIH = 0.75·VDD)'),
 res('R2', 'R100k', '+1V8', 'TXS_OE', 'SHIFT', 'OE nối VCCA qua RC 100 kΩ/100 nF (~10 ms): chỉ bật sau khi VCCA, VCCB ổn định.', 'TXS §8.3 p.20'),
 cap('C10', 'C100n', 'TXS_OE', 'SHIFT', 'Tụ RC trễ OE.', 'TXS §8.3 p.20'),
 cap('C11', 'C100n', '+1V8', 'SHIFT', 'Decoupling VCCA.', 'TXS §8.4'),
 cap('C12', 'C100n', '+3V3', 'SHIFT', 'Decoupling VCCB.', 'TXS §8.4'),
 # skin temperature
 part('U4', 'TEMP', {'1': '+3V3', '2': '+3V3', '3': '+3V3', '4': 'GND', '5': 'GND', '6': 'GND', '8': 'SYS_SDA', '9': 'SYS_SCL',
                     '7': 'TMP_A1', '10': 'TMP_A0'},
      'TEMP', 'Cảm biến nhiệt độ da ±0.1 °C (I2C). GPIO1 = 1, GPIO0 = 0 → địa chỉ 0x52 (tránh 0x51 của RTC); đọc theo chu kỳ, không dùng INT. '
      'Đặt sát tấm tiếp xúc da, cách xa LDO/LED (nguồn nhiệt).', 'M30 p.1, p.6 (chân), Table 3 p.10 (địa chỉ)'),
 cap('C13', 'C100n', '+3V3', 'TEMP', 'Decoupling 0.1 µF.', 'M30 p.6 (VDD)'),
 res('R3', 'R10k', '+3V3', 'TMP_A1', 'TEMP', 'GPIO1 = 1 (bit địa chỉ A1) qua 10 kΩ (an toàn nếu firmware lỡ đặt chân là output).', 'M30 Table 2-3 p.10'),
 res('R4', 'R10k', 'TMP_A0', 'GND', 'TEMP', 'GPIO0 = 0 (bit địa chỉ A0) qua 10 kΩ.', 'M30 Table 2-3 p.10'),
]

BOARDS = {'main': MAIN, 'sensor': SENSOR}
BASE = {'main': 100, 'sensor': 200}
REFMAP = {}
def T(board, s): return re.sub(r'\{([A-Z]+\d+)\}', lambda q: REFMAP[board][q.group(1)], s)
for _b, _parts in BOARDS.items():
    REFMAP[_b] = {p['ref']: '%s%d' % (re.match(r'[A-Z]+', p['ref']).group(0), BASE[_b] + int(re.search(r'\d+$', p['ref']).group(0))) for p in _parts}
for _b, _parts in BOARDS.items():
    for p in _parts:
        p['short'] = p['ref']; p['ref'] = REFMAP[_b][p['ref']]; p['why'] = T(_b, p['why']); p['cite'] = T(_b, p['cite'])

TITLE = {'main': 'Health watch - main board', 'sensor': 'Health watch - sensor board'}
# sheets: (key, title, paper, blocks)
SHEETS = {'main': [('power', 'Power: USB-C, AXP2101 PMIC, battery, current shunts', 'A3', ['USB', 'PMIC']),
                   ('mcu', 'ESP32-S3R8 + 16 MB flash + RF', 'A3', ['MCU', 'RF', 'DEBUG']),
                   ('periph', 'Display FPC, IMU, RTC, LED boost, sensor-board FPC', 'A3', ['DISPLAY', 'SENSORS', 'BOOST', 'FPC']),
                   ('ui', 'Motor, buzzer, SOS button, status LED', 'A4', ['UI'])],
          'sensor': [('sensor', 'PPG AFE, LEDs, photodiodes, level shifter, skin temperature', 'A3', ['FPC', 'LDO', 'AFE', 'SHIFT', 'TEMP'])]}
BLOCK_NAME = {'USB': 'USB-C + ESD', 'PMIC': 'PMIC AXP2101 + pin + shunt đo dòng', 'MCU': 'ESP32-S3R8 + flash + thạch anh + reset/boot',
              'RF': 'Phối hợp RF + ăng-ten gốm', 'DEBUG': 'UART0 debug', 'DISPLAY': 'FPC màn hình AMOLED + cảm ứng', 'SENSORS': 'IMU BMI270 + RTC PCF85063A',
              'BOOST': 'Boost 5 V cho LED PPG', 'FPC': 'FPC sang bo cảm biến', 'UI': 'Motor rung, còi, nút SOS, LED',
              'LDO': 'LDO 1.8 V + shunt', 'AFE': 'MAX86141 + LED + photodiode', 'SHIFT': 'Chuyển mức TXS0108E', 'TEMP': 'MAX30208 nhiệt độ da'}
# I2C bus addresses (7-bit) - checked for clashes in check()
I2C = {'AXP2101': 0x34, 'CST9217 touch': 0x5A, 'BMI270': 0x68, 'PCF85063A': 0x51, 'MAX30208': 0x52}

def check():
    ok = True
    for b, parts in BOARDS.items():
        refs = collections.Counter(p['ref'] for p in parts)
        dup = [r for r, n in refs.items() if n > 1]
        if dup: print('DUP', b, dup); ok = False
        nets = collections.Counter(n for p in parts for n in set(p['pins'].values()) if n)
        single = sorted(n for n, k in nets.items() if k == 1)
        print(b, len(parts), 'parts', len(nets), 'nets; single-pin nets:', single)
    a = collections.Counter(I2C.values())
    assert all(v == 1 for v in a.values()), 'I2C address clash'
    # every net that crosses the FPC must exist on both boards with the same name
    fm = {k: v for k, v in MAIN[[p['short'] for p in MAIN].index('J5')]['pins'].items()}
    fs = {k: v for k, v in SENSOR[0]['pins'].items()}
    assert fm == fs, 'FPC pin maps differ'
    return ok
if __name__ == '__main__': check()
