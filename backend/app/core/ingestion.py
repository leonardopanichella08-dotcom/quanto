"""Ingestion di Fonte A (regole di bando): catalogo, estrazione deterministica, riconciliazione a passaggi multipli.

Stadi (Modulo 9.1):
- Stadio 1: catalogo dei bandi (solo metadati, nessuna regola). Il cliente conferma il bando -> trigger estrazione.
- Cache: regole già pubblicate per un bando vengono riusate senza nuova estrazione.
- Stadio 2: estrazione DETERMINISTICA (codice puro) da tabelle "chiave: valore" e formule di prosa standard.
- Stadio 3: N passaggi indipendenti (forniti da estrattori AI o umani, questo modulo non chiama alcun LLM) sulle regole
  in prosa libera: il CODICE confronta i risultati; concordanza -> regola pubblicata; disaccordo -> coda di verifica umana.
- Una regola pubblicata non viene mai sovrascritta da un'estrazione successiva: solo la revisione umana la corregge.

Le regole pubblicate compongono un ``GrantRuleSet`` il cui ``rule_version_hash`` è l'hash SHA-256 del contenuto
delle regole: cambiare una regola cambia la versione e quindi la Merkle Root dei budget calcolati.
"""
from __future__ import annotations

import hashlib
import json
import re
from enum import Enum
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from pydantic import TypeAdapter, ValidationError

from app.core.db import connect
from app.core.requirements_extractor import extract_more_rules, extract_requirements
from app.models.schemas import GrantRuleSet

IDENTITY_FIELDS = {"bando_id", "bando_name", "rule_version_hash"}
RULE_KEYS = {k for k in GrantRuleSet.model_fields if k not in IDENTITY_FIELDS}
CORE_KEYS = ("max_hourly_rate_personnel", "max_consulting_percentage", "max_overhead_percentage")

_NUM = r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:[.,]\d+)?)"
_DATE = r"(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})"
_CAP = r"(?:non\s+(?:(?:pu[oò]|poss\w+|dev\w+)\s+)?(?:essere\s+)?(?:superior\w+|superare|eccedere|oltre)|massim\w+|max|fino\s+al)"
_KV_LINE = re.compile(r"^\s*([a-z_]+)\s*[:|=]\s*(.+?)\s*$", re.I)


def _num(text: str) -> Decimal:
    t = text.strip()
    t = t.replace(".", "").replace(",", ".") if "," in t else (t.replace(".", "") if re.fullmatch(r"\d{1,3}(\.\d{3})+", t) else t)
    return Decimal(t)


def _pct(text: str) -> str:
    return format((_num(text) / 100).normalize(), "f")


def _date(d: str, m: str, y: str) -> str:
    return date(int(y), int(m), int(d)).isoformat()


# (chiave regola, regex, conversione) — formule di prosa standard riconosciute in modo deterministico
PROSE_PATTERNS = [
    ("max_hourly_rate_personnel", re.compile(r"(?:costo orario|tariffa oraria)[^.\n\d]{0,80}?" + _NUM + r"\s*(?:€|euro|eur)\s*(?:/|all')?\s*(?:ora|h)\b", re.I),
     lambda m: format(_num(m.group(1)).normalize(), "f")),
    ("max_consulting_percentage", re.compile(r"consulenz\w*[^.\n\d]{0,80}?" + _CAP + r"[^.\n\d]{0,30}?" + _NUM + r"\s*%", re.I),
     lambda m: _pct(m.group(1))),
    ("max_overhead_percentage", re.compile(r"spese generali[^.\n\d]{0,80}?(?:" + _CAP + r"|forfett\w+)[^.\n\d]{0,30}?" + _NUM + r"\s*%", re.I),
     lambda m: _pct(m.group(1))),
    ("contribution_rate_pct", re.compile(r"contributo[^.\n\d]{0,60}?(?:pari al|del|fino al)\s*" + _NUM + r"\s*%", re.I),
     lambda m: _pct(m.group(1))),
    ("eligibility_start", re.compile(r"ammissibil\w*[^.\n\d]{0,60}?(?:a\s+partire\s+dal|dal)\s+" + _DATE, re.I),
     lambda m: _date(m.group(1), m.group(2), m.group(3))),
    ("eligibility_end", re.compile(r"(?:ammissibil\w*[^.\n]{0,80}?|termine\s+(?:di\s+)?(?:ammissibilit\w+|rendicontazione)[^.\n\d]{0,20})\s*(?:fino\s+al|entro\s+il)\s+" + _DATE, re.I),
     lambda m: _date(m.group(1), m.group(2), m.group(3))),
    ("requires_cup", re.compile(r"\bCUP\b[^.\n]{0,60}?(?:obbligatori\w*|deve|devono|riportar\w+)", re.I), lambda m: "true"),
]


def normalize_value(rule_key: str, value: Any) -> str:
    """Valida ``value`` contro il tipo del campo di ``GrantRuleSet`` e ne dà la forma canonica (stringa)."""
    if rule_key not in RULE_KEYS:
        raise ValueError(f"Regola sconosciuta: {rule_key}")
    field = GrantRuleSet.model_fields[rule_key]
    raw = value.strip() if isinstance(value, str) else value
    if isinstance(raw, str) and re.fullmatch(_NUM + r"\s*%", raw):   # "20%" -> 0.2
        raw = format((_num(raw.rstrip("% ").strip()) / 100).normalize(), "f")
    elif isinstance(raw, str) and re.fullmatch(_NUM, raw):
        try:
            raw = format(_num(raw).normalize(), "f")
        except InvalidOperation:
            pass
    if isinstance(raw, str) and raw[:1] in "[{":
        try:
            raw = json.loads(raw)
        except ValueError:
            pass
    if isinstance(raw, str) and raw.lower() in ("true", "false", "sì", "si", "no"):
        raw = raw.lower() in ("true", "sì", "si")
    try:
        parsed = TypeAdapter(field.annotation).validate_python(raw)
    except ValidationError as exc:
        raise ValueError(f"Valore non valido per {rule_key}: {exc.errors()[0]['msg']}") from None
    if isinstance(parsed, (int, float, Decimal)) and not isinstance(parsed, bool):
        return format(Decimal(str(parsed)).normalize(), "f")
    if isinstance(parsed, Enum):
        return str(parsed.value)
    if isinstance(parsed, (date, datetime)):
        return parsed.isoformat()
    if isinstance(parsed, (list, dict)):
        return json.dumps(parsed, sort_keys=True, default=lambda o: o.value if isinstance(o, Enum) else str(o))
    return str(parsed).lower() if isinstance(parsed, bool) else str(parsed)


def extract_deterministic(text: str, ambiguous: Optional[Dict[str, List[str]]] = None) -> Dict[str, str]:
    """Stadio 2: solo codice. Tabelle ``chiave: valore`` con chiavi di regola note + formule di prosa standard.

    Se ``ambiguous`` è un dizionario, una formula che nello stesso testo dà valori DIVERSI (es. contributo 75% e 70%) non viene pubblicata:
    i valori trovati finiscono in ``ambiguous`` e la decisione passa a una persona. Senza dizionario vale il primo valore (uso storico)."""
    found: Dict[str, str] = {}
    for line in text.splitlines():
        m = _KV_LINE.match(line)
        if m and m.group(1).lower() in RULE_KEYS:
            try:
                found[m.group(1).lower()] = normalize_value(m.group(1).lower(), m.group(2))
            except ValueError:
                continue  # valore non conforme: non si indovina
    for key, pattern, convert in PROSE_PATTERNS:
        if key in found:
            continue
        values: List[str] = []
        for m in pattern.finditer(text):
            try:
                v = normalize_value(key, convert(m))
            except (ValueError, InvalidOperation):
                continue
            if v not in values:
                values.append(v)
            if ambiguous is None:
                break
        if len(values) > 1 and ambiguous is not None:
            ambiguous[key] = values
        elif values:
            found[key] = values[0]
    for key, value in extract_more_rules(text).items():
        if key not in found:
            try:
                found[key] = normalize_value(key, value)
            except ValueError:
                continue
    return found


@dataclass
class ExtractionOutcome:
    published: Dict[str, str]
    pending_review: List[str]
    cache_hit: bool
    coverage_activated: bool
    requirements: Optional[List[dict]] = None


class Ingestion:
    # ------------------------------------------------------------------ catalogo (Stadio 1)
    @staticmethod
    def catalog(bando_id: str, name: str, issuer: Optional[str] = None, deadline: Optional[str] = None, source_url: Optional[str] = None) -> None:
        with connect() as conn:
            conn.execute(
                "INSERT INTO bandi (bando_id, name, issuer, deadline, source_url) VALUES (?,?,?,?,?) "
                "ON CONFLICT(bando_id) DO UPDATE SET name=excluded.name, issuer=excluded.issuer, deadline=excluded.deadline, source_url=excluded.source_url",
                (bando_id, name, issuer, deadline, source_url))

    @staticmethod
    def list_catalog() -> List[dict]:
        with connect() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM bandi ORDER BY bando_id").fetchall()]

    @staticmethod
    def get_bando(bando_id: str) -> Optional[dict]:
        with connect() as conn:
            row = conn.execute("SELECT * FROM bandi WHERE bando_id=?", (bando_id,)).fetchone()
        return dict(row) if row else None

    @classmethod
    def confirm(cls, bando_id: str) -> bool:
        """Il cliente conferma il bando: registra la richiesta e dice se le regole sono già in cache."""
        with connect() as conn:
            conn.execute("UPDATE bandi SET requested_by_clients = requested_by_clients + 1 WHERE bando_id=?", (bando_id,))
            n = conn.execute("SELECT COUNT(*) c FROM rules WHERE bando_id=? AND status='PUBLISHED'", (bando_id,)).fetchone()["c"]
        return n > 0

    # ------------------------------------------------------------------ estrazione (Stadi 2 e 3)
    @classmethod
    def extract(cls, bando_id: str, source_text: Optional[str] = None, ai_passes: Optional[List[Dict[str, Any]]] = None,
                source_ref: Optional[str] = None, sources: Optional[List[Tuple[str, str]]] = None) -> ExtractionOutcome:
        """``sources`` = [(riferimento, testo)] in ordine di fiducia (prima le ufficiali): regole e requisiti si leggono da tutte, ciascuno con la propria fonte."""
        published: Dict[str, str] = {}
        pending: List[str] = []
        with connect() as conn:
            if not conn.execute("SELECT 1 FROM bandi WHERE bando_id=?", (bando_id,)).fetchone():
                raise KeyError(bando_id)
            existing = {r["rule_key"]: r for r in conn.execute("SELECT * FROM rules WHERE bando_id=?", (bando_id,)).fetchall()}
            cache_hit = any(r["status"] == "PUBLISHED" for r in existing.values())
            had_complete = cache_hit and not any(r["status"] == "PENDING_REVIEW" for r in existing.values())
            reqs: List[dict] = []

            def put(key: str, value: Optional[str], origin: str, status: str, passes: Optional[list] = None, ref: Optional[str] = None) -> None:
                conn.execute(
                    "INSERT INTO rules (bando_id, rule_key, value, origin, status, passes, source_ref) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(bando_id, rule_key) DO UPDATE SET value=excluded.value, origin=excluded.origin, status=excluded.status, "
                    "passes=excluded.passes, source_ref=excluded.source_ref",
                    (bando_id, key, value, origin, status, json.dumps(passes) if passes is not None else None, ref or source_ref))

            def is_published(key: str) -> bool:
                return key in existing and existing[key]["status"] == "PUBLISHED"

            srcs = sources or ([(source_ref or "testo caricato", source_text)] if source_text else [])
            if srcs:                                                   # Stadio 2
                if sources is not None:
                    # analisi su tutte le fonti in memoria: le regole lette in automatico si rifanno (le fonti possono essere cambiate);
                    # quelle decise da una persona restano. L'estrazione classica da un solo testo non sovrascrive mai una regola pubblicata.
                    conn.execute("DELETE FROM rules WHERE bando_id=? AND origin='STRUCTURED_PARSING'", (bando_id,))
                    existing = {k: v for k, v in existing.items() if v["origin"] != "STRUCTURED_PARSING"}
                found: Dict[str, List[Tuple[str, str]]] = {}
                for ref, txt in srcs:
                    amb: Dict[str, List[str]] = {}
                    for key, value in extract_deterministic(txt, amb).items():
                        found.setdefault(key, []).append((ref, value))
                    for key, values in amb.items():
                        found.setdefault(key, []).extend((ref, v) for v in values)
                for key, hits in found.items():
                    if is_published(key):
                        continue
                    values = list(dict.fromkeys(v for _, v in hits))
                    if len(values) == 1:
                        put(key, values[0], "STRUCTURED_PARSING", "PUBLISHED", ref=hits[0][0])
                        published[key] = values[0]
                        existing[key] = {"status": "PUBLISHED", "origin": "STRUCTURED_PARSING"}
                    else:
                        # fonti diverse danno valori diversi: una regola ambigua non diventa un controllo attivo, la decide una persona
                        put(key, None, "STRUCTURED_PARSING", "PENDING_REVIEW", values, ref="; ".join(dict.fromkeys(r for r, _ in hits))[:300])
                        pending.append(key)
                        existing[key] = {"status": "PENDING_REVIEW", "origin": "STRUCTURED_PARSING"}
                seen_req: set = set()
                for ref, txt in srcs:
                    for r in extract_requirements(txt, source_ref=ref):
                        k = re.sub(r"\s+", " ", r["text"].lower())[:160]
                        if k in seen_req or len(reqs) >= 300:
                            continue
                        if r["kind"] == "DA_REVISIONARE" and sum(1 for x in reqs if x["kind"] == "DA_REVISIONARE") >= 80:
                            continue  # una persona non può rivedere centinaia di frasi: le prime 80 bastano a segnalare il problema
                        seen_req.add(k)
                        reqs.append(r)
                conn.execute("DELETE FROM requirements WHERE bando_id=? AND origin='STRUCTURED_PARSING'", (bando_id,))
                base = conn.execute("SELECT COALESCE(MAX(seq), 0) m FROM requirements WHERE bando_id=?", (bando_id,)).fetchone()["m"]
                for i, r in enumerate(reqs, base + 1):
                    conn.execute("INSERT INTO requirements (bando_id, seq, topic, kind, text, criteria, source_ref, origin) VALUES (?,?,?,?,?,?,?,?)",
                                 (bando_id, i, r["topic"], r["kind"], r["text"], json.dumps(r["criteria"]), r["source_ref"], "STRUCTURED_PARSING"))

            if ai_passes:                                              # Stadio 3: il confronto lo fa il codice
                keys = sorted({k for p in ai_passes for k in p})
                for key in keys:
                    if is_published(key):
                        continue
                    normalized: List[Optional[str]] = []
                    for p in ai_passes:
                        try:
                            normalized.append(normalize_value(key, p[key]) if key in p else None)
                        except ValueError:
                            normalized.append(None)
                    agree = len(ai_passes) >= 2 and None not in normalized and len(set(normalized)) == 1
                    if agree:
                        put(key, normalized[0], "MULTI_PASS_AGREEMENT", "PUBLISHED", normalized)
                        published[key] = normalized[0]
                        existing[key] = {"status": "PUBLISHED"}
                    else:
                        put(key, None, "MULTI_PASS_AGREEMENT", "PENDING_REVIEW", normalized)
                        pending.append(key)

            any_published = any(r["status"] == "PUBLISHED" for r in existing.values())
            still_pending = bool(pending) or any(r["status"] == "PENDING_REVIEW" for r in existing.values())
            complete = any_published and not still_pending
            conn.execute("UPDATE bandi SET extraction_status=?, catalog_status='MATCHED' WHERE bando_id=?",
                         ("COMPLETED" if complete else "PARTIAL", bando_id))
        return ExtractionOutcome(published, pending, cache_hit, coverage_activated=complete and not had_complete, requirements=reqs)

    # ------------------------------------------------------------------ revisione umana
    @staticmethod
    def review_queue() -> List[dict]:
        with connect() as conn:
            rows = conn.execute("SELECT bando_id, rule_key, passes, source_ref FROM rules WHERE status='PENDING_REVIEW' ORDER BY bando_id, rule_key").fetchall()
        return [{"bando_id": r["bando_id"], "rule_key": r["rule_key"], "passes": json.loads(r["passes"] or "[]"), "source_ref": r["source_ref"]} for r in rows]

    @classmethod
    def resolve_review(cls, bando_id: str, rule_key: str, value: Any) -> str:
        normalized = normalize_value(rule_key, value)
        with connect() as conn:
            row = conn.execute("SELECT status FROM rules WHERE bando_id=? AND rule_key=?", (bando_id, rule_key)).fetchone()
            if row is None:
                raise KeyError(rule_key)
            conn.execute("UPDATE rules SET value=?, origin='HUMAN_REVIEW', status='PUBLISHED' WHERE bando_id=? AND rule_key=?", (normalized, bando_id, rule_key))
            pending_left = conn.execute("SELECT COUNT(*) c FROM rules WHERE bando_id=? AND status='PENDING_REVIEW'", (bando_id,)).fetchone()["c"]
            conn.execute("UPDATE bandi SET extraction_status=? WHERE bando_id=?", ("PARTIAL" if pending_left else "COMPLETED", bando_id))
        return normalized

    # ------------------------------------------------------------------ stato e composizione del GrantRuleSet
    @staticmethod
    def status(bando_id: str) -> Optional[dict]:
        with connect() as conn:
            bando = conn.execute("SELECT * FROM bandi WHERE bando_id=?", (bando_id,)).fetchone()
            if bando is None:
                return None
            rows = conn.execute("SELECT origin, status FROM rules WHERE bando_id=?", (bando_id,)).fetchall()
        published = [r for r in rows if r["status"] == "PUBLISHED"]
        return {
            "bando_id": bando_id, "catalog_status": bando["catalog_status"], "extraction_status": bando["extraction_status"],
            "cache_hit": len(published) > 0,
            "rules_extracted_total": len(rows),
            "rules_from_structured_parsing": sum(1 for r in published if r["origin"] == "STRUCTURED_PARSING"),
            "rules_from_multi_pass_ai": sum(1 for r in rows if r["origin"] == "MULTI_PASS_AGREEMENT"),
            "rules_with_pass_agreement": sum(1 for r in published if r["origin"] == "MULTI_PASS_AGREEMENT"),
            "rules_pending_human_review": sum(1 for r in rows if r["status"] == "PENDING_REVIEW"),
            "rules_human_reviewed": sum(1 for r in published if r["origin"] == "HUMAN_REVIEW"),
            "rules_from_curated_source": sum(1 for r in published if r["origin"] == "CURATED_SOURCE"),
            "requested_by_clients_count": bando["requested_by_clients"],
        }

    @classmethod
    def build_rule_set(cls, bando_id: str) -> tuple[Optional[GrantRuleSet], List[str]]:
        """Compone il ``GrantRuleSet`` dalle sole regole pubblicate (le altre restano ``None``: nessun default inventato)."""
        bando = cls.get_bando(bando_id)
        if bando is None:
            raise KeyError(bando_id)
        with connect() as conn:
            rows = conn.execute("SELECT rule_key, value FROM rules WHERE bando_id=? AND status='PUBLISHED' ORDER BY rule_key", (bando_id,)).fetchall()
        values = {r["rule_key"]: r["value"] for r in rows}
        if not values:
            with connect() as conn:
                shas = [r["sha256"] for r in conn.execute("SELECT sha256 FROM bando_sources WHERE bando_id=? ORDER BY sha256", (bando_id,)).fetchall()]
            if not shas:
                return None, ["nessuna regola pubblicata"]
            # letto dal testo ma senza regole numeriche: si usa comunque, con i soli controlli che lavorano sui dati della voce (nessun default inventato)
            version = hashlib.sha256(json.dumps(shas, separators=(",", ":")).encode("utf-8")).hexdigest()[:32]
            return (GrantRuleSet.model_validate({"bando_id": bando_id, "bando_name": bando["name"], "rule_version_hash": version}),
                    ["nessuna regola numerica: si eseguono solo i controlli sui dati delle voci"])
        version = hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:32]
        parsed: Dict[str, Any] = {}
        for k, v in values.items():
            parsed[k] = json.loads(v) if v and v[:1] in "[{" else v
            if v in ("true", "false"):
                parsed[k] = v == "true"
        return GrantRuleSet.model_validate({**parsed, "bando_id": bando_id, "bando_name": bando["name"], "rule_version_hash": version}), []
