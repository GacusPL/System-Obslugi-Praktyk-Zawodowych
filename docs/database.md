## Wybór systemu bazy danych

### Prototyp: SQLite

Na etapie prototypu projekt wykorzystuje SQLite jako silnik bazy danych.
Uzasadnienie:

- wbudowana biblioteka standardowa Pythona (moduł `sqlite3`) — zero
  dodatkowych zależności
- nie wymaga osobnego procesu serwerowego, baza to pojedynczy plik `.db`
- pełna zgodność ze standardem SQL używanym w szkielecie tabel
- wystarczająca wydajność dla środowiska developerskiego i testowego
- natywna obsługa w DBeaver i Flask-SQLAlchemy

### Ograniczenia SQLite w kontekście dalszego rozwoju

- brak obsługi współbieżnych zapisów (blokada na poziomie pliku)
- ograniczone wsparcie dla typów danych (brak natywnego BOOLEAN, DATE)
- brak wbudowanej replikacji i mechanizmów backupu hot-copy
- nieodpowiedni dla środowiska produkcyjnego z wieloma jednoczesnym
  sesjami (docelowo 30+ użytkowników jednocześnie wg wymagań)

### Docelowy silnik: MariaDB

Na etapie wdrożenia produkcyjnego rekomendowany jest MariaDB ze względu
na pełne wsparcie dla współbieżności (InnoDB), natywne typy DATE/DATETIME,
mechanizmy replikacji oraz lepsze narzędzia monitorowania.
Migracja ze SQLite do MariaDB jest bezpośrednio wspierana przez
Flask-SQLAlchemy poprzez zmianę connection stringa w konfiguracji aplikacji.

| Kryterium | SQLite | MariaDB |
|---|---|---|
| Konfiguracja | Plik `.db` | Serwer + konfiguracja |
| Współbieżność | Ograniczona | Pełna |
| Typy danych | Uproszczone | Pełny standard SQL |
| Środowisko | Prototyp / dev | Produkcja |
| Migracja | — | Flask-SQLAlchemy |

---

## Narzędzie do prototypowania: DBeaver Community

DBeaver Community jest używany jako główne narzędzie do pracy ze schematem
bazy danych. Uzasadnienie wyboru:

- obsługuje SQLite natywnie oraz MariaDB/PostgreSQL bez zmiany interfejsu
- wbudowany edytor SQL z podpowiadaniem składni i formatowaniem
- graficzny podgląd schematu ERD generowany automatycznie ze struktury tabel
- eksport diagramu do PNG/SVG na potrzeby dokumentacji
- bezpłatna wersja Community pokrywa wszystkie potrzeby projektu studenckiego
- umożliwia płynną migrację narzędzia przy przejściu na MariaDB

---