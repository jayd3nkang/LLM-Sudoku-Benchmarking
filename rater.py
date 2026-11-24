"""
Human-technique difficulty rater (a rough stand-in for Sudoku Explainer).

It solves the puzzle the way a person would. At every step it uses the
easiest technique that makes progress, and the puzzle's rating is the
hardest technique it needed. The ratings use Sudoku Explainer's numbers
for these techniques, so the tiers line up with the paper's:

    Easy      <= 1.2   hidden singles in boxes only
    Medium    <= 1.5   + hidden singles in rows/cols
    Hard      <= 2.5   + naked singles
    Fiendish  2.6-4.0  pointing/claiming, pairs, triples, X-wing, swordfish
    Fiendish+ > 4.0    stuck with these techniques (needs chains etc.;
                       can't separate Fiendish from Diabolical here)
"""
from itertools import combinations

ROWS = [[(r, c) for c in range(9)] for r in range(9)]
COLS = [[(r, c) for r in range(9)] for c in range(9)]
BOXES = [[(br * 3 + i, bc * 3 + j) for i in range(3) for j in range(3)]
         for br in range(3) for bc in range(3)]
UNITS = BOXES + ROWS + COLS
PEERS = {(r, c): {p for u in UNITS if (r, c) in u for p in u} - {(r, c)}
         for r in range(9) for c in range(9)}

SE = {"hidden_single_box": 1.2, "hidden_single_line": 1.5, "naked_single": 2.3,
      "pointing": 2.6, "claiming": 2.8, "naked_pair": 3.0, "x_wing": 3.2,
      "hidden_pair": 3.4, "naked_triple": 3.6, "swordfish": 3.8,
      "hidden_triple": 4.0}


def tier(score):
    if score is None:
        return "fiendish+"
    if score <= 1.2:
        return "easy"
    if score <= 1.5:
        return "medium"
    if score <= 2.5:
        return "hard"
    return "fiendish"


class Board:
    def __init__(self, puzzle):
        self.grid = [row[:] for row in puzzle]
        self.cands = {}
        for r in range(9):
            for c in range(9):
                if self.grid[r][c] == 0:
                    used = {self.grid[pr][pc] for pr, pc in PEERS[(r, c)]}
                    self.cands[(r, c)] = set(range(1, 10)) - used

    def place(self, cell, d):
        r, c = cell
        self.grid[r][c] = d
        del self.cands[cell]
        for p in PEERS[cell]:
            if p in self.cands:
                self.cands[p].discard(d)
        return True

    def eliminate(self, cells, digits):
        changed = False
        for cell in cells:
            if cell in self.cands and self.cands[cell] & digits:
                self.cands[cell] -= digits
                changed = True
        return changed

    # ---- techniques: each returns True if it made progress ----
    def hidden_single(self, units):
        for u in units:
            for d in range(1, 10):
                spots = [x for x in u if x in self.cands and d in self.cands[x]]
                if len(spots) == 1:
                    return self.place(spots[0], d)
        return False

    def naked_single(self):
        for cell, cs in self.cands.items():
            if len(cs) == 1:
                return self.place(cell, next(iter(cs)))
        return False

    def pointing(self):  # digit in box confined to one row/col -> clear rest of line
        for box in BOXES:
            for d in range(1, 10):
                spots = [x for x in box if x in self.cands and d in self.cands[x]]
                if not spots:
                    continue
                for line_units, idx in ((ROWS, 0), (COLS, 1)):
                    if len({x[idx] for x in spots}) == 1:
                        line = line_units[spots[0][idx]]
                        if self.eliminate([x for x in line if x not in box], {d}):
                            return True
        return False

    def claiming(self):  # digit in line confined to one box -> clear rest of box
        for line in ROWS + COLS:
            for d in range(1, 10):
                spots = [x for x in line if x in self.cands and d in self.cands[x]]
                if not spots:
                    continue
                boxes = {(x[0] // 3, x[1] // 3) for x in spots}
                if len(boxes) == 1:
                    br, bc = boxes.pop()
                    box = BOXES[br * 3 + bc]
                    if self.eliminate([x for x in box if x not in line], {d}):
                        return True
        return False

    def naked_subset(self, n):
        for u in UNITS:
            empties = [x for x in u if x in self.cands]
            for combo in combinations(empties, n):
                union = set().union(*(self.cands[x] for x in combo))
                if len(union) == n:
                    if self.eliminate([x for x in empties if x not in combo], union):
                        return True
        return False

    def hidden_subset(self, n):
        for u in UNITS:
            empties = [x for x in u if x in self.cands]
            missing = set().union(*(self.cands[x] for x in empties)) if empties else set()
            for digits in combinations(sorted(missing), n):
                spots = {x for x in empties if self.cands[x] & set(digits)}
                if len(spots) == n:
                    if self.eliminate(spots, set(range(1, 10)) - set(digits)):
                        return True
        return False

    def fish(self, n):  # n=2 X-wing, n=3 swordfish
        for d in range(1, 10):
            for base, cover_idx in ((ROWS, 1), (COLS, 0)):
                lines = []
                for line in base:
                    pos = {x[cover_idx] for x in line if x in self.cands and d in self.cands[x]}
                    if 2 <= len(pos) <= n:
                        lines.append((line, pos))
                for combo in combinations(lines, n):
                    cover = set().union(*(p for _, p in combo))
                    if len(cover) == n:
                        base_cells = {x for line, _ in combo for x in line}
                        targets = [x for x in self.cands
                                   if x[cover_idx] in cover and x not in base_cells]
                        if self.eliminate(targets, {d}):
                            return True
        return False


def rate(puzzle, solution=None):
    """Returns (score, tier, steps). score is None if techniques run out."""
    b = Board(puzzle)
    order = [
        ("hidden_single_box", lambda: b.hidden_single(BOXES)),
        ("hidden_single_line", lambda: b.hidden_single(ROWS + COLS)),
        ("naked_single", b.naked_single),
        ("pointing", b.pointing),
        ("claiming", b.claiming),
        ("naked_pair", lambda: b.naked_subset(2)),
        ("x_wing", lambda: b.fish(2)),
        ("hidden_pair", lambda: b.hidden_subset(2)),
        ("naked_triple", lambda: b.naked_subset(3)),
        ("swordfish", lambda: b.fish(3)),
        ("hidden_triple", lambda: b.hidden_subset(3)),
    ]
    hardest, steps = 0.0, 0
    while b.cands:
        for name, technique in order:
            if technique():
                hardest = max(hardest, SE[name])
                steps += 1
                break
        else:
            return None, tier(None), steps
    if solution is not None:
        assert b.grid == solution, "rater reached a wrong grid (bug)"
    return hardest, tier(hardest), steps
