"""Merkle "passo passo" per la parte didattica dell'app.

Usa **lo stesso algoritmo** di ``MerkleTreeEngine`` (stesse funzioni, stesso prefisso di dominio, nodo dispari promosso):
quello che l'utente vede è ciò che il sistema fa davvero. L'unica differenza dichiarata: qui l'impronta di riga è lo
SHA-256 del testo scritto dall'utente; nel budget vero è lo SHA-256 della rappresentazione canonica della riga validata.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from app.core.merkle_tree import MerkleTreeEngine as M

MAX_ROWS = 12


def _pairs(level: List[str]) -> List[Dict[str, Any]]:
    """Descrive come un livello genera il successivo: coppie combinate e, se dispari, il nodo promosso."""
    out: List[Dict[str, Any]] = []
    for i in range(0, len(level) - 1, 2):
        left, right = level[i], level[i + 1]
        swapped = left > right  # i figli si ordinano: la posizione non cambia il risultato
        first, second = (right, left) if swapped else (left, right)
        out.append({"kind": "combine", "left_index": i, "right_index": i + 1, "left": left, "right": right,
                    "first": first, "second": second, "swapped": swapped, "result": M._combine(left, right)})
    if len(level) % 2:
        out.append({"kind": "promote", "left_index": len(level) - 1, "right_index": None, "left": level[-1], "right": None,
                    "first": None, "second": None, "swapped": False, "result": level[-1]})
    return out


def explain(rows: List[str], prove_index: Optional[int] = None) -> Dict[str, Any]:
    """Ogni passaggio del calcolo della Merkle Root su ``rows`` (1..MAX_ROWS testi)."""
    if not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError(f"servono da 1 a {MAX_ROWS} righe")
    row_hashes = [hashlib.sha256(r.encode("utf-8")).hexdigest() for r in rows]
    leaves = [M.hash_leaf(h) for h in row_hashes]

    levels: List[List[str]] = [leaves]
    rounds: List[Dict[str, Any]] = []
    level = leaves
    while len(level) > 1:
        pairs = _pairs(level)
        level = [p["result"] for p in pairs]
        rounds.append({"pairs": pairs, "size_after": len(level)})
        levels.append(level)
    root = level[0]
    if root != M.compute_merkle_root(row_hashes):  # difesa: la spiegazione non può divergere dal motore
        raise AssertionError("la spiegazione del Merkle diverge dal motore")

    result: Dict[str, Any] = {
        "rows": rows, "row_hashes": row_hashes, "leaves": leaves, "rounds": rounds, "levels": levels, "root": root,
        "leaf_prefix": "00", "node_prefix": "01",
    }

    if prove_index is not None:
        if not 0 <= prove_index < len(rows):
            raise ValueError("prove_index fuori intervallo")
        # percorso dall'indice (non dall'hash: due righe identiche hanno la stessa foglia)
        proof, idx = [], prove_index
        for lvl in levels[:-1]:
            sib = idx + 1 if idx % 2 == 0 else idx - 1
            if sib < len(lvl):
                proof.append({"position": "right" if idx % 2 == 0 else "left", "hash": lvl[sib]})
            idx //= 2
        node, path = leaves[prove_index], []
        for step in proof:
            nxt = M._combine(node, step["hash"])
            path.append({"sibling": step["hash"], "position": step["position"], "from": node, "result": nxt})
            node = nxt
        result["proof"] = {"index": prove_index, "row": rows[prove_index], "steps": path, "reaches_root": node == root,
                           "verified": M.verify_merkle_proof(row_hashes[prove_index], proof, root)}
    return result
