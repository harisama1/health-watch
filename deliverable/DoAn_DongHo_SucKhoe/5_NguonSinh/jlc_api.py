"""Read-only lookups of JLCPCB parts-library and LCSC product data. Prices and stock are live values."""
import json, time, urllib.request
JLC = 'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList'
LCSC = 'https://wmsc.lcsc.com/ftps/wm/product/detail?productCode='
HEAD = {'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}

def jlc(code):
    """JLCPCB library entry whose code is exactly `code`, or {} if absent."""
    req = urllib.request.Request(JLC, data=json.dumps({'keyword': code, 'currentPage': 1, 'pageSize': 5}).encode(), headers=HEAD)
    items = (json.load(urllib.request.urlopen(req, timeout=25))['data']['componentPageInfo'] or {}).get('list') or []
    time.sleep(0.25)
    return next((c for c in items if c.get('componentCode') == code), {})

def lcsc(code):
    """LCSC product entry, or {} if the product page has no data."""
    req = urllib.request.Request(LCSC + code, headers=HEAD)
    time.sleep(0.25)
    return json.load(urllib.request.urlopen(req, timeout=25)).get('result') or {}

def text(j, l):
    """Model, description and package of a part, for matching against the design."""
    return ' | '.join(str(v) for v in (l.get('productModel'), l.get('productIntroEn'), l.get('encapStandard'), j.get('componentModelEn'), j.get('describe'), j.get('componentSpecificationEn')) if v)
