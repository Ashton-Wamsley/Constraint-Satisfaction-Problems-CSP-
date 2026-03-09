This project implements a general Constraint Satisfaction Problem (CSP) solver with support for Sudoku, Australia map coloring, backtracking search, MRV, forward checking, and LCV.

Run Intructions:
python CSP_Solver.py --problem <problem> --instance <instance> --config <config>
Problem Inputs: sudoku, map
Sudoku Instances: easy1, easy2, medium1, medium2, hard1, hard2
Map Instance: australia
Configurations: baseline, mrv, mrv_fc, mrv_fc_lcv
Examples:
python CSP_Solver.py --problem sudoku --instance easy1 --config baseline
python CSP_Solver.py --problem sudoku --instance medium2 --config mrv_fc
python CSP_Solver.py --problem map --instance australia --config mrv_fc_lcv

