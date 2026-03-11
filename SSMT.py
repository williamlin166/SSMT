import time
import itertools
import sympy as sp
import string
import re
from auxiliary_func import var_range_sanity_check, z3_preprocess, fix_expression, wrap, negate_not_equal, replace_vars, latex_parser
from CAD import get_wolfram_result
from sat_equiv import check_equivalance, is_satisfiable
from merge import merge_constraints
from dominate import remove_dominated

def ssmt(vars, var_range, var_dist, condition, quant, ranges): 
  start = time.time()

  # vars = ['x', 'y', 'z']
  # var_range = {'x': '0<=x<=1/2', 'y': '0<=y<=1/2', 'z': '-(x+y+1/2)<=z<=x+y+1/2'}
  # var_dist = {'z': 'Uniform(-(x+y+1/2),x+y+1/2)'}
  # condition = ['((x + y <= 1/2 && 40x - 40y + 10z + 100 >= 85) || (x + y > 1/2 && -80x - 160y + 10z + 160 >= 85))']
  # quant = ['e', 'a', 'r']
  # ranges = [None, None, '2x+2y+1']

  var_range_sanity_check(var_range)
  assert(len(vars) == len(quant))
  for q_ in quant:
    assert(q_ in ['a', 'r', 'e'])
    
  range_constraints = [r_ for r_ in var_range.values() if r_]
  cd_query = 'CylindricalDecomposition[' + '&&'.join(range_constraints) + ('' if len(range_constraints) == 0 else '&&') + '&&'.join(condition) + ',('+ ','.join(vars) + ')]'
  print("cd_query:", cd_query)
  cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars, False)
  print(cd_result)

  cd_result = [
      [item.replace(" = ", "=") for item in sublist]
      for sublist in cd_result
  ]

  def reduce_cells(cd_result, vars):
    while(True):
      eq_pair = {}
      for i, j in itertools.combinations(range(len(cd_result)), 2):
        a = z3_preprocess(cd_result[i])
        b = z3_preprocess(cd_result[j])
        merge = merge_constraints(cd_result[i], cd_result[j], vars)

        if check_equivalance(' '.join(vars), [a, b], [z3_preprocess(merge)]) and len(merge) == len(vars):
          # print("merge:", merge)
          eq_pair[(i, j)] = merge
      # print(eq_pair)
      if not eq_pair:
        break

      # greedy matching

      used = set()
      chosen_merges = {}   # index (representative) -> merged_constraint
      for (i, j), merged in sorted(eq_pair.items()):
          if i not in used and j not in used:
              used.add(i)
              used.add(j)
              chosen_merges[i] = merged

      # update cd_result

      new_cd_result = []
      for idx, c in enumerate(cd_result):
          if idx in chosen_merges:
              new_cd_result.append(chosen_merges[idx])
          elif idx not in used:
              new_cd_result.append(c)

      cd_result = new_cd_result
    return cd_result

  cd_result = reduce_cells(cd_result, vars)

  # print(cd_result)
  for c in cd_result:
    print(c)
    
  # input("Press Enter to Continue: ")

  allowed_letters = [c for c in string.ascii_lowercase if c not in {"e", "i"}]

  if len(vars) <= len(allowed_letters) / 2:
    # use a-z instead
    var_map = {vars[i]: allowed_letters[2*i + 1] for i in range(len(vars))}
  else:
    var_map = {vars[i]: f"x_{i*2+1}" for i in range(len(vars))}
  print("changing variable according to:", var_map)

  cd_result = [[replace_vars(var_map, s) for s in sublist] for sublist in cd_result]
  print(cd_result)

  vars_orig = vars
  vars = list(var_map.values())
  print(vars)
  var_range_orig = var_range
  var_range = {var_map[k]: replace_vars(var_map, v) for k, v in var_range.items()}
  print(var_range)
  var_dist_orig = var_dist
  var_dist = {var_map[k]: replace_vars(var_map, v) for k, v in var_dist.items()}
  print(var_dist)

  # change intervals into probability expressions

  for v in vars:
    _ = sp.symbols(v)

  pe = []
  for intrvl in cd_result:
    pe.append((intrvl, '1'))

  print("pe:", pe)

  confirmed_false_part_history = []
  full_history = []

  while len(vars):
    intrvls_new = []

    v = vars.pop()
    print("v:", v)
    v_syb = sp.symbols(v)
    q = quant.pop()
    print("q:", q)
    r = ranges.pop()
    if type(r) == str:
      r = sp.symbols(replace_vars(var_map, r))
    print("r:", r)

    if q == 'r':
      # Calculate the integral
      for intrvl in pe:
        intrvl, prob_pe = intrvl
        if len(intrvl) == 0:
          intrvls_new.append(([], prob_pe))
          assert len(pe) == 1
          continue
        intrvl, intrvl_v = intrvl[0:-1], intrvl[-1]
        dist = var_dist[v]
        if "Gauss" in dist:
          mu, sigma_sqr = dist.split("(")[1].rstrip(")").split(",")
          mu, sigma = sp.sympify(mu), sp.sqrt(sp.sympify(sigma_sqr))
          if len(re.split('<=|<', intrvl_v)) == 2:
            left, right = re.split('<=|<', intrvl_v)
            assert left == v
            right = sp.sympify(right)
            prob = sp.Rational(1, 2) * (1 + sp.erf((right - mu) / (sigma * sp.sqrt(2)))) * sp.sympify(prob_pe)
            intrvl = (intrvl, prob)
            print(intrvl)
            intrvls_new.append(intrvl)
          elif len(re.split('>=|>', intrvl_v)) == 2:
            left, right = re.split('>=|>', intrvl_v)
            assert left == v
            right = sp.sympify(right)
            prob = (1 - sp.Rational(1, 2) * (1 + sp.erf((right - mu) / (sigma * sp.sqrt(2))))) * sp.sympify(prob_pe)
            intrvl = (intrvl, prob)
            print(intrvl)
            intrvls_new.append(intrvl)
          else:
            raise ValueError("Gauss of this form not supported")
        elif '<' in intrvl_v:
          print("\ninterval:", intrvl_v)
          intrvl_v = re.split('<=|<', intrvl_v)
          left = sp.sympify(fix_expression(intrvl_v[0]))
          right = sp.sympify(fix_expression(intrvl_v[-1]))
          prob = 1/r if str(type(r)) == "<class 'sympy.core.symbol.Symbol'>" else sp.Rational(1, r)
          print("prob:", prob)
          prob_pe = sp.sympify(prob_pe)
          integral = sp.simplify(sp.integrate(prob_pe * prob, (v_syb, left, right)))
          # print(str(sp.latex(integral)), "vs", str(integral))
          # if str(sp.latex(integral)).count("frac") == 1 and str(sp.latex(integral)).startswith("\\frac"):
            # m = re.fullmatch(r'\\frac\{([^}]*)\}\{([^}]*)\}', str(sp.latex(integral)))
            # if m:
              # num, den = m.groups()
              # num, den = num.replace(r"\left(", "(").replace(r"\right)", ")"), den.replace(r"\left(", "(").replace(r"\right)", ")")
              # if not '\\' in num and not '\\' in den:
                # integral = f'{wrap(num)}/{wrap(den)}'
              # else:
                # integral = str(integral)
            # else:
              # raise ValueError("Invalid fraction")
              # integral = str(integral)
          # else:
            # integral = str(integral)
          print(sp.latex(integral))
          integral = latex_parser(sp.latex(integral))
          print("integral:", integral)
          for i in range(len(intrvl)):
            intrvl[i] = fix_expression(intrvl[i])
          intrvl = (intrvl, integral)
          intrvls_new.append(intrvl)
        # else:
        #   intrvls_new.append(([], 0))
      print("Before cleaning:", intrvls_new)
      intrvls_new = [([], 0)] if len(intrvls_new) == 0 else intrvls_new
      intrvls_new = remove_dominated(intrvls_new, vars, 'r')
    elif q == 'e':
      for intrvl in pe:
        # intrvl, intrvl_v = intrvl[0:-1], intrvl[-1]
        # assert v in intrvl_v
        # intrvls_new.append(intrvl)

        intrvl, prob_pe = intrvl
        if len(intrvl) == 0:
            intrvls_new.append(([], prob_pe))
            assert len(pe) == 1
            continue
        intrvl_clean = [i_ for i_ in intrvl if i_]
        if len(vars_orig) <= 13:
          t = chr(ord(v)-1) if chr(ord(v)-1) in allowed_letters else chr(ord(v)-2)
        else:
          t = "x_" + str(int(v[2:]) - 1)
        cd_query = 'CylindricalDecomposition [(' + '&&'.join(intrvl_clean) + "&&" + str(prob_pe) + "=" + t + '),(' + ','.join(vars + [t, v]) + ')]'
        print(cd_query)
        cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars + [t, v], False)
        # cd_result = reduce_cells([intrvl[:-1] for intrvl in cd_result], vars + [t])
        cd_result = reduce_cells(cd_result, vars + [t, v])
        print(cd_result)
        for intrvl in cd_result:
          t_range = re.split(r'(<=|>=|<|>| = |=)', intrvl[-2])
          t_max = t_range[-1]

          print("NEXT:", (list(map(fix_expression, intrvl[:-2])),
                    fix_expression(t_max)), "witness:", intrvl[-1])
          intrvls_new.append((list(map(fix_expression, intrvl[:-2])),
                      fix_expression(t_max)))
      print("Before cleaning:", intrvls_new)
      intrvls_new = remove_dominated(intrvls_new, vars, 'e')
    elif q == 'a':

      coverage = [z3_preprocess(intrvl) for intrvl, _ in pe]
      var_range_z3 = z3_preprocess([var_range[x] for x in vars + [v] if var_range[x]])
      full = check_equivalance(' '.join(vars + [v]), coverage, [var_range_z3], False)
      if full:
        print("Full coverage. No space for forall to falsify. ")

      i = 0
      while i < len(pe): # for intrvl in pe:
        intrvl, prob_pe = pe[i]
        # intrvl, intrvl_v = intrvl[0:-1], intrvl[-1]
        # if intrvl_v == range:
        #   intrvls_new.append(intrvl)
        intrvl = [negate_not_equal(intrvl_) for intrvl_ in intrvl]
        if len(intrvl) == 0:
          intrvls_new.append(([], prob_pe))
          i += 1
          assert len(pe) == 1 and i == 1
          continue
        if not full:
          # First, we check for "unsatisfiability"
          # Check history first
          if any(his == intrvl[:-1] for his in confirmed_false_part_history): 
            print("Skip a lot of CAD from history since", intrvl[:-1], "is checked before")
            i += 1
            continue
          if any(his == intrvl[:-1] for his in full_history): 
            print("Skip a lot of CAD from history since", intrvl[:-1], "is checked before")
            cd_result = [["False"]]
          elif not intrvl[-1]: 
            print("Skip the CAD since forall can't falsify this cell")
            cd_result = [["False"]]
          else: 
            print("Check for UNSAT: ")
            cd_query = 'CylindricalDecomposition[(' + '&&'.join(filter(None, intrvl[:-1])) + ("" if len(list(filter(None, intrvl[:-1])))==0 else "&&") + (var_range[v] + '&&' if var_range[v] else "") + "!(" + intrvl[-1] + ")),(" + ','.join(vars + [v]) + ')]'
            print(cd_query)
            cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars + [v], False)
            print(cd_result)

          if cd_result != [["False"]]:
            # There are strategies that forall can falsify this cell
            print("Remove area that other cells have covered: ")
            sat_cube = []
            for j, item in enumerate(pe):
              if j != i:
                # remove = "Not(And(" + ", ".join(z3_preprocess(item[0])) + "))"
                # print("check overlap:", remove)
                # if is_satisfiable(
                #     ' '.join(vars + [v]),
                #     [z3_preprocess(intrvl) + [remove]], False):
                #   sat_cube.append(item[0])
                if is_satisfiable(
                    ' '.join(vars + [v]),
                    [z3_preprocess(c + item[0]) for c in cd_result], False):
                  sat_cube.append(item[0])
            merge = "(" + ")&&!(".join(
                  "&&".join([negate_not_equal(c_) for c_ in c if c_])
                  for c in sat_cube) + ")"
            if merge == "()": 
              print("Skip the CAD since merge is empty")
              # keep cd_result the same
              # cd_result = [["False"]]
            else: 
              print("merge:", merge)
              if len(cd_result) == 1 and '&&'.join(cd_result[0]) == merge[1:-1]: 
                print("Skip CAD since", '&&'.join(cd_result[0]), "==", merge[1:-1])
                cd_result = [["False"]]
              else: 
                cd_query ='CylindricalDecomposition[((' + ')||('.join('&&'.join(map(negate_not_equal, item)) for item in cd_result) + '))' + ("&&!" if merge!="" else "") + merge + ("" if merge!="" else "") + ",(" + ','.join(vars + [v]) + ')]'
                print(cd_query)
                confirmed_false_part = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars + [v], False)
                if confirmed_false_part == []: 
                  # It has failed -> try to divide and conquer
                  for item in cd_result: 
                    cd_query ='CylindricalDecomposition[(' + '&&'.join(map(negate_not_equal, item)) + ')' + ("&&!" if merge!="" else "") + merge + ("" if merge!="" else "") + ",(" + ','.join(vars + [v]) + ')]'
                    print(cd_query)
                    false_part = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars + [v], False)
                    print(false_part)
                    if false_part != [["False"]]: 
                      for f_ in false_part: 
                        confirmed_false_part.append(f_)
                print(confirmed_false_part)
                cd_result = confirmed_false_part
            # If this is the last one, and we don't get False, the whole formula is false
            if len(vars) == 0 and cd_result != [["False"]]:
              intrvls_new.append(([], '0'))
              i += 1
              continue
            if cd_result != [["False"]]: 
              for item in cd_result:
                confirmed_false_part_history.append(item[:-1])
              print("Remove confirmed false part: ")
              if len(intrvl)>1 and len(cd_result) == 1 and intrvl[:-1] == cd_result[0][:-1]: 
                print("Skip CAD since", '&&'.join(intrvl[:-1]), "==", '&&'.join(cd_result[0][:-1]))
                cd_result = [["False"]]
              else: 
                cd_query = 'CylindricalDecomposition[' + '&&'.join(filter(None, intrvl[:-1])) + ("" if len(list(filter(None, intrvl[:-1])))==0 else "&&") + '!((' + ') || ('.join('&&'.join(item[:-1]) for item in cd_result) + ')),('+ ','.join(vars) + ')]'
                print(cd_query)
                cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars, False)
                print(cd_result)
              if cd_result == [["False"]]: 
                # This cell is UNSAT-able by forall
                # intrvls_new.append(([], '0'))
                i += 1
                continue
              if len(cd_result) > 1:
                for c_ in cd_result[1:]:
                  pe.append((c_, prob_pe))
              intrvl = cd_result[0] + intrvl[-1:] # [var_range[v]]
            else: 
              # Add to full history
              full_history.append(intrvl[:-1])
        if len(vars_orig) <= 13:
          t = chr(ord(v)-1) if chr(ord(v)-1) in allowed_letters else chr(ord(v)-2)
        else:
          t = "x_" + str(int(v[2:]) - 1)
        intrvl_clean = [i_ for i_ in intrvl if i_]
        cd_query = 'CylindricalDecomposition [(' + '&&'.join(intrvl_clean) + '&&' + str(prob_pe) + "=" + t + '),(' + ','.join(vars + [t, v]) + ')]'
        # cd_query = 'CylindricalDecomposition [(' + '&&'.join(intrvl) + "&&" + str(prob_pe) + "=" + t + ')||(!(' + \
        #                         '&&'.join(intrvl) + ")&&" + "0=" + t + '),('+ ','.join(vars + [t, v]) + ')]'
        print(cd_query)
        cd_result = get_wolfram_result(cd_query, ["Solutions", "Solution"], vars + [t, v], False)
        cd_result = reduce_cells([intrvl[:-1] for intrvl in cd_result], vars + [t])
        print(cd_result)
        for intrvl in cd_result:
          t_range = re.split(r'(<=|>=|<|>| = |=)', intrvl[-1])
          if len(t_range) == 3 and (t_range[1] == ' = ' or t_range[1] == '='):
            t_min = t_range[-1]
          else:
            t_min = t_range[0]

          print("NEXT:", (list(map(fix_expression, intrvl[:-1])),
                    fix_expression(t_min)))
          intrvls_new.append((list(map(fix_expression, intrvl[:-1])),
                      fix_expression(t_min)))
        i += 1

      print("Before cleaning:", intrvls_new)
      # if not any(any(v in intrvl[1] for intrvl in intrvls_new) for v in vars):
      #   values = [Fraction(intrvl[1]) for intrvl in intrvls_new]
      #   intrvls_new = [intrvls_new[values.index(min(values))]]
      intrvls_new = remove_dominated(intrvls_new, vars, 'a')

    intrvls_new = [(i_ if any(i__ for i__ in i_) else [], p_) for i_, p_ in intrvls_new]
    print()
    print(intrvls_new)

    pe = intrvls_new

  # intrvls_new = '(' + ') || ('.join(list(map(' && '.join, intrvls_new))) + ')'
  # print()
  # print(intrvls_new)

  end = time.time()
  print("Elapsed time:", end - start, "seconds")
  print(f"Time spent on CAD: {get_wolfram_result.total_time} seconds")
  print(f"Time spent on Checking Eq: {check_equivalance.total_time} seconds")