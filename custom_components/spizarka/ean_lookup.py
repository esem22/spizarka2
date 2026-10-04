from __future__ import annotations

from typing import Any

from aiohttp import ClientError
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import VERSION

OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{code}"
OFF_FIELDS = ",".join(
    [
        "code",
        "product_name",
        "product_name_pl",
        "generic_name",
        "generic_name_pl",
        "brands",
        "categories",
        "quantity",
        "image_front_small_url",
    ]
)


def _clean_code(code: str) -> str:
    value = "".join(ch for ch in str(code) if ch.isdigit())
    if not 8 <= len(value) <= 14:
        raise HomeAssistantError("Kod EAN/GTIN powinien zawierać od 8 do 14 cyfr.")
    return value


def _pick_category(raw: str | None) -> str | None:
    if not raw:
        return None
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    return parts[-1] if parts else None


async def async_lookup_ean(hass: HomeAssistant, code: str) -> dict[str, Any]:
    """Fetch product metadata from Open Food Facts by EAN/GTIN."""
    code = _clean_code(code)
    session = async_get_clientsession(hass)
    headers = {
        "User-Agent": f"SpizarkaHomeAssistant/{VERSION} (https://github.com/esem22/spizarka2)"
    }
    params = {
        "fields": OFF_FIELDS,
        "lc": "pl",
        "cc": "pl",
        "product_type": "all",
    }

    try:
        async with session.get(
            OFF_URL.format(code=code), headers=headers, params=params, timeout=12
        ) as response:
            if response.status == 404:
                return {"found": False, "ean": code, "source": "Open Food Facts"}
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (ClientError, TimeoutError, ValueError) as err:
        raise HomeAssistantError(f"Nie udało się pobrać produktu z Open Food Facts: {err}") from err

    product = payload.get("product") or {}
    if payload.get("status") == 0 or not product:
        return {"found": False, "ean": code, "source": "Open Food Facts"}

    name = (
        product.get("product_name_pl")
        or product.get("product_name")
        or product.get("generic_name_pl")
        or product.get("generic_name")
    )

    return {
        "found": True,
        "ean": str(product.get("code") or code),
        "name": name or "",
        "brand": product.get("brands") or "",
        "category": _pick_category(product.get("categories")) or "",
        "package_quantity": product.get("quantity") or "",
        "image_url": product.get("image_front_small_url") or "",
        "source": "Open Food Facts",
    }
