"""
Pick stratified test sets from the full dataset.

- Even across stages (45 / 36 / 30 / min givens).
- Within a stage, spread across difficulty tiers as evenly as the data allows
  (round-robin over tiers, so rare tiers get all they can and the rest fills in).
- Every puzzle comes from a different solution grid, so results aren't correlated.
- The frontier set is a subset of the open set, so models are compared on the
  same puzzles.

Usage:
  python select_testset.py --data data/puzzles_seed0.jsonl \
      --open-per-stage 50 --frontier-per-stage 25
Output:
  data/test_open.jsonl, data/test_frontier.jsonl
"""

#python select_testset.py --data data/puzzles_seed0.jsonl
import argparse, json, random
from collections import Counter, defaultdict

STAGES = ["45", "36", "30", "min"]
TIERS = ["easy", "medium", "hard", "fiendish", "fiendish+"]


def balanced_pick(pool, k, rng, used_grids):
    """Round-robin over tiers, skipping grids already used."""
    by_tier = defaultdict(list)
    for r in pool:
        by_tier[r["tier"]].append(r)
    for t in by_tier:
        rng.shuffle(by_tier[t])
    picked = []
    while len(picked) < k:
        progress = False
        for t in TIERS:
            while by_tier[t] and by_tier[t][-1]["grid_id"] in used_grids:
                by_tier[t].pop()
            if by_tier[t] and len(picked) < k:
                r = by_tier[t].pop()
                picked.append(r)
                used_grids.add(r["grid_id"])
                progress = True
        if not progress:
            break
    return picked


def show(name, rows):
    c = Counter((r["stage"], r["tier"]) for r in rows)
    print(f"\n{name}: {len(rows)} puzzles, {len({r['grid_id'] for r in rows})} distinct grids")
    print("stage   " + "".join(f"{t:>11}" for t in TIERS))
    for s in STAGES:
        print(f"{s:<8}" + "".join(f"{c[(s, t)]:>11}" for t in TIERS))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/puzzles_seed0.jsonl")
    ap.add_argument("--open-per-stage", type=int, default=50)
    ap.add_argument("--frontier-per-stage", type=int, default=25)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--outdir", default="data")
    a = ap.parse_args()
    rng = random.Random(a.seed)

    rows = [json.loads(l) for l in open(a.data)]
    used = set()
    open_set, frontier_set = [], []
    # do the stage with the rarest hard tiers first so it gets first pick of grids
    for s in ["min", "30", "36", "45"]:
        picked = balanced_pick([r for r in rows if r["stage"] == s],
                               a.open_per_stage, rng, used)
        if len(picked) < a.open_per_stage:
            print(f"warning: stage {s} only has {len(picked)} usable puzzles")
        open_set += picked
        # frontier = balanced subset of this stage's open picks
        frontier_set += balanced_pick(picked, a.frontier_per_stage, rng, set())

    key = lambda r: (STAGES.index(r["stage"]), TIERS.index(r["tier"]), r["id"])
    open_set.sort(key=key)
    frontier_set.sort(key=key)
    for name, data in (("test_open", open_set), ("test_frontier", frontier_set)):
        with open(f"{a.outdir}/{name}.jsonl", "w") as f:
            for r in data:
                f.write(json.dumps(r) + "\n")
    show("test_open", open_set)
    show("test_frontier", frontier_set)