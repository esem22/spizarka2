from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any
from uuid import uuid4

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DEFAULT_LOCATIONS, SIGNAL_DATA_UPDATED, STORAGE_KEY, STORAGE_VERSION


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _expiry_sort_key(batch: dict[str, Any]) -> tuple[int, str]:
    expiry = batch.get("expiry_date")
    return (1, "9999-12-31") if not expiry else (0, expiry)


class SpizarkaManager:
    """Persistent storage and stock operations for Spiżarka."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data: dict[str, Any] = {"products": [], "locations": [], "batches": []}

    async def async_load(self) -> None:
        stored = await self.store.async_load()
        if stored:
            self.data = stored
            self.data.setdefault("products", [])
            self.data.setdefault("locations", [])
            self.data.setdefault("batches", [])
            return

        self.data = {
            "products": [],
            "locations": [
                {"id": _new_id("loc"), "name": name} for name in DEFAULT_LOCATIONS
            ],
            "batches": [],
        }
        await self._async_save()

    async def _async_save(self) -> None:
        await self.store.async_save(self.data)
        async_dispatcher_send(self.hass, SIGNAL_DATA_UPDATED)

    def snapshot(self) -> dict[str, Any]:
        return deepcopy(self.data)

    def _find_product(self, *, product_id: str | None = None, ean: str | None = None, name: str | None = None) -> dict[str, Any]:
        if product_id:
            for product in self.data["products"]:
                if product["id"] == product_id:
                    return product
        if ean:
            for product in self.data["products"]:
                if product.get("ean") == ean:
                    return product
        if name:
            lowered = name.casefold()
            for product in self.data["products"]:
                if product["name"].casefold() == lowered:
                    return product
        raise HomeAssistantError("Nie znaleziono produktu.")

    def _find_location(self, value: str) -> dict[str, Any]:
        for location in self.data["locations"]:
            if location["id"] == value or location["name"].casefold() == value.casefold():
                return location
        raise HomeAssistantError(f"Nie znaleziono lokalizacji: {value}")

    async def add_location(self, name: str) -> dict[str, Any]:
        if any(loc["name"].casefold() == name.casefold() for loc in self.data["locations"]):
            raise HomeAssistantError("Lokalizacja o tej nazwie już istnieje.")
        location = {"id": _new_id("loc"), "name": name.strip()}
        self.data["locations"].append(location)
        await self._async_save()
        return location

    async def add_product(self, name: str, ean: str | None, category: str | None, unit: str, minimum: float) -> dict[str, Any]:
        if ean and any(p.get("ean") == ean for p in self.data["products"]):
            raise HomeAssistantError("Produkt z tym EAN już istnieje.")
        product = {
            "id": _new_id("prod"),
            "name": name.strip(),
            "ean": ean or None,
            "category": category or None,
            "unit": unit.strip() or "szt.",
            "minimum": float(minimum),
        }
        self.data["products"].append(product)
        await self._async_save()
        return product

    async def add_stock(self, *, quantity: float, location: str, expiry_date: str | None = None, product_id: str | None = None, ean: str | None = None, name: str | None = None) -> None:
        if quantity <= 0:
            raise HomeAssistantError("Ilość musi być większa od zera.")
        product = self._find_product(product_id=product_id, ean=ean, name=name)
        loc = self._find_location(location)
        if expiry_date:
            try:
                date.fromisoformat(expiry_date)
            except ValueError as err:
                raise HomeAssistantError("Data ważności musi mieć format RRRR-MM-DD.") from err
        self.data["batches"].append({
            "id": _new_id("batch"),
            "product_id": product["id"],
            "location_id": loc["id"],
            "quantity": float(quantity),
            "expiry_date": expiry_date or None,
        })
        await self._async_save()

    async def consume_stock(self, *, quantity: float, location: str | None = None, product_id: str | None = None, ean: str | None = None, name: str | None = None) -> None:
        if quantity <= 0:
            raise HomeAssistantError("Ilość musi być większa od zera.")
        product = self._find_product(product_id=product_id, ean=ean, name=name)
        location_id = self._find_location(location)["id"] if location else None
        candidates = [
            batch for batch in self.data["batches"]
            if batch["product_id"] == product["id"]
            and (location_id is None or batch["location_id"] == location_id)
            and batch["quantity"] > 0
        ]
        available = sum(batch["quantity"] for batch in candidates)
        if available < quantity:
            raise HomeAssistantError(f"Za mały stan. Dostępne: {available:g} {product['unit']}.")

        remaining = float(quantity)
        for batch in sorted(candidates, key=_expiry_sort_key):
            take = min(batch["quantity"], remaining)
            batch["quantity"] -= take
            remaining -= take
            if remaining <= 0:
                break
        self.data["batches"] = [b for b in self.data["batches"] if b["quantity"] > 0]
        await self._async_save()

    async def move_stock(self, *, quantity: float, from_location: str, to_location: str, product_id: str | None = None, ean: str | None = None, name: str | None = None) -> None:
        if quantity <= 0:
            raise HomeAssistantError("Ilość musi być większa od zera.")
        product = self._find_product(product_id=product_id, ean=ean, name=name)
        source = self._find_location(from_location)
        target = self._find_location(to_location)
        if source["id"] == target["id"]:
            raise HomeAssistantError("Lokalizacja źródłowa i docelowa są takie same.")

        candidates = [b for b in self.data["batches"] if b["product_id"] == product["id"] and b["location_id"] == source["id"] and b["quantity"] > 0]
        available = sum(b["quantity"] for b in candidates)
        if available < quantity:
            raise HomeAssistantError(f"Za mały stan w lokalizacji źródłowej. Dostępne: {available:g} {product['unit']}.")

        remaining = float(quantity)
        new_batches: list[dict[str, Any]] = []
        for batch in sorted(candidates, key=_expiry_sort_key):
            take = min(batch["quantity"], remaining)
            batch["quantity"] -= take
            new_batches.append({
                "id": _new_id("batch"),
                "product_id": product["id"],
                "location_id": target["id"],
                "quantity": take,
                "expiry_date": batch.get("expiry_date"),
            })
            remaining -= take
            if remaining <= 0:
                break
        self.data["batches"].extend(new_batches)
        self.data["batches"] = [b for b in self.data["batches"] if b["quantity"] > 0]
        await self._async_save()

    def product_totals(self) -> dict[str, float]:
        totals = {product["id"]: 0.0 for product in self.data["products"]}
        for batch in self.data["batches"]:
            totals[batch["product_id"]] = totals.get(batch["product_id"], 0.0) + float(batch["quantity"])
        return totals

    def low_stock_products(self) -> list[dict[str, Any]]:
        totals = self.product_totals()
        result = []
        for product in self.data["products"]:
            total = totals.get(product["id"], 0.0)
            if total < float(product.get("minimum", 0)):
                item = deepcopy(product)
                item["quantity"] = total
                result.append(item)
        return result

    def expired_batches(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        return [deepcopy(b) for b in self.data["batches"] if b.get("expiry_date") and b["expiry_date"] < today]

    def expiring_batches(self, days: int = 7) -> list[dict[str, Any]]:
        from datetime import timedelta
        today = date.today()
        limit = today + timedelta(days=days)
        result = []
        for batch in self.data["batches"]:
            expiry = batch.get("expiry_date")
            if not expiry:
                continue
            parsed = date.fromisoformat(expiry)
            if today <= parsed <= limit:
                result.append(deepcopy(batch))
        return result
