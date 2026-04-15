from collections import deque
from copy import deepcopy
import os

SIZE = 9
DIGITS = set(range(1, 10))

backtrack_calls = 0
failures = 0

def read_board(filename):
    """Reads a Sudoku board from a text file into a 9x9 2D list."""
    board = []
    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) != 9:
        raise ValueError(f"{filename}: must contain exactly 9 non-empty lines")

    for line in lines:
        if len(line) != 9 or not line.isdigit():
            raise ValueError(f"{filename}: each line must contain exactly 9 digits")
        board.append([int(ch) for ch in line])

    return board

def print_board(board):
    """Prints the Sudoku board in a formatted, readable grid."""
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            print("-" * 21)
        row_str = ""
        for j, val in enumerate(row):
            if j % 3 == 0 and j != 0:
                row_str += "| "
            row_str += f"{val} "
        print(row_str.strip())

def cell_name(r, c):
    """Returns a tuple representing the cell coordinates."""
    return (r, c)

def build_peers():
    """Precomputes and returns a dictionary of row, column, and grid peers for every cell."""
    peers = {}
    for r in range(SIZE):
        for c in range(SIZE):
            p = set()
            for k in range(SIZE):
                if k != c:
                    p.add((r, k))
                if k != r:
                    p.add((k, c))
            br = (r // 3) * 3
            bc = (c // 3) * 3
            for i in range(br, br + 3):
                for j in range(bc, bc + 3):
                    if (i, j) != (r, c):
                        p.add((i, j))
            peers[(r, c)] = p
    return peers

PEERS = build_peers()

def initial_domains(board):
    """Initializes the possible values (1-9) for each empty cell, or assigns the known value."""
    domains = {}
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] != 0:
                domains[(r, c)] = {board[r][c]}
            else:
                domains[(r, c)] = set(DIGITS)
    return domains

def is_consistent(var, value, assignment):
    """Checks if a potential value assignment conflicts with any already assigned peers."""
    r, c = var
    for pr, pc in PEERS[(r, c)]:
        if (pr, pc) in assignment and assignment[(pr, pc)] == value:
            return False
    return True

def revise(domains, xi, xj):
    """Removes values from domain xi that are no longer possible due to domain xj constraints."""
    revised = False
    to_remove = set()
    if len(domains[xj]) == 1:
        vj = next(iter(domains[xj]))
        for vi in domains[xi]:
            if vi == vj:
                to_remove.add(vi)
    if to_remove:
        domains[xi] -= to_remove
        revised = True
    return revised

def ac3(domains, queue=None):
    """Enforces arc consistency across the board to prune impossible values from domains."""
    if queue is None:
        queue = deque()
        for xi in domains:
            for xj in PEERS[xi]:
                queue.append((xi, xj))
    else:
        queue = deque(queue)

    while queue:
        xi, xj = queue.popleft()
        if revise(domains, xi, xj):
            if len(domains[xi]) == 0:
                return False
            for xk in PEERS[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    return True

def forward_check(domains, var, value):
    """Removes a newly assigned value from the domains of all its unassigned peers."""
    for peer in PEERS[var]:
        if value in domains[peer]:
            domains[peer] = domains[peer] - {value}
            if len(domains[peer]) == 0:
                return False
    return True

def select_unassigned_variable(domains, assignment):
    """Returns the unassigned cell with the fewest remaining possible values (MRV heuristic)."""
    unassigned = [v for v in domains if v not in assignment]
    return min(unassigned, key=lambda v: len(domains[v]))

def order_domain_values(var, domains):
    """Returns a list of the currently available values in a variable's domain."""
    return list(domains[var])

def assignment_complete(assignment):
    """Returns True if all 81 cells have been successfully assigned a value."""
    return len(assignment) == 81

def domains_to_board(domains):
    """Converts the fully solved dictionary of domains back into a standard 9x9 2D list."""
    board = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    for r in range(SIZE):
        for c in range(SIZE):
            board[r][c] = next(iter(domains[(r, c)]))
    return board

def solve_csp(domains, assignment=None):
    """The main recursive backtracking search combined with Forward Checking and AC-3."""
    global backtrack_calls, failures
    backtrack_calls += 1

    if assignment is None:
        assignment = {}

    if assignment_complete(assignment):
        return domains

    var = select_unassigned_variable(domains, assignment)

    for value in order_domain_values(var, domains):
        if not is_consistent(var, value, assignment):
            continue

        new_domains = deepcopy(domains)
        new_assignment = assignment.copy()

        new_domains[var] = {value}
        new_assignment[var] = value

        if not forward_check(new_domains, var, value):
            continue

        if not ac3(new_domains, queue=[(peer, var) for peer in PEERS[var]]):
            continue

        result = solve_csp(new_domains, new_assignment)
        if result is not None:
            return result

    failures += 1
    return None

def solve_board(board):
    """Initializes the board state, runs preprocessing AC-3, and triggers the CSP solver."""
    domains = initial_domains(board)

    if not ac3(domains):
        return None

    result = solve_csp(domains, {})
    if result is None:
        return None

    return domains_to_board(result)

def run_file(filename):
    """Loads a specific file, attempts to solve it, and prints the solution and metrics."""
    global backtrack_calls, failures
    backtrack_calls = 0
    failures = 0

    print(f"\nSolving: {filename}")
    print("=" * 40)

    board = read_board(filename)
    solved = solve_board(board)

    if solved is None:
        print("No solution found.")
    else:
        print_board(solved)

    print(f"\nBacktrack calls : {backtrack_calls}")
    print(f"Backtrack fails : {failures}")

def main():
    """Iterates through the list of required text files and executes the solver on each."""
    files = ["easy.txt", "medium.txt", "hard.txt", "veryhard.txt"]

    for filename in files:
        if os.path.exists(filename):
            run_file(filename)
        else:
            print(f"\n{filename} not found.")

if __name__ == "__main__":
    main()