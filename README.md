# LP Solver in Python using linprog
This project contains two directories: `code` and `data`

The `code` directory contains three python3 programs
- `perms2lp.py`: Converts from a description (`.txt`  file) of the two permutations and the objective function to a description (`,json` file) of the linear program in the format expected by the `linprog` method in `scipy.optimize`
- `minLP.py`: Takes a description (`.json` file) of a min LP problem in the format expected by the `linprog` method in `scipy.optimize`, runs `linprog` and saves the results in `.json` format
- `checkSolution.py`: Takes a `.json` file consisting of two objects (an LP description and a potential solution) and checks to see whether the potential solution satisfies all of the constraints. Useful for debugging.

The `data` directory contains, well, data files.
- The `sample` files just test the `minLP` program and have nothing to do with permutations.
- The `perms*` files contain instances of the 2-permutation problem:
    - `permsn.txt (n=1,...,5)` are inputs for `perms2lp.py`
    - `permsnlp.json (n=1,...,5)` are outputs from `perms2lp.py` and so inputs for `minLP.py`
    - `permsnlpsoln.json (n=1,...,5)` are outputs from `minLP.py`
    - `checkperms1.json` is a sample input for `checkSolution.py` and `checkperms1Out.json` is the output

All three programs take three (optional) parameters:
- `-d dir`: The directory containing input and output files
- `input`: The input file name
- `output`: The output file name
If no input/output file names are given, the programs default to `stdin` and `stdout`. Errors go to `stderr`.
