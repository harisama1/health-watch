"""Check every LCSC code in design.P against the LCSC product API: the listing must match what the design says.
usage: python3 tools/check_bom.py   -> prints one line per code, exit 1 on any mismatch; parts without a code are listed as TODO."""
import json, re, sys, time, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
# part key -> regex the listing (model + description + package) must match
EXPECT = {'ESP32': 'ESP32-S3R8', 'FLASH': 'W25Q128JVSIQ', 'AXP': 'AXP2101', 'BOOST': 'TPS61240DRV', 'IMU': 'BMI270', 'RTC': 'PCF85063ATL', 'AFE': 'MAX86141ENP', 'TEMP': 'MAX30208CLB',
          'LDO18': 'LP5907MFX-1.8', 'TXS': 'TXS0108EPW', 'PD': 'VEMD8080', 'ESD': 'USBLC6-2SC6', 'USBC': 'TYPE-C-31-M-12', 'XTAL40': r'X322540MPB4SI.*40MHz.*10ppm.*15pF', 'NFET': 'AO3400A',
          'BTN': 'TS-1088', 'LED_R': r'KT-0603R.*Red', 'LED_G': r'Green.*0603', 'R0': r'0Ω.*0402', 'R0_0805': r'0Ω.*0805', 'R1M': r'1MΩ.*0402', 'R5k1': r'5\.1kΩ.*0402', 'R10k': r'10kΩ.*0402',
          'R100k': r'100kΩ.*0402', 'R1k': r'1kΩ.*0402', 'R510': r'510Ω.*0402', 'R2k2': r'2\.2kΩ.*0402', 'R4k7': r'4\.7kΩ.*0402', 'R22': r'22Ω.*0402', 'R100': r'100Ω.*0402', 'C100n': r'100nF.*0402',
          'C1u': r'1uF.*0402', 'C10n': r'10nF.*0402', 'C2u2': r'2\.2uF.*0402', 'C4u7': r'4\.7uF.*0603', 'C10u': r'10uF.*10V.*0603', 'C22u': r'22uF.*0603', 'C22p': r'22pF.*C0G.*0402', 'C1n': r'1nF.*0402'}
bad = todo = ok = 0
for key, typ in D.P.items():
    m = re.match(r'C\d+', typ[3] or '')
    if not m:
        print('TODO %-8s %-24s %s' % (key, typ[1], typ[3] or '(không có mã)')); todo += 1; continue
    req = urllib.request.Request('https://wmsc.lcsc.com/ftps/wm/product/detail?productCode=' + m.group(0), headers={'User-Agent': 'Mozilla/5.0'})
    r = (json.load(urllib.request.urlopen(req, timeout=20)).get('result') or {})
    text = '%s | %s | %s' % (r.get('productModel'), r.get('productIntroEn'), r.get('encapStandard'))
    exp = EXPECT.get(key)
    good = bool(exp and re.search(exp, text, re.S))
    print('%-4s %-8s %-9s stock %-8s %s' % ('OK' if good else 'BAD', key, m.group(0), r.get('stockNumber'), text[:90]))
    ok += good; bad += not good; time.sleep(0.25)
print('ok %d | wrong %d | no code yet %d' % (ok, bad, todo))
sys.exit(1 if bad else 0)
