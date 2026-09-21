"""Copia i dati di un vecchio archivio SQLite di QUANTO nel database PostgreSQL configurato.

Uso:  python -m app.tools.sqlite_to_postgres percorso/quanto.sqlite3

Le tabelle si copiano nell'ordine giusto; le righe già presenti (stessa chiave) non vengono toccate. Il registro
firmato (``anchors``) si copia solo se il database di destinazione ha il registro vuoto: una catena di firme non si
mescola con un'altra.
"""
from __future__ import annotations

import sqlite3
import sys
from typing import List

from app.core import db

ORDER = ["bandi", "bando_meta", "rules", "requirements", "bando_sources", "bando_files", "bando_tombstones", "events", "runs", "documents", "anchors"]


def copy(sqlite_path: str) -> dict:
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    have = {r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    report = {}
    with db.connect() as conn:
        for table in ORDER:
            if table not in have:
                continue
            if table == "anchors" and conn.execute("SELECT COUNT(*) c FROM anchors").fetchone()["c"]:
                report[table] = "saltata: il registro di destinazione non è vuoto"
                continue
            rows = src.execute(f"SELECT * FROM {table}").fetchall()
            if not rows:
                report[table] = 0
                continue
            dest_cols: List[str] = db.table_columns(conn, table)
            cols = [c for c in rows[0].keys() if c in dest_cols]
            pk = db.pk_columns(conn, table)
            marks = ",".join("?" for _ in cols)
            sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks}) ON CONFLICT ({','.join(pk)}) DO NOTHING"
            conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
            report[table] = len(rows)
            if table in ("events", "runs", "documents"):      # riallinea la sequenza degli identificativi
                conn.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))")
    return report


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    for t, n in copy(sys.argv[1]).items():
        print(f"{t}: {n}")
