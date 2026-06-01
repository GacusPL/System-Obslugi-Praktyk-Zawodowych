# Dokumentacja Projektu: System Obsługi Praktyk Zawodowych

W tym katalogu znajduje się dokumentacja systemu.

## Spis treści

- [Wymagania Systemowe](requirements.md)

### Baza Danych i Diagram ERD
Specyfikacja techniczna oraz model struktury danych:
- [Diagram ERD](diagrams/erd/erd.md)
- [Wybór i konfiguracja bazy danych](database.md)
- [Schemat SQL (DDL)](../schema.sql)

### Diagramy Sekwencji (Procesy)
Diagramy przedstawiające przepływ sterowania i interakcje między aktorami a systemem dla poszczególnych procesów:
0. [Uwierzytelnianie Microsoft OAuth2](diagrams/sequence/00_logowanie.md)
1. [Rejestracja i konfiguracja praktyki](diagrams/sequence/01_rejestracja.md)
2. [Codzienny dziennik praktyki](diagrams/sequence/02_dziennik.md)
3. [Potwierdzenie efektów uczenia się](diagrams/sequence/03_efekty.md)
4. [Sprawozdanie końcowe studenta](diagrams/sequence/04_sprawozdanie.md)
5. [Kwestionariusz ankiety](diagrams/sequence/05_ankieta.md)
6. [Kompletacja i złożenie pełnej dokumentacji](diagrams/sequence/06_kompletacja.md)
7. [Ścieżka alternatywna](diagrams/sequence/07_sciezka_alternatywna.md)
8. [Egzamin ustny i eksport ocen](diagrams/sequence/08_egzamin.md)
9. [Administracja systemu](diagrams/sequence/09_administracja.md)

### Schematy Blokowe i Diagramy Stanów (Flowcharts)
Diagramy modelujące logikę biznesową i cykl życia obiektów:
- [State Diagram: Cykl życia dokumentu](diagrams/flowcharts/state_diagram.md)
- [Flowchart: Logika uprawnień do edycji dokumentu](diagrams/flowcharts/logika_uprawnien.md)
- [Flowchart: Logika biznesowa kompletacji dokumentacji](diagrams/flowcharts/logika_kompletacji.md)

### Mapowanie Załączników Regulaminu na Encje Systemowe

| Załącznik | Tabela SQL | Diagram sekwencji |
|---|---|---|
| Zał. nr 2a — Program i harmonogram | `harmonogram`, `harmonogram_dzial` | Proces 1 |
| Zał. nr 3 — Karta praktyki zawodowej | `karta_praktyki` | Proces 1, 6 |
| Zał. nr 4 — Potwierdzenie efektów uczenia się | `potwierdzenie_efektow`, `potwierdzenie_efekt_ocena` | Proces 3 |
| Zał. nr 4b — Wniosek o zaliczenie (ścieżka alt.) | `wniosek_alternatywny`, `zalacznik_skan` | Proces 7 |
| Zał. nr 5 — Kwestionariusz ankiety | `ankieta`, `ankieta_odpowiedz` | Proces 5 |
| Zał. nr 6 — Dziennik praktyki zawodowej | `wpis_dziennika`, `wpis_efekt` | Proces 2 |
| Zał. nr 7 — Sprawozdanie z praktyki | `sprawozdanie` | Proces 4 |
| Zał. nr 8 — Protokół egzaminu | `egzamin`, `komisja_czlonek` | Proces 8 |

### Dokumenty źródłowe (regulamin i załączniki)
PDF-y regulaminu i formularzy praktyk znajdują się w katalogu [praktyki/](praktyki/).
