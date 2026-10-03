from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_DATA_UPDATED
from .manager import SpizarkaManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    manager: SpizarkaManager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SpizarkaProductsSensor(manager, entry.entry_id),
        SpizarkaStockSensor(manager, entry.entry_id),
        SpizarkaLowStockSensor(manager, entry.entry_id),
        SpizarkaExpiringSensor(manager, entry.entry_id),
        SpizarkaExpiredSensor(manager, entry.entry_id),
    ])


class SpizarkaBaseSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, manager: SpizarkaManager, entry_id: str, key: str, name: str, icon: str) -> None:
        self.manager = manager
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_DATA_UPDATED, self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class SpizarkaProductsSensor(SpizarkaBaseSensor):
    def __init__(self, manager: SpizarkaManager, entry_id: str) -> None:
        super().__init__(manager, entry_id, "products", "Produkty", "mdi:food-variant")

    @property
    def native_value(self) -> int:
        return len(self.manager.data["products"])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        totals = self.manager.product_totals()
        products = []
        for product in self.manager.data["products"]:
            item = dict(product)
            item["quantity"] = totals.get(product["id"], 0.0)
            products.append(item)
        return {"spizarka_kind": "products", "products": products, "locations": self.manager.data["locations"]}


class SpizarkaStockSensor(SpizarkaBaseSensor):
    def __init__(self, manager: SpizarkaManager, entry_id: str) -> None:
        super().__init__(manager, entry_id, "stock", "Łączny stan", "mdi:package-variant")

    @property
    def native_value(self) -> float:
        return round(sum(float(b["quantity"]) for b in self.manager.data["batches"]), 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"spizarka_kind": "stock", "batches": self.manager.data["batches"]}


class SpizarkaLowStockSensor(SpizarkaBaseSensor):
    def __init__(self, manager: SpizarkaManager, entry_id: str) -> None:
        super().__init__(manager, entry_id, "low_stock", "Niski stan", "mdi:cart-arrow-down")

    @property
    def native_value(self) -> int:
        return len(self.manager.low_stock_products())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"spizarka_kind": "low_stock", "products": self.manager.low_stock_products()}


class SpizarkaExpiringSensor(SpizarkaBaseSensor):
    def __init__(self, manager: SpizarkaManager, entry_id: str) -> None:
        super().__init__(manager, entry_id, "expiring", "Krótki termin", "mdi:calendar-alert")

    @property
    def native_value(self) -> int:
        return len(self.manager.expiring_batches(7))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"spizarka_kind": "expiring", "days": 7, "batches": self.manager.expiring_batches(7)}


class SpizarkaExpiredSensor(SpizarkaBaseSensor):
    def __init__(self, manager: SpizarkaManager, entry_id: str) -> None:
        super().__init__(manager, entry_id, "expired", "Przeterminowane", "mdi:alert-circle-outline")

    @property
    def native_value(self) -> int:
        return len(self.manager.expired_batches())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"spizarka_kind": "expired", "batches": self.manager.expired_batches()}
