# Episode 2, large corpus (2026-10-24): where context and reranking matter

Corpus: 123 documents, 486 chunks (the 27 small-corpus documents unchanged plus 96 generated fictional ones: 30 incident postmortems, 25 policy changes, 14 product guides, 15 country delivery guides, 12 drop reports). Questions: 150 (the 64 from the small corpus plus 86 new, every answer key verified against the expected chunks; 106 dev, 44 test by id hash). Plain RAG, vector search, 6 chunks, answers from the original chunk text. Answers Gemini 3.8 flash, judge DeepSeek flash, four judged runs where complete. Variants were fixed before running; nothing was tuned on the results.

## Main result (all 150 questions, 4 runs each): baseline vs the two context fixes
| System | Right chunks all retrieved (of 138 answerable) | Answers right by majority (of 150) | 95% interval | Cost per question | Time |
|---|---|---|---|---|---|
| Baseline: plain vector, 6 chunks | 76 (55.1%) | 94 (62.7%) | 55 to 70% | $0.00167 | 4.6 s |
| Document context on every chunk (no model call) | 116 (84.1%) | 131 (87.3%) | 81 to 92% | $0.00158 | 4.5 s |
| Model-written context on every chunk | 108 (78.3%) | 124 (82.7%) | 76 to 88% | $0.00158 | 4.5 s |
Paired against the baseline: document context gained 39 questions and lost 2 (exact p < 0.001); model-written context gained 33 and lost 3 (exact p < 0.001). One-time cost of the model-written notes: $0.079 for 486 chunks (about $0.00016 per chunk).

## Where the gain comes from (by question type; baseline / document context / model-written)
| Group | n | Baseline | Document ctx | Model-written |
|---|---|---|---|---|
| New "context" questions (the asked-about fact sits in a chunk whose own text does not say which incident, product or drop it is; the date, service or product name is only in the document's first line) | 55 | 3 | 41 | 35 |
| New "easy" and "near-duplicate" questions (names are in the document title) | 25 | 25 | 25 | 25 |
| New "not covered" questions | 6 | 6 | 6 | 6 |
| The 64 questions from the small corpus | 64 | 60 | 59 | 58 |
**All of the improvement is in the 55 questions built to depend on header information.** Nothing else moved; on the 64 old questions the fixes did not help (one or two questions worse, within noise). We must say this plainly: we designed those questions to test exactly this mechanism, so the size of the effect (3 to 41 of 55) shows what is possible when answers hide behind headers, not how often that happens in a real company's documents.

## Why model-written context scored below document context (partly verified)
The helper rewrote the date in words ("January 13, 2026") in 43 of 101 incident sections, while questions use the same format as the documents ("2026-01-13"). Copying the header verbatim keeps the exact tokens. Whether this is the whole reason is not yet tested (an "exact copy" variant, `llmexact`, was prepared but could not be run, see below).

## Reranker (cross-encoder, 20 candidates in, 6 kept): incomplete
Only some runs completed before the answer-model credits ran out (see Blockers). On the 106 dev questions, one run each:
| System | Right chunks all retrieved (of 99) | Mean reciprocal rank | Answers right (of 106) |
|---|---|---|---|
| Baseline (4 runs) | 57 (57.6%) | 0.808 | 67 (63.2%) |
| Reranker only | 56 (56.6%) | 0.851 | 67 (63.2%) |
| Document context, no reranker (4 runs) | 87 (87.9%) | 0.742 | 94 (88.7%) |
| Document context + reranker | 70 (70.7%) | 0.876 | 81 (76.4%) |
| Model-written context, no reranker (4 runs) | 79 (79.8%) | 0.787 | 89 (84.0%) |
| Model-written context + reranker | 75 (75.8%) | 0.837 | 85 (80.2%) |
Reading: on this corpus the reranker alone did not help; adding it on top of the context fixes lowered the number of questions with all needed chunks kept (the reranker sorts the 20 candidates better by rank but keeps only 6, and questions here need two specific chunks, an overview and a body). These are single runs and the test split is incomplete for these variants, so treat them as indicative, not final.

## Blockers and incomplete items
- **Gemini prepaid credits are depleted** (error 402, "prepayment credits are depleted"). Everything that calls the answer or embedding model is stopped. The remaining reranker runs (docctx_ce and llmctx_ce on test; runs 2 to 4 of each) and the extra exact-copy variant need the credits topped up in Google AI Studio (a billing action for the account owner).
- The reranker memory problem (too many parallel torch processes) was fixed by running two at a time.

## Caveats
- Fictional, generated corpus; large effects come from a deliberately header-dependent question set.
- 486 chunks is still small. Nothing here speaks for thousands of documents, other embedding models, or other rerankers.
- Judge not yet hand-calibrated (a 40-item check sheet is ready).
- The reranker rows are single runs.

## Story for the film (honest version)
1. On a small, tidy set of 10 documents, plain search is already good (95%), and none of the clever fixes helped. Be honest about that first.
2. Real document collections are messier: many look alike and the thing that tells them apart sits in a header. Make the library realistic and the same plain search drops to 63%.
3. Two fixes put the header information on every card: copying the document's first line (87%) or asking a helper to write a note on each card (83%). No cost per question; $0.079 once for the helper.
4. A reranker, the popular fix, did not help here; the lesson is to measure and match the fix to the failure.
5. Show where the gain came from (one group of 55 questions) and be clear about what the test does and does not prove.
