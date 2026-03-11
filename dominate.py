import sympy as sp
import re
from fractions import Fraction
from itertools import combinations
from sat_equiv import check_equivalance, is_satisfiable
from auxiliary_func import z3_preprocess
from CAD import get_wolfram_result

def deduplicate_intrvls(intrvls):
  seen = set()
  unique = []

  for intrvl in intrvls:
    key = (tuple(intrvl[0]), intrvl[1])
    if key not in seen:
      seen.add(key)
      unique.append(intrvl)

  return unique

def has_no_vars(intrvl, vars):
  return not any(v in intrvl[1] for v in vars)

def check_disjoint(intrvls, vars): 
  for a, b in combinations(intrvls, 2): 
    if is_satisfiable(' '.join(vars), [z3_preprocess(a) + z3_preprocess(b)]): 
      return a, b
  return None, None

def remove_dominated(intrvls, vars, q):
  keep = []
  assert q in ['a', 'e', 'r']

  if intrvls == []: 
    return [([], '0')]

  new_intrvls = []
  for i, a in enumerate(intrvls):
    a_0 = a[0].copy()
    for j, b in enumerate(intrvls):
      if i == j or a[0] == b[0]:
        continue
      contain = check_equivalance(' '.join(vars), [z3_preprocess(a_0), [f"Not(And({', '.join(z3_preprocess(b[0]))}))"]], [[]], False)
      if contain: 
        print(i, j, a_0, b[0])
      if contain: 
        if len(a_0) == 1 and len(b[0]) == 1:
          split_a_0 = re.split(r'(<=|>=|<|>| = |=)', a_0[0])
          split_a = re.split(r'(<=|>=|<|>| = |=)', a[0][0])
          split_b = re.split(r'(<=|>=|<|>| = |=)', b[0][0])
          if len(split_a_0) == 5: 
            if len(split_b) == 5: 
              if split_a_0[0] == split_b[0] and split_a_0[4] == split_b[4]: 
                if split_a_0[1] == "<=" and split_b[1] == "<": 
                  new_intrvls.append(([split_a_0[2] + " = " + split_a_0[0]], a[1]))
                  intrvls[i][0][0] = split_a_0[0] + "<" + split_a_0[2] + split_a[3] + split_a_0[4]
                  print(f"modified {intrvls[i][0][0]}, adding {new_intrvls}")
                if split_a_0[3] == "<=" and split_b[3] == "<": 
                  new_intrvls.append(([split_a_0[2] + " = " + split_a_0[4]], a[1]))
                  intrvls[i][0][0] = split_a_0[0] + split_a[1] + split_a_0[2] + "<" + split_a_0[4]
                  print(f"modified {intrvls[i][0][0]}, adding {new_intrvls}")
            elif len(split_b) == 3 and (split_b[1] == " = " or split_b[1] == "="):
              if split_a_0[0] == split_b[2] and split_a_0[1] == "<=": 
                new_intrvls.append(([split_a_0[2] + " = " + split_a_0[0]], a[1]))
                intrvls[i][0][0] = split_a_0[0] + "<" + split_a_0[2] + split_a[3] + split_a_0[4]
                print(f"modified {intrvls[i][0][0]}, adding {new_intrvls}")
              if split_a_0[4] == split_b[2] and split_a_0[3] == "<=": 
                new_intrvls.append(([split_a_0[2] + " = " + split_a_0[4]], a[1]))
                intrvls[i][0][0] = split_a_0[0] + split_a[1] + split_a_0[2] + "<" + split_a_0[4]
                print(f"modified {intrvls[i][0][0]}, adding {new_intrvls}")

  print("After chopping:", intrvls, new_intrvls)
  # input("Press Enter: ")
  intrvls += new_intrvls

  intrvls = deduplicate_intrvls(intrvls)
  print("After deduplication:", intrvls)
  used = set()
  # sat = any(i != [] or (p != 0 and p != '0') for i, p in intrvls)
  sat = any((i, p) not in [([], 0), ([], '0')] for i, p in intrvls)

  
  for i, a in enumerate(intrvls):
    if a in [([], 0), ([], '0')] and sat and q != 'a':
      continue
    if i in used:
      continue
    dominated = False
    for j, b in enumerate(intrvls):
      if i == j or j in used:
        continue
      if a[0] == b[0]:
        if q == 'r':
          # print("HERE!!!!!!!!!!!!!!!!!\n", "AAAAAAAAAAAAAA: ", a, "\nBBBBBBBBBBBBBBBBB: ", b)
          # combined_rhs = str(sp.simplify(f"{a[1]} + {b[1]}"))
          a_expr = sp.sympify(a[1]) if isinstance(a[1], str) else a[1]
          b_expr = sp.sympify(b[1]) if isinstance(b[1], str) else b[1]
          combined_rhs = str(sp.simplify(a_expr + b_expr))
          a = (a[0], combined_rhs)
          used.add(j)
          continue
        if has_no_vars(a, vars) and has_no_vars(b, vars):
          if q == 'e' and Fraction(b[1]) > Fraction(a[1]) or q == 'a' and Fraction(b[1]) < Fraction(a[1]):
            dominated = True
            break
        else:
          if i < j:
            cd_query = 'CylindricalDecomposition[' + '&&'.join(a[0]) + '&&' + a[1] + '=' + b[1] + ',('+ ','.join(vars) + ')]'
            print(cd_query)
            cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars, False)
            assert len(cd_result) == 1 # deal with other cases later
            print(cd_result)
            if not cd_result == [['False']]:
              keep.append((cd_result[0], a[1]))
          if (q == 'a' and (a[1] == '1' or b[1] == '0')) or (q == 'e' and (a[1] == '0' or b[1] == '1')):
            print("Skip CAD since", a[1] + ('<' if q == 'a' else '>') + b[1], "is always False")
            cd_result = [['False']]
          else: 
            cd_query = 'CylindricalDecomposition[' + '&&'.join(a[0]) + '&&' + a[1] + ('<' if q == 'a' else '>') + b[1] + ',('+ ','.join(vars) + ')]'
            print(cd_query)
            cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars, False)
            assert len(cd_result) == 1 # deal with other cases later
            print(cd_result)
          if not cd_result == [['False']]:
            a = (cd_result[0], a[1])
          else:
            dominated = True
            break
      # else: 
        # print(f"Or(And({', '.join(z3_preprocess(a[0]))}), And({', '.join(z3_preprocess(b[0]))}))")
        # contain = check_equivalance(' '.join(vars), [z3_preprocess(a[0]), [f"Not(And({', '.join(z3_preprocess(b[0]))}))"]], [[]], False)
        # print(i, j, a[0], b[0], contain)

    if not dominated:
      keep.append(a)
    
  int_a, int_b = check_disjoint([intrvl for intrvl, _ in keep], vars)
  if int_a and int_b: 
    print(f"Found disjoint on cell {int_a} and {int_b}. Do not garantee correctness after this point. ")

  return keep

def main(): 
  print(remove_dominated(
      [(['-5<=b<=5'], '1'), (['b = -5'], '0'), (['b = 5'], '1'), 
       (['b = 5'], '1/2'), (['-5<b<5'], '(b + 5)/20'), (['-5<=b<5'], '1')]
      , ['b'], 'a'
  ))

if __name__ == "__main__": 
  main()