import json
import time
import os
from argparse import ArgumentParser

class CSP:
    def __init__(self, variables, domains, neighbors, constraints):
        self.variables = variables
        self.domains = {v : set(domains[v]) for v in variables}
        self.neighbors = {v : set(neighbors[v]) for v in variables}
        self.constraints = constraints
        self.assignments_tried = 0
        self.backtracks = 0

    def is_consistent(self, var, value, assignment):
        for n in self.neighbors[var]:
            if n in assignment and not self.constraints(var, value, n, assignment[n]):
                return False
        return True
    
def select_unassigned_variable(csp, assignment, use_mrv):
    unassigned = [ v for v in csp.variables if v not in assignment]
    if not use_mrv:
        return unassigned[0] if unassigned else None
        
    min_var = None
    min_size = float('inf')
    for v in unassigned:
        size = len(csp.domains[v])
        if size < min_size:
            min_size = size
            min_var = v
        return min_var
        
def order_domain_values(csp, var, assignment, use_lcv):
    if not use_lcv:
        return list(csp.domain[var])
        
    def conflicts(value):
        count = 0
        for n in csp.neighbors[var]:
            if n not in assignment:
                for v2 in csp.domains[n]:
                    if not csp.constraints(var, value, n, v2):
                        count += 1
        return count
    return sorted(csp.domains[var], key = conflicts)
    
def forward_check(csp, var, value, assignment, removals):
    for n in csp.neighbors[var]:
        if n not in assignment:
            to_remove = set()
            for v2 in csp.domains[n]:
                if not csp.constraints(var, value, n, v2):
                    to_remove.add(v2)
            if to_remove:
                csp.domains[n] -= to_remove
                removals.append((n, to_remove))
                if not csp.domains[n]:
                    return False
    return True
    
def restore_domains(csp, removals):
    for var, vals in removals:
        csp.domains[var] |= vals

def backtrack(csp, assignment, use_mrv, use_fc, use_lcv):
    if len(assignment) == len(csp.variables):
        return assignment
    
    var = select_unassigned_variable(csp, assignment, use_mrv)
    if var is None:
        return assignment
    
    for value in order_domain_values(csp, var, assignment, use_lcv):
        csp.assignments_tried += 1
        if csp.is_consistent(var, value, assignment):
            assignment[var] = value
            removals = []
            ok = True
            if use_fc:
                ok = forward_check(csp, var, value, assignment, removals)
            if ok:
                result = backtrack(csp, assignment, use_mrv, use_fc, use_lcv)
                if result is not None:
                    return result
            if use_fc:
                restore_domains(csp, removals)
            del assignment[var]
    csp.backtracks += 1
    return None

def solve_csp(csp, config):
    use_mrv = config in ("mrv", "mrv_fc", "mrv_fc_lcv")
    use_fc = config in ("mrv_fc", "mrv_fc_lcv")
    use_lcv = config == "mrv_fc_lcv"

    start = time.time()
    assignment = {}
    result = backtrack(csp, assignment, use_mrv, use_fc, use_lcv)
    end = time.time()
    solved = result is not None

    return {
        "solved" : solved,
        "solution" : result,
        "runtime_ms" : (end - start) * 1000.0,
        "assignments_tried" : csp.assignments_tried,
        "backtracks" : csp.backtracks,
    }

def sudoku_world():
    rows = range(9)
    columns = range(9)
    variables = [(r, c) for r in rows for c in columns]
    neighbors = {v : set() for v in variables}

    for r in rows:
        row_vars = [(r, c) for c in columns]
        for v in row_vars:
            neighbors[v].update(set(row_vars) - {v})
    for c in columns:
        column_vars = [(r, c) for r in rows]
        for v in column_vars:
            neighbors[v].update(set(column_vars) - {v})
    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            block = [(r, c) for r in range(br, br + 3) for c in range(bc, bc +3)]
            for v in block:
                neighbors[v].update(set(block) - {v})
    return variables, neighbors

def sudoku_constraints(Xi, vi, Xj, vj):
    return vi != vj

def parse_sudoku(grid_str):
    assert len(grid_str) == 81
    domains = {}
    idx = 0
    for r in range(9):
        for c in range(9):
            ch = grid_str[idx]
            idx += 1
            if ch == '.' or ch == '0':
                domains[(r, c)] = set(range(1, 10))
            else:
                k = int(ch)
                domains[(r, c)] = {k}
    return domains

def sudoku_grid(solution):
    if solution is None:
        return None
    grid = [[0] * 9 for _ in range(9)]
    for (r, c), v in solution.items():
        grid[r][c] = v
    return grid

def create_sudoku_csp(grid_str):
    variables, neighbors = sudoku_world()
    domains = parse_sudoku(grid_str)
    return CSP(variables, domains, neighbors, sudoku_constraints)

def map_constraints(Xi, vi, Xj, vj):
    return vi != vj

def create_australia_map_csp():
    regions = ["WA", "NT", "SA", "Q", "NSW", "V", "T"]
    colors = ["red", "green", "blue"]
    domains = {r: set(colors) for r in regions}
    neighbors = {
        "WA": {"NT", "SA"},
        "NT": {"WA", "SA", "Q"},
        "SA": {"WA", "NT", "Q", "NSW", "V"},
        "Q": {"NT", "SA", "NSW"},
        "NSW": {"Q", "SA", "V"},
        "V": {"SA", "NSW", "T"},
        "T": {"V"},
    }
    return CSP(regions, domains, neighbors, map_constraints)

SUDOKU_INSTANCES = {
    "easy1" : "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79",
    "easy2" : "1.5..2.84..3.5..1.8..1.9..2.7..4..6..4.8.3..9..6..1.3..2.7..9.5..3.1..71.9..4.2",
    "medium1" : "6..874..1.1..9..7..7..1..9..9..5..3..3...4..5..2..8..2..6..3..8..3..6.4..321..9",
    "medium2" : "..9748...7...........2.1.9..1.7..2..3.....8..6..3.4..4.5.2...........8...7639..",
    "hard1" : ".....6....59.....82....8....8.2.3.9.7.......5.1.9.4.7....2....36.....58....3.....",
    "hard2" : "1....7.9.3..2.....8..1..2..5..9.....4..3.1..9.....4..7..6..8..2.....1..9.8.3....",
}

MAP_INSTANCES = {
    "australia" : "australia"
}

def validate_sudoku_solution(grid):
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                return False

    for r in range(9):
        if sorted(grid[r]) != list(range(1, 10)):
            return False

    for c in range(9):
        column = [grid[r][c] for r in range(9)]
        if sorted(column) != list(range(1, 10)):
            return False

    for br in range(0, 9, 3):
        for bc in range(0, 9, 3):
            block = []
            for r in range(br, br + 3):
                for c in range(bc, bc + 3):
                    block.append(grid[r][c])
            if sorted(block) != list(range(1, 10)):
                return False
    return True

def validate_map_coloring(solution, neighbors):
    for region in neighbors:
        if region not in solution:
            return False
        if solution[region] is None:
            return False

    for u in neighbors:
        for v in neighbors[u]:
            if solution[u] == solution[v]:
                return False
    return True

def run(problem, instance, config, seed = None):
    if problem == "sudoku":
        if instance not in SUDOKU_INSTANCES:
            raise ValueError(f"Unknown sudoku instance {instance}")
        grid_str = SUDOKU_INSTANCES[instance]
        csp = create_sudoku_csp(grid_str)
        res = solve_csp(csp, config)
        res["solution"] = sudoku_grid(res["solution"])
    elif problem == "map":
        if instance not in MAP_INSTANCES:
            raise ValueError(f"Unknown map instance {instance}")
        csp = create_australia_map_csp()
        res = solve_csp(csp, config)
    else:
        raise ValueError("problem has to be 'sudoku' or 'map'")
    
    valid = True

    if problem == "sudoku" and res["solved"]:
        if not validate_sudoku_solution(res["solution"]):
            print("Sudoku solution failed validation.")
            valid = False

    if problem == "map" and res["solved"]:
        map_csp = create_australia_map_csp()
        if not validate_map_coloring(res["solution"], map_csp.neighbors):
            print("Map coloring solution failed validation.")
            valid = False

    
    out = {
        "problem" : problem,
        "instance" : instance,
        "config" : config,
        "solved" : res["solved"],
        "valid": valid,
        "runtime_ms" : res["runtime_ms"],
        "assignments_tried" : res["assignments_tried"],
        "backtracks" : res["backtracks"],
        "solution" : res["solution"],
    }

    base = f"results_{problem}_{instance}_{config}"
    i = 1
    filename = f"{base}_{i}.json"

    while os.path.exists(filename):
        i += 1
        filename = f"{base}_{i}.json"

    print(json.dumps(out, indent=2))
    with open(filename, "w") as f:
        json.dump(out, f, indent=2)

def main():
    parser = ArgumentParser()
    parser.add_argument("--problem", required = True, choices = ["sudoku", "map"])
    parser.add_argument("--instance", required = True)
    parser.add_argument("--config", required = True, choices = ["baseline", "mrv", "mrv_fc", "mrv_fc_lcv"])
    parser.add_argument("--seed", type = int, default = None)
    args = parser.parse_args()
    
    run(args.problem, args.instance, args.config, args.seed)

if __name__ == "__main__":
    main()
