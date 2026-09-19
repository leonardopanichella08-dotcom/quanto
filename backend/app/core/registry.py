"""Registro di asseverazione: catena di hash append-only con firma Ed25519.

Sostituisce l'ancoraggio su blockchain. Ogni registrazione lega (progetto opaco, Merkle Root, istante)
all'hash della registrazione precedente e viene firmata dal server:

- modificare o cancellare una voce passata rompe la catena (hash e ``prev_hash`` non tornano);
- rifirmare l'intera catena è possibile solo con la chiave privata: la chiave PUBBLICA (``/registry/public-key``)
  è la radice di fiducia e va pubblicata/fissata dall'auditor fuori banda;
- un'attestazione (``Attestation``) è verificabile offline con la sola chiave pubblica.

Limite dichiarato: il registro è gestito da QUANTO, non da un testimone terzo indipendente. Per rafforzarlo
si può pubblicare periodicamente ``head_hash`` (es. PEC, repository pubblico, timestamp qualificato).
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Optional, Set

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from app.core.db import connect
from app.core.merkle_tree import normalize_root

logger = logging.getLogger("quanto.registry")

GENESIS_HASH = "0" * 64
_DEV_SEED = hashlib.sha256(b"QUANTO-INSECURE-DEV-SIGNING-KEY").digest()


class AlreadyRegisteredError(Exception):
    def __init__(self, existing_root: str, same_root: bool):
        super().__init__("Budget già registrato per questo progetto")
        self.existing_root = existing_root
        self.same_root = same_root


@dataclass(frozen=True)
class Attestation:
    seq: int
    project_key: str
    merkle_root: str  # hex senza 0x
    registered_at: str
    prev_hash: str
    entry_hash: str
    key_id: str
    public_key: str
    signature: str


@dataclass(frozen=True)
class ChainStatus:
    intact: bool
    entries: int
    head_hash: str
    broken_at_seq: Optional[int] = None
    reason: Optional[str] = None


def project_key(project_id: str) -> str:
    return hashlib.sha256(f"QUANTO_PROJECT:{project_id}".encode("utf-8")).hexdigest()


def _load_private_key() -> tuple[Ed25519PrivateKey, bool]:
    raw = os.getenv("QUANTO_SIGNING_KEY", "").strip()
    if not raw:
        logger.warning("QUANTO_SIGNING_KEY non impostata: uso la chiave di sviluppo (NON usare in produzione).")
        return Ed25519PrivateKey.from_private_bytes(_DEV_SEED), True
    try:
        seed = bytes.fromhex(raw) if len(raw) == 64 else base64.b64decode(raw, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError("QUANTO_SIGNING_KEY non valida: attesi 32 byte in hex (64 caratteri) o base64") from None
    if len(seed) != 32:
        raise ValueError("QUANTO_SIGNING_KEY deve essere di 32 byte")
    return Ed25519PrivateKey.from_private_bytes(seed), False


def _public_hex(key: Ed25519PrivateKey) -> str:
    return key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def key_id_for(public_hex: str) -> str:
    return hashlib.sha256(bytes.fromhex(public_hex)).hexdigest()[:16]


def current_public_key() -> dict:
    key, is_dev = _load_private_key()
    pub = _public_hex(key)
    return {"public_key": pub, "key_id": ("DEV-" if is_dev else "") + key_id_for(pub), "is_dev_key": is_dev}


def trusted_public_keys() -> Set[str]:
    """Chiavi pubbliche di cui ci si fida (corrente + eventuali precedenti, per la rotazione)."""
    keys = {current_public_key()["public_key"]}
    keys |= {k.strip().lower() for k in os.getenv("QUANTO_TRUSTED_PUBLIC_KEYS", "").split(",") if k.strip()}
    return keys


def _entry_hash(seq: int, pkey: str, root: str, at: str, prev: str, key_id: str) -> str:
    payload = {"seq": seq, "project_key": pkey, "merkle_root": root, "registered_at": at, "prev_hash": prev, "key_id": key_id}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _verify_signature(public_hex: str, entry_hash: str, signature_hex: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(bytes.fromhex(signature_hex), bytes.fromhex(entry_hash))
        return True
    except (InvalidSignature, ValueError):
        return False


def _row_to_attestation(row) -> Attestation:
    return Attestation(row["seq"], row["project_key"], row["merkle_root"], row["registered_at"], row["prev_hash"],
                       row["entry_hash"], row["key_id"], row["public_key"], row["signature"])


class Registry:
    @staticmethod
    def register(project_id: str, merkle_root: str) -> Attestation:
        root = normalize_root(merkle_root)
        if len(root) != 64 or int(root, 16) == 0:
            raise ValueError("Merkle Root non valida: attesi 32 byte non nulli in esadecimale")
        key, is_dev = _load_private_key()
        pub = _public_hex(key)
        key_id = ("DEV-" if is_dev else "") + key_id_for(pub)
        pkey = project_key(project_id)
        with connect() as conn:
            existing = conn.execute("SELECT merkle_root FROM anchors WHERE project_key = ?", (pkey,)).fetchone()
            if existing:
                raise AlreadyRegisteredError(existing["merkle_root"], existing["merkle_root"] == root)
            head = conn.execute("SELECT seq, entry_hash FROM anchors ORDER BY seq DESC LIMIT 1").fetchone()
            seq = (head["seq"] + 1) if head else 1
            prev = head["entry_hash"] if head else GENESIS_HASH
            at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            entry_hash = _entry_hash(seq, pkey, root, at, prev, key_id)
            signature = key.sign(bytes.fromhex(entry_hash)).hex()
            conn.execute(
                "INSERT INTO anchors (seq, project_key, merkle_root, registered_at, prev_hash, entry_hash, key_id, public_key, signature) "
                "VALUES (?,?,?,?,?,?,?,?,?)", (seq, pkey, root, at, prev, entry_hash, key_id, pub, signature))
        return Attestation(seq, pkey, root, at, prev, entry_hash, key_id, pub, signature)

    @staticmethod
    def lookup(project_id: str) -> Optional[Attestation]:
        with connect() as conn:
            row = conn.execute("SELECT * FROM anchors WHERE project_key = ?", (project_key(project_id),)).fetchone()
        return _row_to_attestation(row) if row else None

    @staticmethod
    def verify_chain() -> ChainStatus:
        """Ricalcola l'intera catena: link, hash di voce e firme contro le chiavi pubbliche di fiducia."""
        trusted = trusted_public_keys()
        prev, count = GENESIS_HASH, 0
        with connect() as conn:
            rows = conn.execute("SELECT * FROM anchors ORDER BY seq ASC").fetchall()
        for expected_seq, row in enumerate(rows, 1):
            a = _row_to_attestation(row)
            if a.seq != expected_seq:
                return ChainStatus(False, count, prev, a.seq, "numerazione discontinua (voce mancante)")
            if a.prev_hash != prev:
                return ChainStatus(False, count, prev, a.seq, "prev_hash non coincide con la voce precedente")
            if _entry_hash(a.seq, a.project_key, a.merkle_root, a.registered_at, a.prev_hash, a.key_id) != a.entry_hash:
                return ChainStatus(False, count, prev, a.seq, "hash di voce non coincide con il contenuto")
            if a.public_key not in trusted:
                return ChainStatus(False, count, prev, a.seq, "chiave di firma non tra quelle di fiducia")
            if not _verify_signature(a.public_key, a.entry_hash, a.signature):
                return ChainStatus(False, count, prev, a.seq, "firma non valida")
            prev, count = a.entry_hash, count + 1
        return ChainStatus(True, count, prev)

    @staticmethod
    def entries() -> List[Attestation]:
        with connect() as conn:
            return [_row_to_attestation(r) for r in conn.execute("SELECT * FROM anchors ORDER BY seq ASC").fetchall()]


def verify_attestation(att: dict, trusted: Optional[Set[str]] = None) -> bool:
    """Verifica OFFLINE di un'attestazione con la sola chiave pubblica di fiducia (nessun accesso al registro)."""
    trusted = trusted or trusted_public_keys()
    try:
        recomputed = _entry_hash(att["seq"], att["project_key"], att["merkle_root"], att["registered_at"], att["prev_hash"], att["key_id"])
        return (recomputed == att["entry_hash"] and att["public_key"].lower() in trusted
                and _verify_signature(att["public_key"], att["entry_hash"], att["signature"]))
    except (KeyError, TypeError):
        return False


def attestation_dict(att: Attestation) -> dict:
    return asdict(att)
