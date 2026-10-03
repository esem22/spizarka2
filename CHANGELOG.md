# Historia zmian

## 0.1.0 — 2026-10-03

Pierwsza wersja testowa.

- dodano config flow i instalację przez interfejs Home Assistant,
- dodano trwały magazyn danych,
- dodano produkty i lokalizacje,
- dodano partie z ilością i terminem ważności,
- dodano operacje dodawania, zużycia i przenoszenia stanu,
- zużycie działa metodą FEFO,
- dodano sensory zbiorcze: produkty, łączny stan, niski stan, krótki termin i przeterminowane,
- przygotowano strukturę pod dalszą rozbudowę o panel, EAN, listę zakupów i Niimbot.

### HACS
- przygotowano repozytorium pod instalację przez HACS jako Custom Repository,
- dodano `hacs.json`,
- dodano zasoby `brand/icon.png`,
- dodano workflow `.github/workflows/validate.yml` do walidacji HACS,
- zaktualizowano adres repozytorium do `esem22/spizarka2`.
