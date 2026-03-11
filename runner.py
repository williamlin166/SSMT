import json
import sys
from pathlib import Path
from SSMT import ssmt


def load_case(path):
    with open(path) as f:
        return json.load(f)


def run_single(path):
    data = load_case(path)

    log_dir = Path("log")
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / (Path(path).stem + ".log")

    print(f"Running {path}")

    # Redirect print output to file
    original_stdout = sys.stdout
    with open(log_file, "w") as f:
        sys.stdout = f
        try:
            ssmt(**data)
        finally:
            sys.stdout = original_stdout

    print(f"Log saved to {log_file}")



def run_family(folder):
    for case_file in sorted(Path(folder).glob("*.json")):
        run_single(case_file)


def run_all():
    for family in Path("testcases").iterdir():
        if family.is_dir():
            print(f"\n=== Running family: {family.name} ===")
            run_family(family)


if __name__ == "__main__":
    mode = sys.argv[1]

    if mode == "case":
        run_single(sys.argv[2])

    elif mode == "family":
        run_family(sys.argv[2])

    elif mode == "all":
        run_all()