# Episode 2 baseline on the grown corpus (2026-10-24)

Corpus: 27 documents, 114 chunks (the original 10 documents unchanged plus 17 new, including archived old policies, repeated headings, dates only in overviews).
Questions: 64 (`golden_v2.yaml`): 22 episode 1 questions (regression), 22 harder probe questions, 20 new. 58 answerable, 6 not covered. Split fixed by id hash: 45 dev, 19 test.
Models: answers Gemini 3.8 flash, judge DeepSeek flash, embeddings gemini-embedding-001, four judged runs per system (plain vector k=4 has one run).

## Answers (judge), questions wrong by majority vote of four runs
| System | Mean per run | Majority correct | 95% interval | Test split |
|---|---|---|---|---|
| Plain, vector, 6 chunks | 94.1% | 61 of 64 (95.3%) | 87% to 98% | 17 of 19 |
| Plain, hybrid, 6 chunks | 90.6% | 58 of 64 (90.6%) | 81% to 96% | 16 of 19 |
| Plain, vector, 4 chunks (1 run) | 90.6% | 58 of 64 | 81% to 96% | 15 of 19 |

Paired comparisons (same questions): vector k=6 vs hybrid k=6: 4 vs 1, exact McNemar p = 0.375; vector k=6 vs k=4: 3 vs 0, p = 0.25. None of these differences is distinguishable from luck at 64 questions.

## Retrieval (by chunk id, deterministic)
Vector k=6: every expected chunk handed to the model for 84.5% of the 58 answerable questions (49 of 58); recall 89.1%; MRR 0.779. Hybrid k=6: 84.5% / 88.2% / 0.783. Vector k=4: 81.0% / 85.1% / 0.773.
Nine questions miss at least one expected chunk (vector k=6): four originals, one paraphrase, one context, two multi-hop, one superseded.

## What this tells us
1. **Answer accuracy is close to its ceiling (about 95%); retrieval is not (about 85%).** The retrieval measure is where a better search can show a difference; the answer score is too blunt to see small gains at 64 questions (smallest detectable gap is large, see C_evaluation_methods).
2. **Some answers are right for the wrong reason.** o04 ("normal return window") misses the current standard-returns chunk but is still judged correct in 3 of 4 runs because the archived policy and other chunks also say 30 days. The judge sees only the expected evidence and the answer, so a stale source can pass. We should show this on camera and report retrieval separately.
3. **Growing the corpus did hurt the original questions' retrieval** (o01, o04, o05, o06 now miss an expected chunk), while their answers mostly survived.
4. **Three questions fail by answer in every run**: p08 (date lives only in the overview chunk), p14 (needs the drop calendar for two facts), p21 (PC-12 definition needs the glossary and the policy chunk; the new drop calendar's "Rules" chunk outranks the policy). These are the headline examples for contextual chunks and reranking.
5. **Hybrid did not beat vector here either**, within noise (consistent with episode 1 and with the independent reports in research file B).

## Caveats
- 64 questions give wide intervals; differences of a few questions are not conclusions.
- The judge saw expected evidence only; a 30-50 question hand-labelled calibration sample is still to do before we trust small differences.
- Same-provider caveat: answers and embeddings are Google models; the judge is DeepSeek.
- The corpus is fictional and small (114 chunks); nothing here says how larger corpora behave.
- Test split (19 questions) has not been used for any decision yet; keep it that way until the final numbers.
