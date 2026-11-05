"""Markdown report -> HTML -> PDF (google-chrome headless if installed, else flatpak LibreOffice). Needs the `markdown` package.
Usage: python3 tools/md2pdf.py docs/airmouse_schematic_report.md [...]   (PDFs go to outputs/)"""
import base64, os, re, shutil, subprocess, sys, tempfile
import markdown

CSS = """body{font-family:'DejaVu Sans',Arial,sans-serif;font-size:9.5pt;line-height:1.35;color:#111}
h1{font-size:17pt;border-bottom:2px solid #305496}h2{font-size:13pt;color:#305496;margin-top:18pt}h3{font-size:11pt}
table{border-collapse:collapse;width:100%;margin:6pt 0}th,td{border:1px solid #bbb;padding:2pt 4pt;vertical-align:top}
th{background:#305496;color:#fff}pre{font-family:'DejaVu Sans Mono',monospace;font-size:5.5pt;white-space:pre;background:#f4f4f4;padding:4pt}
code{font-family:'DejaVu Sans Mono',monospace;font-size:8.5pt}img{max-width:100%}pre code{font-size:7pt;white-space:pre}"""

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'outputs')
for md in sys.argv[1:]:
    src = os.path.abspath(md)
    body = markdown.markdown(open(src, encoding='utf-8').read(), extensions=['tables', 'fenced_code'])
    # LibreOffice only links <img src="file">; inline the pictures so they end up inside the PDF
    inline = lambda m: 'src="data:image/png;base64,%s"' % base64.b64encode(open(os.path.join(os.path.dirname(src), m.group(1)), 'rb').read()).decode()
    body = re.sub(r'src="([^":]+\.png)"', inline, body)
    page = '<!doctype html><html><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>' % (CSS, body)
    html_path = os.path.splitext(src)[0] + '.html'          # next to the .md so relative image links resolve
    open(html_path, 'w', encoding='utf-8').write(page)
    pdf_path = os.path.join(os.path.abspath(out_dir), os.path.basename(os.path.splitext(src)[0]) + '.pdf')
    with tempfile.TemporaryDirectory() as tmp:
      if shutil.which('google-chrome'):
        subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--user-data-dir=' + tmp,
                        '--print-to-pdf=' + pdf_path, 'file://' + html_path], check=True, capture_output=True)
      else:
        subprocess.run(['flatpak', 'run', '--filesystem=host', '--filesystem=/tmp', 'org.libreoffice.LibreOffice', '--headless', '-env:UserInstallation=file://' + tmp, '--convert-to', 'pdf:writer_web_pdf_Export',
                        '--outdir', os.path.abspath(out_dir), html_path], check=True, capture_output=True)
    os.remove(html_path)
    print('->', os.path.join('outputs', os.path.basename(os.path.splitext(src)[0]) + '.pdf'))
