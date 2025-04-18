import sys
import json
import os
import argparse
import numpy as np
from scipy.optimize import linprog

def load_input_data(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

def write_output_data(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

def solve_lp(lp_data):
    try:
        result = linprog(
        c=lp_data["c"],
        A_ub=lp_data.get("A_ub") or None,
        b_ub=lp_data.get("b_ub") or None,
        A_eq=lp_data.get("A_eq") or None,
        b_eq=lp_data.get("b_eq") or None,
        bounds=lp_data.get("bounds"),
        method="highs"
)
        return {
            "success": result.success,
            "status": result.status,
            "message": result.message,
            "objective_value": result.fun if result.success else None,
            "variable_values": (
                {name: val for name, val in zip(
                    lp_data.get("variable_names", [f"x{i}" for i in range(len(result.x))]),
                    result.x
                )} if result.success else None
            )
        }
    except Exception as e:
        print(f"Error solving LP: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Solve LP minimization problem from JSON input.")
    parser.add_argument("input_file", nargs="?", help="Input JSON file")
    parser.add_argument("output_file", nargs="?", help="Output result file")
    parser.add_argument("-d", dest="directory", default=".", help="Directory for input/output files")
    args = parser.parse_args()

    # Resolve file paths
    input_path = os.path.join(args.directory, args.input_file) if args.input_file else None
    output_path = os.path.join(args.directory, args.output_file) if args.output_file else None

    # Read input
    if input_path:
        lp_data = load_input_data(input_path)
    else:
        try:
            lp_data = json.load(sys.stdin)
        except Exception as e:
            print(f"Error reading input from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    # Solve the LP
    result = solve_lp(lp_data)

    # Output result
    if output_path:
        write_output_data(output_path, result)
    else:
        print(json.dumps(result, indent=2) + "\n")

if __name__ == "__main__":
    main()
