# Đồng hồ đeo tay theo dõi sức khỏe (đồ án) - edge AI + web

**Xem nhanh:**
- Báo cáo phân tích thiết kế (rà soát toàn bộ, Rev 2.2): [outputs/health_watch_design_report.docx](outputs/health_watch_design_report.docx)
- Báo cáo phân tích schematic: [outputs/schematic_analysis_report.docx](outputs/schematic_analysis_report.docx)
- Schematic: [bo chính](outputs/health_watch_main_schematic.pdf), [bo cảm biến](outputs/health_watch_sensor_schematic.pdf); project KiCad: [hardware/](hardware/)
- Sơ đồ khối: [block_diagram.png](outputs/block_diagram.png), [power_tree.png](outputs/power_tree.png), [data_flow.png](outputs/data_flow.png)
- BOM và dự toán PCBA JLCPCB: [health_watch_bom.xlsx](outputs/bom/health_watch_bom.xlsx), [CSV bo chính](outputs/bom/health_watch_main_jlc_bom.csv), [CSV bo cảm biến](outputs/bom/health_watch_sensor_jlc_bom.csv)
- BOM giai đoạn module (linh kiện rời, link tìm Shopee): [health_watch_module_bom.xlsx](outputs/bom/health_watch_module_bom.xlsx)
- Trích dẫn: [citations.pdf](outputs/citations.pdf); datasheet: [bảng link tải](docs/datasheets/README.md) (repo không kèm PDF của hãng)
- Gói nộp đầy đủ: [deliverable/DoAn_DongHo_SucKhoe/](deliverable/DoAn_DongHo_SucKhoe/)


Thiết kế chưa chế tạo, chưa sẵn sàng layout. Hai bo tự thiết kế, chỉ tham khảo mạch Waveshare 1.75C: **bo chính** (ESP32-S3R8, AXP2101, AMOLED 1.75", BMI270, PCF85063A, boost 5 V, motor, còi) và
**bo cảm biến** (MAX86141 + SFH 7016 + 2 × VEMD8080, LP5907 1.8 V, TXS0108E, MAX30208), nối FPC 16 chân.

| Cái gì | Ở đâu |
|---|---|
| Nguồn sự thật (linh kiện, net, lý do, trích dẫn) | `tools/design.py` |
| Số liệu datasheet + kiểm trang | `tools/facts.py` |
| Thư viện symbol/footprint riêng | `hardware/HW_Watch.kicad_sym`, `hardware/HW_Watch.pretty` (từ `tools/libgen.py`); `hardware/HW_IC.kicad_sym`, `hardware/HW_IC.pretty`; symbol KiCad 9 đóng băng trong `tools/stock_symbols/` |
| Schematic KiCad 9 (đi dây tay: `tools/sch_layouts.py`) | `hardware/main/`, `hardware/sensor/` → PDF trong `outputs/` |
| Gói nộp (báo cáo + schematic + sơ đồ + trích dẫn) | `deliverable/DoAn_DongHo_SucKhoe/` |
| Sơ đồ khối, cây nguồn, luồng dữ liệu | `docs/img/*.svg/png` (từ `tools/gen_diagrams.py`) |
| Báo cáo phân tích thiết kế (kết luận, vấn đề còn mở, lộ trình) | `outputs/health_watch_design_report.docx` (nội dung `tools/design_report_content.py`, sinh bằng `tools/gen_design_report.py`) |
| Báo cáo phân tích schematic (review, lỗi đã sửa, vấn đề còn mở) | `outputs/schematic_analysis_report.docx` (nội dung `tools/schematic_report_content.py`, sinh bằng `tools/gen_schematic_report.py`) |
| Datasheet (link tải) | `docs/datasheets/README.md` |

## Sinh lại

```bash
python3 tools/libgen.py                     # thư viện
python3 tools/design.py                     # kiểm tra nhanh (trùng ref, net 1 chân, I2C, FPC)
python3 tools/check_bom.py                  # đối chiếu mã với JLCPCB và LCSC, rc=1 nếu sai
python3 tools/gen_bom.py                    # sinh BOM và dự toán, cần openpyxl
python3 tools/gen_module_bom.py             # sinh BOM giai đoạn module, cần openpyxl
for b in main sensor; do
  python3 tools/gen_sch.py $b hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch erc --severity-all --exit-code-violations -o /tmp/$b.rpt hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch export netlist -o /tmp/$b.net hardware/$b/health_watch_$b.kicad_sch && python3 tools/check_net.py $b /tmp/$b.net
  kicad-cli sch export pdf -o outputs/health_watch_${b}_schematic.pdf hardware/$b/health_watch_$b.kicad_sch
done
python3 tools/facts.py                      # đối chiếu trích dẫn
python3 tools/gen_diagrams.py
python3 tools/gen_citations.py && python3 tools/md2pdf.py docs/citations.md   # cần gói `markdown`, google-chrome
python3 tools/gen_design_report.py           # cần python-docx, matplotlib, pdftoppm
python3 tools/gen_schematic_report.py        # cần python-docx, pdftoppm
```
Schematic sinh tự động: sửa `design.py`, không sửa file `.kicad_sch` (sẽ bị ghi đè). `gen_diagrams.py` dùng `rsvg-convert` hoặc google-chrome. ERC cần bảng thư viện global của KiCad: mở KiCad GUI một lần để tạo, nếu không sẽ có nhiều cảnh báo giả.

## Ghi chú cho repo public

- Không kèm datasheet PDF của hãng: tải theo `docs/datasheets/README.md` trước khi chạy `tools/facts.py` / `tools/gen_citations.py`.
- File schematic ở định dạng KiCad 9. Mở bằng KiCad 10 rồi lưu sẽ nâng định dạng, KiCad 9 không mở lại được; ERC trong báo cáo chạy bằng `kicad-cli` 10.0.8.
- Đáp án/thiết kế là của đồ án, chưa chạy trên phần cứng. **Chưa sẵn sàng để layout**: cơ khí chưa chốt; MAX86141, SFH 7016 và màn hình chưa mua được trên JLCPCB/LCSC; xem mục 7, 8 của báo cáo thiết kế.
