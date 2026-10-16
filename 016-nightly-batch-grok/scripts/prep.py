# 40 AG News test items (10 per class), seed 16, excluding the 200 used in #024. Public data only.
import json, os, random
from datasets import load_dataset
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAB = ["World", "Sports", "Business", "Sci/Tech"]
used = {e["id"] for e in json.load(open(f"{D}/../024-tiny-model-vs-grok/results/test200.json"))}
te = load_dataset("fancyzhx/ag_news", split="test"); random.seed(16)
idx = {c: [i for i, l in enumerate(te["label"]) if l == c and i not in used] for c in range(4)}
pick = sorted(sum((random.sample(idx[c], 10) for c in range(4)), []))
json.dump([{"id": i, "text": te[i]["text"], "label": LAB[te[i]["label"]]} for i in pick], open(f"{D}/results/items40.json", "w"), indent=1)
print(len(pick))
