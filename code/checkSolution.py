import sys
import os
import json
import argparse
import numpy as np

def parse_input(lines):
    try:
        parsed = json.loads("".join(lines))
        if not isinstance(parsed, list) or len(parsed) != 2:
            raise ValueError("Input must be a JSON array of two objects.")
        lp_data, solution_data = parsed
        return lp_data, solution_data["variable_values"]
    except Exception as e:
        print(f"Error parsing input: {e}", file=sys.stderr)
        sys.exit(1)

def format_constraint_row(row, var_names, relation, rhs, lhs_val):
    terms = []
    for coeff, name in zip(row, var_names):
        if abs(coeff) > 1e-8:
            sign = "+" if coeff > 0 else "-"
            mag = abs(coeff)
            if mag == 1:
                terms.append(f"{sign} {name}")
            else:
                terms.append(f"{sign} {mag:g}{name}")
    expr = " ".join(terms).lstrip("+ ").replace("+ -", "- ")
    return {
        "expression": f"{expr} {relation} {float(rhs):g}",
        "lhs": float(lhs_val),
        "rhs": float(rhs),
        "violation": f"{float(lhs_val):.6g} {relation} {float(rhs):.6g} is False"
    }

def check_feasibility(lp, values):
    var_names = lp.get("variable_names")
    x = np.array([values[name] for name in var_names])

    results = {
        "all_constraints_satisfied": True,
        "violations": []
    }

    A_ub = np.array(lp.get("A_ub", []))
    b_ub = np.array(lp.get("b_ub", []))
    if len(A_ub) > 0:
        lhs = A_ub @ x
        for i, (row, lhs_val, rhs_val) in enumerate(zip(A_ub, lhs, b_ub)):
            if lhs_val > rhs_val + 1e-8:
                results["all_constraints_satisfied"] = False
                results["violations"].append({
                    "type": "inequality",
                    "index": int(i),
                    **format_constraint_row(row, var_names, "<=", rhs_val, lhs_val)
                })

    A_eq = np.array(lp.get("A_eq", []))
    b_eq = np.array(lp.get("b_eq", []))
    if len(A_eq) > 0:
        lhs = A_eq @ x
        for i, (row, lhs_val, rhs_val) in enumerate(zip(A_eq, lhs, b_eq)):
            if abs(lhs_val - rhs_val) > 1e-8:
                results["all_constraints_satisfied"] = False
                results["violations"].append({
                    "type": "equality",
                    "index": int(i),
                    **format_constraint_row(row, var_names, "=", rhs_val, lhs_val)
                })

    bounds = lp.get("bounds", [])
    for i, (lower, upper) in enumerate(bounds):
        val = x[i]
        if lower is not None and val < lower - 1e-8:
            results["all_constraints_satisfied"] = False
            results["violations"].append({
                "type": "bound",
                "index": int(i),
                "variable": var_names[i],
                "description": f"{var_names[i]} = {float(val):.6g} is below lower bound {float(lower):.6g}"
            })
        if upper is not None and val > upper + 1e-8:
            results["all_constraints_satisfied"] = False
            results["violations"].append({
                "type": "bound",
                "index": int(i),
                "variable": var_names[i],
                "description": f"{var_names[i]} = {float(val):.6g} is above upper bound {float(upper):.6g}"
            })

    return results

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

    lp_data, var_values = parse_input(lines)
    result = check_feasibility(lp_data, var_values)

    try:
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
                f.write("\n")
        else:
            print(json.dumps(result, indent=2) + "\n")
    except Exception as e:
        print(f"Error writing output: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
