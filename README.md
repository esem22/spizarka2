# Spiżarka dla Home Assistant

Własna integracja magazynowa dla Home Assistant, rozwijana w stylu Grocy.

Repozytorium: https://github.com/esem22/spizarka

## Wersja 0.1.0

Pierwsza wersja testowa zawiera:

- konfigurację przez GUI Home Assistant,
- lokalny zapis danych przez Home Assistant Store,
- produkty: nazwa, EAN, kategoria, jednostka, stan minimalny,
- lokalizacje magazynowe,
- partie produktu z ilością i datą ważności,
- dodawanie stanu,
- zużywanie stanu metodą FEFO,
- przenoszenie stanu pomiędzy lokalizacjami,
- sensory zbiorcze do automatyzacji.

## Instalacja ręczna

1. Rozpakuj ZIP.
2. Skopiuj katalog `custom_components/spizarka` do `/config/custom_components/spizarka` w Home Assistant.
3. Uruchom ponownie Home Assistant.
4. Wejdź w `Ustawienia -> Urządzenia i usługi -> Dodaj integrację`.
5. Wyszukaj `Spiżarka` i dodaj integrację.

## Test v0.1.0

Operacje są dostępne w `Narzędzia deweloperskie -> Akcje`.

### 1. Dodaj produkt

Akcja: `spizarka.add_product`

Przykład:

```yaml
name: Mleko 3,2%
ean: "5901234567890"
category: Nabiał
unit: szt.
minimum: 2
```

### 2. Dodaj stan

Akcja: `spizarka.add_stock`

```yaml
ean: "5901234567890"
quantity: 4
location: Lodówka
expiry_date: "2026-10-10"
```

### 3. Zużyj produkt

Akcja: `spizarka.consume_stock`

```yaml
ean: "5901234567890"
quantity: 1
```

Jeśli produkt ma kilka partii, zużywana jest najpierw partia z najbliższym terminem ważności.

### 4. Przenieś produkt

Akcja: `spizarka.move_stock`

```yaml
ean: "5901234567890"
quantity: 1
from_location: Lodówka
to_location: Spiżarnia
```

## Domyślne lokalizacje

Po pierwszym uruchomieniu tworzone są:

- Spiżarnia
- Lodówka
- Zamrażarka
- Apteczka

Dodatkowe lokalizacje można tworzyć akcją `spizarka.add_location`.

## Sensory

Integracja tworzy sensory zbiorcze:

- `sensor.spizarka_produkty`
- `sensor.spizarka_laczny_stan`
- `sensor.spizarka_niski_stan`
- `sensor.spizarka_krotki_termin`
- `sensor.spizarka_przeterminowane`

Nazwy `entity_id` mogą zostać automatycznie dostosowane przez Home Assistant.

## Plan dalszych wersji

- panel Spiżarki w interfejsie HA,
- edycja i usuwanie produktów,
- skanowanie EAN,
- automatyczna lista zakupów,
- pobieranie informacji o produktach po EAN,
- etykiety i drukarki Niimbot.
