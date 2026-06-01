### Proces 2 — Codzienny dziennik praktyki
> Dane: Zał. nr 6 (kolejny dzień 1–120, data, opis wykonanych prac, nr efektów 01–13, podpis osoby nadzorującej, potwierdzenie całej strony przez wymaganych użytkowników).

```mermaid
sequenceDiagram
    actor S as Student
    actor ZOPZ as Opiekun_Zakl
    actor UOPZ as Opiekun_Uczeln
    participant FE as Frontend
    participant FB as Flask_Backend
    participant DB as Database

    loop Każdy dzień roboczy (1 z 120)
        S->>FE: Wypełnia wpis dzienny (data, opis prac, nr efektów uczenia się)
        FE->>FB: POST /dziennik/wpis {praktyka_id, dzien_nr, data, opis, efekty[]}
        FB->>DB: Walidacja: unikalność dnia, data w zakresie praktyki
        DB-->>FB: OK / błąd duplikatu

        alt Błędne dane
            FB-->>FE: 400 + błąd walidacji
            FE-->>S: Wyświetl komunikat błędu
        else Dane poprawne
            FB->>DB: INSERT wpis_dziennika {status: "Submitted"}
            DB-->>FB: wpis_id
            FB-->>FE: 201 Created
            FE-->>S: Wpis zapisany, oczekuje na podpis ZOPZ
        end
    end

    ZOPZ->>FE: Przegląda wpisy o statusie "Submitted"
    FE->>FB: GET /dziennik/{praktyka_id}?status=Submitted
    FB->>DB: SELECT wpisy WHERE status="Submitted"
    DB-->>FB: lista wpisów
    FB-->>FE: lista wpisów do weryfikacji

    loop Każdy wpis / strona dziennika
        alt ZOPZ odrzuca wpis (zbyt ogólny opis)
            ZOPZ->>FE: Odrzuć + komentarz zwrotny
            FE->>FB: PATCH /dziennik/wpis/{id} {status: "Rejected", komentarz}
            FB->>DB: UPDATE status
            FB->>S: Powiadomienie: wpis do poprawy
            S->>FE: Edytuje wpis
            FE->>FB: PUT /dziennik/wpis/{id} {nowy_opis, efekty[]}
            FB->>DB: UPDATE wpis {status: "Submitted"}
        else ZOPZ potwierdza wpis
            ZOPZ->>FE: Potwierdź (podpis cyfrowy)
            FE->>FB: PATCH /dziennik/wpis/{id} {status: "Approved", podpis_ZOPZ: true}
            FB->>DB: UPDATE status: "Approved"
            DB-->>FB: OK
        end
    end

    FB->>DB: COUNT wpisy WHERE status="Approved" AND praktyka_id=?
    DB-->>FB: liczba zatwierdzonych wpisów
    alt Wszystkie 120 dni zatwierdzone przez ZOPZ
        FB->>DB: UPDATE praktyka {dziennik_status: "Under_Review"}
        FB->>UOPZ: Powiadomienie: Dziennik kompletny, przekazany do finalnej weryfikacji

        Note over UOPZ,DB: Finalna weryfikacja Dziennika przez UOPZ (cykl życia dokumentu)
        UOPZ->>FE: Przegląda kompletny Dziennik
        FE->>FB: GET /dziennik/{praktyka_id}/pelny
        FB->>DB: SELECT wszystkie wpisy WHERE praktyka_id=?
        DB-->>FB: komplet wpisów
        FB-->>FE: wyświetl Dziennik do weryfikacji

        alt UOPZ zwraca Dziennik do poprawek
            UOPZ->>FE: Cofnij + komentarz (np. braki formalne)
            FE->>FB: PATCH /dziennik/{praktyka_id} {status: "Rejected", uwagi}
            FB->>DB: UPDATE praktyka {dziennik_status: "Rejected"}
            FB->>S: Powiadomienie: Dziennik wymaga uzupełnienia
        else UOPZ zatwierdza Dziennik końcowo
            UOPZ->>FE: Zatwierdź Dziennik
            FE->>FB: PATCH /dziennik/{praktyka_id} {status: "Closed"}
            FB->>DB: UPDATE praktyka {dziennik_status: "Closed"}
            DB-->>FB: OK
            FB->>S: Powiadomienie: Dziennik zatwierdzony przez UOPZ
        end
    end
```

> **Uwaga:** Status dziennika (Under_Review, Rejected, Closed) jest polem w tabeli PRAKTYKA, nie osobną encją.
