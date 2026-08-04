"""
Customer Preference API
========================

A small FastAPI service that stores each customer's communication
preferences and exposes add / update / delete / search endpoints. Built as
a test target for the ComplianceAgent guardrail system's Repositories tab
and Engine A contract/mutation probing (see ../cmp-dashboard-develop/README.md).

Run:
    uvicorn main:app --reload --port 8000

OpenAPI spec (for the orchestrator's --openapi flag):
    http://localhost:8000/openapi.json
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Response

from models import Preference, PreferenceCreate, PreferenceUpdate

app = FastAPI(
    title="Customer Preference API",
    version="1.0.0",
    description="Stores per-customer communication preferences.",
)

# In-memory store keyed by customer_id. A real service would back this with
# a database; this is a self-contained test target, not production storage.
_store: dict[str, Preference] = {}


@app.post("/preferences", response_model=Preference, status_code=201)
def add_preference(pref: PreferenceCreate) -> Preference:
    if pref.customer_id in _store:
        raise HTTPException(
            status_code=409,
            detail=f"preference already exists for customer_id={pref.customer_id!r}",
        )
    record = Preference(**pref.model_dump())
    _store[pref.customer_id] = record
    return record


@app.put("/preferences/{customer_id}", response_model=Preference)
def update_preference(customer_id: str, update: PreferenceUpdate) -> Preference:
    existing = _store.get(customer_id)
    if existing is None:
        raise HTTPException(
            status_code=404,
            detail=f"no preference found for customer_id={customer_id!r}",
        )
    data = existing.model_dump()
    data.update(update.model_dump(exclude_unset=True, exclude_none=True))
    updated = Preference(**data)
    _store[customer_id] = updated
    return updated


@app.delete("/preferences/{customer_id}", status_code=204, response_class=Response)
def delete_preference(customer_id: str) -> Response:
    if customer_id not in _store:
        raise HTTPException(
            status_code=404,
            detail=f"no preference found for customer_id={customer_id!r}",
        )
    del _store[customer_id]
    return Response(status_code=204)


@app.get("/preferences", response_model=list[Preference])
def search_preferences(
    customer_id: Optional[str] = None,
    comm_channel: Optional[str] = None,
    marketing_opt_in: Optional[bool] = None,
    zip_code: Optional[str] = None,
    display_name_contains: Optional[str] = None,
) -> list[Preference]:
    results = list(_store.values())
    if customer_id is not None:
        results = [r for r in results if r.customer_id == customer_id]
    if comm_channel is not None:
        results = [r for r in results if r.comm_channel == comm_channel]
    if marketing_opt_in is not None:
        results = [r for r in results if r.marketing_opt_in == marketing_opt_in]
    if zip_code is not None:
        results = [r for r in results if r.zip_code == zip_code]
    if display_name_contains is not None:
        needle = display_name_contains.lower()
        results = [r for r in results if needle in r.display_name.lower()]
    return results
