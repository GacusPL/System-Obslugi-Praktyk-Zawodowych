### Zadanie 2 — State Diagram: Cykl życia dokumentu

> Modeluje ogólny cykl życia dokumentu w systemie. Nie wszystkie encje przechodzą przez każdy stan — patrz tabela poniżej.

```mermaid
stateDiagram-v2
    [*] --> Draft : Student tworzy dokument

    Draft --> Submitted : Student wysyła do weryfikacji
    Draft --> Draft : Student zapisuje szkic

    Submitted --> Under_Review : Backend waliduje dane\ni powiadamia opiekuna
    Submitted --> Draft : Walidacja nieudana\n(dane niekompletne)

    Under_Review --> Approved : Opiekun zatwierdza dokument
    Under_Review --> Rejected : Opiekun odrzuca\nz komentarzem

    Rejected --> Draft : Student nanosi poprawki
    Draft --> Submitted : Student wysyła ponownie

    Approved --> Closed : Dokumentacja skompletowana\ni zarchiwizowana
    Approved --> Under_Review : Wykryto braki formalne\n(cofnięcie przez UOPZ)

    Closed --> [*]

    note right of Draft
        Edycja dostępna
        w stanach Draft
        oraz Rejected
    end note

    note right of Closed
        Stan terminalny
        Dokument archiwalny
        tylko do odczytu
    end note
```

#### Mapowanie stanów na encje

> Nie każda encja wykorzystuje wszystkie stany z diagramu powyżej. Poniższa tabela precyzuje dozwolone przejścia:

| Encja | Draft | Submitted | Under_Review | Approved | Rejected | Closed |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| PRAKTYKA | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| HARMONOGRAM | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| WPIS_DZIENNIKA | ✓ | ✓ | — | ✓ | ✓ | — |
| POTWIERDZENIE_EFEKTOW | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| SPRAWOZDANIE | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| KARTA_PRAKTYKI | ✓ | — | ✓ | ✓ | — | ✓ |
| WNIOSEK_ALTERNATYWNY | — | ✓ | ✓ | ✓ | ✓ | — |
| EGZAMIN | ✓ | — | — | ✓ | ✓ | — |
