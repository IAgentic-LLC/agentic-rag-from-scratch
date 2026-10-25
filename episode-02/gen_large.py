"""python gen_large.py   Builds the LARGE corpus (data_large/docs) and its question set (golden_large.yaml).
The 27 documents of the small corpus are copied unchanged; about 95 more are generated from fixed fact tables with a seeded random generator, so every
answer is known exactly. The documents are deliberately like real company files: many look alike, and the facts that tell them apart (date, service, product)
often sit only in the overview line, not in the section text.  Everything is fictional.
Then it VERIFIES: every question's key strings appear in its expected chunks, expected ids exist, ids are unique."""
import hashlib, random, shutil, sys
from pathlib import Path
import yaml
EP = Path(__file__).resolve().parent; BACKEND = EP.parent / 'backend'
sys.path.insert(0, str(BACKEND)); sys.stdout.reconfigure(encoding='utf-8')
from app.corpus import load_chunks, slug  # noqa: E402
R = random.Random(2026)
OUT = EP / 'data_large' / 'docs'
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for f in (EP / 'data' / 'docs').glob('*.md'): shutil.copy(f, OUT / f.name)
questions = []   # (q, expect, facts, key, tag)
def write(stem, text): (OUT / (stem + '.md')).write_text(text.strip() + '\n', encoding='utf-8')
def dates(n, start=(2026, 1, 6), step=(5, 8)):
    import datetime as dt
    d = dt.date(*start); out = []
    for _ in range(n): d += dt.timedelta(days=R.randint(*step)); out.append(d.isoformat())
    return out
def pick(xs): return xs[R.randrange(len(xs))]

# ---- 1. incident postmortems: the date and the service live ONLY in the overview line -----------------------------
SERVICES = ['checkout', 'search', 'payments', 'inventory', 'waiting room', 'order emails', 'image delivery', 'login', 'order tracking', 'returns portal', 'admin panel', 'partner API']
CAUSES = [('an expired security certificate', 'Certificates now raise an alert 30 days before they expire.'),
          ('a database failover that took too long', 'The failover timeout was cut from 90 seconds to 20 seconds.'),
          ('a configuration change that was pushed to every server at once', 'Configuration changes now roll out to 10% of servers first.'),
          ('a memory leak introduced by a release', 'The release was rolled back and a memory alert was added.'),
          ('a message queue that filled up', 'The queue now has a size alert and a second consumer.'),
          ('an outage at a third-party provider', 'A fallback provider was added.'),
          ('a cache that was cleared by mistake', 'Cache clearing now needs a second person to approve it.'),
          ('a runaway nightly job', 'The job now has a time limit and runs on its own machines.')]
TEAMS = ['Platform', 'Payments', 'Growth', 'Logistics', 'CX and Fraud']
inc_dates = dates(30, (2026, 1, 3), (4, 9)); used = set()
for i, d in enumerate(inc_dates):
    num = 2060 + i; svc = SERVICES[i % len(SERVICES)] if i < 24 else pick(SERVICES)
    cause, fix = CAUSES[(i * 3 + R.randrange(2)) % len(CAUSES)]; sev = pick(['SEV-1', 'SEV-2', 'SEV-2', 'SEV-3']); team = pick(TEAMS)
    mins = R.choice([12, 18, 25, 33, 41, 55, 64, 78, 95, 120, 140, 185]); users = R.choice([240, 410, 650, 980, 1400, 2300, 3100, 5200])
    stem = 'inc-%d-postmortem' % num
    write(stem, f"""# Postmortem INC-{num}
Date: {d}. Severity: {sev}. Owner: {team}. Service: {svc}.

## What happened
The incident was caused by {cause}. It lasted {mins} minutes.

## Impact
About {users:,} customers were affected.

## Fixes
{fix}""")
    qa = (svc, d, cause, mins, users, fix, stem)
    if i < 20: questions.append((f"What caused the {svc} incident on {d}?", [f'{stem}#overview', f'{stem}#what-happened'], f"It was caused by {cause}.", [cause], 'context'))
    if 20 <= i < 26: questions.append((f"How long did the {svc} incident on {d} last?", [f'{stem}#overview', f'{stem}#what-happened'], f"{mins} minutes.", [f'{mins} minutes'], 'context'))
    if 26 <= i < 30: questions.append((f"About how many customers were affected by the {svc} incident on {d}?", [f'{stem}#overview', f'{stem}#impact'], f"About {users:,} customers.", [f'{users:,} customers'], 'context'))
    if i in (3, 9, 15): questions.append((f"What was done to prevent a repeat of the {svc} incident on {d}?", [f'{stem}#overview', f'{stem}#fixes'], fix, [fix.split('.')[0]], 'context'))
    if i in (5, 17): questions.append((f"What did the postmortem for INC-{num} say caused the incident?", [f'{stem}#what-happened'], f"{cause}.", [cause], 'easy'))

# ---- 2. policy change notices: the effective date lives only in the overview line ---------------------------------
PC_TOPICS = [('The waiting room now admits customers in batches of {a} instead of {b}.', 'batches of {a}'), ('The warehouse scan cut-off moved from {b}:00 to {a}:00 CET.', '{a}:00 CET'),
             ('Order confirmation emails now show up to {a} items instead of {b}.', 'up to {a} items'), ('Product pages now show {a} photos instead of {b}.', '{a} photos'),
             ('Support chat now offers {a} saved replies instead of {b}.', '{a} saved replies'), ('Packing slips are now printed in {a} languages instead of {b}.', '{a} languages'),
             ('Invoices are now numbered with {a} digits instead of {b}.', '{a} digits'), ('The customer survey now goes out {a} days after delivery instead of {b}.', '{a} days after delivery')]
pc_nums = [n for n in range(1, 27) if n != 12]; pc_dates = dates(len(pc_nums), (2025, 9, 1), (9, 17))
for k, (n, d) in enumerate(zip(pc_nums, pc_dates)):
    tpl, short = PC_TOPICS[k % len(PC_TOPICS)]; b = R.randint(2, 9) * 10 if 'batches' in tpl or 'photos' in tpl else R.randint(3, 7); a = b + R.choice([2, 3, 4, 5]) * (10 if b >= 20 else 1)
    if 'CET' in tpl: b = R.choice([15, 16, 17]); a = b + R.choice([1, 2])
    owner = pick(TEAMS); stem = 'policy-change-pc-%d' % n; what = tpl.format(a=a, b=b); key = short.format(a=a, b=b)
    write(stem, f"""# Policy Change PC-{n}
Effective: {d}. Owner: {owner}.

## What changed
{what}

## Why
The change was agreed after a review by {owner}.

## Who is affected
Everyone who works with the affected process.""")
    if k < 8: questions.append((f"What changed in the policy change that took effect on {d}?", [f'{stem}#overview', f'{stem}#what-changed'], what, [key], 'context'))
    if k in (9, 14, 19, 22): questions.append((f"What did policy change PC-{n} change?", [f'{stem}#what-changed'], what, [key], 'easy'))

# ---- 3. product guides: the product name lives only in the overview line ------------------------------------------
PRODUCTS = [('Air Glide', 'runs half a size small', 'train'), ('Volt Runner', 'fits true to size', 'train')] + [(n, pick(['runs half a size small', 'fits true to size', 'runs half a size large']), pick(['train', 'trail', 'casual'])) for n in
            ['Trail Glide', 'Cloud Rider', 'Sky Court', 'Terra Lite', 'Swift Loop', 'Dune Walker', 'Harbor Slip', 'Pulse Mid', 'Ridge Pro', 'Echo Low', 'Nova Step', 'Fjord Boot']]
for i, (name, fit, cat) in enumerate(PRODUCTS):
    hours = R.choice([6, 8, 10, 12, 18, 24]); mat = pick(['recycled mesh', 'knit fabric', 'suede', 'coated canvas', 'leather']); sole = pick(['foam', 'rubber', 'cork blend', 'recycled rubber'])
    stem = 'product-guide-' + slug(name)
    write(stem, f"""# Product Guide
Product: {name}. Category: {cat}. Owner: Product.

## Fit
This model {fit}.

## Materials
The upper is {mat} and the sole is {sole}.

## Care
Spot clean and let the pair air dry for {hours} hours away from heat.""")
    if i not in (0, 1):   # Air Glide / Volt Runner fit already asked in the small corpus
        if i < 9: questions.append((f"How does the {name} fit?", [f'{stem}#overview', f'{stem}#fit'], f"It {fit}.", [fit], 'context'))
        elif i < 12: questions.append((f"How long should the {name} air dry after cleaning?", [f'{stem}#overview', f'{stem}#care'], f"{hours} hours.", [f'{hours} hours'], 'context'))
        else: questions.append((f"What is the {name} upper made of?", [f'{stem}#overview', f'{stem}#materials'], f"{mat}.", [mat], 'context'))

# ---- 4. delivery guides per country: the country is in the title (a control: context should not matter here) ------
COUNTRIES = ['Austria', 'Belgium', 'Croatia', 'Czechia', 'Denmark', 'Finland', 'France', 'Germany', 'Ireland', 'Italy', 'Netherlands', 'Poland', 'Portugal', 'Spain', 'Sweden']
for i, c in enumerate(COUNTRIES):
    days = R.choice([3, 4, 5]); pts = R.randint(40, 900); cust = pick(['no customs forms', 'no customs forms but a local tax number on large orders'])
    stem = 'delivery-guide-' + slug(c)
    write(stem, f"""# Delivery Guide: {c}
Owner: Logistics. Region: EU.

## Delivery times
Standard parcels usually arrive in {days} business days.

## Return points
There are {pts} partner return points in {c}.

## Customs
Parcels need {cust}.""")
    if i < 8: questions.append((f"How many partner return points are there in {c}?", [f'{stem}#return-points'], f"{pts} partner return points.", [f'{pts} partner return points'], 'near-duplicate'))
    if i in (9, 11, 13): questions.append((f"How many business days does a standard parcel to {c} usually take?", [f'{stem}#delivery-times'], f"{days} business days.", [f'{days} business days'], 'near-duplicate'))

# ---- 5. drop reports: the drop date lives only in the overview line -------------------------------------------------
DROPS = ['Cloud Rider', 'Sky Court', 'Terra Lite', 'Swift Loop', 'Dune Walker', 'Harbor Slip', 'Pulse Mid', 'Ridge Pro', 'Echo Low', 'Nova Step', 'Fjord Boot', 'Trail Glide Mini']
drop_dates = [d for d in dates(12, (2025, 4, 4), (14, 21)) if d not in ('2026-03-13', '2026-05-08', '2026-10-16', '2026-11-06', '2026-12-04')]
for i, name in enumerate(DROPS):
    d = drop_dates[i]; pairs = R.choice([1500, 2000, 2500, 3000, 3500, 4000]); mins = R.choice([3, 5, 7, 9, 12, 16, 22]); peak = R.choice([900, 1400, 1800, 2200, 2600])
    stem = 'drop-report-' + slug(name)
    write(stem, f"""# Drop Report: {name}
Drop date: {d}. Pairs: {pairs:,}. Owner: Growth.

## Results
The drop sold out in {mins} minutes.

## Traffic
Traffic peaked at {peak:,} requests per second.""")
    if i < 5: questions.append((f"How fast did the {name} drop sell out?", [f'{stem}#results'], f"{mins} minutes.", [f'{mins} minutes'], 'near-duplicate'))
    if 5 <= i < 8: questions.append((f"How many pairs were released in the {name} drop?", [f'{stem}#overview'], f"{pairs:,} pairs.", [f'{pairs:,}'], 'easy'))
    if 8 <= i < 10: questions.append((f"What was the peak traffic of the drop on {d}?", [f'{stem}#overview', f'{stem}#traffic'], f"{peak:,} requests per second.", [f'{peak:,} requests per second'], 'context'))

# ---- 6. not covered ----------------------------------------------------------------------------------------------------
for q in ["What caused the incident on 2026-02-30?", "How does the Glacier High fit?", "How many partner return points are there in Norway?", "What did policy change PC-99 change?",
          "How fast did the Aurora Max drop sell out?", "Which team owns the sitemap service?"]:
    questions.append((q, [], 'Not covered by the documents.', [], 'unanswerable'))

# ---- build the golden file ---------------------------------------------------------------------------------------------
chunks = {c.id: c for c in load_chunks(OUT)}
out = []
for i, (q, expect, facts, key, tag) in enumerate(questions):
    qid = 'L%03d' % (i + 1)
    out.append({'id': qid, 'q': q, 'expect': expect, 'facts': facts, 'key': key, 'answerable': bool(expect), 'tag': tag,
                'split': 'test' if int(hashlib.sha1(qid.encode()).hexdigest(), 16) % 10 < 3 else 'dev'})
problems = []
for d in out:
    for e in d['expect']:
        if e not in chunks: problems.append((d['id'], 'unknown chunk', e))
    blob = ' '.join(chunks[e].text for e in d['expect'] if e in chunks).lower()
    for k in d['key']:
        if k.lower() not in blob: problems.append((d['id'], 'key not in expected chunks', k))
# the question text must NOT contain the unique answer (a leak would make the test trivial)
for d in out:
    for k in d['key']:
        if d['answerable'] and k.lower() in d['q'].lower(): problems.append((d['id'], 'answer inside question', k))
dup = [q for q in {d['q'] for d in out} if sum(x['q'] == q for x in out) > 1]; problems += [('dup', 'duplicate question', q) for q in dup]
(EP / 'golden_large.yaml').write_text('# Large-corpus questions (generated, verified against data_large/docs). Old 64 questions are in golden_v2.yaml and also apply to this corpus.\n' + yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=200), encoding='utf-8')
import collections
print('documents:', len({c.doc for c in chunks.values()}), '| chunks:', len(chunks), '| new questions:', len(out))
print('split:', dict(collections.Counter(d['split'] for d in out)), '| tags:', dict(collections.Counter(d['tag'] for d in out)))
print('PROBLEMS:', len(problems)); [print('  ', p) for p in problems[:30]]
