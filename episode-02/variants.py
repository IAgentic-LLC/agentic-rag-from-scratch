"""Episode 2 variants. We change only WHAT IS SEARCHED (the text that is embedded and keyword-indexed), and optionally re-order the top results with a reranker.
The model that writes the answer always reads the original chunk text, so any difference comes from retrieval.

  python variants.py contexts     write data/ctx_doc.json (no model) and data/ctx_llm.json (a small model writes one situating sentence per chunk; cost recorded)
  python variants.py indexes      embed each variant and save data/index_v2_<variant>.json   (variants: docctx, llmctx; the baseline index is data/index_v2.json)
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
EP = Path(__file__).resolve().parent; BACKEND = EP.parent / 'backend'
sys.path.insert(0, str(BACKEND)); sys.stdout.reconfigure(encoding='utf-8')
from app import config  # noqa: E402
from app.corpus import Chunk, load_chunks  # noqa: E402

DATA = EP / os.getenv('EP2_DATA', 'data')   # 'data' = small corpus, 'data_large' = large corpus
LLM_PROMPT = """Here is a whole document:
<document>
{doc}
</document>

Here is one section of it:
<section>
{chunk}
</section>

Write one or two short sentences that place this section inside the whole document: which document it belongs to, what it is about, and any date, status or version that applies to it. The sentences will be added to the section so that a search engine can find it. Reply with only those sentences."""


LLM_PROMPT_EXACT = LLM_PROMPT.replace("Reply with only those sentences.", "Copy every date, number, identifier and name EXACTLY as it is written in the document (for example keep 2026-01-13, never write January 13, 2026). Reply with only those sentences.")


def chunks_by_doc():
    chunks = load_chunks(DATA / 'docs'); docs = {}
    for c in chunks: docs.setdefault(c.doc, []).append(c)
    return chunks, docs


def doc_context(chunks, docs):
    """No model call: copy the document's overview line (owner, review date, status) onto every section of that document."""
    out = {}
    for c in chunks:
        ov = [x for x in docs[c.doc] if x.section == 'Overview']
        out[c.id] = '' if (c.section == 'Overview' or not ov) else 'About this document: ' + ov[0].text.replace('\n', ' ').strip()
    return out


def llm_context(chunks, docs, prompt=None):
    prompt = prompt or LLM_PROMPT
    from langchain_core.callbacks import UsageMetadataCallbackHandler
    from app.graph import text_of
    from app.models import chat_model, cost_usd
    model = chat_model(config.FAST_MODEL); usage = UsageMetadataCallbackHandler(); out = {}
    def one(c):
        full = '\n\n'.join('## %s\n%s' % (x.section, x.text) for x in docs[c.doc]); full = '# %s\n%s' % (c.title, full)
        for attempt in range(3):
            try: return c.id, text_of(model.invoke(prompt.format(doc=full, chunk='## %s\n%s' % (c.section, c.text)), config={'callbacks': [usage]}).content).strip()
            except Exception as e: time.sleep(2 + attempt * 3); err = e
        raise err
    with ThreadPoolExecutor(6) as ex:
        for cid, text in ex.map(one, chunks): out[cid] = text
    return out, {'model': config.FAST_MODEL, 'chunks': len(chunks), 'usd': cost_usd(usage.usage_metadata), 'tokens': usage.usage_metadata}


def patch_search_text(ctx: dict):
    """Make Chunk.for_search include the context sentence(s) in front (affects both the embedding and the keyword index)."""
    def for_search(self):
        pre = ctx.get(self.id, '')
        return (pre + '\n' if pre else '') + f'{self.title} > {self.section}\n{self.text}'
    Chunk.for_search = for_search


def load_variant_index(variant: str, embedder):
    """variant: base | docctx | llmctx  ->  a HybridIndex whose searchable text matches the variant."""
    from app.retrieval import HybridIndex
    if variant == 'base': return HybridIndex.load(DATA / 'index_v2.json', embedder)
    ctx = json.load(open(DATA / {'docctx': 'ctx_doc.json', 'llmctx': 'ctx_llm.json', 'llmexact': 'ctx_llm_exact.json'}[variant], encoding='utf-8'))
    patch_search_text(ctx)
    return HybridIndex.load(DATA / ('index_v2_%s.json' % variant), embedder)


if __name__ == '__main__':
    cmd = sys.argv[1]; chunks, docs = chunks_by_doc()
    if cmd == 'contexts':
        (DATA / 'ctx_doc.json').write_text(json.dumps(doc_context(chunks, docs), indent=1, ensure_ascii=False), encoding='utf-8')
        ctx, meta = llm_context(chunks, docs)
        (DATA / 'ctx_llm.json').write_text(json.dumps(ctx, indent=1, ensure_ascii=False), encoding='utf-8'); (DATA / 'ctx_llm_cost.json').write_text(json.dumps(meta, indent=1, default=str), encoding='utf-8')
        print('contexts written; model-written context cost: $%.5f for %d chunks' % (meta['usd'], meta['chunks']))
    elif cmd == 'contexts_exact':
        ctx, meta = llm_context(chunks, docs, LLM_PROMPT_EXACT)
        (DATA / 'ctx_llm_exact.json').write_text(json.dumps(ctx, indent=1, ensure_ascii=False), encoding='utf-8'); (DATA / 'ctx_llm_exact_cost.json').write_text(json.dumps(meta, indent=1, default=str), encoding='utf-8')
        print('exact-copy contexts written; cost $%.5f for %d chunks' % (meta['usd'], meta['chunks']))
        from app.models import embedder
        from app.retrieval import HybridIndex
        patch_search_text(ctx); HybridIndex.build(chunks, embedder()).save(DATA / 'index_v2_llmexact.json'); print('indexed llmexact', len(chunks))
    elif cmd == 'indexes':
        from app.models import embedder
        from app.retrieval import HybridIndex
        for variant, f in (('docctx', 'ctx_doc.json'), ('llmctx', 'ctx_llm.json')):
            patch_search_text(json.load(open(DATA / f, encoding='utf-8')))
            HybridIndex.build(chunks, embedder()).save(DATA / ('index_v2_%s.json' % variant)); print('indexed', variant, len(chunks))
