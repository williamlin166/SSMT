import re
from typing import List

def split_chain_inequality(expr: str) -> List[str]:
    tokens = re.split(r'\s*(<=|>=|<|>)\s*', expr)
    if len(tokens) < 3 or len(tokens) % 2 == 0:
        return [expr]  # return as-is if not a chain

    out = []
    for i in range(0, len(tokens) - 2, 2):
        out.append(f"{tokens[i]}{tokens[i+1]}{tokens[i+2]}")
    return out


def split_intervals_flat(intervals: List[str]) -> List[str]:
    result = []
    for expr in intervals:
      if expr:
        result.extend(split_chain_inequality(expr))
    return result

def replace_equals(exprs: list) -> list:
    # return [re.sub(r'(?<![<>])=(?!=)', '==', expr) for expr in exprs]
    return [re.sub(r'(?<![<>!])=(?!=)', '==', expr) for expr in exprs]

def replace_sqrt(exprs: list[str]) -> list[str]:
    # Replace sqrt( with Sqrt(
    return [re.sub(r'\bsqrt\s*\(', 'Sqrt(', expr) for expr in exprs]

import re

def replace_power(exprs: list[str]) -> list[str]:
    """
    Handles simple and parenthesized bases.
    """
    new_exprs = []
    # This regex captures:
    # 1. a base: either a word (\w+) or parenthesized expression (\([^)]+\))
    # 2. ^ symbol
    # 3. an exponent: digits or variable (\w+)
    pattern = re.compile(r'(\([^\)]+\)|\w+)\s*\^\s*(\w+|\d+)')
    
    for expr in exprs:
        while '^' in expr:  # loop until all ^ replaced
            expr = pattern.sub(r'\1**\2', expr)
        new_exprs.append(expr)
    return new_exprs

# def z3_preprocess(x: list[str]):
#   return replace_equals(split_intervals_flat([fix_expression(x_) for x_ in x]))
def z3_preprocess(x: list[str]):
    exprs = [fix_expression(x_) for x_ in x]
    exprs = split_intervals_flat(exprs)
    exprs = replace_equals(exprs)
    exprs = replace_sqrt(exprs)
    exprs = replace_power(exprs)
    return exprs

def fix_expression(expr: str) -> str:

    # Insert * between number or closing parenthesis and opening parenthesis
    # expr = re.sub(r'(\d|\))\s*\(', r'\1*(', expr)

    # Insert * between number/variable and variable (e.g., '2 y' -> '2*y', 'y z' -> 'y*z')
    prev = None
    while prev != expr:
      prev = expr
    #   expr = re.sub(r'([a-zA-Z0-9])\s+([a-zA-Z])', r'\1*\2', expr)
      expr = re.sub(r'([0-9a-zA-Z\)])\s+([a-zA-Z\(])', r'\1*\2', expr)

    return expr

def replace_vars(mapping, s):

  # placeholder = "__GAUSS__"
  # s = s.replace("Gauss", placeholder)

  pattern = re.compile(
      # r'\b(' + '|'.join(map(re.escape, mapping.keys())) + r')\b'
      r'(?<![A-Za-z_])(' + '|'.join(map(re.escape, mapping.keys())) + r')(?![A-Za-z_])'
  )
  return pattern.sub(lambda m: mapping[m.group()], s) if s else s

def var_range_sanity_check(d):
  try:
    for d_ in d:
      assert d_ in d
  except:
    print(f"Error! Invalid variable range for variable {d_} and range {d[d_]}!")

def wrap(expr):
  expr = fix_expression(expr)

  # --- Always wrap exponents in parentheses ---
  expr = re.sub(r'\^\{([^}]+)\}', r'^(\1)', expr)

  expr = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", expr)

  return f'({expr})' if ('+' in expr or '-' in expr) and not (expr[0] == "(" and expr[-1] == ")") else expr

def negate_not_equal(expr: str) -> str:
    if "!=" not in expr:
        return expr  # or raise an error if you prefer
    
    left, right = expr.split("!=", 1)
    return f"!({left.strip()}={right.strip()})"

def insert_empty_string(text, var_order):
    s = [[v for v in var_order if v in t] for t in text]
    new_text = ['' for _ in var_order]
    for i, s_ in enumerate(s):
        for j, v_ in enumerate(var_order[::-1]):
            if v_ in s_:
                break
        assert new_text[len(var_order) - j - 1] == ''
        new_text[len(var_order) - j - 1] = text[i]
    return new_text

import re

def replace_cdot(expr: str) -> str:
    """
    Replace \cdot so that everything on the left multiplies
    everything on the right, grouped properly.
    """
    warned = False
    while r'\cdot' in expr:

        if not warned:
            print("Warning: Detected '\\cdot'. ")
            warned = True
        
        idx = expr.find(r'\cdot')

        left = expr[:idx].strip()
        right = expr[idx + len(r'\cdot'):].strip()

        # Wrap both sides to enforce full multiplication
        left = wrap(left)
        right = wrap(right)

        expr = f"{left}*{right}"

    return expr

def convert_frac(latex_str: str) -> str:

    def extract_braced(s, start):
        """Extract content inside balanced braces starting at s[start] == '{'."""
        assert s[start] == '{'
        depth = 0
        for i in range(start, len(s)):
            if s[i] == '{':
                depth += 1
            elif s[i] == '}':
                depth -= 1
                if depth == 0:
                    return s[start+1:i], i + 1
        raise ValueError("Unbalanced braces")

    def replace_all_fracs(s):
        while r'\frac' in s:
            idx = s.find(r'\frac')

            # Extract numerator
            num, pos = extract_braced(s, idx + len(r'\frac'))

            # Extract denominator
            den, end = extract_braced(s, pos)

            # Recursively convert nested fractions
            num = replace_all_fracs(num)
            den = replace_all_fracs(den)

            num = replace_cdot(num)
            den = replace_cdot(den)

            # Apply your wrap() (which calls fix_expression)
            replacement = f"{wrap(num)}/{wrap(den)}"

            # Replace the full \frac{...}{...}
            s = s[:idx] + replacement + s[end:]

        return s

    return replace_all_fracs(latex_str)

def latex_parser(latex_str: str) -> str:
    latex_str = latex_str.replace(r'\left(', '(').replace(r'\right)', ')')
    result = convert_frac(latex_str)
    result = re.sub(r'\{(\([^\{\}]*\))\}', r'\1', result)  # remove {} around (...)
    result = fix_expression(result)                        # enforce * everywhere
    return result

def main(): 
    # Example
    intervals = ["a<b<=c<d", "t_1 + 1<=t_3<=c", "x<y"]
    print(split_intervals_flat(intervals))

    # Example usage
    example = ["a = 5", "b <= 10", "c >= 20", "d = a + b"]
    print(replace_equals(example))

    print(convert_frac(r"\frac{9 b - d}{3} + \frac{3}{2b+2d+1}"))
    

if __name__ == "__main__": 
    main()
