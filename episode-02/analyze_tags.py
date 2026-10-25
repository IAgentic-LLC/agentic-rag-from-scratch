"""python analyze_tags.py [vardir=qa/large]   Breaks the large-corpus results down by question tag and by question source (old 64 vs 86 new), so we can see WHERE a variant helps.
For each variant: share of questions answered right by majority and share with every expected chunk retrieved (run 1). Exact paired sign p-values are in analyze_variants.py."""
import collections, glob, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
VARDIR = sys.argv[1] if len(sys.argv) > 1 else 'qa/large'
def load(name):
    out = []
    for sp in ('dev', 'test'):
        files = sorted(glob.glob('%s/%s_%s_run*.json' % (VARDIR, name, sp)))
        for i, f in enumerate(files):
            d = json.load(open(f, encoding='utf-8')); rows = d[[k for k in d if k != 'config'][0]]['rows']
            while len(out) <= i: out.append([])
            out[i] += rows
    return [sorted(r, key=lambda x: x['id']) for r in out if r]
variants = [n for n in ['base_none', 'docctx_none', 'llmctx_none', 'base_ce', 'docctx_ce', 'llmctx_ce'] if load(n)]
data = {n: load(n) for n in variants}
def group(r):
    return ('old64 ' if not r['id'].startswith('L') else 'new86 ') + r['tag']
ids = [r['id'] for r in data['base_none'][0]]
data = {v: [r for r in runs if len(r) == len(ids)] for v, runs in data.items()}
variants = [v for v in variants if data[v]]
print('%-24s %4s | ' % ('group', 'n') + ' | '.join('%-13s' % v for v in variants))
groups = collections.OrderedDict()
for i, r in enumerate(data['base_none'][0]): groups.setdefault(group(r), []).append(i)
groups['ALL'] = list(range(len(ids)))
for g, idx in groups.items():
    cells = []
    for v in variants:
        runs = data[v]
        ok = sum(sum(rr[i]['correct'] for rr in runs) * 2 >= len(runs) for i in idx)
        ans = [i for i in idx if runs[0][i]['expect']]
        hit = sum(all(e in runs[0][i]['retrieved'] for e in runs[0][i]['expect']) for i in ans)
        cells.append('ans %2d/%2d ret %2d/%2d' % (ok, len(idx), hit, len(ans)))
    print('%-24s %4d | ' % (g, len(idx)) + ' | '.join('%-13s' % c for c in cells))
print('\nruns per variant:', {v: len(data[v]) for v in variants})
