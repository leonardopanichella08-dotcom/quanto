import hashlib

import pytest

from app.core.anonymizer import PrivacyAnonymizer
from app.core.merkle_tree import EMPTY_ROOT, MerkleTreeEngine as M


def leaves(n):
    return [hashlib.sha256(f"row-{i}".encode()).hexdigest() for i in range(n)]


def test_root_is_deterministic_and_order_of_construction_stable():
    assert M.compute_merkle_root(leaves(5)) == M.compute_merkle_root(leaves(5))
    assert len(M.compute_merkle_root(leaves(5))) == 64
    assert M.compute_merkle_root([]) == EMPTY_ROOT


def test_odd_leaf_is_not_duplicated():
    """Con la duplicazione [a,b,c] e [a,b,c,c] avrebbero la stessa radice (CVE-2012-2459)."""
    abc = leaves(3)
    assert M.compute_merkle_root(abc) != M.compute_merkle_root(abc + [abc[-1]])


def test_single_leaf_root_is_not_the_leaf_hash():
    """Separazione di dominio: la radice di una foglia non coincide con l'hash di riga grezzo."""
    h = leaves(1)[0]
    assert M.compute_merkle_root([h]) != h


def test_any_change_or_reorder_changes_root_only_when_content_changes():
    base = leaves(6)
    tampered = list(base)
    tampered[2] = hashlib.sha256(b"x").hexdigest()
    assert M.compute_merkle_root(base) != M.compute_merkle_root(tampered)
    assert M.compute_merkle_root(base) != M.compute_merkle_root(base[:-1])


@pytest.mark.parametrize("n", range(1, 18))
def test_every_proof_verifies(n):
    ls = leaves(n)
    root = M.compute_merkle_root(ls)
    for h in ls:
        assert M.verify_merkle_proof(h, M.generate_merkle_proof(ls, h), root)


def test_proof_rejects_wrong_leaf_and_wrong_root():
    ls = leaves(7)
    root = M.compute_merkle_root(ls)
    proof = M.generate_merkle_proof(ls, ls[3])
    assert not M.verify_merkle_proof(hashlib.sha256(b"forged").hexdigest(), proof, root)
    assert not M.verify_merkle_proof(ls[3], proof, "0x" + "00" * 32)
    assert M.generate_merkle_proof(ls, "ab" * 32) == []


def test_internal_node_cannot_pass_as_leaf():
    ls = leaves(4)
    root = M.compute_merkle_root(ls)
    left = M._combine(M.hash_leaf(ls[0]), M.hash_leaf(ls[1]))
    right = M._combine(M.hash_leaf(ls[2]), M.hash_leaf(ls[3]))
    # presentare i due nodi interni come se fossero foglie NON deve riprodurre la radice
    assert M.compute_merkle_root([left, right]) != root


def test_tokens_are_opaque_deterministic_and_keyed(monkeypatch):
    t1 = PrivacyAnonymizer.generate_opaque_token("RSSMRA80A01H501U")
    assert t1 == PrivacyAnonymizer.generate_opaque_token("  rssmra80a01h501u ")
    assert t1.startswith("TOK-") and "RSSMRA" not in t1
    monkeypatch.setenv("QUANTO_PII_KEY", "another-key")
    assert PrivacyAnonymizer.generate_opaque_token("RSSMRA80A01H501U") != t1  # senza la chiave non è ricostruibile


def test_sanitize_record_masks_pii_keeps_numbers():
    rec = {"employee_name": "Mario Rossi", "iban": "IT60X0542811101000000123456", "ral_eur": 38000.0}
    out = PrivacyAnonymizer.sanitize_payroll_record(rec)
    assert out["ral_eur"] == 38000.0
    assert out["employee_name"].startswith("TOK-") and out["iban"].startswith("TOK-")
    assert rec["employee_name"] == "Mario Rossi"  # input non mutato


def test_scrub_free_text_masks_iban_and_codice_fiscale():
    text = "Bonifico a RSSMRA80A01H501U su IT60X0542811101000000123456 saldo"
    out = PrivacyAnonymizer.scrub_free_text(text)
    assert "RSSMRA80A01H501U" not in out and "IT60X0542811101000000123456" not in out
    assert out.startswith("Bonifico a TOK-") and out.endswith(" saldo")
