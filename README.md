# Spiżarka dla Home Assistant

Własna integracja magazynowa dla Home Assistant, rozwijana w stylu Grocy.

Repozytorium: https://github.com/esem22/spizarka2

## Wersja 0.2.0

Wersja 0.2.0 dodaje własny panel **Spiżarka** w menu bocznym Home Assistant. Dane utworzone w 0.1.0 są zachowywane.

Panel umożliwia:

- przeglądanie produktów,
- wyszukiwanie po nazwie, EAN i kategorii,
- filtrowanie po lokalizacji i kategorii,
- podgląd stanu i najbliższego terminu ważności,
- dodawanie nowych produktów,
- dodawanie partii z datą ważności,
- zużywanie stanu metodą FEFO,
- przenoszenie stanu pomiędzy lokalizacjami,
- widok produktów z krótkim terminem,
- widok produktów poniżej stanu minimalnego.

## Aktualizacja przez HACS

1. Wgraj pliki wersji 0.2.0 do repozytorium `https://github.com/esem22/spizarka2`.
2. W HACS otwórz **Spiżarka**.
3. Odśwież informacje o repozytorium, jeśli aktualizacja nie pojawi się od razu.
4. Pobierz najnowszą wersję.
5. Uruchom ponownie Home Assistant.
6. Po restarcie w menu bocznym pojawi się pozycja **Spiżarka**.

## Pierwsza instalacja przez HACS

1. HACS → **Integracje**.
2. Menu z trzema kropkami → **Niestandardowe repozytoria**.
3. Repozytorium: `https://github.com/esem22/spizarka2`.
4. Typ: **Integration**.
5. Dodaj repozytorium i pobierz **Spiżarka**.
6. Uruchom ponownie Home Assistant.
7. Ustawienia → Urządzenia i usługi → Dodaj integrację → **Spiżarka**.

## Domyślne lokalizacje

- Spiżarnia
- Lodówka
- Zamrażarka
- Apteczka

## Sensory

Integracja zachowuje sensory zbiorcze:

- Produkty,
- Łączny stan,
- Niski stan,
- Krótki termin,
- Przeterminowane.

## Dane

Produkty i partie są zapisywane przez mechanizm Home Assistant Store. Aktualizacja z 0.1.0 do 0.2.0 nie zmienia formatu danych.
