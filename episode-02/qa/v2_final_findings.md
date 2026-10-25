# Episode 2 final results (2026-10-24): contextual chunks and reranking on the grown corpus

Setup: 27 documents, 114 chunks; 64 golden questions (58 answerable, 6 not covered); plain RAG with vector search, 6 chunks handed to the answer model (Gemini 3.8 flash), judge DeepSeek flash, four judged runs per system. Variants fixed before any result was seen: (a) document context (the document's owner, review date and status copied onto each chunk before indexing; no model call), (b) model-written context (Gemini 3.5 flash-lite writes one or two situating sentences per chunk from the whole document; one-time cost $0.023 for 114 chunks), each with and without a cross-encoder reranker (cross-encoder/ms-marco-MiniLM-L6-v2, CPU, 20 candidates retrieved, best 6 kept). The answer model always reads the original chunk text. Variants were scored first on the 45 dev questions; the 19 sealed test questions were scored once, after the variants were fixed. Pooled table below is all 64.

| System | Right chunks all retrieved (of 58) | Recall | MRR | Answers right by majority (of 64) | 95% interval | Time per question |
|---|---|---|---|---|---|---|
| Baseline: vector, 6 chunks | 49 (84.5%) | 89.1% | 0.779 | 61 (95.3%) | 87 to 98% | 4.5 s |
| Document context | 48 (82.8%) | 85.9% | 0.750 | 61 (95.3%) | 87 to 98% | 4.8 s |
| Model-written context | 48 (82.8%) | 85.9% | 0.727 | 60 (93.8%) | 85 to 98% | 4.8 s |
| Reranker only | 49 (84.5%) | 88.2% | 0.807 | 59 (92.2%) | 83 to 97% | 5.4 s |
| Document context + reranker | 49 (84.5%) | 89.1% | 0.825 | 58 (90.6%) | 81 to 96% | 5.6 s |
| Model-written context + reranker | 50 (86.2%) | 90.8% | 0.830 | 58 (90.6%) | 81 to 96% | 5.7 s |

Paired against the baseline (same questions), every comparison is inside noise: retrieval gained and lost 1 to 3 questions each way (exact p = 1.0); answers differ by 1 to 4 questions (exact p between 0.375 and 1.0).

## What we can say
1. **None of the three fixes beat plain vector search with six chunks on this corpus.** The differences are a few questions out of 64, not distinguishable from luck.
2. **Rerankers moved the right chunk up the list** (MRR 0.78 to 0.81-0.83) and rescued two of the three hard questions at the retrieval level (the incident date, "what does PC stand for?"), but each reranked variant also lost two or three other questions (UK defect window p07, EU Berlin p02, o07), so the net count of fully-retrieved questions is unchanged. They cost about 0.9 to 1.2 seconds more per question on CPU.
3. **Adding context to the searched text did not help retrieval without a reranker** (hit 83% vs 84.5%, MRR slightly lower). One plausible reason (not tested) is that every chunk of a document now shares the same label, so chunks of one document look more alike to the search. Do not state it as the cause.
4. **Answer accuracy was 90.6 to 95.3% for every variant**, with the baseline highest; the interval of each overlaps all the others.
5. **Cost:** model-written context is a one-time $0.023 for 114 chunks (about $0.0002 per chunk); no per-question cost change. Reranking adds latency only (no API cost when run locally).

## What we cannot say
- That these techniques "don't work": they were tested on a 114-chunk fictional corpus where plain search already reaches about 85% full retrieval and 95% answers. Published results (Anthropic's contextual retrieval write-up; independent tests) use larger corpora and different measures; ours does not contradict them.
- Anything about larger corpora, other embedding models, other rerankers (a larger or hosted reranker was not tried), other chunk sizes, or hybrid search combined with these fixes.
- That any variant is worse: differences are within noise.
- That the judge is perfectly reliable: the hand-labelled calibration sample (30 to 50 verdicts) has not been done yet.

## Honest story for the film
"We tried the two ideas the industry recommends. On our small, tidy corpus neither moved the needle, and here is how we know: a scoreboard with ranges and win/loss counts. The reranker did fix two of the hard questions and break three others. Here is when you should expect them to matter (bigger, messier collections), and how you would find out for your own data." The lesson for beginners is the method: build an answer key, measure retrieval separately from answers, compare one change at a time, and show the uncertainty.

## Next steps (not done yet)
1. Hand-label a sample of judge verdicts (30 to 50) and report agreement.
2. Optional extension that matches the published claims: a much larger corpus (hundreds to thousands of chunks) so retrieval failures become common, then re-run the same variants. This would be the honest test of "do these help at scale", and could be the second half of the episode or its own episode.
3. Write the treatment and decide one film or two.
