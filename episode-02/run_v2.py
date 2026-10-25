"""python run_v2.py <out.json> <system> [split]   Runs golden_v2.yaml through ONE plain system with the episode 1 method (same judge, same answer model).
systems: plain_vector_k6 | plain_vector_k4 | plain_hybrid_k6.  split: all (default) | dev | test.
Index and documents come from the environment: DOCS_DIR / INDEX_PATH (see run_baselines.sh).  Retrieval scores are computed by id from the recorded rows (analyze_v2.py)."""
import json, sys
from pathlib import Path
import yaml
BACKEND = Path(__file__).resolve().parents[1] / 'backend'
sys.path.insert(0, str(BACKEND)); sys.stdout.reconfigure(encoding='utf-8')
from app import config  # noqa: E402
from app.graph import build_plain_rag  # noqa: E402
from app.models import chat_model, embedder  # noqa: E402
from app.retrieval import HybridIndex  # noqa: E402
from evals.run_evals import evaluate  # noqa: E402

sysname = sys.argv[2]; split = sys.argv[3] if len(sys.argv) > 3 else 'all'
golden = yaml.safe_load(open(Path(__file__).parent / 'golden_v2.yaml', encoding='utf-8'))
if split != 'all': golden = [g for g in golden if g['split'] == split]
index = HybridIndex.load(config.INDEX_PATH, embedder()); chunks = {c.id: c for c in index.chunks}
bad = [e for g in golden for e in g['expect'] if e not in chunks]
assert not bad, 'unknown chunk ids: %s' % bad
chat, judge = chat_model(config.CHAT_MODEL), chat_model(config.JUDGE_MODEL)
modes = {'plain_vector_k6': ('vector', 6), 'plain_vector_k4': ('vector', 4), 'plain_hybrid_k6': ('hybrid', 6)}
mode, k = modes[sysname]
res = evaluate(sysname, build_plain_rag(index, chat, mode=mode, k=k), golden, judge, chunks)
for row, g in zip(res['rows'], golden): row['id'] = g['id']; row['expect'] = g['expect']; row['split'] = g['split']; row['tag'] = g['tag']
out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({sysname: res, 'config': {'chat': config.CHAT_MODEL, 'judge': config.JUDGE_MODEL, 'embed': config.EMBED_MODEL, 'index': str(config.INDEX_PATH.name), 'questions': len(golden)}}, indent=1, ensure_ascii=False), encoding='utf-8')
print('correct %.1f%% untrue %.1f%% %.1fs $%.5f' % (100 * res['correct'], 100 * res['hallucinated'], res['avg_seconds'], res['avg_cost']))
