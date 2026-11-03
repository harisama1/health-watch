"""Citation index -> docs/citations.md: every datasheet number (facts.py, re-checked on the PDF page now) and every
part's reference (design.py), with the file it points to."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import design as D, facts as F
L = ['# Trích dẫn - đồng hồ theo dõi sức khỏe', '',
     'Mọi số liệu dùng trong báo cáo và schematic đều trỏ về một trang của tài liệu trong thư mục `datasheets/`.',
     'Số trang = trang PDF (trùng số in trên trang; riêng HDG: số in = PDF − 3). **ASSUME** = giả định, chưa có tài liệu.', '',
     '## 1. Tài liệu', '', '| Khóa | Tài liệu | File |', '|---|---|---|']
L += ['| %s | %s | `datasheets/%s` |' % (k, d[1], d[0]) for k, d in D.DOCS.items()]
ok, bad = F.verify()
badk = {b[0] for b in bad}
L += ['', '## 2. Số liệu đã đối chiếu tự động (%d/%d khớp trang PDF)' % (ok, len(F.F)), '', '| Số liệu | Giá trị | Tài liệu, trang | Đoạn văn bản phải có trên trang | Kiểm |', '|---|---|---|---|---|']
for k, (doc, page, rx, val, unit, text) in F.F.items():
    L.append('| %s | %s %s | %s p.%d (%s) | `%s` | %s |' % (text, val, unit, doc, page, D.DOCS[doc][0], rx.replace('|', '/')[:70], 'KHÔNG' if k in badk else 'OK'))
for board, parts in D.BOARDS.items():
    L += ['', '## 3. Trích dẫn theo linh kiện - %s' % D.TITLE[board], '', '| Ref | Giá trị | Tài liệu (khóa §/bảng/trang) |', '|---|---|---|']
    L += ['| %s | %s | %s |' % (p['ref'], D.P[p['typ']][1], p['cite'] or '-') for p in parts]
open(os.path.join(HERE, '..', 'docs', 'citations.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('citations.md:', ok, '/', len(F.F), 'verified')
