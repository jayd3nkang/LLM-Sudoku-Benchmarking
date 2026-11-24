from z3 import Solver, Bool, And, Or, Not, Implies, sat, unsat
#Jayden's hw3 source code 

class SudokuSolver:
    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.solver = None
        self.variables = None

    def create_variables(self):
        """
        Set self.variables as a 3D list containing the Z3 variables. 
        self.variables[i][j][k] is true if cell i,j contains the value k+1.
        """
        # Your code here
        #i is the rows and j is the column and each i j pair contain a list of booleans representing numbers 1 - 9 
        self.variables = []        
        for i in range(9):
            first_list = []
            for j in range (9):
                second_list = []
                for k in range (9):
                    second_list.append(Bool(f"x_{i}_{j}_{k}"))
                first_list.append(second_list)
            self.variables.append(first_list)
        
        
                    

    def encode_rules(self):
        """
        Encode the rules of Sudoku into the solver.
        The rules are:
        1. Each cell must contain a value between 1 and 9.
        2. Each row must contain each value exactly once.
        3. Each column must contain each value exactly once.
        4. Each 3x3 subgrid must contain each value exactly once.
        """
        # Your code here
        
        #rule 1 
        #the case where it where solver will reject is when two true values for same i j but different k
        for i in range(9):
            for j in range(9):
                self.solver.add(Or(self.variables[i][j]))
                for k1 in range(9):
                    for k2 in range(9):
                        if k1 == k2:
                            continue
                        else: 
                            self.solver.add(Not(And(self.variables[i][j][k1], self.variables[i][j][k2])))
                
        #rule 2
        my_list = []
        for i in range(9):
            for k in range(9):
                my_list = []
                for j1 in range(9):
                    my_list.append(self.variables[i][j1][k])
                    for j2 in range(9):
                        if j1 == j2: 
                            continue
                        self.solver.add(Not(And(self.variables[i][j1][k], self.variables[i][j2][k])))
                self.solver.add(Or(my_list))
                    
        # rule 3 
        for j in range(9):
            for k in range(9):
                my_list = []
                for i1 in range(9):
                    my_list.append(self.variables[i1][j][k])
                    for i2 in range(9):
                        if i1 == i2: 
                            continue 
                        self.solver.add(Not(And(self.variables[i1][j][k], self.variables[i2][j][k])))
                self.solver.add(Or(my_list))
                
        # rule 4
        for box_row in range(3):
            for box_col in range(3): 
                start_i = box_row * 3
                start_j = box_col * 3
                
                for k in range(9):
                    my_list = []
                    for i1 in range(start_i, start_i+3):
                        for j1 in range(start_j, start_j+3):
                            my_list.append(self.variables[i1][j1][k])
                            for i2 in range(start_i, start_i+3):
                                for j2 in range(start_j, start_j+3):
                                    if i1 == i2 and j1 == j2:
                                        continue
                                    self.solver.add(Not(And(self.variables[i1][j1][k], self.variables[i2][j2][k])))
                    self.solver.add(Or(my_list))
                            
        
        
        
        
    def encode_puzzle(self):
        """
        Encode the initial puzzle into the solver.
        """
        # Your code here
        for i in range(9):
            for j in range(9):
                current_var = self.puzzle[i][j]
                if current_var != 0: 
                    self.solver.add(self.variables[i][j][current_var-1])
        
    
    def extract_solution(self, model):
        """
        Extract the satisfying assignment from the given model and return it as a 
        9x9 list of lists.
        Args:
            model: The Z3 model containing the satisfying assignment.
        Returns:
            A 9x9 list of lists of integers representing the Sudoku solution.
        Hint:
            To access the value of a variable in the model, you can use:
            value = model.evaluate(var)
            where `var` is the Z3 variable whose value you want to retrieve.
        """
        solution = []
        for i in range(9):
            row = []
            for j in range(9):
                for k in range(9):
                    if model.evaluate(self.variables[i][j][k], model_completion=True):
                        row.append(k + 1)
                        break
            solution.append(row)
        return solution
    
    def solve(self):
        """
        Solve the Sudoku puzzle.
        
        :return: A 9x9 list of lists representing the solved Sudoku puzzle, or None if no solution exists.
        """
        self.solver = Solver()
        self.create_variables()
        self.encode_rules()
        self.encode_puzzle()
        
        if self.solver.check() == sat:
            model = self.solver.model()
            solution = self.extract_solution(model)
            return solution
        else:
            return None
    
    #written question 2
    def is_unique(self):
        # Returns (unique, first, second):
        # unique is True if exactly one solution exists,
        # first is the first solution, second is another solution or None.

        first = self.solve()
        if first is None:
            return False, None, None   # no solution at all

        # block the first solution: at least one cell must differ
        block = []
        for i in range(9):
            for j in range(9):
                block.append(Not(self.variables[i][j][first[i][j] - 1]))
        self.solver.add(Or(block))

        if self.solver.check() == sat:
            second = self.extract_solution(self.solver.model())
            return False, first, second
        return True, first, None

def main():
    print("Attempting to solve:")
    puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    
    #written question #1
    puzzle_two = [
        [8, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 3, 6, 0, 0, 0, 0, 0],
        [0, 7, 0, 0, 9, 0, 2, 0, 0],
        [0, 5, 0, 0, 0, 7, 0, 0, 0],
        [0, 0, 0, 0, 4, 5, 7, 0, 0],
        [0, 0, 0, 1, 0, 0, 0, 3, 0],
        [0, 0, 1, 0, 0, 0, 0, 6, 8],
        [0, 0, 8, 5, 0, 0, 0, 1, 0],
        [0, 9, 0, 0, 0, 0, 4, 0, 0]
    ]
    for row in puzzle:
        print(row)
    print()
    for row in puzzle_two:
        print(row)

    solver = SudokuSolver(puzzle)
    solution = solver.solve()
    
    
    solver_two = SudokuSolver(puzzle_two)
    solution_two = solver_two.solve()

    print()
    unique, first, second = solver.is_unique()
    print("Unique:", unique)
    if unique:
        print("Unique solution:")
        for row in first:
            print(row)
    elif first is not None:
        print("Solution 1:")
        for row in first:
            print(row)
        print("Solution 2:")
        for row in second:
            print(row)

    print()
    unique_two, first_two, second_two = solver_two.is_unique()
    print("Unique for puzzle two:", unique_two)
    if unique_two:
        print("Unique solution for puzzle two:")
        for row in first_two:
            print(row)
    elif first_two is not None:
        print("Solution 1 for puzzle two:")
        for row in first_two:
            print(row)
        print("Solution 2 for puzzle two:")
        for row in second_two:
            print(row)
    

if __name__ == "__main__":
    main()
