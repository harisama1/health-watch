# Đồ án: Đồng hồ đeo tay theo dõi sức khỏe (edge AI + web)

| Thư mục | Nội dung |
|---|---|
| `1_BaoCao/` | **Báo cáo phân tích thiết kế** (`health_watch_design_report.pdf`, bản Markdown + hình) |
| `2_Schematic/` | Schematic PDF bo chính (5 trang) và bo cảm biến (2 trang); `kicad/` = project KiCad 9 mở được ngay (`main/health_watch_main.kicad_pro`, `sensor/health_watch_sensor.kicad_pro`) kèm thư viện symbol/footprint riêng |
| `3_SoDoKhoi/` | Sơ đồ khối phần cứng, cây nguồn + điểm đo dòng, luồng dữ liệu edge AI → web (PNG + SVG) |
| `4_TrichDan/` | `citations.pdf`: bảng trích dẫn (29 số liệu đã đối chiếu đúng trang PDF + tài liệu của từng linh kiện); `datasheets/`: toàn bộ tài liệu gốc |
| `5_NguonSinh/` | Script sinh lại toàn bộ (design.py = nguồn sự thật: linh kiện, net, lý do, trích dẫn) |

Kiểm tra: ERC 0 lỗi / 0 cảnh báo cả 2 bo; netlist khớp design.py theo từng chân; 29/29 trích dẫn số liệu khớp trang PDF.
Chưa làm: layout PCB, chạy thật trên phần cứng. Việc còn mở: xem mục 9 của báo cáo.
