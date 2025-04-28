import sys
import os
import argparse
import json
import re
from scipy.optimize import linprog

def parse_input(lines):
    try:
        P1 = list(map(int, lines[0].strip().split()))
        P2 = list(map(int, lines[1].strip().split()))
        obj_expr = lines[2].strip()
        return P1, P2, obj_expr
    except Exception as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(1)

def parse_objective(expr, n):
    # Initialize zero coefficients for 2n variables
    coeffs = [0] * (2 * n)
    # Matches terms like '3 x_1', '- x_2', 'y_4', etc.
    tokens = re.findall(r'[+-]?\s*\d*\s*[xy]_\d+', expr)
    for token in tokens:
        token = token.replace(' ', '')
        match = re.match(r'([+-]?)(\d*)([xy])_(\d+)', token)
        if match:
            sign, num, var, idx = match.groups()
            idx = int(idx) - 1
            if idx < 0 or idx >= n:
                print(f"Invalid variable index in objective: {token}", file=sys.stderr)
                sys.exit(1)
            coeff = int(num) if num else 1
            if sign == '-':
                coeff = -coeff
            if var == 'x':
                coeffs[idx] = coeff
            else:
                coeffs[n + idx] = coeff
    return coeffs

def build_full_constraints(P1, P2, n):
    from itertools import chain
    A_ub, b_ub = [], []

    # Helpers from earlier constraint groups
    def add_constraints(generator):
        A, b = generator(P1, P2, n)
        A_ub.extend(A)
        b_ub.extend(b)

    add_constraints(generate_monotonicity_constraints)
    add_constraints(generate_spacing_constraints)
    add_constraints(generate_combined_constraints)

    return A_ub, b_ub

def generate_monotonicity_constraints(P1, P2, n):
    A_ub, b_ub = [], []
    row = [0] * (2 * n)
    row[P1[0] - 1] = -1
    A_ub.append(row[:])
    b_ub.append(-1)
    row = [0] * (2 * n)
    row[n + P2[0] - 1] = -1
    A_ub.append(row[:])
    b_ub.append(-1)
    for i in range(n - 1):
        row = [0] * (2 * n)
        row[P1[i] - 1] = 1
        row[P1[i + 1] - 1] = -1
        A_ub.append(row)
        b_ub.append(0)
    for i in range(n - 1):
        row = [0] * (2 * n)
        row[n + P2[i] - 1] = 1
        row[n + P2[i + 1] - 1] = -1
        A_ub.append(row)
        b_ub.append(0)
    return A_ub, b_ub

def generate_spacing_constraints(P1, P2, n):
    A_ub, b_ub = [], []

    # 1-based inverse permutations: Q1[i] = position of i+1 in P1
    Q1 = [0] * n
    Q2 = [0] * n
    for i in range(n):
        Q1[P1[i] - 1] = i + 1
        Q2[P2[i] - 1] = i + 1

    # Constraints based on Q2 and P1 → x variables
    for i in range(1, n - 1):  # i from 1 to n-2 → i+1 is in [2, n-1]
        a = Q2[P1[i - 1] - 1]
        b = Q2[P1[i] - 1]
        c = Q2[P1[i + 1] - 1]
        if (a - b) * (c - b) > 0:
            row = [0] * (2 * n)
            row[P1[i - 1] - 1] = 1
            row[P1[i + 1] - 1] = -1
            A_ub.append(row)
            b_ub.append(-1)

    # Constraints based on Q1 and P2 → y variables
    for i in range(1, n - 1):
        a = Q1[P2[i - 1] - 1]
        b = Q1[P2[i] - 1]
        c = Q1[P2[i + 1] - 1]
        if (a - b) * (c - b) > 0:
            row = [0] * (2 * n)
            row[n + P2[i - 1] - 1] = 1
            row[n + P2[i + 1] - 1] = -1
            A_ub.append(row)
            b_ub.append(-1)

    return A_ub, b_ub

def generate_combined_constraints(P1, P2, n):
    A_ub, b_ub = [], []

    # Build 1-based inverse permutations
    Q1 = [0] * n
    Q2 = [0] * n
    for i in range(n):
        Q1[P1[i] - 1] = i + 1
        Q2[P2[i] - 1] = i + 1

    # Constraints from P1 and Q2
    for i in range(n - 1):
        u = P1[i + 1]
        v = P1[i]
        q_u = Q2[u - 1]
        q_v = Q2[v - 1]

        row = [0] * (2 * n)
        row[u - 1] = -1     # -x_u
        row[v - 1] = 1      # +x_v

        if q_v < q_u:
            row[n + u - 1] = -1     # -y_u
            row[n + v - 1] = 1      # +y_v
        else:
            row[n + v - 1] = -1     # -y_v
            row[n + u - 1] = 1      # +y_u

        A_ub.append(row)
        b_ub.append(-1)

    # Constraints from P2 and Q1
    for i in range(n - 1):
        u = P2[i + 1]
        v = P2[i]
        q_u = Q1[u - 1]
        q_v = Q1[v - 1]

        row = [0] * (2 * n)
        row[n + u - 1] = -1     # -y_u
        row[n + v - 1] = 1      # +y_v

        if q_v < q_u:
            row[u - 1] = -1     # -x_u
            row[v - 1] = 1      # +x_v
        else:
            row[v - 1] = -1     # -x_v
            row[u - 1] = 1      # +x_u

        A_ub.append(row)
        b_ub.append(-1)

    return A_ub, b_ub

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", nargs="?")
    parser.add_argument("output_file", nargs="?")
    parser.add_argument("-d", dest="directory", default=".")
    args = parser.parse_args()

    input_path = os.path.join(args.directory, args.input_file) if args.input_file else None
    output_path = os.path.join(args.directory, args.output_file) if args.output_file else None

    try:
        if input_path:
            with open(input_path) as f:
                lines = f.readlines()
        else:
            lines = sys.stdin.readlines()
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    P1, P2, obj_expr = parse_input(lines)
    n = len(P1)
    c = parse_objective(obj_expr, n)
    A_ub, b_ub = build_full_constraints(P1, P2, n)
    bounds = [[0, None] for _ in range(2 * n)]
    var_names = [f"x{i+1}" for i in range(n)] + [f"y{i+1}" for i in range(n)]

    lp_json = {
        "c": c,
        "A_ub": A_ub,
        "b_ub": b_ub,
        "A_eq": [],
        "b_eq": [],
        "bounds": bounds,
        "variable_names": var_names
    }

    try:
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(lp_json, f, indent=2)
                f.write("\n")
        else:
            print(json.dumps(lp_json, indent=2) + "\n")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
