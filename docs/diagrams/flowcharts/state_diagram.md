### Zadanie 2 — State Diagram: Cykl życia dokumentu

> Modeluje wszystkie stany przez które przechodzi dowolny dokument w systemie (Dziennik, Sprawozdanie, Wniosek, Karta Praktyki). Rozgałęzienie przy `Under_Review` odzwierciedla decyzję opiekuna.

```mermaid
stateDiagram-v2
    [*] --> Draft : Student tworzy dokument

    Draft --> Submitted : Student wysyła do weryfikacji
    Draft --> Draft : Student zapisuje szkic

    Submitted --> Under_Review : Backend waliduje dane\ni powiadamia opiekuna
    Submitted --> Draft : Walidacja nieudana\n(dane niekompletne)

    Under_Review --> Approved : Opiekun zatwierdza dokument
    Under_Review --> Rejected : Opiekun odrzuca\nz komentarzem

    Rejected --> Submitted : Student nanosi poprawki\ni wysyła ponownie

    Approved --> Closed : Dokumentacja skompletowana\ni zarchiwizowana
    Approved --> Under_Review : Wykryto braki formalne\n(cofnięcie przez UOPZ)

    Closed --> [*]

    note right of Draft
        Edycja dostępna
        tylko w tym stanie
        oraz po Rejected
    end note

    note right of Closed
        Stan terminalny
        Dokument archiwalny
        tylko do odczytu
    end note
```
