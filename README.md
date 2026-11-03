# Đồng hồ đeo tay theo dõi sức khỏe (đồ án) - edge AI + web

**Xem nhanh:**
- Báo cáo phân tích thiết kế: [outputs/health_watch_design_report.pdf](outputs/health_watch_design_report.pdf) ([Markdown](docs/health_watch_design_report.md))
- Schematic: [bo chính](outputs/health_watch_main_schematic.pdf), [bo cảm biến](outputs/health_watch_sensor_schematic.pdf); project KiCad: [hardware/](hardware/)
- Sơ đồ khối: [block_diagram.png](outputs/block_diagram.png), [power_tree.png](outputs/power_tree.png), [data_flow.png](outputs/data_flow.png)
- Trích dẫn: [citations.pdf](outputs/citations.pdf); datasheet: [bảng link tải](docs/datasheets/README.md) (repo không kèm PDF của hãng)
- Gói nộp đầy đủ: [deliverable/DoAn_DongHo_SucKhoe/](deliverable/DoAn_DongHo_SucKhoe/)


Thiết kế chốt 2026-11-04. Hai bo: **bo chính** (ESP32-S3R8, AXP2101, AMOLED 1.75", BMI270, PCF85063A, boost 5 V, motor, còi) và
**bo cảm biến** (MAX86141 + SFH 7013 + 2 × VEMD8080, LP5907 1.8 V, TXS0108E, MAX30208), nối FPC 16 chân.

| Cái gì | Ở đâu |
|---|---|
| Nguồn sự thật (linh kiện, net, lý do, trích dẫn) | `tools/design.py` |
| Số liệu datasheet + kiểm trang | `tools/facts.py` |
| Thư viện symbol/footprint riêng | `hardware/HW_Watch.kicad_sym`, `hardware/HW_Watch.pretty` (từ `tools/libgen.py`) |
| Schematic KiCad 9 (đi dây tay: `tools/sch_layouts.py`) | `hardware/main/`, `hardware/sensor/` → PDF trong `outputs/` |
| Gói nộp (báo cáo + schematic + sơ đồ + trích dẫn) | `deliverable/DoAn_DongHo_SucKhoe/` |
| Sơ đồ khối, cây nguồn, luồng dữ liệu | `docs/img/*.svg/png` (từ `tools/gen_diagrams.py`) |
| Báo cáo phân tích thiết kế | `docs/health_watch_design_report.md` → `outputs/health_watch_design_report.pdf` |
| Datasheet (link tải) | `docs/datasheets/README.md` |

## Sinh lại

```bash
python3 tools/libgen.py                     # thư viện
python3 tools/design.py                     # kiểm tra nhanh (trùng ref, net 1 chân, I2C, FPC)
for b in main sensor; do
  python3 tools/gen_sch.py $b hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch erc hardware/$b/health_watch_$b.kicad_sch
  kicad-cli sch export netlist -o /tmp/$b.net hardware/$b/health_watch_$b.kicad_sch && python3 tools/check_net.py $b /tmp/$b.net
  kicad-cli sch export pdf -o outputs/health_watch_${b}_schematic.pdf hardware/$b/health_watch_$b.kicad_sch
done
python3 tools/facts.py                      # đối chiếu trích dẫn
python3 tools/gen_diagrams.py
python3 tools/gen_citations.py && python3 tools/gen_report.py && ~/tools/docvenv/bin/python tools/md2pdf.py docs/health_watch_design_report.md docs/citations.md
```
Schematic sinh tự động: sửa `design.py`, không sửa file `.kicad_sch` (sẽ bị ghi đè).

## Ghi chú cho repo public

- Không kèm datasheet PDF của hãng: tải theo `docs/datasheets/README.md` trước khi chạy `tools/facts.py` / `tools/gen_report.py`.
- `tools/libgen.py` và `tools/gen_sch.py` đọc thêm thư viện `HW_IC` của repo học PCB riêng (đường dẫn `~/workspace/PCB_design_learning/kicad_lib`).
  Mở project KiCad thì không cần: symbol đã nhúng trong file schematic, footprint dùng `hardware/HW_Watch.pretty` + `hardware/HW_IC.pretty`.
- Đáp án/thiết kế là của đồ án, chưa chạy trên phần cứng.
