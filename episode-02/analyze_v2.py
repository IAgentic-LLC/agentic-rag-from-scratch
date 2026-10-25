"""python analyze_v2.py [system ...]   Scores recorded runs in qa/v2/<system>_run*.json.
Retrieval (by chunk id, deterministic, taken from run 1): hit = every expected chunk was handed to the model; recall = share of expected chunks handed over; MRR = 1 / rank of the first expected chunk.
Answers (judge, 4 runs): mean score over runs, run range, and the question-level majority outcome (>= half of the runs correct) with a 95% Wilson interval.
Paired comparison of two systems on the same questions: win/loss counts and an exact McNemar p-value (majority outcomes)."""
import glob, json, sys
from math import comb, sqrt
sys.stdout.reconfigure(encoding='utf-8')
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)
def load(system):
    files = sorted(glob.glob('qa/v2/%s_run*.json' % system)); runs = [json.load(open(f, encoding='utf-8'))[system]['rows'] for f in files]
    return runs
def retrieval(rows):
    hits = rec = mrr = n = 0
    for r in rows:
        if not r['expect']: continue
        n += 1; got = r['retrieved']; found = [e for e in r['expect'] if e in got]
        hits += len(found) == len(r['expect']); rec += len(found) / len(r['expect'])
        ranks = [got.index(e) + 1 for e in r['expect'] if e in got]; mrr += 1 / min(ranks) if ranks else 0
    return hits / n, rec / n, mrr / n, n
def report(system, runs):
    n = len(runs[0]); per_run = [sum(x['correct'] for x in r) for r in runs]
    maj = [sum(r[i]['correct'] for r in runs) * 2 >= len(runs) for i in range(n)]
    lo, hi = wilson(sum(maj), n); h, rc, m, na = retrieval(runs[0])
    print('%-16s runs=%d  answers per run: %s of %d (mean %.1f%%) | majority %d of %d = %.1f%%, 95%% interval %.0f%% to %.0f%%' % (system, len(runs), per_run, n, 100 * sum(per_run) / len(runs) / n, sum(maj), n, 100 * sum(maj) / n, 100 * lo, 100 * hi))
    print('%-16s retrieval on %d answerable: hit %.1f%%  recall %.1f%%  MRR %.3f | avg %.1fs  $%.5f per question' % ('', na, 100 * h, 100 * rc, m, sum(x['seconds'] for r in runs for x in r) / len(runs) / n, sum(x['cost'] for r in runs for x in r) / len(runs) / n))
    for sp in ('dev', 'test'):
        idx = [i for i in range(n) if runs[0][i]['split'] == sp]; print('%-16s   %s split: %d of %d correct by majority' % ('', sp, sum(maj[i] for i in idx), len(idx)))
    return maj
systems = sys.argv[1:] or ['plain_vector_k6', 'plain_hybrid_k6', 'plain_vector_k4']
res = {}
for s in systems:
    runs = load(s)
    if runs: res[s] = (runs, report(s, runs))
names = list(res)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = res[names[i]][1], res[names[j]][1]; wa = sum(x and not y for x, y in zip(a, b)); wb = sum(y and not x for x, y in zip(a, b))
        print('paired %s vs %s: %d only-first right, %d only-second right, exact McNemar p = %.3f' % (names[i], names[j], wa, wb, mcnemar(wa, wb)))
if names:
    runs, maj = res[names[0]]
    print('\nQuestions the first system gets wrong by majority (with tag) and what it retrieved:')
    for i, ok in enumerate(maj):
        if not ok:
            r = runs[0][i]; print('  %s [%s/%s] %s' % (r['id'], r['tag'], r['split'], r['q'][:88])); print('      expected %s | retrieved %s' % (','.join(r['expect']) or '-', ','.join(r['retrieved'])))
