"""python build_golden.py   Builds golden_v2.yaml (64 questions) from: the 22 episode 1 questions, the 22 usable hard-probe questions and 20 new ones
written against the grown corpus, adds an answer-key check (`key`: strings that must appear in the expected chunks) and a fixed dev/test split,
then VERIFIES every question against data/docs: expected chunk ids exist, every key string is really in the expected chunks, unanswerable questions expect nothing."""
import hashlib, sys
from pathlib import Path
import yaml
EP = Path(__file__).resolve().parent; BACKEND = EP.parent / 'backend'
sys.path.insert(0, str(BACKEND)); sys.stdout.reconfigure(encoding='utf-8')
from app.corpus import load_chunks  # noqa: E402
chunks = {c.id: c for c in load_chunks(EP / 'data' / 'docs')}

orig = yaml.safe_load(open(BACKEND / 'evals' / 'golden.yaml', encoding='utf-8'))
probe = yaml.safe_load(open(EP / 'golden_probe.yaml', encoding='utf-8'))
orig_keys = [['Air Glide restock', '7-day return window', '14-day'], ['3-D Secure', '10 minutes'], ['5 checkout attempts', '60 seconds'], ['30 days', 'unworn'],
             ['41%', '12 accounts', '7 days'], ['2026-04-01'], ['14-day'], ['40 pods'], ['2%', '#drop-war-room'], ['within 5 minutes'], ['09:50'], ['removed'],
             ['2 to 4 business days'], ['cannot change the delivery address'], ['3,000 requests per second', '18%'], ['100 requests per minute', 'burst of 20'],
             ['90 days'], [], ['do not ship to other countries'], [], [], []]
# probe questions in file order (0-based); dropped: 15 (gift cards, same as episode 1) and 16 (ambiguous wording)
probe_keys = {0: ['30 days'], 1: ['14-day'], 2: ['1 pair per customer'], 3: ['5 business days'], 4: ['#drop-war-room', 'payments on-call'], 5: ['40 pods', '8 pods'],
              6: ['90 days'], 7: ['2026-05-08', 'E-4029'], 8: ['09:50', 'free express delivery'], 9: ['10 GBP'], 10: ['10 minutes', 'team lead'], 11: ['41%', '1,180'],
              12: ['has not been charged'], 13: ['2026-04-01', 'Volt Runner'], 14: ['7-day'], 17: ['cx-policy@dropline.example'], 18: ['Monday at 09:00 CET'],
              19: ['EU countries, the UK and the US'], 20: ['policy change', '2026-04-01'], 21: ['has not been charged'], 22: ['5,000 pairs', '4 minutes'], 23: ['removed']}
probe_tags = {1: 'multi-hop', 5: 'multi-hop', 7: 'context', 9: 'superseded', 13: 'multi-hop', 14: 'multi-hop', 19: 'superseded', 20: 'multi-hop', 22: 'multi-hop'}
new = [
    ('A customer bought regular running shoes on 1 December. What is the last day they can return them?', ['holiday-returns-and-hours#holiday-returns'], '31 January of the next year (holiday extension).', ['31 January', '15 November'], 'near-duplicate'),
    ('Where are covered repairs done and how long do they take?', ['repairs-and-defects#repairs'], 'At the partner workshop in Rotterdam, 10 to 15 business days.', ['Rotterdam', '10 to 15 business days'], 'easy'),
    ('Can a customer swap a limited drop pair for another size?', ['exchanges-and-sizing#size-exchanges'], 'No. Limited drop items cannot be exchanged; they can only be returned inside the drop window.', ['cannot be exchanged'], 'near-duplicate'),
    ('Does Air Glide run big or small?', ['exchanges-and-sizing#sizing-advice'], 'Half a size small; most customers go up half a size.', ['half a size small'], 'easy'),
    ('A customer disputed a payment with their bank. Should I also send them a refund?', ['payments-and-chargebacks#chargebacks'], 'No second refund. Send the order reference to the Payments team within 2 business days.', ['do not issue a second refund', '2 business days'], 'paraphrase'),
    ('How long can a bank take to show a refund after we issue it?', ['payments-and-chargebacks#refund-timing'], 'Up to 10 more business days after we issue it (we issue within 5 business days of the scan).', ['10 more business days'], 'near-duplicate'),
    ('How many returns from drops trigger a fraud review?', ['fraud-and-reseller-controls#account-review'], 'More than 3 drop returns in 90 days.', ['more than 3 drop returns in 90 days'], 'paraphrase'),
    ('Where do I forward a customer who wants a copy of their personal data?', ['data-requests#access-and-export'], 'privacy@dropline.example; agents must not export data themselves; we reply within 30 days.', ['privacy@dropline.example'], 'paraphrase'),
    ('When was version 1 of the partner API shut down, and what do calls to it return now?', ['partner-api-changelog#version-1'], '2026-06-30; HTTP 410.', ['2026-06-30', 'HTTP 410'], 'context'),
    ('What request rate did the old version 1 of the partner API allow?', ['partner-api-changelog#version-1'], '60 requests per minute with no burst (the current limit is 100 per minute).', ['60 requests per minute'], 'near-duplicate'),
    ('After a SEV-1 page, how soon must the first status update go out and how often after that?', ['status-and-incident-comms#sev-1-updates'], 'Within 15 minutes, then every 30 minutes until resolved.', ['within 15 minutes', 'every 30 minutes'], 'near-duplicate'),
    ('Why were about 2,400 EU parcels late in July?', ['inc-2052-postmortem#what-happened'], 'A carrier hub in Cologne closed for 3 days after a strike.', ['Cologne', '2,400'], 'context'),
    ('What went wrong with the size chart in the April Air Glide order email?', ['inc-2049-postmortem#what-happened'], 'European sizes were shown under US labels for 2 hours; 1,900 customers saw it.', ['1,900 customers'], 'context'),
    ('How many points make a member Gold, and do points ever expire?', ['drop-club-tiers#gold-tier', 'drop-club-tiers#points-expiry'], '2,000 points; yes, 12 months after they were earned.', ['2,000 points', '12 months'], 'multi-hop'),
    ('When is the next Volt Runner drop and how many pairs?', ['drop-calendar-h2-2026#upcoming-drops'], 'Friday 2026-11-06 at 10:00, 4,000 pairs.', ['2026-11-06', '4,000 pairs'], 'easy'),
    ('If a customer tried the shoes on indoors, can they still return them?', ['product-care#returns'], 'Yes. Trying on indoors is fine; pairs worn outdoors are refused.', ['Trying a pair on indoors'], 'paraphrase'),
    ('Do we offer gift wrapping?', [], 'Not covered by the documents.', [], 'unanswerable'),
    ('How much does the Trail Glide cost?', [], 'Not covered by the documents (only its drop date and size are listed).', [], 'unanswerable'),
    ('How many days do defective items have for a refund under the current policy?', ['refund-policy#exceptions'], '90 days (the archived policy said 60).', ['90 days'], 'superseded'),
    ('What return window did limited drops have before PC-12?', ['refund-policy#limited-drops'], 'The standard 30-day window.', ['Before PC-12'], 'superseded'),
]
out = []
def add(qid, q, expect, facts, key, answerable, hops=None, tag='regression'):
    d = {'id': qid, 'q': q, 'expect': expect, 'facts': facts, 'key': key, 'answerable': answerable, 'tag': tag}
    if hops: d['hops'] = hops
    out.append(d)
for i, g in enumerate(orig): add('o%02d' % (i + 1), g['q'], g['expect'], g['facts'], orig_keys[i], g['answerable'], g.get('hops'), 'regression')
for i, g in enumerate(probe):
    if i in (15, 16): continue
    exp = list(g['expect'])
    if i == 7: exp = ['inc-2051-postmortem#overview', 'inc-2051-postmortem#fixes']
    add('p%02d' % (i + 1), g['q'], exp, g['facts'], probe_keys[i], g['answerable'], g.get('hops'), probe_tags.get(i, 'paraphrase'))
for i, (q, exp, facts, key, tag) in enumerate(new): add('n%02d' % (i + 1), q, exp, facts, key, bool(exp), None, tag)
for d in out:
    d['split'] = 'test' if int(hashlib.sha1(d['id'].encode()).hexdigest(), 16) % 10 < 3 else 'dev'

problems = []
for d in out:
    for e in d['expect']:
        if e not in chunks: problems.append((d['id'], 'unknown chunk', e))
    blob = ' '.join(chunks[e].text for e in d['expect'] if e in chunks).lower()
    for k in d['key']:
        if k.lower() not in blob: problems.append((d['id'], 'key not in expected chunks', k))
    if d['answerable'] and not d['expect']: problems.append((d['id'], 'answerable but no expected chunks', ''))
    if not d['answerable'] and (d['expect'] or d['key']): problems.append((d['id'], 'unanswerable but has expect/key', ''))
ids = [d['id'] for d in out]; assert len(ids) == len(set(ids))
(EP / 'golden_v2.yaml').write_text('# Episode 2 golden set. Built by build_golden.py, verified against data/docs. split: dev (we may look at failures) / test (fixed, never tuned on).\n' + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=200), encoding='utf-8')
import collections
print('questions:', len(out), '| chunks in corpus:', len(chunks), 'from', len({c.doc for c in chunks.values()}), 'documents')
print('split:', dict(collections.Counter(d['split'] for d in out)), '| answerable:', sum(d['answerable'] for d in out), '| unanswerable:', sum(not d['answerable'] for d in out))
print('tags:', dict(collections.Counter(d['tag'] for d in out)))
print('PROBLEMS:', len(problems)); [print('  ', p) for p in problems]
