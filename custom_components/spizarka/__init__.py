from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, PLATFORMS
from .manager import SpizarkaManager

PRODUCT_SELECTOR = {
    vol.Optional("product_id"): cv.string,
    vol.Optional("ean"): cv.string,
    vol.Optional("name"): cv.string,
}


def _product_args(data: dict) -> dict:
    args = {key: data.get(key) for key in ("product_id", "ean", "name")}
    if not any(args.values()):
        raise HomeAssistantError("Podaj product_id, ean albo name.")
    return args


def _manager(hass: HomeAssistant) -> SpizarkaManager:
    entries = hass.data.get(DOMAIN, {})
    for value in entries.values():
        if isinstance(value, SpizarkaManager):
            return value
    raise HomeAssistantError("Integracja Spiżarka nie jest skonfigurowana.")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def handle_add_product(call: ServiceCall) -> None:
        await _manager(hass).add_product(
            call.data["name"],
            call.data.get("ean"),
            call.data.get("category"),
            call.data.get("unit", "szt."),
            call.data.get("minimum", 0),
        )

    async def handle_add_location(call: ServiceCall) -> None:
        await _manager(hass).add_location(call.data["name"])

    async def handle_add_stock(call: ServiceCall) -> None:
        await _manager(hass).add_stock(
            **_product_args(call.data),
            quantity=call.data["quantity"],
            location=call.data["location"],
            expiry_date=call.data.get("expiry_date"),
        )

    async def handle_consume_stock(call: ServiceCall) -> None:
        await _manager(hass).consume_stock(
            **_product_args(call.data),
            quantity=call.data["quantity"],
            location=call.data.get("location"),
        )

    async def handle_move_stock(call: ServiceCall) -> None:
        await _manager(hass).move_stock(
            **_product_args(call.data),
            quantity=call.data["quantity"],
            from_location=call.data["from_location"],
            to_location=call.data["to_location"],
        )

    hass.services.async_register(
        DOMAIN,
        "add_product",
        handle_add_product,
        schema=vol.Schema({
            vol.Required("name"): cv.string,
            vol.Optional("ean"): cv.string,
            vol.Optional("category"): cv.string,
            vol.Optional("unit", default="szt."): cv.string,
            vol.Optional("minimum", default=0): vol.Coerce(float),
        }),
    )
    hass.services.async_register(
        DOMAIN,
        "add_location",
        handle_add_location,
        schema=vol.Schema({vol.Required("name"): cv.string}),
    )
    hass.services.async_register(
        DOMAIN,
        "add_stock",
        handle_add_stock,
        schema=vol.Schema({
            **PRODUCT_SELECTOR,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Required("location"): cv.string,
            vol.Optional("expiry_date"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        "consume_stock",
        handle_consume_stock,
        schema=vol.Schema({
            **PRODUCT_SELECTOR,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Optional("location"): cv.string,
        }),
    )
    hass.services.async_register(
        DOMAIN,
        "move_stock",
        handle_move_stock,
        schema=vol.Schema({
            **PRODUCT_SELECTOR,
            vol.Required("quantity"): vol.Coerce(float),
            vol.Required("from_location"): cv.string,
            vol.Required("to_location"): cv.string,
        }),
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager = SpizarkaManager(hass)
    await manager.async_load()
    hass.data[DOMAIN][entry.entry_id] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded
