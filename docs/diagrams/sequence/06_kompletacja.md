### Proces 6 — Kompletacja i złożenie pełnej dokumentacji
> Dane: Agregacja Zał. 3 (ocena ZOPZ 2–5 param. + opisowa), Zał. 4, Zał. 5, Zał. 6 (120 dni), Zał. 7 (ocena UOPZ 2–5). Termin: 7 dni po zakończeniu praktyki (§4 pkt 2).

```mermaid
sequenceDiagram
    actor S as Student
    actor ZOPZ as Opiekun_Zakl
    actor UOPZ as Opiekun_Uczeln
    participant FE as Frontend
    participant FB as Flask_Backend
    participant DB as Database
    participant PDF as Generator_PDF

    Note over S,DB: Finalizacja – max 7 dni po zakończeniu praktyki (§4 pkt 2)
    ZOPZ->>FE: Wypełnia ocenę końcową na Karcie Praktyki (Zał. nr 3)
    FE->>FB: POST /karta-praktyki/ocena {praktyka_id, ocena_param (2-5), ocena_opisowa}
    FB->>DB: UPDATE karta_praktyki {ocena_ZOPZ, status: "Under_Review"}
    FB->>S: Powiadomienie: Zakład wystawił ocenę

    S->>FE: Sprawdza status wszystkich dokumentów
    FE->>FB: GET /dokumentacja/checklist/{praktyka_id}
    FB->>DB: SELECT status każdego dokumentu (Zał. 3, 4, 5, 6, 7)
    DB-->>FB: checklist ze statusami
    FB-->>FE: lista z oznaczeniem Approved/brakujący

    alt Brakujące dokumenty
        FE-->>S: Lista braków z linkami do uzupełnienia
    else Wszystkie dokumenty kompletne
        S->>FE: Kliknij "Złóż dokumentację"
        FE->>FB: POST /dokumentacja/zloz {praktyka_id}
        FB->>DB: Walidacja: Zał.2a✓ Zał.3✓ Zał.4✓ Zał.5(ankieta_wypelniona)✓ Zał.6(Closed+120)✓ Zał.7✓
        DB-->>FB: OK / lista braków

        alt Dokumentacja niekompletna
            FB-->>FE: 422 + lista niezaliczonych wymagań
            FE-->>S: Wyróżnij brakujące elementy
        else Dokumentacja kompletna
            FB->>DB: UPDATE praktyka {status: "Submitted", data_zlozenia}
            FB->>UOPZ: Powiadomienie: komplet dokumentów do weryfikacji

            UOPZ->>FE: Weryfikuje kompletność
            FE->>FB: GET /dokumentacja/{praktyka_id}/pelna
            FB->>DB: SELECT wszystkie dokumenty i statusy
            DB-->>FB: pełna dokumentacja
            FB-->>FE: panel weryfikacji

            UOPZ->>FE: Wystawia ocenę UOPZ na Karcie Praktyki (Zał. nr 3)
            FE->>FB: PATCH /karta-praktyki/{id} {ocena_param_UOPZ, ocena_opisowa_UOPZ}
            FB->>DB: UPDATE karta_praktyki
            DB-->>FB: OK

            alt UOPZ odrzuca dokumentację
                UOPZ->>FE: Odrzuć z komentarzem
                FE->>FB: PATCH /dokumentacja/{id} {status: "Rejected", uwagi}
                FB->>DB: UPDATE status
                FB->>S: Powiadomienie z wykazem braków
            else UOPZ zatwierdza dokumentację
                FE->>FB: PATCH /dokumentacja/{id} {status: "Approved"}
                FB->>DB: UPDATE status
                FB->>DB: SELECT wszystkie dane praktyki
                DB-->>FB: komplet danych
                FB->>PDF: render_harmonogram_zal2a(dane)
                FB->>PDF: render_karta_zal3(dane)
                FB->>PDF: render_potwierdzenie_zal4(dane)
                FB->>PDF: render_dziennik_zal6(dane)
                FB->>PDF: render_sprawozdanie_zal7(dane)
                PDF-->>FB: 5x PDF
                FB->>DB: INSERT archiwum {praktyka_id, pliki[], status: "Closed"}
                FB-->>FE: Dokumentacja zaarchiwizowana
                FE-->>S: Dokumentacja złożona pomyślnie
            end
        end
    end
```
