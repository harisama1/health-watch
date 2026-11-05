"""Text and numbers of the overall design report, read by gen_design_report.py. Markup: see report_docx.py."""

# Average battery current per load, mA: (load, old report, best, nominal, worst, basis). None = counted inside another row.
BUDGET = [
 ('ESP32 light-sleep + PSRAM', 0.238, 0.37, 0.63, 2.21, 'DS p.68: 240 + 140 µA; danh định/xấu nhất giả định'),
 ('Flash chờ', 0, 0, 0.01, 0.08, 'W25 p.63'),
 ('AMOLED ngủ + touch chờ', 0, 0.05, 0.22, 1.29, 'Giả định, theo panel 1,43" tương tự'),
 ('BMI270', 0.679, 0.41, 0.75, 1.25, 'BMI p.11'),
 ('TXS0108E + pull-up', None, 0.01, 0.29, 0.35, 'TXS p.7, p.18; mức nghỉ thấp giả định'),
 ('LP5907 + MAX86141 VDD', 0.023, 0.03, 0.06, 0.13, 'MAX p.7, LP p.6'),
 ('MAX30208, RTC, R113, pull-up I2C', 0.010, 0.04, 0.09, 0.65, 'Tính từ R; giả định'),
 ('AXP2101 khi chạy', 0.100, 0.06, 0.15, 0.30, 'Giả định; datasheet không có số'),
 ('Panel sáng', 1.982, 0.70, 1.96, 6.81, 'Giả định 25/40/80 mA; 3/5/8 % thời gian'),
 ('ESP32 khi màn sáng', 3.176, 0.70, 2.44, 6.81, 'DS p.67; giả định 25/50/80 mA'),
 ('AI té ngã mỗi 2 s', 0.806, 0.62, 1.99, 8.61, 'Giả định 20/50/150 ms'),
 ('Model AF + giấc ngủ', 0, 0.01, 0.04, 0.15, 'Giả định'),
 ('Đọc FIFO IMU qua I2C', 0, 0.36, 0.80, 2.42, 'Giả định 35 ms mỗi 2 s'),
 ('FIFO PPG + DSP', 0.318, 0.20, 0.69, 4.08, 'Giả định'),
 ('Chuyển trạng thái ngủ/thức', 0, 0.04, 0.20, 1.02, 'Giả định'),
 ('WiFi HTTPS', 0.396, 0.14, 0.82, 2.36, 'Giả định 2,5 s/110 mA; 5 s/150 mA; 8 s/200 mA'),
 ('BLE dự phòng', 0, 0, 0, 1.60, 'Giả định'),
 ('LED PPG qua boost', 0.703, 0.21, 0.40, 0.94, 'MAX p.7; tỉ lệ dòng giả định'),
 ('TPS61240 không tải', 0.030, 0.04, 0.05, 0.05, 'TPS p.6'),
 ('Motor + còi', 0.019, 0.01, 0.03, 0.20, 'Giả định'),
]
LIFE = [('Tốt nhất', 90), ('Báo cáo cũ (Rev 1.0)', 40), ('Danh định', 27.6), ('Danh định, pin già 80 %', 22), ('Danh định, pin già, 0-10 °C', 16), ('Xấu nhất (biên)', 4.6)]

CONTENT = r'''
# Báo cáo phân tích thiết kế: đồng hồ theo dõi sức khỏe

| Phiên bản | Ngày | Người phụ trách | Nội dung |
|---|---|---|---|
| 1.0 | 04/11/2026 | HaiLV25 | Tạo tài liệu |
| 2.0 | 05/11/2026 | HaiLV25 | Viết lại sau khi rà soát toàn bộ thiết kế theo 5 mảng |
| 2.1 | 05/11/2026 | HaiLV25 | Sửa BOM, đổi SFH 7016, sửa mạch; đổi kế hoạch cảnh báo và tính năng; vẽ lại các hình |

Đối tượng: thiết kế đồng hồ đeo tay đo sức khỏe gồm hai PCB, edge AI (chạy mô hình trên thiết bị) và web. Thiết kế **chưa được chế tạo**; firmware, mô hình AI, web và layout PCB đều chưa làm. Mọi kết luận dựa trên datasheet, tính toán và công cụ tự động, không có số đo phần cứng.

## 1. Kết luận

**Sau Rev 2.1, các lỗi sửa được trên giấy đã sửa; thiết kế vẫn chưa sẵn sàng để layout** vì cơ khí và 23 mục BOM chưa chốt, các giả định chưa được đo. Firmware, mô hình AI, web đều chưa làm.

| Đã sửa trong Rev 2.1 | Chi tiết |
|---|---|
| BOM | Bỏ toàn bộ mã LCSC sai; `tools/check_bom.py`: 39 mã khớp, 0 sai, 23 mục chưa có mã (có mục không cần mã: test point, DNP) |
| LED | SFH 7013 ngừng sản xuất → SFH 7016 (symbol, footprint 6 chân, đọc datasheet v1.5) |
| Mạch | R126 VMID-VSYS không lắp; R105 0805; R113 1 MΩ; linh kiện phối hợp RF 0201; 5 test point bus; MAX86141ENP+T; thông số còi |
| Kế hoạch | Logic cảnh báo mới; bỏ phân giai đoạn ngủ, stress, gửi vị trí; SpO2 và mẫu mạch không đều thành thử nghiệm; SOS ngoài WiFi chỉ báo tại chỗ |
| Hình | Vẽ lại sơ đồ khối, cây nguồn, luồng dữ liệu; thêm hình logic cảnh báo |

Bảng dưới là kết quả rà soát ban đầu; các dòng ghi **Đã sửa** hoặc **Đã xử lý** ở những mục sau cho biết điều gì đã đổi. ERC và netlist sau sửa: 0 vi phạm, 0 khác biệt.

| Mảng | Chặn | Lớn | Đánh giá |
|---|---|---|---|
| Mạch điện | 0 | 4 | Netlist khớp thiết kế; ERC 0 vi phạm; rủi ro chính là OTP của AXP2101 |
| Nguồn và pin | 0 | 5 | Pin danh định khoảng 27,6 h, không phải 40 h; pin già còn 22 h, dưới mục tiêu 24 h |
| Cảm biến và AI | 5 | 8 | Đủ năng lực tính toán; SpO2, AF, té ngã, giấc ngủ, stress chưa khả thi theo kế hoạch |
| Hệ thống và firmware | 1 | 9 | SOS ngoài vùng WiFi không đến người nhận; chưa có bảo mật, OTA, xử lý lỗi, kế hoạch thử |
| Sản xuất | 3 | 9 | Nhiều mã LCSC trỏ sai linh kiện; SFH 7013 ngừng sản xuất; panel chưa mua được theo mã |

"Chặn" nghĩa là không thể chế tạo, hoặc chức năng không thể hoạt động như kế hoạch. Một số mục "lớn" trùng nhau giữa các mảng nên tổng số chỉ để định hướng.

**Bốn quyết định tạm theo đề xuất, chưa có xác nhận của người phụ trách** (chi tiết ở mục 8):

1. Thu hẹp phạm vi tính năng cho mẫu đồ án (đã áp dụng vào kế hoạch).
2. SOS khi không có WiFi chỉ báo tại chỗ (đã ghi vào yêu cầu).
3. Giữ TXS0108E và đo trên bo mẫu; đã đổi SFH 7016.
4. Chấp nhận mẫu dày khoảng 16 mm; vỏ, cáp FPC, panel, cell pin **chưa chốt**.

## 2. Mô tả thiết kế

Đồng hồ đo nhịp tim, nhiệt độ da và chuyển động (SpO2 ở mức thử nghiệm); chạy mô hình AI trên thiết bị; gửi kết quả lên web qua WiFi HTTPS theo lô 15 phút; sự kiện khẩn gửi ngay.

| Hạng mục | Lựa chọn |
|---|---|
| Phần cứng | Bo chính 111 linh kiện, bo cảm biến 27 linh kiện, nối FPC 16 chân |
| Bộ xử lý | ESP32-S3R8 (2 nhân LX7 240 MHz, 8 MB PSRAM, WiFi + BLE 5), flash W25Q128JV 16 MB |
| Cảm biến | MAX86141 + SFH 7016 + 2 × VEMD8080 (PPG: đo mạch bằng quang), BMI270 (IMU), MAX30208 (nhiệt độ) |
| Nguồn | AXP2101 + LiPo khoảng 400 mAh, USB-C; TPS61240 5 V cho LED; LP5907 1,8 V cho AFE |
| Giao diện | AMOLED 1,75" CO5300 + cảm ứng, motor rung, còi, nút nguồn và SOS, LED |
| Mục tiêu pin | ≥ 1 ngày |
| Mức hoàn thiện | PCB tự thiết kế, cỡ đồng hồ nhưng được phép to hơn (demo) |

{{fig|block_diagram|Sơ đồ khối phần cứng sau khi sửa.|16.5}}

{{fig|power_tree|Cây nguồn và điểm đo dòng.|16.5}}

{{fig|data_flow|Luồng dữ liệu theo kế hoạch đã sửa.|16.5}}

## 3. Mạch điện

Đã rà từng chân IC với datasheet: ESP32-S3R8, W25Q128JV, AXP2101, TPS61240, BMI270, PCF85063A, MAX86141, MAX30208, LP5907, TXS0108E, USBLC6-2SC6, USB-C, SFH 7013, VEMD8080. Netlist khớp `tools/design.py` trên toàn bộ 532 chân; ERC 0 lỗi, 0 cảnh báo. Không tìm thấy đường cấp nguồn ngược nào trên bo; cực tính MOSFET và diode dập đúng. Chi tiết lỗi đã sửa: `schematic_analysis_report.docx`.

| # | Mức | Vấn đề | Hệ quả | Xử lý |
|---|---|---|---|---|
| E1 | Lớn | Điện áp và trạng thái DCDC1 do OTP (cấu hình nạp sẵn lúc xuất xưởng) quyết định (AXP p.22, p.37). UVP của DCDC2-4 mặc định bật trong khi VIN2-4 để trống | Nếu OTP khác 3,3 V, ESP32 không chạy và firmware không cứu được. Waveshare cùng cách nối là bằng chứng gián tiếp | Đọc toàn bộ thanh ghi trên bo Waveshare; mua đúng mã OTP |
| E2 | Lớn | VBUS → VSYS chỉ đi qua buck SW, L102, R105; không có liên kết VMID-VSYS (AXP p.17; WS p.1: RP1 không lắp) | Nếu OTP không bật buck: USB không cấp VSYS, không sạc. R105 0402 mang toàn bộ dòng vào | **Đã sửa:** thêm R126 không lắp, R105 0805. Còn phải đo trên bàn thử |
| E3 | Lớn | FPC 16 chân không đối xứng; cáp đảo đưa VLED 5 V vào `PPG_INT`, `PPG_CS` | Có thể hỏng ESP32 (VIH tối đa VDD + 0,3 V, DS p.65). Loại cáp phụ thuộc cách xếp bo, chưa có bản vẽ | Chốt bằng mô hình giấy; đo thông mạch cáp trước khi cấp nguồn |
| E4 | Lớn | TXS0108E: VOH tối thiểu 2,21 V so với ESP32 VIH 2,475 V; 1,21 V so với MAX86141 VIH 1,4 V (TXS p.7; DS p.65; MAX p.8) | Không có đảm bảo trường hợp xấu nhất; tải nhẹ nên nhiều khả năng vẫn chạy | Quyết định 3, mục 8 |
| E5 | Nhỏ | OE nối thẳng `+1V8`, trong khi TI khuyên kéo xuống đến khi rail ổn định (TXS p.20) | Có thể có xung lạ lúc lên nguồn. GPIO47/48 còn trống, nhưng FPC không còn chân để đưa OE sang bo cảm biến | Chấp nhận, hoặc đổi một chân GND của FPC thành OE |
| E6 | Nhỏ | +1V8 giữ 10,3 µF khi tắt, có thể vượt VIN + 0,3 V của LP5907 và VCCA > VCCB (LP p.5; TXS p.20) | Biên độ chưa biết | Đo; thêm Schottky 1V8 → 3V3 nếu vượt |
| E7 | Nhỏ | RF: HDG yêu cầu linh kiện 0201 (đã dùng 0402); không có ESD ở ăng-ten | Khó phối hợp trở kháng | **Đã sửa:** C128-C131, L106, R117 sang 0201. ESD ăng-ten còn mở |

## 4. Nguồn và pin

Tự lập lại ngân sách từ dưới lên cho thấy Rev 1.0 lạc quan: thiếu 140 µA của PSRAM (DS p.68), đọc FIFO IMU qua I2C, chuyển trạng thái ngủ/thức, panel ngủ, touch, pull-up TXS. Mức danh định là **11,6 mA, tức 27,6 h**. Biên so với mục tiêu 24 h chỉ khoảng 15 % ở pin mới. **Đa số đầu vào là giả định**, phải đo trên bo Waveshare trước khi chốt. Cột xấu nhất cộng dồn mọi cực trị nên chỉ là biên. Các sửa trong Rev 2.1 (R113, bỏ model giấc ngủ) giảm dưới 0,1 mA nên chưa tính lại; burst 100 mẫu/s cho PRV thêm khoảng 0,16-0,23 mA cũng chưa tính.

{{fig|budget_life|Thời lượng pin theo kịch bản so với mục tiêu 24 h.|15}}

{{hook|budget}}

{{fig|budget_loads|Các tải từ lớn đến nhỏ, kịch bản danh định. Màn hình cùng ESP32 khi màn sáng chiếm khoảng 38 %.|15}}

| # | Mức | Vấn đề | Hệ quả | Xử lý |
|---|---|---|---|---|
| P1 | Lớn | Không có chính sách sụt áp. Dưới 3,05 V flash ngoài điều kiện; dưới 3,0 V ESP32 ngoài khuyến nghị; UVP tắt PMIC ở 2,805 V; VOFF mặc định 2,6 V (DS p.64-65; W25 p.63; AXP p.20, p.37) | Hỏng bộ đệm hoặc OTA; có thể mất SOS đúng lúc pin yếu | Đặt REG24 = 3,3 V; cắt WiFi, độ sáng, rung theo ngưỡng VBAT |
| P2 | Lớn | Chưa chọn cell cụ thể. Pin chịu đỉnh khoảng 0,7 A (1,75C) khi TX + màn + motor | Mô hình (giả định ESR): pin già ở 0 °C reset khi OCV dưới 3,62-3,86 V, tức còn khoảng nửa dung lượng | Chọn cell có MPN, ESR, ngưỡng bảo vệ; không chạy motor cùng TX |
| P3 | Lớn | Chưa phân tích nhiệt khi sạc. Tổn hao tuyến tính 0,16-0,40 W ở 200 mA | Ước tính +7-16 K, đeo khi sạc có thể đạt 40-46 °C. NTC đo bo, không đo cell | Cấm sạc khi đeo; dừng sạc theo MAX30208; pack 3 dây có NTC; đo trên mẫu |
| P4 | Lớn | Mặc định sạc không hợp 400 mAh: 300 mA trước khi firmware chạy, precharge 125 mA, ITERM 125 mA (AXP p.23-24, p.47-48) | Sạc dừng sớm, mất dung lượng; vượt 0,5C nếu firmware chưa chạy | Đặt REG61, REG62, REG63 sớm; kiểm tra spec cell |
| P5 | Lớn | Boost tắt khi CPU ngủ: mức 240 µA yêu cầu GPIO high-Z, R113 kéo EN xuống, mâu thuẫn với PPG liên tục (DS Table 5-10) | Ngân sách và chức năng không nhất quán | Giữ GPIO3 bằng RTC hold; cập nhật ngân sách |
| P6 | Nhỏ | R112 nằm sau FB1 nên không được bù: ở 0,6 A +3V3 thấp nhất 3,14 V, chỉ dư 90 mV so với flash. R112 không tách được ESP32 và màn | Giảm biên; không đo được riêng màn như dự định | Lấy FB1 sau shunt, hoặc 0 Ω ở bản sản xuất |
| P7 | Nhỏ | NTC B3950 lệch bảng TS: cửa sổ sạc khoảng +4,5…+41,8 °C (tính từ AXP p.26). R113 100 kΩ tốn 33 µA khi EN cao | Sạc hẹp hơn dự kiến; tổn hao nhỏ | Đặt lại REG54-57. **Đã sửa:** R113 1 MΩ |

## 5. Cảm biến và AI

Tính toán không phải vấn đề: mô hình CNN 3 lớp trên 128×6 cần khoảng 350 k phép nhân, 7 KB trọng số, 8-16 KB bộ nhớ làm việc, 3-15 ms trên ESP32-S3 (ước tính), nên vừa trong SRAM nội, không cần PSRAM. Vấn đề nằm ở dữ liệu, độ tin cậy và logic cảnh báo.

| Chức năng | Kế hoạch cũ khả thi? | Kế hoạch đã sửa (Rev 2.1) |
|---|---|---|
| Nhịp tim | Khi nghỉ: có. Khi vận động: không | Đưa gia tốc vào lọc nhiễu; cờ chất lượng; so với dây đeo ngực. Mục tiêu sai số dưới 5 bpm khi nghỉ, khoảng 10 bpm khi hoạt động |
| HRV/PRV | Chỉ ban đêm | 100 sps, khi đứng yên, cửa sổ ≥ 2-5 phút; gọi là PRV (biến thiên mạch), không phải HRV |
| SpO2 | **Không** (số liệu) | Ghi là ước tính thử nghiệm chưa hiệu chuẩn; loại tín hiệu kém; không cảnh báo |
| Rung nhĩ (AF) | **Không** | Đòi hỏi kéo dài khoảng 30 phút; thông báo không khẩn; dữ liệu PPG cổ tay; đổi cách gọi |
| Nhiệt độ da | Chỉ xu hướng | Thiết kế đường dẫn nhiệt; thử tự nóng |
| Té ngã | **Không** (logic cảnh báo) | Kích hoạt theo va chạm, kiểm tra nằm yên 5-10 s, cho hủy 30-60 s; báo cáo báo động giả/ngày |
| Hoạt động | Một phần | Ít lớp hơn (gộp ngồi/nằm); dữ liệu tự thu; cùng tần số lấy mẫu |
| Giấc ngủ | **Không** | Chỉ ngủ/thức và thời lượng; dữ liệu có nhãn PSG |
| Stress | **Không** | Khi thức và đứng yên; cửa sổ dài hơn; bỏ LF/HF; gọi là "chỉ số thư giãn" |
| Đếm bước | Có | Dùng bộ đếm trong BMI270 (BMI §4.8.8); kiểm bằng đếm tay |

{{fig|alert_flow|Logic cảnh báo đã sửa. Các tham số là điểm khởi đầu, chưa được đo.|16.5}}

Các phát hiện dưới đây là lý do của kế hoạch mới. S1-S5 đã được xử lý về mặt kế hoạch, nhưng chưa có dữ liệu chứng minh.

| # | Mức | Vấn đề | Bằng chứng | Hệ quả |
|---|---|---|---|---|
| S1 | Chặn | Stress: 30 s ban đêm, huấn luyện trên WESAD | WESAD là thí nghiệm ban ngày, 15 người, cổ tay E4 64 Hz có EDA, chỉ dùng phi thương mại. LF/HF cần ≥ 2 phút | Không suy rộng sang thiết bị này |
| S2 | Chặn | Giấc ngủ: nhãn từ nhật ký tự ghi | Không thể gán nhãn từng epoch 30 s; công bố dùng PSG | Không huấn luyện được |
| S3 | Chặn | SpO2 không có đường R → SpO2, thiết bị đối chứng | Hiệu chuẩn cần giảm bão hòa có kiểm soát (dự thảo FDA 2025, nguồn thứ cấp). So sánh lúc nghỉ 95-100 % không tạo được đường chuẩn | Số hiển thị không có ý nghĩa đo lường |
| S4 | Chặn | AF: một cửa sổ mỗi 5 phút đưa thẳng tới rung, còi, gửi ngay | Giả định độ đặc hiệu 98 %, 100 cửa sổ/ngày: xác suất báo giả 87 %/ngày (tính toán). Apple và Fitbit đòi hỏi lặp lại nhiều lần | Khoảng 850/1000 người bị báo giả mỗi ngày |
| S5 | Chặn | Té ngã: 43.200 cửa sổ/ngày | ≤ 0,1 báo giả/ngày cần FPR ≤ 2,3×10⁻⁶ cửa sổ. Độ đặc hiệu 99,9 % vẫn cho 43 cửa sổ giả/ngày (tính toán). Thuật toán trên ca ngã thật: nhạy trung bình 57 % (Bagalà, nguồn thứ cấp) | Không dùng được làm cảnh báo |
| S6 | Lớn | FIFO 128 mục, mỗi PD/LED một mục (MAX p.1) | Đầy sau 2,56 s (xanh 25 sps, 2 PD); 0,64 s (100 sps); 0,32 s (đỏ + IR 100 sps). Xử lý "mỗi 1 s" tràn ở 100 sps | Mất mẫu, nhất là khi TLS hoặc xóa flash dừng cache |
| S7 | Lớn | PPG và IMU không đồng bộ; FPC không có chân sync | Sai số tốc độ tới 3,7 % (MAX, BMI; tính toán), tương đương khoảng 5,5 bpm ở 150 bước/phút | Khử nhiễu chuyển động kém |
| S8 | Lớn | 25 sps ban ngày thấp cho AF/stress | Nhiễu IBI khoảng 28 ms, cỡ RMSSD lúc nghỉ; 100 sps còn 7 ms (tính toán) | Cần burst 100 sps, thêm khoảng 0,16-0,23 mA |
| S9 | Lớn | Không có đường ghi dữ liệu thô, trong khi kế hoạch cần tự thu | 2.450 B/s, tức 8,8 MB/giờ (tính toán) | Cần firmware ghi riêng qua BLE hoặc USB |
| S10 | Lớn | Không có kế hoạch đánh giá | Không có số người, thiết bị đối chứng, cách chia tập, tiêu chí đạt. MIMIC chỉ 16 người không AF: 0 báo giả vẫn có cận trên 95 % khoảng 17 % | Không chứng minh được kết quả |
| S11 | Lớn | Dữ liệu lệch thiết bị | UMAFall khoảng 20 Hz so với 50 Hz; ngã của WEDA do người trẻ ngã lên nệm; MIMIC bệnh nhân nặng, 125 Hz, tại giường; R-R từ ECG không có nhiễu PPG | Độ chính xác trên giấy không chuyển sang thực tế |
| S12 | Lớn | Cách gọi y khoa | "Sàng lọc AF" là tuyên bố về bệnh; lời khuyến cáo không biến nó thành sản phẩm wellness (nguồn thứ cấp) | Ghi "nguyên mẫu nghiên cứu, không phải thiết bị y tế", "mẫu mạch không đều"; xin phê duyệt đạo đức khi thu dữ liệu người khác |
| S13 | Lớn | Quang học chưa định nghĩa | Không có khoảng cách LED-PD, chiều cao vách, độ dày cửa sổ, mục tiêu rò sáng | Thử 2-3 khoảng cách, đo rò sáng trên nhiều màu da trước khi layout |

## 6. Hệ thống, firmware, bảo mật

Hình 3 đã đưa các yêu cầu này vào kế hoạch, nhưng chưa có thiết kế chi tiết hay mã nguồn. Tài liệu trước Rev 2.1 không đề cập: secure boot, mã hóa, rollback, watchdog, brownout, đồng bộ giờ, cấu hình WiFi, đồng ý của người dùng, lịch dự án, kế hoạch bring-up.

| # | Mức | Vấn đề | Hệ quả | Xử lý |
|---|---|---|---|---|
| H1 | Chặn | Không có modem. BLE dự phòng cần app nhưng app không có trong danh sách việc; Web Bluetooth không chạy nền (chưa kiểm chứng) | Ngoài vùng WiFi, SOS và té ngã chỉ còn còi và rung tại chỗ | **Đã đổi yêu cầu:** ghi rõ giới hạn; BLE chỉ để cấu hình WiFi (quyết định 2, mục 8) |
| H2 | Lớn | Không có đảm bảo gửi cảnh báo: không event ID, ACK, retry, cửa sổ hủy, kênh đẩy; dashboard chỉ hiện khi có người mở | Người thân có thể không nhận được | Event ID + ACK, hàng đợi flash, FCM/SMS phía server, mục tiêu độ trễ |
| H3 | Lớn | Không có cách nhập SSID, gắn thiết bị với người dùng; không có backoff khi mất mạng | Không đưa được vào mạng; tốn pin khi quét liên tục | BLE provisioning, ghi danh một lần, backoff |
| H4 | Lớn | Không có secure boot, mã hóa flash, kế hoạch eFuse; USB-JTAG, UART0 mở; OTA chưa có chữ ký và điều kiện rollback | Token và dữ liệu sức khỏe đọc được từ flash SOIC-8 bằng kẹp | Secure Boot V2 + mã hóa flash trên mẫu demo; token riêng; `APP_ROLLBACK`; chặn OTA khi pin yếu |
| H5 | Lớn | Web và riêng tư gần như trống: chỉ 2 POST và token + TLS; không có đăng nhập, phân quyền, retention, consent | Dữ liệu HR, SpO2, nhãn AF vẫn lên server. Luật 91/2025/QH15 và NĐ 356/2025 có hiệu lực 01/01/2026 (nguồn thứ cấp; cần đọc phân loại dữ liệu) | Mô hình đe dọa, luồng dữ liệu, consent bằng văn bản, mã hóa khi lưu |
| H6 | Lớn | Không có xử lý lỗi. Một bus I2C chung cho PMIC, IMU, RTC, touch, MAX30208, kéo qua FPC | Một slave giữ SDA là mất cả PMIC và IMU; chỉ khôi phục được bằng tắt nguồn | Khôi phục bus 9 xung, timeout, TWDT, ngưỡng pin cho SOS, phát hiện tháo tay |
| H7 | Lớn | RTC cấp từ DCDC1, không đồng bộ giờ | Tắt PMIC là mất giờ; dữ liệu offline mang giờ sai | Cấp từ VRTC nếu mức áp hợp, đọc cờ OS, SNTP mỗi lần kết nối |
| H8 | Lớn | Chức năng không có chủ: quản lý nguồn/AXP_IRQ, MAX30208, lưu flash, đồng bộ giờ, provisioning, OTA, BLE GATT, tháo tay, chẩn đoán, ghi dữ liệu thô | Khối lượng firmware bị đánh giá thấp | Thêm vào kiến trúc task; gán người làm |
| H9 | Lớn | Không có kế hoạch thử và lịch; mục "kiểm tra" chỉ xét thiết kế | Không biết khi nào xong | Lập lịch ngược; firmware trên Waveshare trước PCB; bring-up theo rail → I2C → SPI → RF |
| H10 | Lớn | "Sự kiện kèm vị trí" không có nguồn nếu hiểu là vị trí địa lý; không có GNSS | Tính năng không có dữ liệu | **Đã bỏ** khỏi kế hoạch |
| H11 | Nhỏ | Chế độ ngủ không nhất quán: cảm biến liên tục loại trừ deep sleep, PSRAM mất dữ liệu khi deep sleep (chưa kiểm chứng); BMI270 không có high-g | Chân "đánh thức deep sleep" không có use case | Định nghĩa máy trạng thái nguồn; dùng any-motion |
| H12 | Nhỏ | Đệm flash, màn hình chưa đặc tả: ghi đè một sector mỗi phút hết 100k chu kỳ sau 69 ngày; frame 434 KB | Mòn flash; chưa biết fps | Log vòng/LittleFS; đo tải LVGL; PPG và màn dùng host SPI khác nhau |

## 7. Sản xuất và cơ khí

### 7.1 Mã linh kiện sai (đã xử lý)

Tra cứu LCSC ngày 05/11/2026. Các mã dưới đây đã được thay hoặc xóa khỏi `tools/design.py`. Từ nay chạy `python3 tools/check_bom.py` trước khi đặt hàng.

| Mã | Khai báo | Thực tế | Dùng cho |
|---|---|---|---|
| C2838510 | Thạch anh 32,768 kHz | MOSFET P SI7923DN | Y102 |
| C25563 | NTC 10 k | Điện trở 47 kΩ | RT101 |
| C129937 | Shunt 0,05 Ω | IC sạc BQ24296 | R111 |
| C1546 | Tụ 1,5 pF | Tụ 100 pF (gần như chập RF) | C128, C129 |
| C25100 | 499 Ω | 27 Ω | R118 |
| C191023 | BAT54WS | 1N5819WS | D102, D103 |
| C2917717 | 2450AT18A100E | 2450AT18B100E, hết hàng | AE101 |
| C23733 | 4,7 µF footprint 0603 | Vỏ 0402, hết hàng | C114 |
| C506807, C22381 | FH12, 0,1 Ω | Không có kết quả | J105, J201, R112... |

Mã đã xác nhận mới: C19666 (4,7 µF 0603), C17477 (0 Ω 0805), C26083 (1 MΩ). C9010 trên LCSC ghi rõ 40 MHz, ±10 ppm, 15 pF, nên thạch anh Y101 hợp với cặp tụ 22 pF. Còn thiếu mã: toàn bộ cuộn cảm, shunt, NTC, thạch anh 32 kHz, ăng-ten, FH12, BAT54WS, 499 Ω, linh kiện RF 0201. Không có dòng BOM: panel, cell pin, cáp FFC, đầu cắm PicoBlade.

### 7.2 Vấn đề chế tạo

| # | Mức | Vấn đề | Xử lý |
|---|---|---|---|
| M1 | Đã xử lý | Nhiều mã BOM sai (mục 7.1) | **Đã sửa:** không còn mã sai; `tools/check_bom.py` kiểm tự động. Tìm mã theo từ khóa bị LCSC chặn, nên 23 mục còn lại phải chọn thủ công |
| M2 | Đã xử lý | SFH 7013 ngừng sản xuất (ams-OSRAM ghi 停产), LCSC hết hàng | **Đã đổi SFH 7016** (ams-OSRAM ghi 量产, Q65112A7849): 1,85×1,65×0,6 mm, cùng 530/655/940 nm, VF xanh tối đa 2,80 V ở 20 mA, chịu xung đủ cho 124 mA (SFH p.5, p.11-12). Chưa có nguồn mua xác nhận |
| M3 | Chặn | Panel và J104 không có mã đặt được; Waveshare chỉ ghi "0.3-31pin" | Mua panel trước hoặc lấy từ bo Waveshare, đo FPC, rồi chọn đầu nối |
| M4 | Lớn | Kích thước: tổng courtyard bo chính 1.032 mm², bo cảm biến 280 mm². Đĩa ⌀44 mm khoảng 1.520 mm². Có hệ số đi dây 1,4, bo chính cần khoảng 1.450 mm² nên phải 2 mặt | Ước tính dày khoảng 16 mm, vỏ khoảng ⌀50 mm: chỉ vừa cho mẫu demo dày. Thay SOIC-8 bằng WSON, TSSOP-20, PicoBlade, header 2,54 mm, dùng FPC 0,3 mm |
| M5 | Lớn | MAX30208 chỉ chịu reflow +220 °C (p.2), SAC305 khoảng 245 °C | Hàn sau cùng bằng Sn-Bi, hoặc hỏi ADI |
| M6 | Lớn | MAX86141 nguồn cung: LCSC 0, DigiKey "Discontinued at DigiKey"; tình trạng ở ADI chưa kiểm | Mua sẵn ≥ 5 con trước khi layout |
| M7 | Lớn | Ăng-ten: yêu cầu góc bo và khoảng cấm khoảng 6,5×6,5 mm (Johanson Rev 4.0); bo tròn không có góc; cạnh panel, pin, cổ tay | Vát một cạnh bo; chỉnh trong vỏ trên cổ tay; thêm cổng RF không lắp; hoặc dùng module ESP32-S3-MINI-1 |
| M8 | Lớn | Nút TS-1088 bấm vuông góc mặt bo, không bấm được qua thành vỏ | Nút góc vuông hoặc cần gạt; RESET/BOOT chuyển thành pad |
| M9 | Lớn | Quang học và vỏ chưa định nghĩa: không có IP, gioăng, vật liệu tiếp xúc da | Định nghĩa cửa sổ, vách, gioăng; mục tiêu IP; vật liệu ISO 10993 |
| M10 | Lớn | Thiếu ESD ở nút, J103, CC1/CC2; SW102/SW103 nối thẳng CHIP_PU/GPIO0 | TVS điện dung thấp, điện trở nối tiếp |
| M11 | Lớn | WLP-20 pitch 0,4 mm cần via-in-pad; 4 lớp đủ, không cần HDI toàn phần | Hỏi nhà sản xuất về via lấp ở 4 lớp; đọc AN1891 |
| M12 | Lớn | Chứng nhận (chưa đọc văn bản): sản phẩm cần radio, EMC, SAR; pin UN 38.3, IEC 62133-2; AF và SpO2 có thể là chức năng thiết bị y tế | Mẫu đồ án không đưa ra thị trường; ghi rõ phạm vi |
| M13 | Nhỏ | Còi CMT-8504 định mức 5 V, 150 mA, 4 kHz theo DigiKey; thiết kế cũ lái ~2,7 kHz từ VSYS. Test point cũ chỉ có nguồn/GND | **Đã sửa:** PWM 4 kHz, thêm TP110-114 (I2C, SPI, PPG_INT). Âm lượng ở VSYS cần đo |

Chưa làm vì phụ thuộc cơ khí: nút góc vuông, ESD ở nút, thay SOIC-8/TSSOP-20/PicoBlade/header, vát cạnh ăng-ten, FB1 sau shunt, NTC gắn cell.

Giá mẫu (ước tính): linh kiện khoảng $70-95 mỗi bộ; 5 bộ gồm PCB 4 lớp, lắp ráp 2 mặt, vỏ in: khoảng $700-1.000, tức $150-200 mỗi cái, chưa gồm VNA và chứng nhận.

## 8. Quyết định và lộ trình

| # | Quyết định (đang áp dụng tạm) | Đề xuất | Lý do |
|---|---|---|---|
| 1 | Phạm vi tính năng | **Lõi demo:** nhịp tim khi nghỉ, đếm bước, té ngã có hủy, xu hướng nhiệt độ, SOS. **Thử nghiệm, có nhãn rõ, không cảnh báo:** SpO2, PRV, mẫu mạch không đều. **Bỏ:** phân giai đoạn ngủ, stress | Tập trung vào phần chứng minh được với nguồn lực đồ án |
| 2 | SOS khi không có WiFi | Ghi rõ giới hạn trong yêu cầu: chỉ báo tại chỗ khi không có mạng. Làm app native hoặc LTE-M chỉ khi yêu cầu đề tài bắt buộc | Modem cần thêm phần cứng, diện tích, pin |
| 3 | TXS0108E, SFH 7013 | Giữ TXS và đo ở 4 MHz trên bo mẫu (TP112, TP113). Đã đổi sang SFH 7016 | SPI chịu +6 V nên có phương án bỏ TXS (nối thẳng SCLK, SDI, CSB; chỉ SDO qua buffer), nhưng cần chọn linh kiện |
| 4 | Cơ khí | Chấp nhận mẫu dày khoảng 16 mm; chốt vỏ, panel, cell, cáp FPC bằng mô hình giấy trước khi layout | Mọi ràng buộc PCB phụ thuộc mục này |

**Giai đoạn A: trên bo Waveshare 1.75C, chưa cần PCB**

- Đọc thanh ghi OTP của AXP2101 và đo đường VBUS → VSYS.
- Đo dòng thực: light-sleep với PSRAM, màn, WiFi. Cập nhật ngân sách pin.
- Viết firmware lõi: quản lý nguồn, FIFO theo watermark, đồng bộ giờ, provisioning, OTA có rollback, xử lý lỗi.
- Thử té ngã có ground truth; đo báo động giả/ngày trên nhiều ngày đeo.

**Giai đoạn B: trước khi layout**

- Chọn mã cho các mục BOM còn trống, chạy `tools/check_bom.py`. Mua MAX86141, SFH 7016, panel, cell.
- Chốt cơ khí, ăng-ten, quang học; sửa footprint MAX30208 và pad MAX86141 theo AN1891.
- Đổi linh kiện chiếm diện tích, nút bấm góc vuông; thêm ESD ở nút và CC1/CC2.

**Giai đoạn C: trên bo mẫu**

- Bring-up theo rail → I2C → SPI → RF; đo TXS ở 4 MHz; chỉnh ăng-ten trong vỏ.
- Đánh giá theo protocol: chia theo người, báo cáo khoảng tin cậy và tỉ lệ loại tín hiệu.

## 9. Độ tin cậy của báo cáo

| Mức | Ý nghĩa |
|---|---|
| Đã kiểm độc lập | Toàn bộ mã LCSC qua API, SFH 7013 và 7016 (trạng thái, datasheet, chân, pad, xung), GPIO47/48, FIFO 128 mục, L102/RP1 trên Waveshare, các phép tính AF, té ngã, tổng ngân sách pin |
| Đã đọc tài liệu | Các mục có trang datasheet: do agent review đọc, chưa đọc lại từng số |
| Tính toán | Ghi rõ "tính toán"; phụ thuộc giả định đã nêu |
| Giả định | Đa số đầu vào ngân sách pin, ESR pin, mô hình nhiệt, kích thước vỏ, giá |
| Nguồn thứ cấp | Nghiên cứu AF/té ngã, FDA, pháp luật: đọc từ tóm tắt hoặc trích đoạn, cần đọc bản gốc trước khi trích dẫn chính thức |
| Chưa kiểm được | Mở bằng KiCad 9; datasheet panel CO5300, CST9217, còi, motor, BAT54WS, AO3400A, AN1891; trạng thái sản xuất của MAX86141 ở ADI; toàn bộ hành vi phần cứng |

**Giới hạn:** con số 40 h trong Rev 1.0 đã được thay. Footprint SFH 7016 đọc từ bản vẽ, chưa thử in stencil. Kiểm tra `tools/facts.py` chỉ xác nhận mẫu văn bản có trên trang, không so giá trị số. Các nguồn đã tra: ams-OSRAM (SFH 7013; SFH 7016 datasheet v1.5), LCSC, DigiKey, JLCPCB, Johanson 2450AT18A0100001E Rev 4.0, PPG-DaLiA, WESAD, WEDA-FALL, MIMIC PERform AF, Nghị định 356/2025/NĐ-CP (thuvienphapluat.vn). Link datasheet: `docs/datasheets/README.md`.

{{landscape}}

## Phụ lục A: bản vẽ schematic Rev 1.2

{{fig|main_power|Bo chính: USB-C, AXP2101, pin, shunt đo dòng.|21}}

{{fig|main_mcu|Bo chính: ESP32-S3R8, flash, thạch anh, RF.|21}}

{{fig|main_periph|Bo chính: FPC màn hình, IMU, RTC, boost 5 V, FPC sang bo cảm biến.|21}}

{{fig|main_ui|Bo chính: motor, còi, nút SOS, LED trạng thái.|21}}

{{fig|sensor|Bo cảm biến: MAX86141, LED, photodiode, chuyển mức, MAX30208.|21}}

{{portrait}}

## Phụ lục B: gán GPIO của ESP32-S3R8

{{hook|gpio}}

## Phụ lục C: danh sách linh kiện

Theo `tools/design.py`. Cột "Mã đặt" là mã LCSC đã kiểm hoặc ghi chú "chọn mã" khi chưa có.

{{hook|parts}}
'''
