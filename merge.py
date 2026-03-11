import re
from typing import List, Tuple
from auxiliary_func import z3_preprocess, fix_expression, insert_empty_string
from sat_equiv import check_equivalance

# -----------------------------
# Tokenization & parsing
# -----------------------------
def tokenize(s: str) -> List[str]:
    pattern = r'(<=|>=|<|>|=)'
    tokens = re.split(pattern, s) #s.replace(" ", ""))
    return [t.strip() for t in tokens if t]

def parse_chain(chain: str) -> List[Tuple[str, str, str]]:
    t = tokenize(chain)
    return [(t[i], t[i+1], t[i+2]) for i in range(0, len(t)-2, 2)]

def rebuild_chain(values: List[str], ops: List[str]) -> str:
    return "".join(v + o for v, o in zip(values, ops)) + values[-1]


# -----------------------------
# Operator upgrade (preserves your semantics)
# -----------------------------
def upgrade_op(op: str, ops_seen: set) -> str:
    if ops_seen == {'='}: return '='
    if ops_seen == {'<'}: return '<'
    if ops_seen == {'>'}: return '>'
    if ops_seen <= {'<', '<='}: return '<='
    if ops_seen <= {'>', '>='}: return '>='
    if '=' in ops_seen:
        if any(o in ('<', '<=') for o in ops_seen): return '<='
        if any(o in ('>', '>=') for o in ops_seen): return '>='
    return op


# ====================================================================
#                     SHORT REWRITE OF MERGING LOGIC
# ====================================================================
def merge_constraints(list1: List[str], list2: List[str], varlist: List[str]) -> List[str]:
    # print(list1, list2, varlist)
    assert len(varlist) == len(list1) == len(list2)

    # Track variables that become "strong" (assigned via equality)
    strong_vars = set()
    var_order = {v: i for i, v in enumerate(varlist)}
    final_result = []

    # -------------------------------------------------------------
    # Process each variable independently (per index)
    # -------------------------------------------------------------
    for i, var in enumerate(varlist):

        # Collect the two constraints for this variable
        group = []
        if list1[i]: group.append(list1[i])
        if list2[i] and list2[i] != list1[i]:
            group.append(list2[i])

        if not group:
            continue

        # --------------------------------------------
        # Gather all op-sets among variable pairs
        # --------------------------------------------
        pair_ops = {}
        for c in group:
            for a, op, b in parse_chain(c):
                key = frozenset([a, b])
                pair_ops.setdefault(key, set()).add(op)

        # --------------------------------------------
        # Rebuild constraints with upgraded operators
        # --------------------------------------------
        rebuilt = []
        for c in group:
            triples = parse_chain(c)
            assert all(len(t) >= 3 for t in triples)
            values = [triples[0][0]] + [t[2] for t in triples]
            ops = [
                upgrade_op(op, pair_ops[frozenset([l, r])])
                for l, op, r in triples
            ]
            rebuilt.append(rebuild_chain(values, ops))

        # print("rebuilt:", rebuilt)
        # Deduplicate
        unique = []
        seen = set()
        for ch in rebuilt:
            if ch not in seen:
                seen.add(ch)
                unique.append(ch)
        # print("unique:", unique)

        semantic_unique = []
        for ch in unique:
            expr_ch = z3_preprocess([ch])[0]
            redundant = False
            for kept in semantic_unique:
                expr_kept = z3_preprocess([kept])[0]

                if check_equivalance(
                    " ".join(varlist[:i+1]),
                    [[expr_ch]],
                    [[expr_kept]]
                ):
                    redundant = True
                    break

            if not redundant:
                semantic_unique.append(ch)
        # print("semantic_unique:", semantic_unique)
        unique = semantic_unique

        parsed = {ch: parse_chain(ch) for ch in unique}

        # --------------------------------------------
        # Extract strong/equality variable info
        # --------------------------------------------
        # eq_pairs = []
        for c in group:
            for a, op, b in parse_chain(c):
                if op == '=':
                    strong_vars.add(a)
                    # eq_pairs.append((a, b))
        # print("strong_vars:", strong_vars)
        def involves_strong(v):
            return any(sv in v for sv in strong_vars)

        # ---------------------------------------------------
        # Redundancy check using your original intention
        # ---------------------------------------------------
        def implied(small, big):

            def order_ok(a, c, x, z):
                # later variable cannot influence earlier variable
                return max(var_order.get(a, -1), var_order.get(c, -1)) <= \
                       max(var_order.get(x, -1), var_order.get(z, -1))

            for a, b, c in small:
                found = False
                for x, y, z in big:

                    same_pair = {a, c} == {x, z}

                    strong_match = (
                        (involves_strong(x) and c == z) or
                        (involves_strong(z) and a == x)
                    ) and order_ok(a, c, x, z)

                    if (same_pair or strong_match):
                        # Check operator implication
                        if (
                            (b in ['<', '<=', '='] and y == '<=') or
                            (b in ['>', '>='] and y == '>=') or
                            b == y
                        ):
                            found = True
                            break
                if not found:
                    return False
            return True

        # ---------------------------------------------------
        # Keep only non-implied constraints (list1 dominates)
        # ---------------------------------------------------
        group_result = []
        for ch in unique:
            if not any(ch != other and implied(parsed[ch], parsed[other]) for other in unique):
                group_result.append(ch)

        final_result.extend(group_result)

    # print("Before insert empty string:", final_result)
    # return insert_empty_string(final_result, varlist)
    return final_result

def main(): 
  # --- Example ---
  # list1 = ['0<=t<=1', '0<=x<1', 'x<=y<1', 'y<=z<=1']
  # list2 = ['0<=t<=1', '0<=x<=1', 'y=1', 'z=1']
  # varlist = ['t', 'x', 'y', 'z']
  # list1 = ['a>=2', 'a<=b<=a+1', 'c=b', '0<=t_1<b-1', 't_1+1<=t_2<=b', 't_1+1<=t_3<=b']
  # list2 = ['a>=2', 'a<=b<=a+1', 'c=b', 't_1=b-1', 't_2=b', 't_3=b']
  # varlist = ['a', 'b', 'c', 't_1', 't_2', 't_3']
  # list1 = ['a>=2', 'a<=b<=a+1', 'c>b', '0<=t_1<b-1', 't_1+1<=t_2<=b', 't_1+1<=t_3<=c']
  # list2 = ['a>=2', 'a<=b<=a+1', 'c>b', 't_1=b-1', 't_2=b', 'b<=t_3<=c']
  # list1 = ['x>=3']
  # list2 = ['3>=x']
  # varlist = ['x']
  list1 = ['2/3<b<=1']
  list2 = ['b = 2/3']
  varlist = ['b']
  print(merge_constraints(list1, list2, varlist))

if __name__ == "__main__": 
  main()