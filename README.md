# SSMT

This repository contains the implementation and benchmark instances accompanying the paper:

> **Exact Symbolic Reasoning for Nonlinear Stochastic SMT via Cylindrical Algebraic Decomposition**  
> Jung-Cheng Lin, Chia-Hsuan Su, Jie-Hong R. Jiang, and Hiroshi Unno  
> *29th International Conference on Theory and Applications of Satisfiability Testing (SAT 2026)*  
> Leibniz International Proceedings in Informatics (LIPIcs), Volume 377, Article 24, pp. 24:1--24:19, 2026.  
> DOI: https://doi.org/10.4230/LIPIcs.SAT.2026.24

The implementation performs exact symbolic reasoning for nonlinear Stochastic Satisfiability Modulo Theories (SSMT) formulas. It supports existential, universal, and randomized quantification and uses Cylindrical Algebraic Decomposition (CAD) through the Wolfram|Alpha API, together with SymPy for symbolic manipulation and Z3 for satisfiability/equivalence checks.

## Repository Structure

```text
.
├── CAD.py              # Interface to Wolfram|Alpha for CAD queries
├── SSMT.py             # Main SSMT solving procedure
├── runner.py           # Command-line benchmark runner
├── parse_CAD.py        # Parser for CAD results returned by Wolfram|Alpha
├── auxiliary_func.py   # Expression-processing utilities
├── sat_equiv.py        # Z3-based satisfiability/equivalence checks
├── merge.py            # Constraint/cell merging utilities
├── dominate.py         # Dominance elimination
├── time_count.py       # Runtime accounting utilities
└── TB/                 # Benchmark instances
    ├── base/
    ├── game/
    └── prob/
```

## Requirements

The current implementation requires Python 3.9 or newer and the following Python packages:

- `requests`
- `sympy`
- `z3-solver`

A simple setup is:

```bash
git clone https://github.com/NTU-ALComLab/SSMT.git
cd SSMT

python3 -m venv .venv
source .venv/bin/activate
pip install requests sympy z3-solver
```


## Wolfram|Alpha API AppID

The solver sends `CylindricalDecomposition` queries to the Wolfram|Alpha Full Results API. Therefore, before running the program, you must provide your own Wolfram|Alpha **AppID**.

1. Obtain an AppID from the Wolfram|Alpha Developer Portal:
   https://developer.wolframalpha.com/
2. Open `CAD.py`.
3. Replace the empty `app_id` string with your own AppID:

```python
app_id = "YOUR_WOLFRAMALPHA_APP_ID"
```

Do not commit or publish your private AppID in a public repository.

## Running the Benchmarks

Run the commands below from the repository root. `runner.py` provides three modes: `case`, `family`, and `all`.

### 1. Run a Single Test Case

Use `case` mode and provide the path to one JSON benchmark file:

```bash
python3 runner.py case TB/base/ex1.json
```

The selected JSON file is loaded and passed to the SSMT solver.

### 2. Run a Benchmark Family

Use `family` mode and provide a directory containing JSON benchmark files:

```bash
python3 runner.py family TB/base
```

For example, the benchmark families included in this repository can be run with:

```bash
python3 runner.py family TB/base
python3 runner.py family TB/game
python3 runner.py family TB/prob
```

All `*.json` files directly inside the selected directory are executed in sorted filename order.

### 3. Run All Benchmark Families

Use `all` mode to run every benchmark family under `TB/`:

```bash
python3 runner.py all
```

This runs the benchmark directories such as `TB/base`, `TB/game`, and `TB/prob` sequentially.

## Output

For every benchmark case, `runner.py` redirects the solver's detailed standard output to a log file under the `log/` directory:

```text
log/<testcase-name>.log
```

For example:

```bash
python3 runner.py case TB/base/ex1.json
```

produces:

```text
log/ex1.log
```

The terminal only reports which testcase is being executed and where its log file is saved.

## Test Case Format

Each benchmark is represented as a JSON object. For example, `TB/base/ex1.json` has the following structure:

```json
{
  "vars": ["x", "y", "z"],
  "var_range": {
    "x": "0<=x<=1",
    "y": "0<=y<=1",
    "z": "0<=z<=1"
  },
  "var_dist": {
    "x": "Uniform(0,1)",
    "z": "Uniform(0,1)"
  },
  "condition": [
    "y>=x",
    "y<=z"
  ],
  "quant": ["r", "e", "r"],
  "ranges": [1, null, 1]
}
```

The fields are interpreted as follows:

| Field | Description |
| --- | --- |
| `vars` | Variables in quantifier order. |
| `var_range` | Domain constraint for each variable. The expressions use Wolfram-style arithmetic/inequality syntax. |
| `var_dist` | Probability distribution for randomized (`r`) variables. The supplied benchmarks primarily use `Uniform(...)`. |
| `condition` | List of formula constraints. The constraints in the list are conjoined before the initial CAD query. |
| `quant` | Quantifier type for each variable. `e` = existential, `a` = universal/adversarial, and `r` = randomized. |
| `ranges` | Normalization range associated with each variable. For non-randomized variables this is normally `null`; for a uniform randomized variable this is the width of its sampling interval and may be a numeric value or a symbolic expression such as `"b-a"`. |

The entries in `vars`, `quant`, and `ranges` must correspond position by position. For example,

```json
"vars":   ["x", "y", "z"],
"quant":  ["e", "a", "r"],
"ranges": [null, null, "2x+2y+1"]
```

means that `x` is existentially quantified, `y` is universally quantified, and `z` is randomized.

## Benchmark Families

The supplied testbench is organized into three groups:

- `TB/base/`: baseline and generated SSMT examples.
- `TB/game/`: strategic/game-style examples containing existential, universal, and randomized choices.
- `TB/prob/`: probabilistic benchmark instances.

These benchmarks correspond to the kinds of examples evaluated in the accompanying SAT 2026 paper.

## Citation

If you use this implementation, please cite:

```bibtex
@InProceedings{lin_et_al:LIPIcs.SAT.2026.24,
  author    = {Lin, Jung-Cheng and Su,```bibtex
@InProceedings{lin_et_al:LIPIcs.SAT.2026.24,
  author =	{Lin, Jung-Cheng and Su, Chia-Hsuan and Jiang, Jie-Hong R. and Unno, Hiroshi},
  title =	{{Exact Symbolic Reasoning for Nonlinear Stochastic SMT via Cylindrical Algebraic Decomposition}},
  booktitle =	{29th International Conference on Theory and Applications of Satisfiability Testing (SAT 2026)},
  pages =	{24:1--24:19},
  series =	{Leibniz International Proceedings in Informatics (LIPIcs)},
  ISBN =	{978-3-95977-431-4},
  ISSN =	{1868-8969},
  year =	{2026},
  volume =	{377},
  editor =	{Ignatiev, Alexey and Szeider, Stefan},
  publisher =	{Schloss Dagstuhl -- Leibniz-Zentrum f{\"u}r Informatik},
  address =	{Dagstuhl, Germany},
  URL =		{https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2026.24},
  URN =		{urn:nbn:de:0030-drops-263307},
  doi =		{10.4230/LIPIcs.SAT.2026.24},
  annote =	{Keywords: Stochastic Satisfiability Modulo Theories (SSMT), Cylindrical Algebraic Decomposition (CAD), Quantifier Elimination}
}
```

## Paper

The paper is available through the LIPIcs/Dagstuhl proceedings:

https://doi.org/10.4230/LIPIcs.SAT.2026.24
