# I cut my nightly AI job's bill by 92% without touching the Batch API

*Draft for Tech in General: real numbers, 15 Oct 2026.*

Every night I want a digest: for each news item, a topic label, a one-line summary and the names in it. The obvious way is one AI call per item. The advice you hear is "use the Batch API, it's half price." I wanted to know what you can save with just the Grok CLI I already pay for, which has no batch mode.

## The test

40 public news headlines (AG News), four topics. I asked Grok (Grok Build CLI) for a topic, a summary of at most 15 words, and up to 3 names copied exactly from the text. I ran it five ways:

1. One item per call (40 calls)
2. Same, with reasoning effort set to low
3. 10 items per call (4 calls)
4. All 40 in one call
5. All 40 in one call, effort low

Costs are the CLI's own API-equivalent estimates.

## Results

| | Cost per 1,000 items | Topic accuracy | Time |
|---|---|---|---|
| 1 per call | $6.11 | 97.5% | ~12 min of calls |
| 1 per call, low effort | $4.57 | 97.5% | ~7 min |
| 10 per call | $1.88 | 96.7% | ~6 min |
| 40 in one call | $1.28 | 95% | ~4 min |
| **40 in one call, low effort** | **$0.47** | **95%** | **~1 min** |

Every summary stayed under 15 words and ~98% of extracted names appeared word-for-word in the item, in every setup.

## What happened

- **The waste was overhead, not answers.** Each CLI call carries ~5,700 tokens of its own setup. 40 calls pay that 40 times; one call pays it once.
- **"Thinking" was most of the output.** Reasoning tokens were most of what Grok generated (74–96%). Setting effort to low on the big call cut them by about three quarters and the bill by another 63%.
- **The accuracy cost was one headline.** A story about a tax-cut deal in Congress was labelled Business instead of World in *every* setup. The 40-item runs also called a software-theft court case Business instead of Sci/Tech. Honestly, both are debatable.

## My takeaway

For a nightly job, pack the items into one prompt and turn reasoning down. That one change got me 13× cheaper for one borderline label. The Batch API's discount is a separate lever I haven't tested yet; it needs an API key, and I'll measure it next.

*Caveats: 40 short items, 1–3 runs per setup, CLI costs include the CLI's own overhead (raw API calls would show a smaller gap).*
