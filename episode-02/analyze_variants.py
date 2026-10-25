"""python analyze_variants.py [split=dev]   Compares every recorded variant with the baseline on ONE split.
Retrieval (deterministic, by chunk id): hit = all expected chunks handed to the model, recall, MRR; paired sign counts against the baseline with an exact p-value.
Answers (judge, 4 runs): mean per run, question-level majority outcome with a 95% Wilson interval, paired win/loss against the baseline with an exact McNemar p-value.
Also time and cost per question. The sealed test split must only be analysed once, at the end."""
import glob, json, os, sys
from math import comb, sqrt
sys.stdout.reconfigure(encoding='utf-8')
split = sys.argv[1] if len(sys.argv) > 1 else 'dev'
VARDIR = os.getenv('VARDIR', 'qa/v2var')   # qa/large for the large-corpus runs (baseline = base_none there)
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def sign_p(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def runs_from(pattern, key=None):
    out = []
    for f in sorted(glob.glob(pattern)):
        d = json.load(open(f, encoding='utf-8')); k = key or [x for x in d if x != 'config'][0]
        out.append(sorted([r for r in d[k]['rows'] if split == 'all' or r['split'] == split], key=lambda r: r['id']))
    return out
sets = {}
def runs_all(name):
    # 'all' = dev runs followed by test runs of the same variant, run by run (runs 1-4)
    dev, tst = runs_from(VARDIR + '/%s_dev_run*.json' % name), runs_from(VARDIR + '/%s_test_run*.json' % name)
    return [sorted(a + b, key=lambda r: r['id']) for a, b in zip(dev, tst)]
BASE = 'baseline (plain vector, 6 chunks)'
if VARDIR == 'qa/v2var': sets[BASE] = runs_from('qa/v2/plain_vector_k6_run*.json', 'plain_vector_k6')
else: sets[BASE] = []
for f in sorted(glob.glob(VARDIR + '/*_run*.json')):
    name = f.replace('\\', '/').split('/')[-1].rsplit('_run', 1)[0]
    for sp in ('_dev', '_test'):
        if name.endswith(sp): sets.setdefault(name[:-len(sp)], [])
for name in list(sets):
    if name.startswith('baseline'): continue
    sets[name] = runs_all(name) if split == 'all' else runs_from(VARDIR + '/%s_%s_run*.json' % (name, split))
if VARDIR != 'qa/v2var':
    sets[BASE] = sets.pop('base_none') if 'base_none' in sets else []
def info(runs):
    n = len(runs[0]); maj = [sum(r[i]['correct'] for r in runs) * 2 >= len(runs) for i in range(n)]
    hit = [all(e in runs[0][i]['retrieved'] for e in runs[0][i]['expect']) if runs[0][i]['expect'] else None for i in range(n)]
    return maj, hit
base_runs = sets['baseline (plain vector, 6 chunks)']; base_maj, base_hit = info(base_runs); n = len(base_runs[0])
print('split = %s, %d questions (%d answerable)\n' % (split, n, sum(h is not None for h in base_hit)))
for name, runs in sets.items():
    if not runs: continue
    maj, hit = info(runs); idx = [i for i, h in enumerate(hit) if h is not None]; lo, hi = wilson(sum(maj), n)
    rec = sum(sum(e in runs[0][i]['retrieved'] for e in runs[0][i]['expect']) / len(runs[0][i]['expect']) for i in idx) / len(idx)
    mrr = sum((1 / min([runs[0][i]['retrieved'].index(e) + 1 for e in runs[0][i]['expect'] if e in runs[0][i]['retrieved']] or [10 ** 9])) for i in idx) / len(idx)
    per = [sum(x['correct'] for x in r) for r in runs]
    print('%-34s retrieval: hit %2d of %d (%.1f%%)  recall %.1f%%  MRR %.3f | answers per run %s of %d, majority %d (%.1f%%, interval %.0f%% to %.0f%%) | %.1fs  $%.5f' % (
        name, sum(hit[i] for i in idx), len(idx), 100 * sum(hit[i] for i in idx) / len(idx), 100 * rec, mrr, per, n, sum(maj), 100 * sum(maj) / n, 100 * lo, 100 * hi,
        sum(x['seconds'] for r in runs for x in r) / len(runs) / n, sum(x['cost'] for r in runs for x in r) / len(runs) / n))
    if name.startswith('baseline'): continue
    hw = sum(hit[i] and not base_hit[i] for i in idx); hl = sum(base_hit[i] and not hit[i] for i in idx)
    aw = sum(maj[i] and not base_maj[i] for i in range(n)); al = sum(base_maj[i] and not maj[i] for i in range(n))
    print('%-34s   vs baseline  retrieval: %d questions gained, %d lost (exact p = %.3f) | answers: %d gained, %d lost (exact p = %.3f)' % ('', hw, hl, sign_p(hw, hl), aw, al, sign_p(aw, al)))
    lost = [runs[0][i]['id'] for i in idx if base_hit[i] and not hit[i]]; gained = [runs[0][i]['id'] for i in idx if hit[i] and not base_hit[i]]
    print('%-34s   gained: %s | lost: %s' % ('', ','.join(gained) or '-', ','.join(lost) or '-'))
print('\nStill missing in the best variant? Re-run with a different split only at the end; this list is dev only.')
