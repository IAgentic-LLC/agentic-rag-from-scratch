"""python run_variant.py <out.json> <variant> <rerank> [split]
variant: base | docctx | llmctx      rerank: none | ce  (ce = cross-encoder ms-marco-MiniLM-L6-v2, 20 candidates in, 6 out)      split: dev (default) | test | all
Plain RAG, vector search, answers from the ORIGINAL chunk text; same answer model, judge and method as episode 1. Needs GOOGLE_API_KEY and DEEPSEEK_API_KEY in the environment."""
import json, os, sys, time
from pathlib import Path
import yaml
EP = Path(__file__).resolve().parent; BACKEND = EP.parent / 'backend'
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(EP)); sys.stdout.reconfigure(encoding='utf-8')
from langgraph.graph import END, START, StateGraph  # noqa: E402
from app import config, prompts  # noqa: E402
from app.graph import AgentState, announce, citations_in, numbered, text_of  # noqa: E402
from app.models import chat_model, embedder  # noqa: E402
from evals.run_evals import evaluate  # noqa: E402
import variants  # noqa: E402

out_path, variant, rerank = Path(sys.argv[1]), sys.argv[2], sys.argv[3]; split = sys.argv[4] if len(sys.argv) > 4 else 'dev'
N_IN, K_OUT = 20, 6
golden = [g for f in os.getenv('GOLDEN_FILES', 'golden_v2.yaml').split(',') for g in yaml.safe_load(open(EP / f, encoding='utf-8'))]   # GOLDEN_FILES: comma list
if split != 'all': golden = [g for g in golden if g['split'] == split]
index = variants.load_variant_index(variant, embedder()); chunks = {c.id: c for c in index.chunks}
chat, judge = chat_model(config.CHAT_MODEL), chat_model(config.JUDGE_MODEL)
ce = None
if rerank == 'ce':
    from sentence_transformers import CrossEncoder
    ce = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2', device='cpu')

def build():
    def plain(state: AgentState) -> AgentState:
        q = state['question']; announce('plain_retrieve', query=q)
        if ce is None: docs = index.search(q, k=K_OUT, mode='vector')
        else:
            cand = index.search(q, k=N_IN, mode='vector')
            scores = ce.predict([(q, chunks[d['id']].for_search()) for d in cand])   # the reranker reads what the index reads
            docs = [d for _, d in sorted(zip(scores, cand), key=lambda t: -t[0])][:K_OUT]
        announce('plain_generate')
        answer = text_of(chat.invoke(prompts.PLAIN.format(question=q, sources=numbered(docs))).content)
        return {'docs': docs, 'relevant': docs, 'answer': answer, 'citations': citations_in(answer, docs), 'outcome': 'answered'}
    g = StateGraph(AgentState); g.add_node('plain', plain); g.add_edge(START, 'plain'); g.add_edge('plain', END); return g.compile()

name = '%s_%s' % (variant, rerank)
res = evaluate(name, build(), golden, judge, chunks)
for row, g in zip(res['rows'], golden): row['id'] = g['id']; row['expect'] = g['expect']; row['split'] = g['split']; row['tag'] = g['tag']
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps({name: res, 'config': {'chat': config.CHAT_MODEL, 'judge': config.JUDGE_MODEL, 'embed': config.EMBED_MODEL, 'variant': variant, 'rerank': rerank, 'candidates_in': N_IN if ce else None, 'k_out': K_OUT, 'questions': len(golden)}}, indent=1, ensure_ascii=False), encoding='utf-8')
print('correct %.1f%% untrue %.1f%% %.1fs $%.5f' % (100 * res['correct'], 100 * res['hallucinated'], res['avg_seconds'], res['avg_cost']))
