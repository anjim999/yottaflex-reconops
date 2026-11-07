import pytest

from recon.engine.run import reconcile
from recon.generate.pipeline import generate


@pytest.fixture(scope="session")
def run():
    r = generate("starter", 20261022)
    r["out"] = reconcile(r["tables"], r["run_config"])
    return r


@pytest.fixture(scope="session")
def tables(run):
    return run["tables"]


@pytest.fixture(scope="session")
def out(run):
    return run["out"]


@pytest.fixture(scope="session")
def gt(run):
    return run["ground_truth"]
