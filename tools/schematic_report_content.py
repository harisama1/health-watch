"""Text of the schematic analysis report, read by gen_schematic_report.py. Light markup: #, ##, ###, | tables, - lists, {{fig|...}}."""
CONTENT = r'''
# Báo cáo phân tích schematic: đồng hồ theo dõi sức khỏe

| Phiên bản | Ngày | Người phụ trách | Nội dung |
|---|---|---|---|
| 1.0 | 05/11/2026 | HaiLV25 | Tạo tài liệu |
| 1.1 | 05/11/2026 | HaiLV25 | Sửa lý do của S2; nâng mục L102/VMID (O8); trỏ sang báo cáo thiết kế tổng |
| 1.2 | 05/11/2026 | HaiLV25 | Thêm S7-S12 (SFH 7016, R126, R105, R113, RF 0201, test point, BOM); cập nhật số liệu và bản vẽ |

Đối tượng phân tích: schematic Rev 1.2 của bo chính (`hardware/main/`) và bo cảm biến (`hardware/sensor/`). Thiết kế **chưa được chế tạo**: mọi kết luận dựa trên datasheet và công cụ kiểm tra tự động, không có số đo phần cứng.

## 1. Kết luận

- Không tìm thấy lỗi làm bo chắc chắn không hoạt động hoặc gây hỏng linh kiện theo datasheet đã đọc.
- Đã sửa 12 sai sót trên schematic và thư viện, 8 nội dung mô tả sai (mục 5), và các lỗi của công cụ kiểm tra (mục 4.3).
- Báo cáo này chỉ xét schematic; BOM, pin, cảm biến, firmware và sản xuất nằm trong `health_watch_design_report.docx`.
- Còn 3 vấn đề lớn chưa thể đóng bằng cách sửa schematic (mục 6): boot phụ thuộc OTP của AXP2101, đường VBUS → VSYS qua L102 và R105, và TXS0108E không có đảm bảo mức logic trong datasheet.
- Sau khi sửa: ERC 0 lỗi, 0 cảnh báo trên cả hai bo; netlist khớp `tools/design.py` trên toàn bộ chân, tên net, giá trị và footprint.

| Bo | Linh kiện | Chân | Net |
|---|---|---:|---:|
| Bo chính | 111 | 403 | 80 |
| Bo cảm biến | 27 | 129 | 26 |

## 2. Phương pháp

| Lớp kiểm tra | Cách làm | Giới hạn |
|---|---|---|
| Đối chiếu datasheet | Đọc trực tiếp theo trang; mỗi phát hiện ghi tài liệu và trang | Tài liệu chưa đọc được liệt kê ở mục 8 |
| ERC (Electrical Rule Check: kiểm tra luật điện) | `kicad-cli` 10.0.8, `--severity-all --exit-code-violations` | `gen_sch.py` tự thêm `PWR_FLAG` cho rail không có chân `power_out`, nên ERC không xác nhận được rail có nguồn cấp |
| Netlist so với thiết kế | `tools/check_net.py` | Chỉ so với `design.py`: nếu `design.py` sai về nguyên lý thì kiểm tra này vẫn đạt |
| Kiểm tra công cụ bằng lỗi cấy | Cố ý làm sai rồi xem công cụ có bắt không (mục 4.2) | Chỉ các dạng lỗi đã cấy |
| Đối chiếu trang | `tools/facts.py` | Chỉ xác nhận mẫu văn bản có trên trang, không so giá trị số |

## 3. Kiến trúc được phân tích

Đồng hồ gồm bo chính (ESP32-S3R8, AXP2101, màn AMOLED 1,75", BMI270, PCF85063A, boost 5 V, motor, còi) và bo cảm biến (MAX86141, SFH 7013, 2 × VEMD8080, LP5907 1,8 V, TXS0108E, MAX30208), nối qua FPC 16 chân. Bản vẽ đầy đủ của từng sheet ở Phụ lục B.

{{fig|block_diagram|Sơ đồ khối hai bo.|16.5}}

{{fig|power_tree|Cây nguồn và các điểm đo dòng.|16.5}}

## 4. Kết quả kiểm chứng

### 4.1 Trước và sau khi sửa

| Tiêu chí | Trước | Sau |
|---|---|---|
| ERC bo chính (có bảng thư viện global) | 3 cảnh báo, gồm 2 cảnh báo thiếu thư viện `HW_IC` | 0 |
| ERC bo cảm biến | 0 | 0 |
| `check_net.py` trên netlist KiCad 10 | Không đọc được netlist: báo 80/80 và 26/26 net khác | 0 khác biệt |
| Sinh lại bo chính từ repo công khai | Lỗi `ValueError`, `KeyError` | Chạy được |
| Sinh lại khi chưa đổi thiết kế | Không trùng bản đã commit | Trùng từng byte (kiểm tra trước khi sửa thiết kế) |
| `facts.py` trên datasheet | 28/29 (một regex lệch) | 29/29 |

Trên máy chưa có bảng thư viện global của KiCad, ERC bản cũ báo 322 cảnh báo (bo chính) và 97 (bo cảm biến). Hầu hết là báo giả do thiếu bảng thư viện, không phải lỗi mạch.

### 4.2 Lỗi cấy vào để thử công cụ

| Lỗi cấy | Công cụ cũ | Công cụ mới |
|---|---|---|
| Đổi nhãn global `SYS_SDA` thành local trên một sheet (net đứt thật) | Đạt | `SPLIT/MISSING`, rc=1 |
| Hoán đổi tên `PPG_MISO` và `PPG_MOSI` | Đạt | `NAME`, rc=1 |
| Đổi tên `PPG_INT` | Đạt | `NAME`, rc=1 |
| R204 đổi giá trị thành 1 MΩ | Đạt | `PART`, rc=1 |
| Đổi net một chân R205 trong `design.py` | Chưa thử | `DIFF`, rc=1 |
| Bỏ một chân của U204 khỏi `design.py` | Đạt | Generator dừng, rc=1 |

### 4.3 Lỗi công cụ đã sửa

| File | Lỗi | Sửa |
|---|---|---|
| `tools/check_net.py` | Regex chỉ đọc được bố cục netlist KiCad 9; gộp net `/sheet/X` với `X` nên không thấy net đứt; không báo sai tên; không so giá trị và footprint | Viết lại |
| `tools/gen_sch.py` | Cảnh báo chân thiếu và chập net vẫn trả rc=0 | Trả lỗi khi có cảnh báo |
| `tools/gen_sch.py` | Đọc symbol theo KiCad đang cài nhưng ghi nhãn định dạng KiCad 9 | Đóng băng symbol trong `tools/stock_symbols/` |
| `tools/gen_sch.py`, `tools/libgen.py` | Phụ thuộc repo riêng `PCB_design_learning` | Dùng `hardware/HW_IC.kicad_sym`, `hardware/HW_Watch.kicad_sym` |
| `tools/design.py` | Kết quả `check()` bị bỏ qua | Thoát với rc=1 khi có lỗi |
| `tools/facts.py` | Regex `afe_absmax` phụ thuộc cách trích văn bản | Nới regex |
| `tools/md2pdf.py` | Chỉ chạy được với flatpak LibreOffice | Ưu tiên Chrome headless |
| `tools/check_bom.py` (mới) | Không có kiểm tra mã BOM | Đối chiếu từng mã LCSC với API; rc=1 nếu sai |

## 5. Các lỗi đã sửa

### 5.1 Trên schematic và thư viện

| # | Mức | Vị trí | Lỗi và hệ quả | Căn cứ | Sửa |
|---|---|---|---|---|---|
| S1 | Lớn | U202.C5, D202/D203 chân 5 | `PD_GND` gộp vào `GND` chung. Đường hồi photodiode không thể tách khỏi dòng xung LED ở PGND (tới 124 mA) | MAX86141 p.12, p.88 và Note 3 (shorting via hoặc 0 Ω) | Thêm net `PD_GND`, nối về `GND` tại một điểm qua R205 0 Ω |
| S2 | Nhỏ | U203.10 (OE), R202, C210 | RC 100 kΩ/100 nF tạo sườn khoảng 5,6 ms/V, trong khi giới hạn chân điều khiển là 10 ns/V. Chân OE dừng lâu ở vùng chuyển mức, có thể gây xung lạ trên CSB. Datasheet không mô tả RC này như đã ghi | TXS0108E p.6, §8.3 p.20 | Nối thẳng OE vào `+1V8`, bỏ R202, C210. Chưa làm cách của TI (pull-down và lái OE): GPIO47/48 còn trống nhưng FPC 16 chân không còn chân để đưa OE sang bo cảm biến |
| S3 | Nhỏ | C205 | Tổng tụ trên ngõ ra LP5907 11,3 µF danh định, vượt tối đa 10 µF | LP5907 p.7 | C205 không lắp (giữ footprint), còn 10,3 µF danh định. Cần xác nhận giá trị hiệu dụng ≤ 10 µF ở 1,8 V bằng đường cong DC-bias của tụ. ESR 5–500 mΩ đạt với R201 0,1 Ω |
| S4 | Nhỏ | J101, U101 | Symbol `HW_IC` không có trong bảng thư viện của project; file nguồn nằm ngoài repo | ERC | Thêm `hardware/HW_IC.kicad_sym` và mục trong `sym-lib-table` |
| S5 | Nhỏ | Sheet Power, net `VBUS` | Nhãn local trùng tên power symbol (cảnh báo `same_local_global_label`) | ERC | Thay nhãn bằng power symbol |
| S6 | Nhỏ | `.kicad_pro` | `meta.filename` còn `airmouse_mouse.kicad_pro` từ dự án khác | Đọc file | Sửa đúng tên |
| S7 | Lớn | D201 | SFH 7013 ngừng sản xuất, LCSC hết hàng | ams-OSRAM (停产) | Đổi SFH 7016: anode chân 2 và 5, cathode IR/xanh/đỏ chân 1/3/4, chân 6 NC; footprint pad 0,4 mm, paste 0,3 mm (SFH p.13-14) |
| S8 | Lớn | R126, R105 | Chỉ có đường VBUS → SW → L102 → R105 → VSYS; R105 0402 mang toàn bộ dòng vào | AXP p.12, p.17; WS p.1 | Thêm R126 VMID-VSYS không lắp; R105 đổi 0805 |
| S9 | Nhỏ | R113 | 100 kΩ tốn 33 µA khi EN cao | TPS p.5 | Đổi 1 MΩ |
| S10 | Nhỏ | C128-C131, L106, R117 | Linh kiện phối hợp RF dùng 0402 | HDG (yêu cầu 0201) | Đổi footprint 0201 |
| S11 | Nhỏ | TP110-TP114 | Không có điểm đo trên bus | Rà soát | Thêm test point SDA, SCL, SCLK, MISO, PPG_INT |
| S12 | Lớn | BOM trong `design.py` | Nhiều mã LCSC trỏ sai linh kiện (ví dụ tụ 100 pF thay cho 1,5 pF trên RF) | API LCSC | Xóa mã sai, thêm `tools/check_bom.py`; không đổi kết nối |

So netlist của S1-S6 với bản ban đầu: bo chính không đổi tập chân của bất kỳ net nào; bo cảm biến chỉ đổi đúng theo S1 và S2. S7-S11 thêm chân mới và đã qua `check_net.py`, ERC với 0 khác biệt.

{{stacked|afe_before|afe_after|S1: `PD_GND` trước khi sửa nối thẳng vào GND; sau khi sửa về GND qua R205 0 Ω.|11}}

{{pair|oe_before|oe_after|S2: OE của U203 trước khi sửa qua RC R202/C210; sau khi sửa nối thẳng +1V8.|8}}

{{pair|ldo_before|ldo_after|S3: C205 trên ngõ ra LP5907, sau khi sửa đánh dấu không lắp (DNP).|8}}

### 5.2 Nội dung mô tả sai

| # | Trước | Sau | Căn cứ |
|---|---|---|---|
| T1 | Chân SPI của MAX86141 chịu tối đa 2,2 V | 2,2 V là giới hạn của VDD; SCLK, SDO, SDI, CSB, INT chịu tới +6,0 V | MAX86141 p.4 |
| T2 | Giữ GPIO màn hình đúng như Waveshare | Thứ tự chân FPC giữ theo J3; LCD_RST = GPIO1, TP_RST = GPIO2 là lựa chọn riêng, phải đổi hằng số chân nếu dùng code mẫu | Waveshare 1.75 (bản không C) dùng GPIO39/40; bản 1.75C chưa đối chiếu được GPIO này |
| T3 | NTC đặt sát pin | NTC trên bo; đầu nối pin chỉ 2 dây nên đo nhiệt độ bo, không phải cell | `design.py`: J102 2 chân |
| T4 | Duty motor ≤ 75 % | Duty ≈ 3 V/VSYS (71 % ở 4,2 V), khớp với báo cáo thiết kế | Tính toán |
| T5 | Sai số nhiệt ±0,1 °C không kèm điều kiện | ±0,1 °C trong +30…+50 °C, chỉ của chip; thêm giới hạn reflow +220 °C | MAX30208 p.1, p.2 |
| T6 | DS §3.3 Table 3-4 | §3.2 (§3.3 là ROM Messages) | ESP32-S3 Datasheet p.34 |
| T7 | Ghi chú R125 còn phép tính nháp; VF LED xanh không kèm dòng | Viết lại; ghi VF theo dòng (nay 2,80 V ở 20 mA với SFH 7016) | SFH p.5 |
| T8 | Cây nguồn: nhánh VSYS sang TPS61240 bị hở; ghi chú "OE sau RC ~10 ms" | Nối liền nhánh; ghi "OE nối thẳng VCCA" | `tools/gen_diagrams.py` |

## 6. Vấn đề chưa sửa

Các mục này không sửa được bằng schematic, hoặc việc sửa cần quyết định thiết kế.

| # | Mức | Vấn đề | Hệ quả | Hành động đề xuất |
|---|---|---|---|---|
| O1 | Lớn | Điện áp và trạng thái mặc định của DCDC1 do OTP (nạp sẵn lúc xuất xưởng) của AXP2101 quyết định; repo không ghi điều này (AXP2101 Table 6-1 p.22, §6.6 p.23) | Nếu OTP không bật DCDC1 khoảng 3,3 V, ESP32 không có nguồn để cấu hình PMIC. Rail ALDO/BLDO/DLDO nếu bật mặc định sẽ chạy không có tụ ra | Ghi rõ mã OTP khi mua; đọc thanh ghi REG80, REG90–91 trên bo thật. Căn cứ duy nhất hiện có: Waveshare 1.75C ghi DCDC1 = VCC3V3 |
| O2 | Lớn | Mức đảm bảo của TXS0108E không đạt trên giấy: VOHB tối thiểu 0,67·3,3 = 2,21 V so với ESP32 VIH 2,475 V; VOHA tối thiểu 0,67·1,8 = 1,21 V so với MAX86141 VIH 1,4 V (TXS p.7, dòng ghi VCCA = 1,4 V; ESP32-S3 Table 5-4 p.65; MAX86141 p.8) | Tải chỉ vài chục µA nên nhiều khả năng vẫn chạy, nhưng không có đảm bảo trường hợp xấu nhất | **Cần quyết định.** (a) Giữ TXS, đo trên bàn thử ở 4 MHz. (b) Vì SPI/INT chịu +6 V: nối thẳng SCLK, SDI, CSB; kéo INT lên 3,3 V; chỉ SDO qua một buffer chuyển mức. Phương án (b) cần chọn linh kiện và đọc datasheet trước khi áp dụng |
| O3 | Có điều kiện | R106 kéo `AXP_IRQ` lên `+3V3`, rail này mất khi PMIC tắt. IRQ thấp > 16 ms có thể là nguồn bật máy, tuỳ OTP (AXP p.20) | Đồng hồ có thể không tắt hẳn được | Không sửa. Waveshare kéo lên VCC-RTC, nhưng trên thiết kế này cách đó có thể cấp ngược vào GPIO16 của ESP32 đang tắt và vẫn giữ IRQ thấp (suy luận, chưa đo). Thử tắt nguồn trên bo thật rồi mới quyết định |
| O4 | Có điều kiện | Sơ đồ chân FPC 16 không chịu được đảo cáp: đảo cáp đưa VLED 5 V vào `PPG_CS`, `PPG_INT`, và 3V3 vào I2C | Có thể hỏng linh kiện | Chốt loại cáp FFC và cách xếp bo trên bản vẽ cơ khí trước khi đặt mạch |
| O5 | Nhỏ | U107 (RTC) cấp từ `+3V3`, không có nguồn dự phòng | Mất giờ khi PMIC tắt; deep sleep không ảnh hưởng | Đồng bộ lại qua mạng sau khi bật. Chuyển sang VRTC cần tách I2C |
| O6 | Nhỏ | HDG khuyến nghị dành footprint 0 Ω nối tiếp trên SPI flash; Waveshare không có | Không phải lỗi; mất khả năng chỉnh EMC về sau | Thêm nếu còn chỗ khi layout |
| O7 | Nhỏ | Thạch anh Y101: LCSC C9010 ghi 40 MHz, ±10 ppm, 15 pF, khớp thiết kế; bảng datasheet chung không ghi riêng mã này. Waveshare dùng tụ 15 pF | Cặp tụ 22 pF vẫn phải kiểm bằng đo tần số | Tinh chỉnh theo HDG |
| O8 | Lớn | VBUS → VSYS chỉ đi qua buck SW, L102 và R105 (AXP Fig 6-1 p.17; WS p.1), giới hạn tới 2 A (AXP p.12). Dải VSYS 3,4–4,4 V không có căn cứ | Nếu OTP không bật buck: USB không cấp VSYS, không sạc. Đã có R126 dự phòng (S8) | Đo trên bàn thử; lắp R126 nếu cần |
| O9 | Nhỏ | Dòng sạc mặc định chưa hợp pin 400 mAh: ICHG 300 mA, kết thúc sạc 125 mA (AXP §6.7.1 p.23, Table 6-2 p.24). Ngưỡng NTC lệch với B3950: khoảng 4,6–41,9 °C (tính toán) | Sạc dừng sớm | Firmware đặt ITERM, IPRECHG, REG54/55 |
| O10 | Nhỏ | Footprint SFH 7016 chỉ có pad và paste; datasheet còn vẽ vùng Cu mở rộng và một ô mở mask 1,7×1,55 mm (SFH p.14) | Ảnh hưởng hàn và tản nhiệt | Vẽ vùng Cu và mask khi layout |
| O11 | Lắp ráp | MAX30208: reflow tối đa +220 °C (p.2), trong khi profile không chì thường cao hơn (chưa đối chiếu nguồn). Footprint LGA-10 còn `PRELIM` | Hỏng hoặc mất độ chính xác sau hàn | Thống nhất profile với nhà lắp ráp; tải land pattern 90-100101 |

## 7. Phân tích theo khối: các điểm đã kiểm và đúng

| Khối | Kết quả | Tài liệu |
|---|---|---|
| ESP32-S3R8: strapping | GPIO0 kéo lên + nút BOOT; GPIO45, GPIO46 kéo xuống; GPIO3 không ảnh hưởng với eFuse mặc định | DS Table 3-1…3-5 |
| ESP32-S3R8: bộ nhớ | GPIO33–37, SPICS1 để trống cho PSRAM octal; VDD_SPI 3,3 V; flash ngoài | DS p.13, p.17; HDG |
| USB và nạp | GPIO19/20 đúng cực; 22 Ω nối tiếp; USB + UART0 + BOOT/RESET | DS p.17 |
| Đánh thức | GPIO8, 9, 10, 11, 16, 17, 21 đều thuộc miền RTC | DS Table 2-1 |
| Reset | PWROK → CHIP_PU, RC 10 kΩ/1 µF; SW102 chỉ reset ESP32 khi REG10H[3] = 0 | HDG; AXP p.21, p.32 |
| I2C | Không trùng địa chỉ: 0x34, 0x51, 0x52, 0x5A, 0x68. AXP in "0x68/0x69" là dạng 8-bit (0x34). Riêng 0x5A của CST9217 chưa có datasheet | AXP p.18; BMI §5; PCF Table 39; M30 Table 3 |
| FPC | FPC 31 chân khớp J3 Waveshare; FPC 16 chân khớp giữa hai bo | Waveshare p.1; `design.py` |
| Boost 5 V | Chân WSON đúng; L 1 µH; COUT 14,8 µF ≤ 20 µF; đỉnh 124 mA dưới mức 200 mA | TPS61240 p.1, 3–5, 12 |
| AXP2101 | Gán chân khớp bảng chân; DCDC1 3,3 V trong dải; DCDC2–4 để trống như Waveshare | AXP Table 4-1 |
| MAX86141 | Bump map, nguồn, tụ VLED/VDD/VREF khớp; LED đủ headroom ở 5 V | MAX p.4–6, 11–13, 88 |
| SFH 7016, VEMD8080 | Anode chân 2 và 5, cathode 1/3/4, chân 6 NC; VEMD chân 5 anode, 7 cathode; pad đúng kích thước | SFH p.13-14; VEMD p.4 |
| MAX30208 | Chân, nguồn 3,3 V, địa chỉ 0x52 | M30 p.2, p.6, p.10 |
| Chuyển mức (thời gian) | Ánh xạ kênh đúng; 4 MHz trong khả năng; đường MISO khoảng 60 ns so với nửa chu kỳ 125 ns; INT cực máng hở dùng được | TXS p.5, §7.3.5; MAX p.8 |

## 8. Chưa kiểm được

| Hạng mục | Lý do |
|---|---|
| Mở bằng KiCad 9 | Máy chỉ có 10.0.8. File vẫn ở định dạng 20250114, symbol đóng băng từ bản KiCad 9 đã commit. Lưu lại bằng KiCad 10 sẽ nâng định dạng và KiCad 9 không mở được nữa |
| CO5300, CST9217, ăng-ten Johanson, CMT-8504, motor 1027, BAT54WS, AO3400A, cell pin | Thiếu datasheet hoặc không tải được |
| Bảng GPIO của Waveshare 1.75C | Chỉ đối chiếu J3, AXP2101 và ESP32; GPIO reset đối chiếu trên bản 1.75 |
| Land pattern AN1891, 90-100101 | Không tải được từ trang ADI |
| Layout PCB, nhiễu, đường dẫn nhiệt | Chưa có PCB; schematic không chứng minh được các yếu tố này |
| Nội dung OTP thực tế của AXP2101; hoạt động thật | Chưa có phần cứng |

## 9. Phát hiện ngoài schematic

Thuộc báo cáo thiết kế, chưa sửa vì nằm ngoài phạm vi review schematic:

- **SpO2:** không có đường chuẩn, không có căn cứ độ chính xác; phần cứng có đủ LED đỏ và IR nhưng chỉ cho số đếm ADC thô.
- **Nhiệt độ da:** không có đường dẫn nhiệt được thiết kế; U204 chủ yếu sẽ đo nhiệt độ bo (MAX30208 p.7).
- **AF/HRV:** phát hiện rung nhĩ ban ngày dùng 25 sps, độ phân giải 40 ms, lỗi lượng tử cỡ RMSSD bình thường. Cần burst ≥ 100 sps và phải đưa vào ngân sách pin.
- **Ngân sách pin:** thiếu PSRAM 140 µA (DS Table 5-10 p.68), pull-up TXS khoảng 0,25 mA, chế độ chờ của panel và cảm ứng, và các suy luận AF/giấc ngủ. Mục tiêu ≥ 1 ngày còn dư địa, nhưng con số 1,7 ngày là lạc quan.
- **Tài liệu:** link datasheet WS và HDG hỏng; gói nộp ghi có "toàn bộ tài liệu gốc" nhưng chỉ có bảng link; `5_NguonSinh` không tự sinh lại được; còn dấu vết quy trình trong báo cáo (ví dụ "7 vòng audit"); `facts.py` không so giá trị số.

## 10. Đề xuất tiếp theo

1. Quyết định O2 (giữ TXS hay đổi sang phương án (b)) và chốt O4 (cáp FPC) trước khi layout.
2. Sửa footprint (O10, O11) rồi layout, giữ R205 và các tụ AFE sát MAX86141.
3. Trên bo mẫu đầu tiên: đọc OTP (O1), thử tắt nguồn (O3), đo TXS ở 4 MHz (O2), đo VSYS (O8).

## Phụ lục A: tái lập

```bash
python3 tools/design.py
for b in main sensor; do
  python3 tools/gen_sch.py $b hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch erc --severity-all --exit-code-violations -o /tmp/$b.rpt hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch export netlist -o /tmp/$b.net hardware/$b/health_watch_$b.kicad_sch
  python3 tools/check_net.py $b /tmp/$b.net
done
```

{{landscape}}

## Phụ lục B: bản vẽ schematic Rev 1.2

{{fig|main_power|Bo chính: USB-C, AXP2101, pin, shunt đo dòng.|21}}

{{fig|main_mcu|Bo chính: ESP32-S3R8, flash, thạch anh, RF.|21}}

{{fig|main_periph|Bo chính: FPC màn hình, IMU, RTC, boost 5 V, FPC sang bo cảm biến.|21}}

{{fig|main_ui|Bo chính: motor, còi, nút SOS, LED trạng thái.|21}}

{{fig|sensor|Bo cảm biến: MAX86141, LED, photodiode, chuyển mức, MAX30208.|21}}

'''
