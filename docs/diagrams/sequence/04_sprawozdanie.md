### Proces 4 — Sprawozdanie końcowe studenta
> Dane: Zał. nr 7 (sekcja I: charakterystyka miejsca, sekcja II: opis i analiza prac, sekcja III: samoocena efektów 01–13 z odniesieniem do wykonanych prac; ocena sprawozdania przez UOPZ w skali 2–5).

```mermaid
sequenceDiagram
    actor S as Student
    actor UOPZ as Opiekun_Uczeln
    participant FE as Frontend
    participant FB as Flask_Backend
    participant J as JSON_Database
    participant PDF as Generator_PDF

    S->>FE: Otwiera formularz sprawozdania (Zał. nr 7)
    FE->>FB: GET /sprawozdanie/szablon/{praktyka_id}
    FB->>J: SELECT dane praktyki, zakladu, efekty_uczenia_sie
    J-->>FB: dane bazowe
    FB-->>FE: formularz z sekcjami I, II, III

    S->>FE: Sekcja I – Charakterystyka miejsca praktyki
    S->>FE: Sekcja II – Opis i analiza wykonywanych prac
    S->>FE: Sekcja III – Samoocena efektów 01–13 z odniesieniem do prac
    FE->>FB: POST /sprawozdanie {praktyka_id, sekcja_I, sekcja_II, samoocena[13]}
    FB->>J: Walidacja długości tekstu (min. 100 znaków per sekcja)
    J-->>FB: OK / ostrzeżenie zbyt krótki opis

    alt Student zapisuje szkic
        FB->>J: INSERT sprawozdanie {status: "Draft"}
        FB-->>FE: Szkic zapisany
    else Student składa finalnie
        FB->>J: UPDATE sprawozdanie {status: "Submitted", data_zlozenia}
        FB->>UOPZ: Powiadomienie e-mail: nowe sprawozdanie

        UOPZ->>FE: Czyta sprawozdanie
        FE->>FB: GET /sprawozdanie/{id}
        FB->>J: SELECT sprawozdanie + sekcje
        J-->>FB: pełne sprawozdanie
        FB-->>FE: wyświetl sekcje

        alt UOPZ odsyła do poprawy
            UOPZ->>FE: Komentarz + zwróć do poprawy
            FE->>FB: PATCH /sprawozdanie/{id} {status: "Rejected", uwagi}
            FB->>J: UPDATE status
            FB->>S: Powiadomienie z uwagami
            S->>FE: Edytuje sprawozdanie
            FE->>FB: PUT /sprawozdanie/{id} {poprawione_sekcje}
            FB->>J: UPDATE sprawozdanie {status: "Submitted", wersja++}
        else UOPZ zatwierdza i wystawia ocenę
            UOPZ->>FE: Wpisuje ocenę sprawozdania (2–5)
            FE->>FB: PATCH /sprawozdanie/{id} {ocena_sprawozdania, status: "Approved"}
            FB->>J: UPDATE sprawozdanie {ocena, data_oceny}
            J-->>FB: OK
            FB->>J: SELECT student, sekcje, ocena, podpisy
            J-->>FB: dane do PDF
            FB->>PDF: render_sprawozdanie(dane)
            PDF-->>FB: sprawozdanie_zal7.pdf
            FB->>J: INSERT dokument {typ: "zal_nr7"}
            FB-->>FE: URL do pobrania
            FE-->>S: Sprawozdanie zatwierdzone, pobierz PDF
        end
    end
```
