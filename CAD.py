import requests
from parse_CAD import *
from auxiliary_func import insert_empty_string
from time_count import cumulative_timer

app_id = "X326PW3KEJ"
url = f"http://api.wolframalpha.com/v2/query"

def is_valid_parentheses(s: str) -> bool:
    balance = 0
    for ch in s:
        if ch == '(':
            balance += 1
        elif ch == ')':
            balance -= 1
            if balance < 0:
                return False
    return balance == 0

@cumulative_timer
def get_wolfram_result(query, title, var_order, verbose = False):

  output = []

  params = {
    "input": query,
    "appid": app_id,
    "podstate": "LocusSolution__More solutions",
    "output": "json"
  }

  # params = {
  #   "input": query,
  #   "appid": app_id,
  #   "format": "plaintext",
  #   "output": "json",
  #   "includepodid": "LocusSolution",
  # }

  res = requests.get(url, params=params).json()
  if verbose:
    print("res:", res)

  if not res["queryresult"]["success"]:
    print("Query failed! ")
    return output

  try:
    titles = [pod["title"] for pod in res["queryresult"]["pods"]]
  except:
    raise ValueError("No pods found! res: " + str(res))
  if 'Exact result' in titles:
    # we assume the "solutions" would be approximated in these cases
    for pod in res["queryresult"]["pods"]:
      if pod["title"] == "Exact result":
        if verbose:
          print("===", pod["title"], "===")
        assert len(pod["subpods"]) == 1
        for sub in pod["subpods"]:
          if sub.get("plaintext"):
            # text = sub["plaintext"].split(' ∧ ')
            cubes = formula_to_cubes(sub["plaintext"])
            if verbose:
              for c in cubes:
                print(c)
          try:
            for c in cubes:
              assert len(c) == len(var_order)
              for t in c:
                assert(is_valid_parentheses(t))
                any(o in t for o in ['<', '>', '='])
          except:
            print(f"Can't parse result from 'Exact result'. Unpaired parenthesis in string \"{t}\". Try other source. ")
          else:
            # for c in cubes:
              # output.append(c)
            return cubes # output
  if any(item in title for item in titles):
    for pod in res["queryresult"]["pods"]:
      if pod["title"] in title:
        if verbose:
          print("===", pod["title"], "===")
        for sub in pod["subpods"]:
          if sub.get("plaintext"):
            text = sub["plaintext"].split(', ')
            if verbose:
              print(text)
            try:
              for i in range(len(var_order)):
                assert var_order[i] in text[i]
            except:
              try:
                # s = [[v for v in var_order if v in t] for t in text]
                # new_text = ['' for _ in var_order]
                # for i, s_ in enumerate(s):
                #   for j, v_ in enumerate(var_order[::-1]):
                #     if v_ in s_:
                #       break
                #   assert new_text[len(var_order) - j - 1] == ''
                #   new_text[len(var_order) - j - 1] = text[i]
                new_text = insert_empty_string(text, var_order)
                if verbose:
                  print(new_text)
              except:
                print("Error! Incompatible variable order! ")
              else:
                output.append(new_text)
            else:
              output.append(text)
  else:
    for pod in res["queryresult"]["pods"]:
      if pod["title"] == "Result":
        if verbose:
          print("===", pod["title"], "===")
        for sub in pod["subpods"]:
          if sub.get("plaintext"):
            text = sub["plaintext"].split(' ∧ ')
            if verbose:
              print(text)
          try:
            for t in text:
              assert(is_valid_parentheses(t))
          except:
            print("Can't parse result. Unpaired parenthesis in string \"", t, "\"", sep="")
          else:
            output.append(text)
  return output


# Testing on example 3

# query = "CylindricalDecomposition [(0<=t<=1 && 0<=x<=1 && 0<=y<=1 && 0<=z<=1 && y>=x && y<=z), (t, x, y, z)]"
# var_order = ['t', 'x', 'y', 'z']
# cd_result = get_wolfram_result(query, ["Solutions", "Solution"], var_order, True)

# print(cd_result)
