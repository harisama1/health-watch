"""Compare a KiCad netlist export with design.py: connectivity of every pin, net names, and each part's value + footprint.
Handles the netlist layouts of KiCad 9 and 10 (whitespace differs).
usage: check_net.py <main|sensor> <file.net>   ->  prints differences, exit 1 if any"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
board, path = sys.argv[1], sys.argv[2]
t = open(path, encoding='utf-8').read()
nets = collections.defaultdict(set)    # full netlist name -> pins (a label left local to one sheet stays a separate net)
for c in re.split(r'\(net\s+\(code "\d+"\)\s+', t)[1:]:
    name = re.match(r'\(name "([^"]*)"', c).group(1)
    for ref, pin in re.findall(r'\(node\s+\(ref "([^"]+)"\)\s+\(pin "([^"]+)"', c):
        nets[name].add((ref, pin))
unconnected = {k for n, s in nets.items() if n.startswith('unconnected-') for k in s}
nets = {n: s for n, s in nets.items() if not n.startswith('unconnected-')}
where = {k: n for n, s in nets.items() for k in s}
want = {(p['ref'], k): v for p in D.BOARDS[board] for k, v in p['pins'].items()}
dn = collections.defaultdict(set)
for k, v in want.items():
    if v: dn[v].add(k)
bad = auto = 0
for net, pins in sorted(dn.items()):
    names = {where.get(k, 'MISSING') for k in pins}
    if len(names) != 1 or 'MISSING' in names: print('SPLIT/MISSING', net, sorted(names)); bad += 1; continue
    g = names.pop()
    if nets[g] != pins: print('DIFF', net, 'extra pins in netlist:', sorted(nets[g] - pins)); bad += 1
    elif g.startswith('Net-('): auto += 1        # short local wire with no drawn label: KiCad names it after a pin
    elif g.split('/')[-1] != net: print('NAME', net, 'is called', g); bad += 1
for k, v in want.items():
    if v is None and k in where: print('NC pin connected', k, where[k]); bad += 1
for k in set(where) - set(want): print('pin not in design', k, where[k]); bad += 1
for k in unconnected - set(want): print('pin not in design', k, 'unconnected'); bad += 1
comps = {m.group(1): m.group(2) for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)(?=\(comp\s+\(ref |\(libparts|\Z)', t, re.S)}
for p in D.BOARDS[board]:
    typ = D.P[p['typ']]
    c = comps.get(p['ref'])
    if c is None: print('part missing', p['ref']); bad += 1; continue
    for field, expect in (('value', typ[1]), ('footprint', typ[2])):
        m = re.search(r'\(%s "([^"]*)"' % field, c)
        if not m or m.group(1) != expect: print('PART', p['ref'], field, repr(m and m.group(1)), 'expected', repr(expect)); bad += 1
for r in set(comps) - {p['ref'] for p in D.BOARDS[board]}: print('part not in design', r); bad += 1
print(board, 'nets:', len(dn), 'pins:', len(want), 'parts:', len(comps), '| differences:', bad, '| nets with KiCad auto names (no label drawn):', auto)
sys.exit(1 if bad else 0)
