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

    
