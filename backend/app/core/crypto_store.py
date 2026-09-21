"""Cifratura a riposo dei file dei clienti (Modulo 16): AES-256-GCM con chiave dell'ambiente.

``QUANTO_FILE_KEY`` = 32 byte in esadecimale (64 caratteri) o base64. Senza la chiave i file non si caricano: meglio un rifiuto
esplicito che documenti con retribuzioni e codici fiscali salvati in chiaro. Formato salvato: versione(1) | nonce(12) | testo cifrato + tag.
Il nome del file e l'impronta SHA-256 restano in chiaro (servono a riconoscere il documento); il contenuto no.
"""
from __future__ import annotations

import base64
import binascii
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

VERSION = b"\x01"


class FileKeyError(RuntimeError):
    """La chiave di cifratura manca o non è valida."""


def _key() -> bytes:
    raw = os.getenv("QUANTO_FILE_KEY", "").strip()
    if not raw:
        raise FileKeyError("QUANTO_FILE_KEY non impostata: i documenti dei clienti non si possono conservare senza cifratura")
    try:
        key = bytes.fromhex(raw) if len(raw) == 64 else base64.b64decode(raw, validate=True)
    except (ValueError, binascii.Error):
        raise FileKeyError("QUANTO_FILE_KEY non valida: attesi 32 byte in esadecimale o base64") from None
    if len(key) != 32:
        raise FileKeyError("QUANTO_FILE_KEY deve essere di 32 byte")
    return key


def encrypt(data: bytes, aad: bytes = b"") -> bytes:
    nonce = os.urandom(12)
    return VERSION + nonce + AESGCM(_key()).encrypt(nonce, data, aad)


def decrypt(blob: bytes, aad: bytes = b"") -> bytes:
    blob = bytes(blob)
    if not blob or blob[:1] != VERSION:
        raise FileKeyError("Formato del file cifrato sconosciuto")
    return AESGCM(_key()).decrypt(blob[1:13], blob[13:], aad)
