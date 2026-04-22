### Proces 2 — Codzienny dziennik praktyki
> Dane: Zał. nr 6 (kolejny dzień 1–120, data, opis wykonanych prac, nr efektów 01–13, podpis osoby nadzorującej, potwierdzenie całej strony przez wymaganych użytkowników).

```mermaid
sequenceDiagram
    actor S as Student
    actor ZOPZ as Opiekun_Zakl
    actor UOPZ as Opiekun_Uczeln
    participant FE as Frontend
    participant FB as Flask_Backend
    participant J as JSON_Database

    loop Każdy dzień roboczy (1 z 120)
        S->>FE: Wypełnia wpis dzienny (data, opis prac, nr efektów uczenia się)
        FE->>FB: POST /dziennik/wpis {praktyka_id, dzien_nr, data, opis, efekty[]}
        FB->>J: Walidacja: unikalność dnia, data w zakresie praktyki
        J-->>FB: OK / błąd duplikatu

        alt Błędne dane
            FB-->>FE: 400 + błąd walidacji
            FE-->>S: Wyświetl komunikat błędu
        else Dane poprawne
            FB->>J: INSERT wpis_dziennika {status: "Submitted"}
            J-->>FB: wpis_id
            FB-->>FE: 201 Created
            FE-->>S: Wpis zapisany, oczekuje na podpis ZOPZ
        end
    end

    ZOPZ->>FE: Przegląda wpisy o statusie "Submitted"
    FE->>FB: GET /dziennik/{praktyka_id}?status=Submitted
    FB->>J: SELECT wpisy WHERE status="Submitted"
    J-->>FB: lista wpisów
    FB-->>FE: lista wpisów do weryfikacji

    loop Każdy wpis / strona dziennika
        alt ZOPZ odrzuca wpis (zbyt ogólny opis)
            ZOPZ->>FE: Odrzuć + komentarz zwrotny
            FE->>FB: PATCH /dziennik/wpis/{id} {status: "Rejected", komentarz}
            FB->>J: UPDATE status
            FB->>S: Powiadomienie: wpis do poprawy
            S->>FE: Edytuje wpis
            FE->>FB: PUT /dziennik/wpis/{id} {nowy_opis, efekty[]}
            FB->>J: UPDATE wpis {status: "Submitted"}
        else ZOPZ potwierdza wpis
            ZOPZ->>FE: Potwierdź (podpis cyfrowy)
            FE->>FB: PATCH /dziennik/wpis/{id} {status: "Approved", podpis_ZOPZ: true}
            FB->>J: UPDATE status: "Approved"
            J-->>FB: OK
        end
    end

    FB->>J: COUNT wpisy WHERE status="Approved" AND praktyka_id=?
    J-->>FB: liczba zatwierdzonych wpisów
    alt Wszystkie 120 dni zatwierdzone przez ZOPZ
        FB->>J: UPDATE dziennik {status: "Under_Review"}
        FB->>UOPZ: Powiadomienie: Dziennik kompletny, przekazany do finalnej weryfikacji

        Note over UOPZ,J: Finalna weryfikacja Dziennika przez UOPZ (cykl życia dokumentu)
        UOPZ->>FE: Przegląda kompletny Dziennik
        FE->>FB: GET /dziennik/{praktyka_id}/pelny
        FB->>J: SELECT wszystkie wpisy WHERE praktyka_id=?
        J-->>FB: komplet wpisów
        FB-->>FE: wyświetl Dziennik do weryfikacji

        alt UOPZ zwraca Dziennik do poprawek
            UOPZ->>FE: Cofnij + komentarz (np. braki formalne)
            FE->>FB: PATCH /dziennik/{praktyka_id} {status: "Rejected", uwagi}
            FB->>J: UPDATE dziennik {status: "Rejected"}
            FB->>S: Powiadomienie: Dziennik wymaga uzupełnienia
        else UOPZ zatwierdza Dziennik końcowo
            UOPZ->>FE: Zatwierdź Dziennik
            FE->>FB: PATCH /dziennik/{praktyka_id} {status: "Closed"}
            FB->>J: UPDATE dziennik {status: "Closed"}
            J-->>FB: OK
            FB->>S: Powiadomienie: Dziennik zatwierdzony przez UOPZ
        end
    end
```
