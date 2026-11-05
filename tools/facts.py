"""Numbers taken from the datasheets, each with the page it is printed on and a regex that must match that page.
`python3 tools/facts.py` re-opens every PDF page (pdftotext) and checks the regex -> citation check for the report.
Page = PDF page (equal to the printed number for all these documents)."""
import os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
DS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'datasheets')

# key: (doc, page, regex, value, unit, text)
F = {
 'esp_light':   ('DS', 68, r'Light-sleep1?\s+VDD_SPI and Wi-Fi are powered down.*?240', 0.240, 'mA', 'ESP32-S3 light-sleep (Table 5-10)'),
 'esp_deep':    ('DS', 68, r'RTC memory is powered up\. RTC peripherals are powered down\.\s+7', 0.007, 'mA', 'ESP32-S3 deep-sleep (Table 5-10)'),
 'esp_160':     ('DS', 67, r'160\s+Dual core running 32-bit data access instructions\s+49\.6\s+64\.1', 64.1, 'mA', 'ESP32-S3 160 MHz, 2 nhân chạy (Table 5-9, Typ2)'),
 'esp_240':     ('DS', 67, r'240\s+Dual core running 32-bit data access instructions\s+66\.2\s+81\.3', 81.3, 'mA', 'ESP32-S3 240 MHz, 2 nhân chạy (Table 5-9, Typ2)'),
 'wifi_tx':     ('DS', 66, r'802\.11n, HT20, MCS7, @18\.5 dBm\s+283', 283, 'mA', 'WiFi TX đỉnh HT20 MCS7 (Table 5-7)'),
 'wifi_rx':     ('DS', 66, r'802\.11b/g/n, HT20\s+88', 88, 'mA', 'WiFi RX (Table 5-7)'),
 'ble_tx0':     ('DS', 67, r'Bluetooth LE @ 0 dBm\s+176', 176, 'mA', 'BLE TX 0 dBm đỉnh (Table 5-8)'),
 'afe_led25':   ('MAX', 7, r'PPG_SR=25sps\s+185', 0.185, 'mA', 'MAX86141 ILED, 1 LED 62 mA, 25 sps'),
 'afe_led100':  ('MAX', 7, r'PPG_SR = 100sps\s+735', 0.735, 'mA', 'MAX86141 ILED, 1 LED 62 mA, 100 sps'),
 'afe_vdd25':   ('MAX', 7, r'PPG_SR = 25sps\s+11', 0.011, 'mA', 'MAX86141 IDD, 25 sps, LP_MODE'),
 'afe_shdn':    ('MAX', 7, r'VDD Current in Shutdown\s+TA = \+25°C\s+0\.6', 0.0006, 'mA', 'MAX86141 IDD shutdown'),
 'afe_vdd':     ('MAX', 6, r'1\.7\s+1\.8\s+2\.0\s+V', 1.8, 'V', 'MAX86141 VDD 1.7-2.0 V'),
 'afe_vled':    ('MAX', 6, r'LED Supply Voltage\s+VLED\s+Verified during PSRR Test\s+3\.1\s+5\.5', 3.1, 'V', 'MAX86141 VLED 3.1-5.5 V'),
 'afe_spi':     ('MAX', 8, r'SCLK Frequency\s+fSCLK\s+4\s+MHz', 4, 'MHz', 'MAX86141 SPI tối đa'),
 'afe_vih':     ('MAX', 8, r'Input Voltage High\s+VIH\s+SDI, SCLK, CSB, GPIO1, GPIO2\s+1\.4', 1.4, 'V', 'MAX86141 VIH'),
 'afe_absmax':  ('MAX', 4, r'VDD_DIG to GND_ANA[. ]+-0\.3V to \+2\.2V', 2.2, 'V', 'MAX86141 abs max VDD'),
 'sfh_vf_g':    ('SFH', 5, r'Forward voltage.*?max\.\s+2\.80 V', 2.80, 'V', 'SFH 7016 VF xanh lá max'),
 'imu_ag':      ('BMI', 11, r'A\+G Normal Mode.*?685', 0.685, 'mA', 'BMI270 acc+gyro normal'),
 'imu_a':       ('BMI', 11, r'Aonly Normal Mode.*?210', 0.210, 'mA', 'BMI270 acc normal (ODR max)'),
 'imu_addr':    ('BMI', 128, r'0b1101000 \(0x68\)', 0x68, '', 'BMI270 địa chỉ I2C'),
 'tps_iq':      ('TPS', 5, r'Operating quiescent current\s+IOUT = 0 mA, Power save mode\s+30\s+40', 0.030, 'mA', 'TPS61240 Iq'),
 'tps_cin':     ('TPS', 12, r'2\.2 μF, X5R, 6\.3 V, 0402', 2.2, 'uF', 'TPS61240 CIN'),
 'lp_iq':       ('LP', 6, r'VEN = 1\.2 V, IOUT = 0 mA\s+12\s+25', 0.012, 'mA', 'LP5907 Iq'),
 'm30_stby':    ('M30', 1, r'0\.5μA Standby Current', 0.0005, 'mA', 'MAX30208 standby'),
 'axp_off':     ('AXP', 11, r'IBAT\s+Battery discharge current\s+40', 0.040, 'mA', 'AXP2101 dòng pin khi tắt (chỉ RTCLDO)'),
 'axp_sda':     ('AXP', 9, r'needs a 2\.2kΩ Pull High', 2.2, 'kΩ', 'AXP2101 kéo lên I2C'),
 'axp_vsys':    ('AXP', 8, r'Connect two\s+22uF capacitors', 22, 'uF', 'AXP2101 tụ VSYS'),
 'txs_pu':      ('TXS', 18, r'40kΩ when the output is driving low.*?4kΩ when the output is driving high', 4, 'kΩ', 'TXS0108E pull-up nội'),
 'txs_vcca':    ('TXS', 20, r'ensure that VCCA ≤ VCCB at all times', 0, '', 'TXS0108E VCCA ≤ VCCB'),
}

def page_text(doc, page):
    fn = os.path.join(DS_DIR, D.DOCS[doc][0])
    return subprocess.run(['pdftotext', '-f', str(page), '-l', str(page), '-layout', fn, '-'], capture_output=True, text=True).stdout

def find_pages(doc, rx, n=200):
    out = []
    for p in range(1, n + 1):
        t = page_text(doc, p)
        if not t: break
        if re.search(rx, t, re.S): out.append(p)
    return out

def verify(fix=False):
    ok, bad = 0, []
    for k, (doc, page, rx, *_rest) in F.items():
        if re.search(rx, page_text(doc, page), re.S): ok += 1
        else: bad.append((k, doc, page, find_pages(doc, rx) if fix else '?'))
    return ok, bad

def val(k): return F[k][3]
def cite(k): return '%s p.%d' % (F[k][0], F[k][1])

if __name__ == '__main__':
    ok, bad = verify(fix=True)
    print('citations verified: %d/%d' % (ok, len(F)))
    for b in bad: print('NOT FOUND', b)
