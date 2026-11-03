# Trích dẫn - đồng hồ theo dõi sức khỏe

Mọi số liệu dùng trong báo cáo và schematic đều trỏ về một trang của tài liệu trong thư mục `datasheets/`.
Số trang = trang PDF (trùng số in trên trang; riêng HDG: số in = PDF − 3). **ASSUME** = giả định, chưa có tài liệu.

## 1. Tài liệu

| Khóa | Tài liệu | File |
|---|---|---|
| DS | Espressif ESP32-S3 Series Datasheet v2.2 | `datasheets/ESP32-S3_Datasheet.pdf` |
| HDG | Espressif ESP32-S3 Hardware Design Guidelines | `datasheets/ESP32-S3_Hardware_Design_Guidelines.pdf` |
| AXP | X-Powers AXP2101 datasheet | `datasheets/LCSC_C3036461_AXP2101.pdf` |
| MAX | Analog Devices MAX86140/MAX86141 datasheet | `datasheets/LCSC_C5328762_MAX86141.pdf` |
| M30 | Maxim MAX30208 datasheet | `datasheets/LCSC_C2874216_MAX30208.pdf` |
| BMI | Bosch BMI270 datasheet BST-BMI270-DS000-08 | `datasheets/Bosch_BMI270_datasheet.pdf` |
| TPS | TI TPS61240/TPS61241 datasheet SLVS806D | `datasheets/LCSC_C133991_TPS61240.pdf` |
| TXS | TI TXS0108E datasheet SCES642L | `datasheets/LCSC_C17206_TXS0108E.pdf` |
| LP | TI LP5907 datasheet | `datasheets/LCSC_C92498_LP5907-1.8.pdf` |
| W25 | Winbond W25Q128JV datasheet | `datasheets/LCSC_C97521_W25Q128JVSIQ.pdf` |
| SFH | OSRAM SFH 7013 datasheet (Chinese edition) v1.3 | `datasheets/OSRAM_SFH7013.pdf` |
| VEMD | Vishay VEMD8080 datasheet rev 1.0 | `datasheets/LCSC_C511402_VEMD8080.pdf` |
| LC6 | ST USBLC6-2 datasheet | `datasheets/LCSC_C7519_USBLC6-2SC6.pdf` |
| TYC | USB-C receptacle TYPE-C-31-M-12 drawing | `datasheets/LCSC_C165948_TYPE-C-31-M-12.pdf` |
| XT | 40 MHz crystal X322540MPB4SI | `datasheets/LCSC_C9010_X322540MPB4SI_40MHz.pdf` |
| TS | tact switch TS-1088 | `datasheets/LCSC_C720477_TS-1088_tact_switch.pdf` |
| AO | AO3401A (P-FET, reference only) | `datasheets/LCSC_C15127_AO3401A.pdf` |
| WS | Waveshare ESP32-S3-Touch-AMOLED-1.75C schematic (reference design) | `datasheets/Waveshare_ESP32-S3-Touch-AMOLED-1.75C_schematic.pdf` |

## 2. Số liệu đã đối chiếu tự động (29/29 khớp trang PDF)

| Số liệu | Giá trị | Tài liệu, trang | Đoạn văn bản phải có trên trang | Kiểm |
|---|---|---|---|---|
| ESP32-S3 light-sleep (Table 5-10) | 0.24 mA | DS p.68 (ESP32-S3_Datasheet.pdf) | `Light-sleep1?\s+VDD_SPI and Wi-Fi are powered down.*?240` | OK |
| ESP32-S3 deep-sleep (Table 5-10) | 0.007 mA | DS p.68 (ESP32-S3_Datasheet.pdf) | `RTC memory is powered up\. RTC peripherals are powered down\.\s+7` | OK |
| ESP32-S3 160 MHz, 2 nhân chạy (Table 5-9, Typ2) | 64.1 mA | DS p.67 (ESP32-S3_Datasheet.pdf) | `160\s+Dual core running 32-bit data access instructions\s+49\.6\s+64\.` | OK |
| ESP32-S3 240 MHz, 2 nhân chạy (Table 5-9, Typ2) | 81.3 mA | DS p.67 (ESP32-S3_Datasheet.pdf) | `240\s+Dual core running 32-bit data access instructions\s+66\.2\s+81\.` | OK |
| WiFi TX đỉnh HT20 MCS7 (Table 5-7) | 283 mA | DS p.66 (ESP32-S3_Datasheet.pdf) | `802\.11n, HT20, MCS7, @18\.5 dBm\s+283` | OK |
| WiFi RX (Table 5-7) | 88 mA | DS p.66 (ESP32-S3_Datasheet.pdf) | `802\.11b/g/n, HT20\s+88` | OK |
| BLE TX 0 dBm đỉnh (Table 5-8) | 176 mA | DS p.67 (ESP32-S3_Datasheet.pdf) | `Bluetooth LE @ 0 dBm\s+176` | OK |
| MAX86141 ILED, 1 LED 62 mA, 25 sps | 0.185 mA | MAX p.7 (LCSC_C5328762_MAX86141.pdf) | `PPG_SR=25sps\s+185` | OK |
| MAX86141 ILED, 1 LED 62 mA, 100 sps | 0.735 mA | MAX p.7 (LCSC_C5328762_MAX86141.pdf) | `PPG_SR = 100sps\s+735` | OK |
| MAX86141 IDD, 25 sps, LP_MODE | 0.011 mA | MAX p.7 (LCSC_C5328762_MAX86141.pdf) | `PPG_SR = 25sps\s+11` | OK |
| MAX86141 IDD shutdown | 0.0006 mA | MAX p.7 (LCSC_C5328762_MAX86141.pdf) | `VDD Current in Shutdown\s+TA = \+25°C\s+0\.6` | OK |
| MAX86141 VDD 1.7-2.0 V | 1.8 V | MAX p.6 (LCSC_C5328762_MAX86141.pdf) | `1\.7\s+1\.8\s+2\.0\s+V` | OK |
| MAX86141 VLED 3.1-5.5 V | 3.1 V | MAX p.6 (LCSC_C5328762_MAX86141.pdf) | `LED Supply Voltage\s+VLED\s+Verified during PSRR Test\s+3\.1\s+5\.5` | OK |
| MAX86141 SPI tối đa | 4 MHz | MAX p.8 (LCSC_C5328762_MAX86141.pdf) | `SCLK Frequency\s+fSCLK\s+4\s+MHz` | OK |
| MAX86141 VIH | 1.4 V | MAX p.8 (LCSC_C5328762_MAX86141.pdf) | `Input Voltage High\s+VIH\s+SDI, SCLK, CSB, GPIO1, GPIO2\s+1\.4` | OK |
| MAX86141 abs max VDD | 2.2 V | MAX p.4 (LCSC_C5328762_MAX86141.pdf) | `VDD_DIG to GND_ANA\. \.+-0\.3V to \+2\.2V` | OK |
| SFH 7013 VF xanh lá max | 3.35 V | SFH p.3 (OSRAM_SFH7013.pdf) | `VF\s+典型值\s+3\.00 V.*?最大值\s+3\.35 V` | OK |
| BMI270 acc+gyro normal | 0.685 mA | BMI p.11 (Bosch_BMI270_datasheet.pdf) | `A\+G Normal Mode.*?685` | OK |
| BMI270 acc normal (ODR max) | 0.21 mA | BMI p.11 (Bosch_BMI270_datasheet.pdf) | `Aonly Normal Mode.*?210` | OK |
| BMI270 địa chỉ I2C | 104  | BMI p.128 (Bosch_BMI270_datasheet.pdf) | `0b1101000 \(0x68\)` | OK |
| TPS61240 Iq | 0.03 mA | TPS p.5 (LCSC_C133991_TPS61240.pdf) | `Operating quiescent current\s+IOUT = 0 mA, Power save mode\s+30\s+40` | OK |
| TPS61240 CIN | 2.2 uF | TPS p.12 (LCSC_C133991_TPS61240.pdf) | `2\.2 μF, X5R, 6\.3 V, 0402` | OK |
| LP5907 Iq | 0.012 mA | LP p.6 (LCSC_C92498_LP5907-1.8.pdf) | `VEN = 1\.2 V, IOUT = 0 mA\s+12\s+25` | OK |
| MAX30208 standby | 0.0005 mA | M30 p.1 (LCSC_C2874216_MAX30208.pdf) | `0\.5μA Standby Current` | OK |
| AXP2101 dòng pin khi tắt (chỉ RTCLDO) | 0.04 mA | AXP p.11 (LCSC_C3036461_AXP2101.pdf) | `IBAT\s+Battery discharge current\s+40` | OK |
| AXP2101 kéo lên I2C | 2.2 kΩ | AXP p.9 (LCSC_C3036461_AXP2101.pdf) | `needs a 2\.2kΩ Pull High` | OK |
| AXP2101 tụ VSYS | 22 uF | AXP p.8 (LCSC_C3036461_AXP2101.pdf) | `Connect two\s+22uF capacitors` | OK |
| TXS0108E pull-up nội | 4 kΩ | TXS p.18 (LCSC_C17206_TXS0108E.pdf) | `40kΩ when the output is driving low.*?4kΩ when the output is driving h` | OK |
| TXS0108E VCCA ≤ VCCB | 0  | TXS p.20 (LCSC_C17206_TXS0108E.pdf) | `ensure that VCCA ≤ VCCB at all times` | OK |

## 3. Trích dẫn theo linh kiện - Health watch - main board

| Ref | Giá trị | Tài liệu (khóa §/bảng/trang) |
|---|---|---|
| J101 | TYPE-C-31-M-12 | TYC; HDG §1.3.13 |
| R101 | 5.1k | USB Type-C spec (Rd = 5.1 kΩ) |
| R102 | 5.1k | USB Type-C spec |
| U101 | USBLC6-2SC6 | LC6 p.1; HDG §1.3.13 |
| R103 | 22 | HDG §1.3.13; WS p.1 (R13) |
| R104 | 22 | HDG §1.3.13; WS p.1 (R14) |
| TP101 | TP | - |
| U102 | AXP2101 | AXP p.1 (features), Table 4-1 p.7-9 (chân), Fig 7-1 p.57 (mạch ứng dụng); WS p.1 |
| C101 | 10uF 10V | AXP Fig 7-1 p.57 |
| C102 | 10uF 10V | AXP Fig 7-1 p.57; WS p.1 (CP2) |
| C103 | 22uF 6.3V | AXP Table 4-1 p.8 (pin 34) |
| C104 | 22uF 6.3V | AXP Table 4-1 p.8 (pin 34) |
| C105 | 1uF | AXP Table 4-1 p.8 (pin 33) |
| C106 | 1uF | AXP Fig 7-1 p.57 |
| C107 | 1uF | AXP Fig 7-1 p.57 |
| C108 | 2.2uF | WS p.1 (CP13); AXP Fig 7-1 p.57 |
| C109 | 1uF | AXP Fig 7-1 p.57 |
| C110 | 1uF | AXP Fig 7-1 p.57 |
| L101 | 1uH 2.5A | AXP Fig 7-1 p.57, §6.6 p.22 (3 MHz) |
| C111 | 22uF 6.3V | AXP Fig 7-1 p.57 |
| L102 | 1uH 2.5A | WS p.1 (LP2, RP2); AXP Fig 7-1 p.57 |
| R105 | 0R | WS p.1 (RP2) |
| RT101 | NTC 10k B3950 | AXP Table 4-1 p.8 (pin 31 TS); WS p.1 (RP4) |
| R106 | 4.7k | AXP Table 4-1 p.8 (pin 38) |
| R107 | 2.2k | AXP Table 4-1 p.9 (pin 39 "needs a 2.2kΩ pull high") |
| R108 | 2.2k | AXP Table 4-1 p.9 (pin 40) |
| R109 | 510 | WS p.1 (RP6) |
| C112 | 1nF | WS p.1 (CP14) |
| SW101 | TS-1088 4x3mm | AXP Table 4-1 p.8 (pin 30 PWRON, kéo lên 100k nội) |
| R110 | 1k | AXP Fig 7-1 p.57 (LED từ VSYS về CHGLED) |
| D101 | Red 0603 | AXP Table 4-1 p.7 (pin 1) |
| J102 | LiPo 1S ~400mAh | - |
| R111 | 0.05R 1% 0805 | yêu cầu đo dòng (user) |
| TP102 | TP | - |
| TP103 | TP | - |
| R112 | 0.1R 1% 0603 | yêu cầu đo dòng (user) |
| TP104 | TP | - |
| TP105 | TP | - |
| TP106 | TP | - |
| TP107 | TP | - |
| U103 | TPS61240DRVT | TPS p.1, p.3 (chân), §10.2.2 p.12 (CIN 2.2 µF, COUT 4.7 µF, L 1 µH); MAX p.6 (VLED 3.1-5.5 V); SFH p.3 (VF green max 3.35 V) |
| L103 | 1uH 1A | TPS §10.2.2 p.12 (L = 1 µH) |
| C113 | 2.2uF | TPS §10.2.2 p.12 |
| C114 | 4.7uF | TPS §10.2.2 p.12 |
| R113 | 100k | DS §3 Table 3-1 p.32 (GPIO3 strapping) |
| R114 | 0.1R 1% 0603 | yêu cầu đo dòng (user) |
| TP108 | TP | - |
| TP109 | TP | - |
| U104 | ESP32-S3R8 | DS p.2 (features), Table 1-1 (R8 = 8 MB PSRAM), Table 2-1 (chân) |
| C115 | 10uF 10V | HDG §1.3.2 p.8 |
| C116 | 1uF | HDG Fig.1 p.5 |
| C117 | 100nF | HDG Fig.1 p.5 |
| L104 | 2.0nH | HDG §1.3.2 p.8; WS p.1 (IND1 2.0nH) |
| C118 | 1uF | HDG Fig.1 p.5 |
| C119 | 10nF | HDG Fig.1 p.5 |
| C120 | 100nF | HDG §1.3.2 |
| C121 | 100nF | HDG §1.3.2 |
| C122 | 100nF | HDG §1.3.2 p.7 |
| C123 | 1uF | HDG §1.3.2 p.7 |
| R115 | 10k | HDG §1.3.3 Table 2 p.8; WS p.1 (R8) |
| C124 | 1uF | HDG §1.3.3 p.8 |
| SW102 | TS-1088 4x3mm | HDG §1.3.3 |
| R116 | 10k | DS §3 Table 3-1 p.32; HDG §1.3.9 |
| SW103 | TS-1088 4x3mm | DS Table 3-3 p.33; HDG §1.3.9 |
| Y101 | 40MHz 10ppm CL15pF | HDG §1.3.5 p.10; XT |
| L105 | 24nH | HDG §1.3.5 p.10; WS p.1 (R10 24nH) |
| C125 | 22pF C0G | HDG §1.3.5 p.11 |
| C126 | 22pF C0G | HDG §1.3.5 p.11 |
| U105 | W25Q128JVSIQ | W25 p.1, §3 (chân SOIC-8 208 mil); DS §3.3 Table 3-4 p.34 (VDD_SPI theo GPIO45); WS p.1 (U2) |
| C127 | 100nF | W25 |
| C128 | 1.5pF C0G | HDG §1.3.6 Table 6 p.13 |
| L106 | 2.4nH | HDG §1.3.6 Table 6 p.13 |
| C129 | 1.5pF C0G | HDG §1.3.6 p.12-13 |
| C130 | DNP | HDG §1.3.6 p.12 |
| R117 | 0R | HDG §1.3.6 p.12 |
| C131 | DNP | HDG §1.3.6 p.12 |
| AE101 | 2450AT18A100E | HDG §1.3.6; datasheet Johanson (chưa tải - ASSUME) |
| R118 | 499 | HDG §1.3.7 p.13 |
| J103 | UART0 1x03 2.54 | yêu cầu user |
| J104 | FPC 0.3mm 31P back-flip | WS p.1 (J3, bảng GPIO) |
| C132 | 10uF 10V | ASSUME (thực hành chung) |
| C133 | 100nF | - |
| U106 | BMI270 | BMI Table 22 p.135 (chân, cách nối I2C), §5 p.128 (địa chỉ 0x68) |
| C134 | 100nF | BMI §7 (sơ đồ nối) - ASSUME giá trị 100 nF |
| C135 | 100nF | BMI §7 |
| U107 | PCF85063ATL/1 | ASSUME: datasheet NXP PCF85063A chưa tải được; pinout lấy từ symbol KiCad Timer_RTC:PCF85063ATL |
| Y102 | 32.768kHz CL7pF | ASSUME (datasheet PCF85063A) |
| C136 | 100nF | - |
| R119 | 10k | - |
| Q101 | AO3400A | AO3400A datasheet (ASSUME, chưa tải) |
| R120 | 100 | - |
| R121 | 100k | DS §3 Table 3-1 p.32, Table 3-3 p.33 (GPIO46) |
| M101 | Coin motor 1027 3V | - |
| D102 | BAT54WS | - |
| Q102 | AO3400A | - |
| R122 | 100 | - |
| R123 | 100k | DS §3 Table 3-1 p.32, Table 3-4 p.34 (GPIO45) |
| BZ101 | CMT-8504-100-SMT | CUI CMT-8504 (ASSUME, chưa tải) |
| D103 | BAT54WS | - |
| SW104 | TS-1088 4x3mm | DS §2.3 p.23-24 (RTC GPIO) |
| R124 | 10k | - |
| C137 | 100nF | - |
| R125 | 1k | - |
| D104 | Green 0603 | yêu cầu user |
| J105 | FH12-16S-0.5SH | Hirose FH12 (footprint KiCad) |

## 3. Trích dẫn theo linh kiện - Health watch - sensor board

| Ref | Giá trị | Tài liệu (khóa §/bảng/trang) |
|---|---|---|
| J201 | FH12-16S-0.5SH | - |
| C201 | 10uF 10V | - |
| C202 | 10uF 10V | MAX p.12 (VLED: bypass 10 µF to PGND) |
| C203 | 100nF | ASSUME |
| U201 | LP5907MFX-1.8 | LP p.1 (noise, PSRR); MAX p.6 (VDD 1.7-2.0 V), p.7 (shutdown 0.6 µA) |
| C204 | 1uF | LP p.6 (điều kiện đo CIN = COUT = 1 µF) |
| C205 | 1uF | LP p.6 (COUT 1 µF) |
| R201 | 0.1R 1% 0603 | yêu cầu đo dòng (user) |
| TP201 | TP | - |
| TP202 | TP | - |
| TP203 | TP | - |
| U202 | MAX86141ENP+ | MAX p.1, p.6 (VLED, VDD), p.8 (SPI 4 MHz, VIH 1.4 V), p.11 (bump map), p.12 (chân) |
| C206 | 1uF | MAX p.12 (VREF) |
| C207 | 100nF | MAX p.12 (VDD_ANA) |
| C208 | 10uF 10V | MAX p.12 (VDD_ANA) |
| C209 | 100nF | MAX p.12 (VDD_DIG); sơ đồ khối MAX p.40 |
| D201 | SFH 7013 | SFH p.1, p.3 (VF), p.9 (chân); MAX p.12 (nối LED) |
| D202 | VEMD8080 | VEMD p.1, p.4 (chân); MAX p.12 (PD1_IN) |
| D203 | VEMD8080 | VEMD p.4; MAX p.12 (PD2_IN, chỉ MAX86141) |
| U203 | TXS0108EPWR | TXS p.1, p.4 (chân), §7.3.5 p.18 (pull-up 4k/40k nội), §8.3 p.20 (OE, VCCA ≤ VCCB); MAX p.4 (abs max 2.2 V), DS Table 5-4 p.65 (VIH = 0.75·VDD) |
| R202 | 100k | TXS §8.3 p.20 |
| C210 | 100nF | TXS §8.3 p.20 |
| C211 | 100nF | TXS §8.4 |
| C212 | 100nF | TXS §8.4 |
| U204 | MAX30208CLB+ | M30 p.1, p.6 (chân), Table 3 p.10 (địa chỉ) |
| C213 | 100nF | M30 p.6 (VDD) |
| R203 | 10k | M30 Table 2-3 p.10 |
| R204 | 10k | M30 Table 2-3 p.10 |
