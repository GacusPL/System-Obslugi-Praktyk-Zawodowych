# System Obsługi Praktyk Zawodowych — IIS

System do cyfryzacji i zarządzania obiegiem dokumentacji praktyk zawodowych w Instytucie Informatyki Stosowanej.

## Stos technologiczny

| Warstwa | Technologia |
|---|---|
| Backend | Python 3 + Flask |
| Baza danych (prototyp) | SQLite |
| Baza danych (produkcja) | MariaDB |
| Uwierzytelnianie | Microsoft OAuth2 + Flask-Login |
| Frontend | HTML + JavaScript (Vanilla) |
| Generowanie PDF | reportlab / weasyprint |
| Diagramy | Mermaid |

## Struktura repozytorium

```
├── docs/                    # Dokumentacja projektu
│   ├── README.md            # Spis treści dokumentacji
│   ├── requirements.md      # Wymagania funkcjonalne i niefunkcjonalne
│   ├── database.md          # Wybór bazy danych
│   ├── diagrams/            # Diagramy Mermaid
│   │   ├── erd/             # Diagram ERD
│   │   ├── sequence/        # Diagramy sekwencji (procesy 0–9)
│   │   └── flowcharts/      # Schematy blokowe i diagram stanów
│   └── praktyki/            # PDF-y regulaminu i załączników
├── schema.sql               # Schemat bazy danych (DDL)
└── readme.md                # Ten plik
```

## Dokumentacja

Pełna dokumentacja projektowa znajduje się w katalogu [docs/](docs/README.md).

## Aktorzy systemu

- **Student** — zgłaszanie praktyki, dziennik, sprawozdanie, ankieta
- **ZOPZ** (Zakładowy Opiekun Praktyki) — weryfikacja wpisów, potwierdzenie efektów
- **UOPZ** (Uczelniany Opiekun Praktyk) — nadzór, oceny, zatwierdzanie dokumentacji
- **Administrator / Dziekanat** — zarządzanie danymi, eksport ocen
- **Dyrektor Instytutu** — decyzje ws. ścieżki alternatywnej