"""Check every LCSC code in design.P against the JLCPCB and LCSC listings: the listing must match what the design says.
usage: python3 tools/check_bom.py   -> prints one line per code, exit 1 on any mismatch; parts without a code are listed as TODO."""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
import jlc_api as A
# part key -> regex the listing (model + description + package) must match
EXPECT = {'ESP32': 'ESP32-S3R8', 'FLASH': 'W25Q128JVSIQ', 'AXP': 'AXP2101', 'BOOST': 'TPS61240DRV', 'IMU': 'BMI270', 'RTC': 'PCF85063ATT', 'AFE': 'MAX86141ENP', 'TEMP': 'MAX30208CLB',
          'LDO18': 'LP5907MFX-1.8', 'TXS': 'TXS0108EPW', 'PD': 'VEMD8080', 'ESD': 'USBLC6-2SC6', 'USBC': 'TYPE-C-31-M-12', 'XTAL40': r'X322540MPB4SI.*40MHz.*10ppm.*15pF', 'NFET': 'AO3400A',
          'BTN': 'TS-1088', 'LED_R': r'KT-0603R.*Red', 'LED_G': r'KT-0603G', 'R0': r'0Ω.*0402', 'R0_0805': r'0Ω.*0805', 'R1M': r'1MΩ.*0402', 'R5k1': r'5\.1kΩ.*0402', 'R10k': r'10kΩ.*0402',
          'R100k': r'100kΩ.*0402', 'R1k': r'1kΩ.*0402', 'R510': r'510Ω.*0402', 'R2k2': r'2\.2kΩ.*0402', 'R4k7': r'4\.7kΩ.*0402', 'R22': r'22Ω.*0402', 'R100': r'100Ω.*0402', 'C100n': r'100nF.*0402',
          'C1u': r'1uF.*0402', 'C10n': r'10nF.*0402', 'C2u2': r'2\.2uF.*0402', 'C4u7': r'4\.7uF.*0603', 'C10u': r'10uF.*10V.*0603', 'C22u': r'22uF.*0603', 'C22p': r'22pF.*C0G.*0402', 'C1n': r'1nF.*0402',
          'XTAL32': r'32\.768kHz.*7pF.*SMD2012', 'ANT': '2450AT18D0100', 'DFLY': 'BAT54WS', 'MOTOR': 'LCM1027', 'BUZZ': 'CMT-8504-100-SMT-TR', 'NTC': r'10kΩ.*3950|KNTC0402', 'BAT': '53261|532610271', 'FPC31': '0.3K-HX-31PWB', 'FPC16': 'FH12-16S-0.5SH',
          'HDR3': 'PZ254V-11-03P', 'R0_RF': r'0Ω.*0201', 'R499': r'499Ω.*0402', 'RS50m': r'50mΩ.*0805', 'RS100m': r'100mΩ.*0603', 'C1p5': r'1\.5pF.*C0G.*0201', 'L2n0': r'2nH.*0402', 'L2n4': r'2\.4nH.*0201', 'L24n': r'24nH.*0402', 'L1u_2A': r'1uH.*1008', 'L1u_1A': r'1uH.*0805'}
bad = todo = ok = 0
for key, typ in D.P.items():
    m = re.match(r'C\d+', typ[3] or '')
    if not m:
        print('TODO %-8s %-24s %s' % (key, typ[1], typ[3] or '(không có mã)')); todo += 1; continue
    j, l = A.jlc(m.group(0)), A.lcsc(m.group(0))
    body = A.text(j, l)
    exp = EXPECT.get(key)
    good = bool(exp and re.search(exp, body, re.S))
    print('%-4s %-8s %-9s JLC %-9s LCSC %-8s %s' % ('OK' if good else 'BAD', key, m.group(0), j.get('stockCount'), l.get('stockNumber'), body[:80]))
    ok += good; bad += not good
print('ok %d | wrong %d | no code yet %d' % (ok, bad, todo))
sys.exit(1 if bad else 0)
