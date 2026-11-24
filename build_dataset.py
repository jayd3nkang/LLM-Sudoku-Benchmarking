
#build 9x9 dataset
#usage: python build_dataset.py --grids 600 --workers 16 --seed 0 --verify -1
#output is a json file
import argparse, json, random, time
from collections import Counter
from multiprocessing import Pool

from z3 import Solver, Not, sat, unsat
from sudoku import SudokuSolver
from rater import rate


#since on 6x6 problems, open source models did not perform well, take snapshots on the way 
SNAPSHOTS = (45, 36, 30)
_base = None  # one encoded solver per worker process


def make_base():
    s = SudokuSolver([[0] * 9 for _ in range(9)])
    s.solver = Solver()
    s.create_variables()
    s.encode_rules()
    return s


def random_full_grid(s, rng):
    while True:
        s.solver.push()
        for b in range(3):  # diagonal boxes don't share rows/cols
            for idx, k in enumerate(rng.sample(range(9), 9)):
                s.solver.add(s.variables[3 * b + idx // 3][3 * b + idx % 3][k])
        ok = s.solver.check() == sat
        grid = s.extract_solution(s.solver.model()) if ok else None
        s.solver.pop()
        if ok:
            return grid


def has_other_solution(s, puzzle, cell, value):
    """Is there a solution of `puzzle` with `cell` != value?"""
    i, j = cell
    s.solver.push()
    for a in range(9):
        for b in range(9):
            if puzzle[a][b]:
                s.solver.add(s.variables[a][b][puzzle[a][b] - 1])
    s.solver.add(Not(s.variables[i][j][value - 1]))
    result = s.solver.check() == sat
    s.solver.pop()
    return result


def dig(s, grid, rng):
    puzzle = [r[:] for r in grid]
    cells = [(i, j) for i in range(9) for j in range(9)]
    rng.shuffle(cells)
    saved = {}
    for i, j in cells:
        v = puzzle[i][j]
        puzzle[i][j] = 0
        if has_other_solution(s, puzzle, (i, j), v):
            puzzle[i][j] = v  # removing it breaks uniqueness
        n = sum(x != 0 for r in puzzle for x in r)
        if n in SNAPSHOTS and n not in saved:
            saved[str(n)] = [r[:] for r in puzzle]
    saved["min"] = puzzle
    return saved


def work(args):
    grid_id, seed = args
    global _base
    if _base is None:
        _base = make_base()
    rng = random.Random(seed)
    solution = random_full_grid(_base, rng)
    rows = []
    for stage, puzzle in dig(_base, solution, rng).items():
        score, tier, steps = rate(puzzle, solution)
        rows.append({
            "id": f"g{grid_id:04d}_{stage}",
            "grid_id": grid_id,
            "stage": stage,
            "givens": sum(x != 0 for r in puzzle for x in r),
            "puzzle": puzzle,
            "solution": solution,
            "se_approx": score,
            "tier": tier,
            "rater_steps": steps,
        })
    return rows


def check_one(r):
    """Independent uniqueness check with the original HW class."""
    unique, first, _ = SudokuSolver(r["puzzle"]).is_unique()
    return r["id"], unique and first == r["solution"]


def verify(pool, rows, sample=None):
    todo = rows if sample is None else random.Random(1).sample(rows, sample)
    bad = [pid for pid, ok in pool.imap_unordered(check_one, todo) if not ok]
    assert not bad, f"failed uniqueness check: {bad[:10]}"
    return len(todo)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--grids", type=int, default=300)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="puzzles.jsonl")
    ap.add_argument("--verify", type=int, default=-1,
                    help="how many puzzles to re-check for uniqueness (-1 = all)")
    a = ap.parse_args()

    t0 = time.time()
    jobs = [(g, a.seed * 1_000_003 + g) for g in range(a.grids)]
    with Pool(a.workers) as pool:
        rows = [r for batch in pool.imap(work, jobs) for r in batch]
        print(f"generated {len(rows)} puzzles from {a.grids} grids in {time.time() - t0:.0f}s")
        t1 = time.time()
        n = verify(pool, rows, None if a.verify < 0 else min(a.verify, len(rows)))
        print(f"uniqueness re-checked on {n} puzzles in {time.time() - t1:.0f}s: all OK")

    with open(a.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    order = ["easy", "medium", "hard", "fiendish", "fiendish+"]
    stages = ["45", "36", "30", "min"]
    table = Counter((r["stage"], r["tier"]) for r in rows)
    print("\nstage   " + "".join(f"{t:>11}" for t in order))
    for s in stages:
        print(f"{s:<8}" + "".join(f"{table[(s, t)]:>11}" for t in order))
    mins = [r["givens"] for r in rows if r["stage"] == "min"]
    print(f"\nminimal givens: {min(mins)}-{max(mins)}, mean {sum(mins) / len(mins):.1f}")
