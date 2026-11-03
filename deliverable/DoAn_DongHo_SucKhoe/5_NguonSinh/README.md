# Đồng hồ đeo tay theo dõi sức khỏe (đồ án) - edge AI + web

Thiết kế chốt 2026-11-04. Hai bo: **bo chính** (ESP32-S3R8, AXP2101, AMOLED 1.75", BMI270, PCF85063A, boost 5 V, motor, còi) và
**bo cảm biến** (MAX86141 + SFH 7013 + 2 × VEMD8080, LP5907 1.8 V, TXS0108E, MAX30208), nối FPC 16 chân.

| Cái gì | Ở đâu |
|---|---|
| Nguồn sự thật (linh kiện, net, lý do, trích dẫn) | `tools/design.py` |
| Số liệu datasheet + kiểm trang | `tools/facts.py` |
| Thư viện symbol/footprint riêng | `hardware/HW_Watch.kicad_sym`, `hardware/HW_Watch.pretty` (từ `tools/libgen.py`) |
| Schematic KiCad 9 | `hardware/main/`, `hardware/sensor/` → PDF trong `outputs/` |
| Sơ đồ khối, cây nguồn, luồng dữ liệu | `docs/img/*.svg/png` (từ `tools/gen_diagrams.py`) |
| Báo cáo phân tích thiết kế | `docs/health_watch_design_report.md` → `outputs/health_watch_design_report.pdf` |
| Datasheet | `docs/datasheets/` |

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
python3 tools/gen_report.py && ~/tools/docvenv/bin/python tools/md2pdf.py docs/health_watch_design_report.md
```
Schematic sinh tự động: sửa `design.py`, không sửa file `.kicad_sch` (sẽ bị ghi đè).
