import hashlib

import pytest
from fastapi.testclient import TestClient

from app.core import merkle_lab
from app.core.merkle_tree import MerkleTreeEngine as M
from main import app

client = TestClient(app)
ROWS = ["Stipendio Rossi 26.282,70", "Server 12.000,00", "Consulenza audit 8.500,00", "Affitto 4.800,00", "Formazione 2.000,00"]


def test_lab_root_equals_engine_root():
    res = merkle_lab.explain(ROWS)
    row_hashes = [hashlib.sha256(r.encode()).hexdigest() for r in ROWS]
    assert res["root"] == M.compute_merkle_root(row_hashes)
    assert res["levels"] == M.build_levels(row_hashes)
    assert res["row_hashes"] == row_hashes


@pytest.mark.parametrize("n", range(1, 13))
def test_every_size_and_every_proof_reaches_root(n):
    rows = [f"riga {i}" for i in range(n)]
    for i in range(n):
        res = merkle_lab.explain(rows, i)
        assert res["proof"]["reaches_root"] and res["proof"]["verified"]


def test_duplicate_rows_still_give_valid_proof_for_second_copy():
    res = merkle_lab.explain(["uguale", "uguale", "altra"], 1)
    assert res["proof"]["verified"]


def test_odd_node_is_promoted_not_duplicated():
    res = merkle_lab.explain(["a", "b", "c"])
    kinds = [p["kind"] for p in res["rounds"][0]["pairs"]]
    assert kinds == ["combine", "promote"]
    assert res["root"] != merkle_lab.explain(["a", "b", "c", "c"])["root"]


def test_one_character_change_changes_root_and_all_ancestors_only():
    a = merkle_lab.explain(ROWS)
    b = merkle_lab.explain([ROWS[0].replace("26.282,70", "26.282,71")] + ROWS[1:])
    assert a["root"] != b["root"]
    assert a["levels"][0][1:] == b["levels"][0][1:]  # le altre foglie non cambiano
    assert a["levels"][0][0] != b["levels"][0][0]
    # solo un percorso (una foglia -> radice) cambia in un albero a 5 foglie
    assert sum(x != y for x, y in zip(a["levels"][1], b["levels"][1])) == 1


def test_children_order_does_not_matter():
    res = merkle_lab.explain(["x", "y"])
    pair = res["rounds"][0]["pairs"][0]
    assert pair["first"] <= pair["second"]
    assert M._combine(pair["left"], pair["right"]) == M._combine(pair["right"], pair["left"]) == res["root"]


def test_limits():
    with pytest.raises(ValueError):
        merkle_lab.explain([])
    with pytest.raises(ValueError):
        merkle_lab.explain(["x"] * 13)
    with pytest.raises(ValueError):
        merkle_lab.explain(["x"], 1)


def test_endpoint_public_and_validated():
    r = client.post("/api/v2/registry/merkle-lab", json={"rows": ROWS, "prove_index": 2})
    assert r.status_code == 200
    d = r.json()
    assert d["root"] == merkle_lab.explain(ROWS)["root"] and d["proof"]["verified"]
    assert client.post("/api/v2/registry/merkle-lab", json={"rows": []}).status_code == 422
    assert client.post("/api/v2/registry/merkle-lab", json={"rows": ["  "]}).status_code == 422
    assert client.post("/api/v2/registry/merkle-lab", json={"rows": ["x" * 201]}).status_code == 422
    assert client.post("/api/v2/registry/merkle-lab", json={"rows": ["x"], "prove_index": 5}).status_code == 422
    assert client.post("/api/v2/registry/merkle-lab", json={"rows": ["x"], "extra": 1}).status_code == 422
