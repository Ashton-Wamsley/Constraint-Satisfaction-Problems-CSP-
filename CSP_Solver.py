import sys
import json
import time
from copy import deepcopy
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


