"""Albero di Merkle per l'asseverazione crittografica dei budget (Cryptographic Evidence Package).

Rispetto a uno schema naïf (concatenazione di hash + duplicazione dell'ultimo nodo) sono
applicate due difese standard (RFC 6962 / CVE-2012-2459):

1. Separazione di dominio: foglie = SHA256(0x00 || h_riga), nodi = SHA256(0x01 || min || max).
   Un nodo interno non può quindi essere presentato come foglia (second-preimage).
2. Nodo dispari promosso invariato al livello superiore invece di essere duplicato:
   [a,b,c] e [a,b,c,c] producono radici diverse.

I figli sono ordinati (min||max) come nello schema originale: la prova di inclusione non richiede
la posizione, ma per compatibilità la posizione resta nel formato della proof.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List

LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"
EMPTY_ROOT = hashlib.sha256(b"EMPTY_BUDGET_PAYLOAD").hexdigest()


def normalize_root(root: str) -> str:
    """Forma canonica per i confronti: minuscolo, senza prefisso 0x."""
    r = root.strip().lower()
    return r[2:] if r.startswith("0x") else r


class MerkleTreeEngine:
    @staticmethod
    def hash_sha256(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_leaf(item_hash_hex: str) -> str:
        return hashlib.sha256(LEAF_PREFIX + bytes.fromhex(item_hash_hex)).hexdigest()

    @staticmethod
    def _combine(left: str, right: str) -> str:
        a, b = (left, right) if left <= right else (right, left)
        return hashlib.sha256(NODE_PREFIX + bytes.fromhex(a) + bytes.fromhex(b)).hexdigest()

    @classmethod
    def compute_merkle_root(cls, leaf_hashes: List[str]) -> str:
        """Radice esadecimale (64 char, senza 0x) dalla lista degli hash di riga."""
        if not leaf_hashes:
            return EMPTY_ROOT
        level = [cls.hash_leaf(h) for h in leaf_hashes]
        while len(level) > 1:
            nxt = [cls._combine(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
            if len(level) % 2:
                nxt.append(level[-1])  # promozione, non duplicazione
            level = nxt
        return level[0]

    @classmethod
    def build_levels(cls, leaf_hashes: List[str]) -> List[List[str]]:
        """Tutti i livelli dell'albero (foglie -> radice), per la visualizzazione. Stessa costruzione di ``compute_merkle_root``."""
        if not leaf_hashes:
            return [[EMPTY_ROOT]]
        level = [cls.hash_leaf(h) for h in leaf_hashes]
        levels = [level]
        while len(level) > 1:
            nxt = [cls._combine(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
            if len(level) % 2:
                nxt.append(level[-1])
            levels.append(nxt)
            level = nxt
        return levels

    @classmethod
    def generate_merkle_proof(cls, leaf_hashes: List[str], target_hash: str) -> List[Dict[str, str]]:
        """Prova di inclusione: nodi fratelli dal basso verso la radice ([] se la foglia non c'è)."""
        if target_hash not in leaf_hashes:
            return []
        level = [cls.hash_leaf(h) for h in leaf_hashes]
        idx = leaf_hashes.index(target_hash)
        proof: List[Dict[str, str]] = []
        while len(level) > 1:
            is_left = idx % 2 == 0
            sibling = idx + 1 if is_left else idx - 1
            if sibling < len(level):
                proof.append({"position": "right" if is_left else "left", "hash": level[sibling]})
            nxt = [cls._combine(level[i], level[i + 1]) for i in range(0, len(level) - 1, 2)]
            if len(level) % 2:
                nxt.append(level[-1])
            idx //= 2
            level = nxt
        return proof

    @classmethod
    def verify_merkle_proof(cls, item_hash_hex: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
        node = cls.hash_leaf(item_hash_hex)
        for step in proof:
            node = cls._combine(node, step["hash"])
        return node == normalize_root(expected_root)
