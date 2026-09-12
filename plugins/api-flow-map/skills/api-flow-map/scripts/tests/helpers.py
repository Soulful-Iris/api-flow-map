import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def fixture(name: str) -> str:
    return os.path.join(FIXTURES, name)


def all_steps(steps):
    for s in steps:
        yield s
        yield from all_steps(s.children)
        for b in s.branches:
            yield from all_steps(b.steps)


def labels(ep):
    return [s.label for s in all_steps(ep.flow)]


def find_ep(model, method, path_suffix):
    for e in model.endpoints:
        if e.method == method and e.path.endswith(path_suffix):
            return e
    raise AssertionError(f"endpoint {method} …{path_suffix} not found; have {[e.id for e in model.endpoints]}")
