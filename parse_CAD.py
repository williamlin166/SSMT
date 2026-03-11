import re

# -------------------------
# Step 1: Tokenizer
# -------------------------

# def tokenize_CAD(s):
#     tokens = []
#     i = 0
#     while i < len(s):
#         if s[i] in '()':
#             tokens.append(s[i])
#             i += 1
#         elif s[i] == '∧':
#             tokens.append('AND')
#             i += 1
#         elif s[i] == '∨':
#             tokens.append('OR')
#             i += 1
#         else:
#             # read atomic expression
#             j = i
#             while j < len(s) and s[j] not in '()∧∨':
#                 j += 1
#             tokens.append(s[i:j].strip())
#             i = j
#     return [t for t in tokens if t != '']

def tokenize_CAD(s):
    tokens = []
    i = 0
    while i < len(s):
        if s[i] in ')':
            tokens.append(s[i])
            i += 1
        elif s[i] == '∧':
            tokens.append('AND')
            i += 1
        elif s[i] == '∨':
            tokens.append('OR')
            i += 1
        elif s[i] == ' ':
            i += 1
        else:
            # read atomic expression
            # print("i:", i)
            j = i
            while j < len(s):
                # print("j:", j)
                if s[j] in '∧∨':
                    break  # stop at normal operators
                elif s[j] == '(':
                    # look ahead to see if this is logical or arithmetic
                    paren_level = 1
                    k = j + 1
                    found_logical = False

                    while k < len(s) and paren_level > 0:
                        if s[k] == '(':
                            paren_level += 1
                        elif s[k] == ')':
                            paren_level -= 1
                        elif paren_level == 1 and s[k] in '∧∨':
                            found_logical = True
                            break
                        k += 1

                    if found_logical:
                        # this '(' starts a logical group
                        break
                    else:
                        # arithmetic parentheses → include them
                        j = k
                        continue
                elif s[j] == ')':
                    break  # stop at closing parenthesis
                else:
                    j += 1
            if j == i:
                tokens.append(s[i].strip())
                i = j + 1
            else:
                tokens.append(s[i:j].strip())
                i = j
    return [t for t in tokens if t != '']

# -------------------------
# Step 2: Recursive Parser
# -------------------------

def parse_expression(tokens):
    def parse():
        elements = []
        while tokens:
            token = tokens.pop(0)
            if token == '(':
                elements.append(parse())
            elif token == ')':
                break
            else:
                elements.append(token)
        return elements
    return parse()


# -------------------------
# Step 3: Expand Logic
# -------------------------

def expand(node):
    # If it's a string (ATOM)
    if isinstance(node, str):
        return [[node]]

    # node is list
    result = [[]]
    current_op = 'AND'

    i = 0
    while i < len(node):
        element = node[i]

        if element == 'AND':
            current_op = 'AND'
        elif element == 'OR':
            current_op = 'OR'
        else:
            expanded = expand(element)

            if current_op == 'AND':
                new_result = []
                for r in result:
                    for e in expanded:
                        new_result.append(r + e)
                result = new_result

            elif current_op == 'OR':
                result = result + expanded

            current_op = 'AND'

        i += 1

    return result


# -------------------------
# Main Function
# -------------------------

def formula_to_cubes(formula):
    tokens = tokenize_CAD(formula)
    parsed = parse_expression(tokens)
    cubes = expand(parsed)

    # clean whitespace
    cubes = [[atom.strip() for atom in cube] for cube in cubes]

    return cubes

def main():
    # -------------------------
    # Example
    # -------------------------

    # formula = "(a = 0 ∧ 2/3<=b<=1 ∧ ((y_1 = 2 - 2 b ∧ y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (2 - 2 b<y_1<=b ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))))) ∨ (0<a<1/2 ∧ ((2/3<=b<=(2 - a)/2 ∧ ((y_1 = 2 - 2 b ∧ y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (2 - 2 b<y_1<=b ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))))) ∨ ((2 - a)/2<b<1 ∧ ((a<=y_1<=-a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (-a - b + 2<y_1<=b ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))))) ∨ (b = 1 ∧ ((a<=y_1<1 - a ∧ ((y_2 = 1 - y_1 ∧ y_3 = -y_1 - y_2 + 2) ∨ (1 - y_1<y_2<=1 ∧ -y_1 - y_2 + 2<=y_3<=1))) ∨ (y_1 = 1 - a ∧ ((y_2 = 1 - y_1 ∧ y_3 = -y_1 - y_2 + 2) ∨ (1 - y_1<y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=1))) ∨ (1 - a<y_1<=1 ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=1) ∨ (-a - y_1 + 2<y_2<=1 ∧ a<=y_3<=1))))))) ∨ (1/2<=a<2/3 ∧ ((2/3<=b<(2 - a)/2 ∧ ((y_1 = 2 - 2 b ∧ y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (2 - 2 b<y_1<=b ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))))) ∨ (b = (2 - a)/2 ∧ ((y_1 = 2 - 2 b ∧ y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (2 - 2 b<y_1<-a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (y_1 = -a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b))))) ∨ ((2 - a)/2<b<2 - 2 a ∧ ((a<=y_1<-a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (y_1 = -a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (-a - b + 2<y_1<=b ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))))) ∨ (b = 2 - 2 a ∧ ((y_1 = -a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (-a - b + 2<y_1<b ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))) ∨ (y_1 = b ∧ ((y_2 = -a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))))) ∨ (2 - 2 a<b<=1 ∧ ((a<=y_1<2 - 2 a ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))) ∨ (y_1 = 2 - 2 a ∧ ((y_2 = -a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))) ∨ (2 - 2 a<y_1<=b ∧ a<=y_2<=b ∧ a<=y_3<=b))))) ∨ (a = 2/3 ∧ ((b = 2/3 ∧ y_1 = 2/3 ∧ y_2 = 2/3 ∧ y_3 = 2/3) ∨ (2/3<b<=1 ∧ 2/3<=y_1<=b ∧ 2/3<=y_2<=b ∧ 2/3<=y_3<=b))) ∨ (2/3<a<=1 ∧ ((b = a ∧ y_1 = b ∧ y_2 = b ∧ y_3 = b) ∨ (a<b<=1 ∧ a<=y_1<=b ∧ a<=y_2<=b ∧ a<=y_3<=b)))"
    # formula = "(0<a<1/2 ∧ (((2 - a)/2<b<1 ∧ ((a<=y_1<=-a - b + 2 ∧ ((y_2 = -b - y_1 + 2 ∧ y_3 = -y_1 - y_2 + 2) ∨ (-b - y_1 + 2<y_2<=b ∧ -y_1 - y_2 + 2<=y_3<=b))) ∨ (-a - b + 2<y_1<=b ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=b) ∨ (-a - y_1 + 2<y_2<=b ∧ a<=y_3<=b))))) ∨ (b = 1 ∧ ((a<=y_1<1 - a ∧ ((y_2 = 1 - y_1 ∧ y_3 = -y_1 - y_2 + 2) ∨ (1 - y_1<y_2<=1 ∧ -y_1 - y_2 + 2<=y_3<=1))) ∨ (y_1 = 1 - a ∧ ((y_2 = 1 - y_1 ∧ y_3 = -y_1 - y_2 + 2) ∨ (1 - y_1<y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=1))) ∨ (1 - a<y_1<=1 ∧ ((a<=y_2<=-a - y_1 + 2 ∧ -y_1 - y_2 + 2<=y_3<=1) ∨ (-a - y_1 + 2<y_2<=1 ∧ a<=y_3<=1)))))))"
    formula = '(x<0 ∧ y>1/2 (1 - 2 x) ∧ z>=8 x + 16 y - 6) ∨ (x = 0 ∧ ((0<=y<1/6 ∧ 4 y<=z<=1/2 (2 y + 1)) ∨ (y = 1/6 ∧ z = 2/3) ∨ (y>1/2 ∧ z>=16 y - 6))) ∨ (0<x<1/8 ∧ ((0<=y<1/6 (10 x + 1) ∧ 4 y - 4 x<=z<=1/2 (2 x + 2 y + 1)) ∨ (y = 1/6 (10 x + 1) ∧ z = 1/2 (2 x + 2 y + 1)) ∨ (y>1/2 (1 - 2 x) ∧ z>=8 x + 16 y - 6))) ∨ (x = 1/8 ∧ ((0<=y<3/8 ∧ 4 y - 1/2<=z<=1/2 (2 y + 5/4)) ∨ (y = 3/8 ∧ z = 1) ∨ (y>3/8 ∧ z>=16 y - 5))) ∨ (1/8<x<1/6 ∧ ((0<=y<=1/2 (1 - 2 x) ∧ 4 y - 4 x<=z<=1/2 (2 x + 2 y + 1)) ∨ (1/2 (1 - 2 x)<y<1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6) ∨ (y = 1/30 (13 - 14 x) ∧ z>=1/2 (2 x + 2 y + 1)) ∨ (y>1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6))) ∨ (x = 1/6 ∧ ((0<=y<=1/3 ∧ 4 y - 2/3<=z<=1/2 (2 y + 4/3)) ∨ (1/3<y<16/45 ∧ z>=16 y - 14/3) ∨ (y = 16/45 ∧ z>=46/45) ∨ (y>16/45 ∧ z>=16 y - 14/3))) ∨ (1/6<x<3/8 ∧ ((0<=y<=1/10 (6 x - 1) ∧ 1/2 (-2 x - 2 y - 1)<=z<=1/2 (2 x + 2 y + 1)) ∨ (1/10 (6 x - 1)<y<=1/2 (1 - 2 x) ∧ 4 y - 4 x<=z<=1/2 (2 x + 2 y + 1)) ∨ (1/2 (1 - 2 x)<y<1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6) ∨ (y = 1/30 (13 - 14 x) ∧ z>=1/2 (2 x + 2 y + 1)) ∨ (y>1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6))) ∨ (x = 3/8 ∧ ((0<=y<=1/8 ∧ 1/2 (-2 y - 7/4)<=z<=1/2 (2 y + 7/4)) ∨ (1/8<y<31/120 ∧ z>=16 y - 3) ∨ (y = 31/120 ∧ z>=17/15) ∨ (y>31/120 ∧ z>=16 y - 3))) ∨ (3/8<x<1/2 ∧ ((0<=y<=1/2 (1 - 2 x) ∧ 1/2 (-2 x - 2 y - 1)<=z<=1/2 (2 x + 2 y + 1)) ∨ (1/2 (1 - 2 x)<y<1/34 (11 - 18 x) ∧ z>=8 x + 16 y - 6) ∨ (y = 1/34 (11 - 18 x) ∧ z>=1/2 (-2 x - 2 y - 1)) ∨ (1/34 (11 - 18 x)<y<1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6) ∨ (y = 1/30 (13 - 14 x) ∧ z>=1/2 (2 x + 2 y + 1)) ∨ (y>1/30 (13 - 14 x) ∧ z>=8 x + 16 y - 6))) ∨ (x = 1/2 ∧ ((y = 0 ∧ -1<=z<=1) ∨ (0<y<1/17 ∧ z>=16 y - 2) ∨ (y = 1/17 ∧ z>=-18/17) ∨ (1/17<y<1/5 ∧ z>=16 y - 2) ∨ (y = 1/5 ∧ z>=6/5) ∨ (y>1/5 ∧ z>=16 y - 2))) ∨ (x>1/2 ∧ y>1/2 (1 - 2 x) ∧ z>=8 x + 16 y - 6)'

    cubes = formula_to_cubes(formula)

    print(len(cubes))
    for cube in cubes:
        print(cube)

    for cube in cubes:
        try:
            assert len(cube) == 3
            assert all(any(o in c for o in ['<', '>', '=']) for c in cube)
        except:
            raise ValueError("cube: " + str(cube))

    cd_result = cubes

    # cd_result = reduce_cells(cd_result, vars)

    # print(cd_result)
    # for c in cd_result:
    # print(c)

if __name__ == "__main__":
    main()