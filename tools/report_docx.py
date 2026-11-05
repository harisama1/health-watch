"""Word report builder shared by the report generators: light markup -> .docx with python-docx.
Markup: # title, ## heading 1, ### heading 2, | tables, - bullets, 1. numbers, ``` code, **bold**, `code`,
{{fig|key|caption|cm}} {{pair|a|b|caption|cm}} {{stacked|a|b|caption|cm}} {{landscape}} {{portrait}} {{hook|name}}.
Image keys: main_power main_mcu main_periph main_ui sensor (rendered from outputs/*_schematic.pdf), else docs/img/<key>.png or
docs/img/schematic_review/<key>.png. Hooks are callables(builder) for tables built from design data."""
import os, re, subprocess, tempfile
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
FONT, MONO, BLUE = 'Arial', 'Consolas', RGBColor(0x30, 0x54, 0x96)
SHEETS = {'main_power': ('main', 2), 'main_mcu': ('main', 3), 'main_periph': ('main', 4), 'main_ui': ('main', 5), 'sensor': ('sensor', 2)}

class Report:
    def __init__(self, header, title):
        self.doc = Document(); self.tmp = tempfile.mkdtemp(); self.fign = 0; self.total = 17.0; st = self.doc.styles
        self._font(st['Normal'], 10.5); st['Normal'].paragraph_format.space_after = Pt(6); st['Normal'].paragraph_format.line_spacing = 1.1
        self._font(st['Title'], 22, True, BLUE)
        for name, size, before, after in (('Heading 1', 15, 16, 6), ('Heading 2', 12, 12, 4), ('Heading 3', 11, 10, 3)):
            self._font(st[name], size, True, BLUE)
            pf = st[name].paragraph_format; pf.space_before = Pt(before); pf.space_after = Pt(after); pf.keep_with_next = True
        self._font(st['Caption'], 9, False, RGBColor(0x40, 0x40, 0x40)); st['Caption'].font.italic = True
        self._font(st['List Bullet'], 10.5); self._font(st['List Number'], 10.5)
        sec = self.doc.sections[0]; self._a4(sec)
        h = sec.header.paragraphs[0]; r = h.add_run(header); r.font.size = Pt(8.5); r.font.color.rgb = RGBColor(0x60, 0x60, 0x60)
        f = sec.footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER; r = f.add_run('Trang '); r.font.size = Pt(8.5); self._field(f, 'PAGE'); r = f.add_run(' / '); r.font.size = Pt(8.5); self._field(f, 'NUMPAGES')
        p = self.doc.core_properties; p.title = title; p.author = 'HaiLV25'; p.comments = ''
    @staticmethod
    def _font(style, size, bold=None, color=None):
        style.font.name = FONT; style.font.size = Pt(size)
        if bold is not None: style.font.bold = bold
        if color is not None: style.font.color.rgb = color
        rpr = style.element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'): rf.set(qn(a), FONT)
        for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
            if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    @staticmethod
    def _a4(sec, landscape=False):
        sec.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
        sec.page_width, sec.page_height = (Cm(29.7), Cm(21.0)) if landscape else (Cm(21.0), Cm(29.7))
        sec.left_margin = sec.right_margin = Cm(1.5 if landscape else 2.0); sec.top_margin = Cm(2.0); sec.bottom_margin = Cm(1.8)
    @staticmethod
    def _field(par, code):
        for kind, text in (('begin', None), (None, code), ('end', None)):
            r = par.add_run(); r.font.size = Pt(8.5)
            if kind:
                f = OxmlElement('w:fldChar'); f.set(qn('w:fldCharType'), kind); r._r.append(f)
            else:
                i = OxmlElement('w:instrText'); i.set(qn('xml:space'), 'preserve'); i.text = text; r._r.append(i)
    def img(self, key):
        if key in SHEETS:
            board, page = SHEETS[key]; base = os.path.join(self.tmp, key)
            subprocess.run(['pdftoppm', '-r', '220', '-f', str(page), '-l', str(page), '-png', '-singlefile', os.path.join(ROOT, 'outputs', 'health_watch_%s_schematic.pdf' % board), base], check=True)
            return base + '.png'
        p = os.path.join(ROOT, 'docs', 'img', key + '.png')
        return p if os.path.exists(p) else os.path.join(ROOT, 'docs', 'img', 'schematic_review', key + '.png')
    @staticmethod
    def inline(par, text, size=None, color=None):
        for tok in re.split(r'(\*\*[^*]+\*\*|`[^`]+`)', text):
            if not tok: continue
            if tok.startswith('**'): r = par.add_run(tok[2:-2]); r.bold = True
            elif tok.startswith('`'):
                r = par.add_run(tok[1:-1]); r.font.name = MONO; r._r.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), MONO)
                if size: r.font.size = Pt(size - 0.5)
                if color is not None: r.font.color.rgb = color
                continue
            else: r = par.add_run(tok)
            if size: r.font.size = Pt(size)
            if color is not None: r.font.color.rgb = color
    @staticmethod
    def _shade(cell, fill):
        s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), fill); cell._tc.get_or_add_tcPr().append(s)
    @staticmethod
    def _widths(rows, total):
        n = len(rows[0]); w = []
        for c in range(n):
            lens = [len(re.sub(r'[*`]', '', r[c])) for r in rows]
            w.append(max(min(max(lens), 9), (sum(lens) / len(lens)) ** 0.75 * 1.6, 1.8))
        s = sum(w); w = [total * x / s for x in w]
        # no column narrower than its longest word, so short columns ("#", "Mức") never wrap letter by letter
        floor = [min(max(len(word) for r in rows for word in re.sub(r'[*`]', '', r[c]).split() or ['']) * 0.2 + 0.65, 3.0) for c in range(n)]
        fixed = [c for c in range(n) if w[c] < floor[c]]
        rest = total - sum(floor[c] for c in fixed); free = sum(w[c] for c in range(n) if c not in fixed)
        return [floor[c] if c in fixed else w[c] * rest / free for c in range(n)]
    def table(self, rows):
        t = self.doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        ws = self._widths(rows, self.total)
        for gc, wd in zip(t._tbl.tblGrid.findall(qn('w:gridCol')), ws): gc.set(qn('w:w'), str(int(wd * 567)))
        for i, row in enumerate(rows):
            tr = t.rows[i]._tr.get_or_add_trPr(); tr.append(OxmlElement('w:cantSplit'))
            if i == 0: tr.append(OxmlElement('w:tblHeader'))
            cells = t.rows[i].cells
            for j, txt in enumerate(row):
                c = cells[j]; c.width = Cm(ws[j]); p = c.paragraphs[0]; pf = p.paragraph_format; pf.space_after = Pt(1); pf.space_before = Pt(1); pf.line_spacing = 1.0
                if i == 0: self._shade(c, '305496'); self.inline(p, '**%s**' % txt, 9, RGBColor(0xFF, 0xFF, 0xFF))
                else:
                    if i % 2 == 0: self._shade(c, 'F2F5FA')
                    self.inline(p, txt, 9)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(4)
    def caption(self, text):
        self.fign += 1
        p = self.doc.add_paragraph(style='Caption'); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run('Hình %d. %s' % (self.fign, text.replace('`', '')))
    def _pic(self, key, width, after=2):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; pf = p.paragraph_format; pf.keep_with_next = True; pf.space_after = Pt(after)
        p.add_run().add_picture(self.img(key), width=Cm(width))
    def figure(self, key, cap, width): self._pic(key, width); self.caption(cap)
    def pair(self, a, b, cap, width):
        t = self.doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        for j, (k, lab) in enumerate(((a, 'Trước khi sửa'), (b, 'Sau khi sửa'))):
            c = t.cell(0, j); c.width = Cm(width + 0.4); p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; r = p.add_run(lab); r.bold = True; r.font.size = Pt(9)
            c = t.cell(1, j); c.width = Cm(width + 0.4); p = c.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.add_run().add_picture(self.img(k), width=Cm(width))
        self.caption(cap)
    def stacked(self, a, b, cap, width):
        for k, lab in ((a, 'Trước khi sửa'), (b, 'Sau khi sửa')):
            p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(1); r = p.add_run(lab); r.bold = True; r.font.size = Pt(9)
            self._pic(k, width, 4)
        self.caption(cap)
    def render(self, content, out, hooks=None):
        lines = content.strip('\n').split('\n'); i = 0; doc = self.doc
        while i < len(lines):
            l = lines[i]
            if not l.strip(): i += 1; continue
            if l.startswith('{{'):
                a = l.strip('{} ').split('|'); kind = a[0]
                if kind == 'fig': self.figure(a[1], a[2], float(a[3]))
                elif kind == 'pair': self.pair(a[1], a[2], a[3], float(a[4]))
                elif kind == 'stacked': self.stacked(a[1], a[2], a[3], float(a[4]))
                elif kind == 'landscape': self._a4(doc.add_section(WD_SECTION.NEW_PAGE), True); self.total = 26.0
                elif kind == 'portrait': self._a4(doc.add_section(WD_SECTION.NEW_PAGE)); self.total = 17.0
                elif kind == 'hook': hooks[a[1]](self)
                i += 1
            elif l.startswith('# '): doc.add_paragraph(l[2:], style='Title'); i += 1
            elif l.startswith('### '): doc.add_heading(l[4:], 3); i += 1
            elif l.startswith('## '): doc.add_heading(l[3:], 1); i += 1
            elif l.startswith('|'):
                rows = []
                while i < len(lines) and lines[i].startswith('|'):
                    cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r':?-+:?', c) for c in cells): rows.append(cells)
                    i += 1
                self.table(rows)
            elif l.startswith('```'):
                i += 1; p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.0; code = []
                while not lines[i].startswith('```'): code.append(lines[i]); i += 1
                r = p.add_run('\n'.join(code)); r.font.name = MONO; r.font.size = Pt(8.5); i += 1
            elif l.startswith('- '): self.inline(doc.add_paragraph(style='List Bullet'), l[2:]); i += 1
            elif re.match(r'\d+\. ', l): self.inline(doc.add_paragraph(style='List Number'), l.split('. ', 1)[1]); i += 1
            else: self.inline(doc.add_paragraph(), l); i += 1
        doc.save(out); print('->', os.path.relpath(out, ROOT), '| figures', self.fign)
