# #016 Nightly digest job on Grok CLI: sequential (1 item/call) vs batched-in-one-prompt (10 or 40 items/call), plus reasoning-effort low.
# ARMS env: seq,b10,b40,b40low  REPS env (per arm, comma list)
import json, os, sys, re, tempfile, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from grok_log import run_grok, QuotaHit
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IT = json.load(open(f"{D}/results/items40.json")); CSV = f"{D}/results/grok_calls.csv"
LEAN = ["--system-prompt-override", "You are a precise news-digest assistant. Output only what is asked.", "--disable-web-search", "--no-subagents", "--tools", "read_file"]
SPEC = ("For each numbered news item, output one JSON object per line (JSON Lines, no code fences, nothing else) with keys: "
        "\"n\" (the item number), \"topic\" (exactly one of World, Sports, Business, Sci/Tech), "
        "\"summary\" (one sentence, at most 15 words), \"entities\" (up to 3 organisations, people or places named in the item, copied exactly as written).")
def prompt(chunk):
    return SPEC + "\n\n" + "\n".join(f"{j+1}. {e['text']}" for j, e in enumerate(chunk))
def parse(text, chunk):
    got = {}
    for line in (text or "").splitlines():
        line = line.strip().strip(",")
        if not line.startswith("{"): continue
        try:
            o = json.loads(line); got[int(o["n"])] = o
        except Exception:
            pass
    return [dict(id=e["id"], gold=e["label"], parsed=(j + 1) in got, out=got.get(j + 1)) for j, e in enumerate(chunk)]
def job(arm, rep, k, chunk, extra):
    r = run_grok(prompt(chunk), f"{arm}_r{rep}_c{k}", CSV, "016-" + arm, rep, cwd=tempfile.mkdtemp(), extra=extra)
    return dict(arm=arm, rep=rep, chunk=k, exit=r["exit_code"], cost=r["cost_usd"], latency=r["latency_s"], items=parse(r["text"], chunk))
CONF = {"seq": (1, LEAN), "b10": (10, LEAN), "b40": (40, LEAN), "b40low": (40, LEAN + ["--reasoning-effort", "low"]), "seqlow": (1, LEAN + ["--reasoning-effort", "low"])}
if __name__ == "__main__":
    arms = os.environ.get("ARMS", "seq,b10,b40,b40low").split(","); reps = [int(x) for x in os.environ.get("REPS", "1").split(",")]
    jobs = []
    for a in arms:
        size, extra = CONF[a]
        for rep in reps:
            out = f"{D}/results/preds_{a}_r{rep}.json"
            if os.path.exists(out): continue
            jobs.append((a, rep, out, [(k, IT[i:i + size]) for k, i in enumerate(range(0, 40, size))], extra))
    hit = False
    with cf.ThreadPoolExecutor(int(os.environ.get("PAR", "5"))) as ex:
        for a, rep, out, chunks, extra in jobs:
            futs = [ex.submit(job, a, rep, k, c, extra) for k, c in chunks]; res = []
            for f in cf.as_completed(futs):
                try: res.append(f.result())
                except QuotaHit as e: hit = True; print("QUOTA HIT", e, flush=True)
            if len(res) == len(chunks):
                json.dump(sorted(res, key=lambda r: r["chunk"]), open(out, "w"), indent=1)
            print(a, rep, "chunks ok", len(res), "/", len(chunks), flush=True)
            if hit: break
    sys.exit(3 if hit else 0)
