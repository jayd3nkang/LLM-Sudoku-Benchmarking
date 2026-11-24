import random, time
from sudoku import SudokuSolver
from z3 import Solver, Not, sat, unsat

def make_base():
    s = SudokuSolver([[0]*9 for _ in range(9)])
    s.solver = Solver(); s.create_variables(); s.encode_rules()
    return s

def random_full_grid(s):
    while True:
        s.solver.push()
        for b in range(3):
            for idx, k in enumerate(random.sample(range(9), 9)):
                s.solver.add(s.variables[3*b + idx//3][3*b + idx%3][k])
        ok = s.solver.check() == sat
        grid = s.extract_solution(s.solver.model()) if ok else None
        s.solver.pop()
        if ok: return grid

def dig(s, grid, snapshots=(45, 36, 30)):
    puzzle = [r[:] for r in grid]
    cells = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(cells)
    saved = {}
    for i, j in cells:
        v = puzzle[i][j]; puzzle[i][j] = 0
        s.solver.push()
        for a in range(9):
            for b in range(9):
                if puzzle[a][b]:
                    s.solver.add(s.variables[a][b][puzzle[a][b]-1])
        s.solver.add(Not(s.variables[i][j][v-1]))
        still_unique = s.solver.check() == unsat
        s.solver.pop()
        if not still_unique:
            puzzle[i][j] = v
        n = sum(x != 0 for r in puzzle for x in r)
        if n in snapshots and n not in saved:
            saved[n] = [r[:] for r in puzzle]
    saved["min"] = puzzle
    return saved

if __name__ == "__main__":
    s = make_base()  # encode rules once, reuse via push/pop
    for _ in range(5):
        t = time.time()
        grid = random_full_grid(s)
        out = dig(s, grid)          # {45: ..., 36: ..., 30: ..., "min": ...}
        m = out["min"]
        n = sum(x != 0 for r in m for x in r)
        u, first, _ = SudokuSolver(m).is_unique()   # independent check
        print(f"{time.time()-t:.1f}s  min_givens={n}  unique={u}  matches={first == grid}")