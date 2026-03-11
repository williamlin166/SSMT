from z3 import *
from time_count import cumulative_timer

def eval_expr(expr_str, env):
    # Replace rational literals like '1/3' with Q(1,3)
    import re
    def replace_frac(match):
        num, den = match.groups()
        return f"Q({num},{den})"
    expr_fixed = re.sub(r'(\d+)/(\d+)', replace_frac, expr_str)
    return eval(expr_fixed, {}, env)

@cumulative_timer
def check_equivalance(vars_str, left_constraints_str, right_constraints_str, verbose = False):
  # print("check:", vars_str, left_constraints_str, right_constraints_str)

  # if any(any("sqrt" in c_ for c_ in c) for c in left_constraints_str) or any(any("sqrt" in c_ for c_ in c) for c in right_constraints_str): 
    # print("We don't suppor sqrt, returning False")
    # return False
  # variables
  vars = Reals(vars_str)
  env = {name: var for name, var in zip(vars_str.split(), vars)}
  env.update({"And": And, "Or": Or, "Not": Not, "Q": Q, "Sqrt": Sqrt})

  left_constraints = [[eval_expr(expr, env) for expr in const] for const in left_constraints_str]
  A = Or(*(And(*const) for const in left_constraints))
  if verbose:
    print("A:", A)

  right_constraints = [[eval_expr(expr, env) for expr in const] for const in right_constraints_str]
  B = Or(*(And(*const) for const in right_constraints))
  if verbose:
    print("B:", B)

  # check if A == B
  s = Solver()
  # s.add(Not(A == B))
  s.add(Xor(A, B))

  if s.check() == unsat:
    if verbose:
      print("A == B ✅")
    return True
  else:
    if verbose:
      print("A does NOT == B ❌")
      print("Counterexample:", s.model())
    return False

def is_satisfiable(vars_str, constraints_str, verbose=False):
    if verbose: 
        print("is_satisfiable:", vars_str, constraints_str)
    # if any(any("sqrt" in c_ for c_ in c) for c in constraints_str): 
    #     print("We don't suppor sqrt, returning False")
    #     return False
    vars = Reals(vars_str)
    env = {name: var for name, var in zip(vars_str.split(), vars)}
    env.update({"And": And, "Or": Or, "Not": Not, "Sqrt": Sqrt})

    constraints = [[eval(expr, {}, env) for expr in const]
                   for const in constraints_str]

    A = Or(*(And(*const) for const in constraints))

    s = Solver()
    s.add(A)

    result = s.check()

    if verbose:
        print("Formula:", A)
        print("Result:", result)
        if result == sat:
            print("Model:", s.model())

    return result == sat

def main(): 
  check_equivalance(
      't x y z',
      [['0<=t', 't<=1', '0<=x', 'x<1', 'x<=y', 'y<1', 'y<=z', 'z<=1'], ['0<=t', 't<=1', '0<=x', 'x<=1', 'y == 1', 'z == 1']],
      [['0<=t', 't<=1', '0<=x', 'x<=1', 'x<=y', 'y<=1', 'y<=z', 'z<=1']],
      True
  )

if __name__ == "__main__":
    main()

