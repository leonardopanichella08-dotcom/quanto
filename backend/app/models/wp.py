"""Schemi della ripartizione delle voci di budget tra i pacchetti di lavoro (WP) del bando (Modulo 2.1)."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.schemas import CostCategory


class WorkPackage(BaseModel):
    """Un pacchetto di lavoro con i suoi vincoli. Nessun vincolo è inventato: li indica chi sa come il bando divide il lavoro (o nessuno)."""

    model_config = ConfigDict(extra="forbid")

    wp_id: str = Field(..., min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._\- ]+$")
    name: str = Field(default="", max_length=120)
    min_share_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Quota minima del totale ammesso (0,10 = 10%)")
    target_share_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Quota desiderata: il piano si avvicina il più possibile")
    max_share_pct: Optional[float] = Field(default=None, ge=0, le=1, description="Quota massima del totale ammesso")
    allowed_categories: Optional[List[CostCategory]] = Field(default=None, description="Categorie di spesa che il WP può contenere (None = tutte)")
    category_max_share: Dict[CostCategory, float] = Field(default_factory=dict, description="Tetto per categoria sul totale del WP (es. consulenze al 20% del WP)")

    @field_validator("category_max_share")
    @classmethod
    def _unit(cls, v: Dict[CostCategory, float]) -> Dict[CostCategory, float]:
        if any(not 0 <= x <= 1 for x in v.values()):
            raise ValueError("I tetti per categoria vanno da 0 a 1")
        return v

    @model_validator(mode="after")
    def _order(self) -> "WorkPackage":
        lo, tg, hi = self.min_share_pct, self.target_share_pct, self.max_share_pct
        if lo is not None and hi is not None and lo > hi:
            raise ValueError(f"WP {self.wp_id}: la quota minima supera la massima")
        if tg is not None and ((lo is not None and tg < lo) or (hi is not None and tg > hi)):
            raise ValueError(f"WP {self.wp_id}: la quota desiderata deve stare tra minima e massima")
        return self


class WPItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str = Field(..., min_length=1, max_length=64)
    category: CostCategory
    amount_eur: float = Field(..., gt=0, description="Importo AMMESSO dal motore (non quello richiesto)")
    description: str = Field(default="", max_length=200)
    pinned_wp: Optional[str] = Field(default=None, max_length=32, description="Se l'utente ha già deciso il WP di questa voce")


class WPRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: Optional[str] = Field(default=None, max_length=64)
    items: List[WPItem] = Field(..., min_length=1, max_length=400)
    work_packages: List[WorkPackage] = Field(..., min_length=1, max_length=20)
    allow_split: bool = Field(default=False, description="Se vero una voce può essere divisa tra più WP; altrimenti sta tutta in uno")

    @model_validator(mode="after")
    def _consistent(self) -> "WPRequest":
        ids = [w.wp_id for w in self.work_packages]
        if len(ids) != len(set(ids)):
            raise ValueError("wp_id duplicati")
        item_ids = [i.item_id for i in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("item_id duplicati")
        for it in self.items:
            if it.pinned_wp is not None and it.pinned_wp not in ids:
                raise ValueError(f"La voce {it.item_id} è assegnata a un WP che non esiste: {it.pinned_wp}")
        return self
