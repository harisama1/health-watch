"""Module-stage BOM (bought modules wired together, before any custom PCB) -> outputs/bom/health_watch_module_bom.xlsx.
Reference prices are typed in from the listed sources; Shopee prices must be filled in by hand. Needs openpyxl."""
import os
import urllib.parse
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter as CL
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs', 'bom', 'health_watch_module_bom.xlsx')
HEAD = ['#', 'Module', 'SL', 'Tìm trên Shopee (bấm để mở)', 'Thay cho khối', 'So với thiết kế PCB', 'Kiểm tra trước khi mua', 'Giá Shopee (₫/cái, tự nhập)', 'Giá tham khảo thấp ($/cái)', 'Giá tham khảo cao ($/cái)', 'Nguồn giá tham khảo']
REQUIRED = [
 ('ESP32-S3 DevKitC N16R8', 1, 'ESP32-S3 N16R8 DevKitC', 'ESP32-S3R8 + flash 16 MB', 'Cùng lõi, flash 16 MB, PSRAM 8 MB octal; dùng module WROOM thay chip QFN', 'Lấy đúng N16R8. GPIO45/46 phải ở mức thấp lúc khởi động: không nối module kéo các chân này lên cao', 9.99, 9.99, 'waveshare.com ESP32-S3-DEV-KIT, chỉ để so giá cùng cấu hình; mua hãng bất kỳ'),
 ('Màn tròn 1,28" GC9A01 + cảm ứng CST816S', 1, 'GC9A01 1.28 touch CST816S', 'AMOLED 1,75" CO5300 + CST9217', 'Khác: LCD 240×240, SPI, khác driver màn và cảm ứng. Lớp giao diện LVGL dùng lại được, phải đổi driver và bố cục khi sang AMOLED', 'Chọn bản có cảm ứng và ghi rõ mức 3,3 V. Nếu không có, mua GC9A01 không cảm ứng và điều khiển bằng nút nhấn', 18.89, 18.89, 'spotpear.com'),
 ('Module IMU BMI160 (GY-BMI160)', 1, 'GY-BMI160', 'IMU BMI270', 'Thay thế: cùng hãng Bosch, 6 trục, I2C/SPI, nhưng khác IC và driver. Mô hình té ngã và hoạt động phải đánh giá lại trên BMI270', 'Địa chỉ I2C 0x68 hoặc 0x69 theo chân SDO; nếu tìm được BMI270 thì ưu tiên', 5.00, 6.95, 'electroslab.com (đang hết hàng); fruugo.ca, chưa gồm vận chuyển'),
 ('Module MAX30102', 1, 'MAX30102 module', 'MAX86141 + SFH 7016 + 2 × VEMD8080', 'Khác: I2C, 1 photodiode, chỉ có LED đỏ và IR, không có LED xanh. Chỉ dùng để phát triển firmware', 'Chọn module có bộ ổn áp và chịu được I2C 3,3 V; xem mô tả và ảnh của người bán', 6.99, 13.00, 'shillehtek.com; makersportal.com'),
 ('Cảm biến nhiệt độ DS18B20', 1, 'DS18B20', 'Nhiệt độ da MAX30208', 'Thay thế: vẫn đo tiếp xúc, chỉ xem xu hướng; giao tiếp 1-Wire, độ chính xác thấp hơn MAX30208, không dùng để đánh giá sai số', 'Cần điện trở kéo lên 4,7 kΩ nếu module chưa có; ưu tiên bản dễ áp vào da', None, None, 'Chưa có giá'),
 ('Module RTC PCF8563', 1, 'PCF8563 module', 'RTC PCF85063A', 'Thay thế: cùng hãng, cùng địa chỉ I2C 0x51, khác một số thanh ghi nên phải chỉnh driver', 'Lấy bản chạy 3,3 V; pin giữ giờ nếu có thì tháo hoặc kiểm tra mạch nạp', 3.99, 3.99, 'waveshare.com PCF8563 RTC Board, chỉ để so giá; olimex.com €3,95'),
 ('Module sạc TP4056 Type-C có bảo vệ DW01', 1, 'TP4056 Type-C DW01', 'Mạch sạc của AXP2101', 'Khác: không có I2C, không đọc được trạng thái PMIC. Firmware quản lý nguồn phải để lớp giả lập đến khi có PCB', 'Dòng sạc mặc định thường 1 A: dùng pin ≥ 1000 mAh hoặc đổi Rprog', 1.99, 3.49, 'pmdway.com ($9,95/5 cái); reach.dog'),
 ('Module boost 5 V MT3608', 1, 'MT3608 boost 5V', 'Nguồn 5 V vào DevKit khi chạy pin', 'Không có trên PCB: PCB dùng DCDC1 3,3 V của AXP2101', 'Chỉnh đúng 5,0 V bằng đồng hồ trước khi nối. Không cấp pin và cắm USB cùng lúc nếu chưa kiểm tra diode trên DevKit', None, None, 'Chưa có giá'),
 ('Pin LiPo 3,7 V ≥ 1000 mAh có mạch bảo vệ', 1, 'pin lipo 3.7V 1000mAh', 'Pin LiPo', 'Lớn hơn pin 390 mAh của PCB; số giờ chạy không chuyển thẳng', 'Kiểm tra cực tính dây. Dung lượng để hợp với dòng sạc 1 A', None, None, 'Chưa có giá'),
 ('Motor rung 1027 3 V kèm mạch lái', 1, 'module motor rung', 'Motor + AO3400A', 'Cùng chức năng', 'Chọn module có transistor và diode dập, kích được bằng mức 3,3 V', None, None, 'Chưa có giá'),
 ('Module còi 3,3 V', 1, 'module còi buzzer 3.3V', 'Còi CMT-8504 + AO3400A', 'Âm lượng khác còi trên PCB', 'Chọn loại mức kích hoạt 3,3 V', None, None, 'Chưa có giá'),
 ('Nút nhấn SOS 6 mm', 2, 'nút nhấn 6x6', 'Nút SOS', 'Cùng chức năng', 'Cái thứ hai để dự phòng', None, None, 'Chưa có giá'),
 ('Breadboard 830 lỗ', 1, 'breadboard 830', 'Nối dây', '-', '-', None, None, 'Chưa có giá'),
 ('Dây Dupont', 1, 'dây dupont', 'Nối dây', '-', 'Đủ dây đực-đực, đực-cái', None, None, 'Chưa có giá'),
 ('Điện trở 4,7 kΩ', 1, 'điện trở 4.7k', 'Kéo lên đường dữ liệu DS18B20', '-', 'Không cần nếu module DS18B20 đã có sẵn', None, None, 'Chưa có giá'),
 ('Điện trở 100 kΩ', 2, 'điện trở 100k', 'Chia áp đo VBAT qua ADC', 'Thay phép đo % pin của AXP2101, độ chính xác thấp hơn', '-', None, None, 'Chưa có giá'),
]
OPTIONAL = [
 ('MAX86140EVSYS (có bo cảm biến MAX86141)', 1, 'MAX86140EVSYS', 'Chuỗi PPG thật', 'Cùng IC AFE, 2 photodiode. Là hệ riêng có bo thu dữ liệu, không nối sẵn vào ESP32', 'Thường không có trên Shopee. Chỉ mua khi cần đo tín hiệu MAX86141 trước khi làm bo cảm biến', 138.12, 138.12, 'arrow.com; hết hàng tại Arrow, chờ 10 tuần; DigiKey UK niêm yết £117,23'),
 ('Module fuel gauge MAX17048', 1, 'MAX17048 module', 'Đo % pin của AXP2101', 'Khác IC, chính xác hơn chia áp', 'Chỉ mua khi cần % pin tin cậy trong giao diện', None, None, 'Chưa có giá'),
]
wb = Workbook(); ws = wb.active; ws.title = 'BOM module'
A = Font(name='Arial'); B = Font(name='Arial', bold=True); W = Font(name='Arial', bold=True, color='FFFFFF'); BLUE = Font(name='Arial', color='0000FF')
LINK = Font(name='Arial', color='0563C1', underline='single')
SEARCH = 'https://shopee.vn/search?keyword='
FILL = PatternFill('solid', fgColor='305496'); SEC = PatternFill('solid', fgColor='D9E2F3'); INPUT = PatternFill('solid', fgColor='FFFF00')
ws['A1'] = 'BOM giai đoạn module: đồng hồ theo dõi sức khỏe'; ws['A1'].font = B
ws['A2'] = 'Nhập giá Shopee vào cột H. Cột I, J là giá tham khảo ngoài Shopee, đọc ngày 06/11/2026, chưa gồm vận chuyển.'; ws['A2'].font = A
R = 4
for i, h in enumerate(HEAD, 1):
    c = ws.cell(R, i, h); c.fill = FILL; c.font = W; c.alignment = Alignment(wrap_text=True, vertical='center')
for i, w in enumerate([4, 38, 5, 30, 34, 44, 50, 14, 11, 11, 44], 1): ws.column_dimensions[CL(i)].width = w
def section(title, items, start):
    r = start; ws.cell(r, 1, title).font = B
    for k in range(1, len(HEAD) + 1): ws.cell(r, k).fill = SEC
    first = r + 1
    for n, it in enumerate(items, 1):
        r += 1
        name, qty, kw, block, diff, check, lo, hi, src = it
        for k, v in enumerate([n, name, qty, kw, block, diff.replace('**', ''), check.replace('**', ''), None, lo, hi, src], 1):
            c = ws.cell(r, k, v); c.font = A; c.alignment = Alignment(wrap_text=True, vertical='top')
        ws.cell(r, 4).hyperlink = SEARCH + urllib.parse.quote(kw); ws.cell(r, 4).font = LINK
        ws.cell(r, 8).fill = INPUT; ws.cell(r, 8).font = BLUE; ws.cell(r, 8).number_format = '#,##0'
        ws.cell(r, 9).number_format = ws.cell(r, 10).number_format = '0.00'
    r += 1
    ws.cell(r, 2, 'Cộng (chỉ các dòng có giá)').font = B
    ws.cell(r, 8, '=SUMPRODUCT(C%d:C%d,H%d:H%d)' % (first, r - 1, first, r - 1)).font = B; ws.cell(r, 8).number_format = '#,##0'
    for col, L in ((9, 'I'), (10, 'J')):
        c = ws.cell(r, col, '=SUMPRODUCT(C%d:C%d,%s%d:%s%d)' % (first, r - 1, L, first, L, r - 1)); c.font = B; c.number_format = '0.00'
    return r
end = section('Bắt buộc', REQUIRED, R + 1)
end2 = section('Tùy chọn', OPTIONAL, end + 2)
notes = ['Link là trang tìm kiếm Shopee theo từ khóa, không phải trang sản phẩm đã kiểm tra: chọn người bán và đối chiếu đúng mã trước khi mua.', 'BMI160, DS18B20, PCF8563 chỉ thay trong giai đoạn module; PCB vẫn theo tools/design.py.', 'Giới hạn: chưa kiểm được giá và tồn kho trên Shopee. Dòng không có giá USD không nằm trong tổng.',
         'MAX30102 không có LED xanh, nên kết quả đo ở cổ tay không chuyển thẳng sang MAX86141 + SFH 7016.',
         'Không tìm thấy module AXP2101 bán lẻ và module AMOLED CO5300 có sẵn chân cắm: phần nguồn PMIC và driver AMOLED chỉ kiểm được trên PCB.',
         'Giữ gán GPIO theo tools/design.py khi có thể để firmware chuyển sang PCB ít phải sửa. Chạy quét I2C sau khi nối để kiểm tra trùng địa chỉ.']
for i, n in enumerate(notes): ws.cell(end2 + 2 + i, 2, n).font = A
ws.freeze_panes = 'C5'
wb.save(OUT); print('->', OUT)
