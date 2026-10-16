# #016 Nightly digest job on Grok CLI: one item per call vs batched-in-one-prompt

**Engine:** Grok Build CLI 1.0.52 (SuperGrok, `grok-4.7-build`). All costs are **API-equivalent estimates** from the CLI's `total_cost_usd`; nothing was billed per call on the subscription.

**Plan row (016):** "Move nightly jobs to batch: a week of summaries via batch vs live; compare cost and delay." The plan's premise is xAI's Batch API discount (~50%). That API needs an xAI API key and **was not tested**; the CLI has no batch mode. This experiment tests what *is* reachable from the CLI: packing many items into one prompt instead of one call per item, plus reasoning effort `low`.

**Answer, short.** Packing 40 items into one call with `--reasoning-effort low` cut the cost from **$6.11 to $0.47 per 1,000 items (−92%)** and wall time from ~708 s of call time to ~68 s, for a 2.5-point drop in topic accuracy (97.5% → 95%, one extra miss on one item). Summary-length compliance (100%) and entity grounding (~98%) did not change. Most of the saving comes from not re-paying the CLI's fixed prompt overhead (~5.7k input tokens per call) 40 times.

## Setup
- **Data:** 40 public AG News test items (10 per class, seed 16, excluding the 200 items used in #024): `results/items40.json`, built by `scripts/prep.py`. No private data.
- **Task per item:** JSON Lines with `topic` (World/Sports/Business/Sci/Tech), one-sentence `summary` ≤15 words, up to 3 `entities` copied verbatim.
- **Arms:** `seq` (1 item/call, 40 calls), `seqlow` (same, effort low), `b10` (10 items/call, 4 calls), `b40` (40 items/call, 1 call), `b40low` (40 items/call, effort low).
- **Lean flags:** `--system-prompt-override "You are a precise news-digest assistant. Output only what is asked." --disable-web-search --no-subagents --tools read_file`, fresh temp cwd per call, 5 calls in parallel.
- **Scoring:** exact topic match vs gold label; word count ≤15; entity string found verbatim in the item text.
- Run 2026-10-15, 01:41–02:06 IST. 138 Grok calls, 0 failures, 0 limit hits. Total spend **$1.05 API-equivalent**.

```bash
source /workspace/tools/setup.sh; PY=/workspace/tools/mlenv/bin/python
$PY scripts/prep.py
ARMS=b40,b40low,b10,seq REPS=1 $PY scripts/run_016.py
ARMS=b40,b40low,b10 REPS=2,3 $PY scripts/run_016.py; ARMS=seqlow REPS=2,3 $PY scripts/run_016.py
$PY scripts/analyse_016.py     # -> results/runs.csv, results/summary.csv, chart.png
```

## Results (mean over reps)

| arm | reps | calls | topic acc | summary ≤15 w | entities verbatim | USD / 1k items (API-equiv.) | input tok | output tok (of which reasoning) | summed call time | slowest call |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 item/call | 1 | 40 | 97.5% | 100% | 98.2% | $6.11 | 229,765 | 43,133 (41,291) | 708 s | 46 s |
| 1 item/call, effort low | 2 | 40 | 97.5% | 100% | 98.1% | $4.57 | 252,075 | 20,268 (18,366) | 446 s | 36 s |
| 10 items/call | 3 | 4 | 96.7% (95–97.5) | 100% | 98.7% | $1.88 | 24,850 | 29,345 (27,523) | 363 s | 113 s |
| 40 items/call | 3 | 1 | 95.0% | 100% | 98.3% | $1.28 | 7,773 | 22,715 (21,017) | 240 s | 240 s |
| **40 items/call, effort low** | 3 | 1 | 95.0% | 100% | 98.0% | **$0.47** | 7,774 | 6,863 (5,056) | 68 s | 68 s |

- Every arm parsed 40/40 items.
- The errors are the same two items every time: #2306 (US tax-cut deal in Congress, gold *World*) → *Business* in every arm; #5546 (ex-Microsoft staff charged over software theft, gold *Sci/Tech*) → *Business* in all 40-item runs and one 10-item run. Both are arguably ambiguous labels, so the accuracy gap is one borderline item.
- Reasoning tokens are most of the output in every arm; effort `low` cut them ~75% in the 40-item call.
- Spread between reps: 40-item cost ranged $1.02–1.63/1k (default effort) and $0.40–0.59/1k (low).
- Raw data: per-call usage `results/grok_calls.csv`; per-item outputs `results/preds_<arm>_r<rep>.json`; per-run scores `results/runs.csv`; arm means `results/summary.csv`; run logs `results/run*.log`.

## Caveats
- **Not the Batch API.** The plan's "~50% off for batch" claim is untested here. If xAI's Batch API discount stacks on top of prompt-packing, the API route could be cheaper still; it would also add queue delay (not measured).
- **Unequal reps:** `seq` has 1 rep and `seqlow` 2 (the sequential arms are the costly ones); batched arms have 3. The sequential arms' accuracy was identical across their reps.
- 40 short, clean news items, not "a week of summaries"; long inputs would make one 40-item prompt much larger and could hurt output quality or hit length limits.
- The CLI's cost field reflects its own system prompt and caching; real API calls with a minimal prompt would have much less fixed overhead per call, which shrinks the sequential-vs-batched gap.
- Latency: a single 40-item call is one long wait (60–320 s); for a nightly job that is irrelevant, for interactive use it is not.
