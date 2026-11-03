"""Compare a KiCad netlist export with design.py (every pin of every part, net names included).
usage: check_net.py <main|sensor> <file.net>   ->  prints differences, exit 1 if any"""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
board, path = sys.argv[1], sys.argv[2]
t = open(path, encoding='utf-8').read()
got = {}
chunks = re.split(r'\n\s*\(net \(code "\d+"\) ', t)[1:]
for c in chunks:
    name = re.match(r'\(name "([^"]*)"', c).group(1).split('/')[-1]
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"', c):
        got[(ref, pin)] = None if name.startswith('unconnected-') else name
want = {(p['ref'], k): v for p in D.BOARDS[board] for k, v in p['pins'].items()}
# compare connectivity: every design net must be exactly one netlist net (same set of pins); names compared separately
dn, gn = collections.defaultdict(set), collections.defaultdict(set)
for k, v in want.items():
    if v: dn[v].add(k)
for k, v in got.items():
    if v: gn[v].add(k)
gby = {k: v for k, v in got.items() if v}
bad = renamed = 0
for net, pins in sorted(dn.items()):
    names = {gby.get(k, 'MISSING') for k in pins}
    if len(names) != 1 or 'MISSING' in names: print('SPLIT/MISSING', net, sorted(names)); bad += 1; continue
    g = names.pop()
    if gn[g] != pins: print('DIFF', net, 'extra pins in netlist:', sorted(gn[g] - pins)); bad += 1
    elif g != net: renamed += 1
for k, v in want.items():
    if v is None and gby.get(k): print('NC pin connected', k, gby[k]); bad += 1
print(board, 'nets:', len(dn), 'pins:', len(want), '| connectivity differences:', bad, '| nets with KiCad auto names (no label drawn):', renamed)
sys.exit(1 if bad else 0)
