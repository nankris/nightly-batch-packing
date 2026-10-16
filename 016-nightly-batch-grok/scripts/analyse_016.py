import json, os, re, glob, statistics as st
import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IT = {e["id"]: e for e in json.load(open(f"{D}/results/items40.json"))}
calls = pd.read_csv(f"{D}/results/grok_calls.csv")
rows = []
for f in sorted(glob.glob(f"{D}/results/preds_*_r*.json")):
    arm, rep = re.search(r"preds_(\w+?)_r(\d+)\.json", f).groups(); R = json.load(open(f))
    items = [i for r in R for i in r["items"]]
    c = calls[calls.label.str.match(rf"^{arm}_r{rep}_c\d+$")]
    ok = [i for i in items if i["parsed"]]
    def words(s): return len(re.findall(r"\S+", s or ""))
    ents = [(e, IT[i["id"]]["text"]) for i in ok for e in (i["out"].get("entities") or []) if isinstance(e, str)]
    rows.append(dict(arm=arm, rep=int(rep), calls=len(R), failed_calls=sum(r["exit"] != 0 for r in R), items=len(items), parsed=len(ok),
                     topic_acc=sum((i["out"] or {}).get("topic") == i["gold"] for i in items) / 40,
                     summary_le15=sum(words(i["out"].get("summary")) <= 15 for i in ok) / max(1, len(ok)),
                     entities_per_item=len(ents) / max(1, len(ok)), entity_grounded=sum(e in t for e, t in ents) / max(1, len(ents)),
                     cost=c.cost_usd.sum(), cost_per_1k_items=c.cost_usd.sum() / 40 * 1000, in_tok=(c.input_tokens + c.cache_read_input_tokens).sum(),
                     out_tok=c.output_tokens.sum(), reasoning_tok=c.reasoning_tokens.sum(), latency_sum=c.latency_s.sum(), latency_max=c.latency_s.max()))
t = pd.DataFrame(rows); t.to_csv(f"{D}/results/runs.csv", index=False)
order = [a for a in ["seq", "seqlow", "b10", "b40", "b40low"] if a in set(t.arm)]
g = t.groupby("arm").agg({c: "mean" for c in ["topic_acc", "summary_le15", "entity_grounded", "entities_per_item", "cost", "cost_per_1k_items", "in_tok", "out_tok", "reasoning_tok", "latency_sum", "latency_max", "parsed", "failed_calls"]} | {"rep": "count"}).loc[order]
g = g.rename(columns={"rep": "n_reps"}); g["topic_acc_min"] = t.groupby("arm").topic_acc.min(); g["topic_acc_max"] = t.groupby("arm").topic_acc.max()
g.round(5).to_csv(f"{D}/results/summary.csv"); print(g.round(4).to_string())
lab = {"seq": "1 item/call\n(40 calls)", "seqlow": "1 item/call\neffort low", "b10": "10 items/call\n(4 calls)", "b40": "40 items/call\n(1 call)", "b40low": "40 items/call\neffort low"}
col = {"seq": "#4C72B0", "seqlow": "#8DA0CB", "b10": "#6C8EBF", "b40": "#DD8452", "b40low": "#55A868"}
fig, ax = plt.subplots(1, 2, figsize=(13, 5)); x = range(len(order))
ax[0].bar(x, g.cost_per_1k_items, color=[col[a] for a in order]); ax[0].set_xticks(list(x)); ax[0].set_xticklabels([lab[a] for a in order])
ax[0].set_ylabel("USD per 1,000 items (API-equivalent est.)"); ax[0].set_title("Cost of the nightly digest job")
for i, v in enumerate(g.cost_per_1k_items): ax[0].text(i, v * 1.02, f"${v:.2f}", ha="center")
w = .27
ax[1].bar([i - w for i in x], g.topic_acc * 100, w, label="topic accuracy", color="#4C72B0")
ax[1].bar(list(x), g.summary_le15 * 100, w, label="summary <= 15 words", color="#DD8452")
ax[1].bar([i + w for i in x], g.entity_grounded * 100, w, label="entities found verbatim in item", color="#55A868")
ax[1].set_xticks(list(x)); ax[1].set_xticklabels([lab[a] for a in order]); ax[1].set_ylim(0, 112); ax[1].set_ylabel("% (mean over reps)"); ax[1].set_title("Quality on 40 public AG News items"); ax[1].legend(fontsize=8, loc="lower left")
for i, a in enumerate(order): ax[1].text(i - w, g.topic_acc.iloc[i] * 100 + 1, f"{g.topic_acc.iloc[i]*100:.0f}", ha="center", fontsize=8)
fig.suptitle("#016 Nightly job on Grok Build CLI: sequential vs batched-in-one-prompt (no Batch API via CLI)")
plt.tight_layout(); plt.savefig(f"{D}/chart.png", dpi=125)
