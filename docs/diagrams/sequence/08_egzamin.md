### Proces 8 — Egzamin ustny i eksport ocen
> Dane: Regulamin §4 pkt 5–10 (egzamin przed Komisją, protokół Zał. nr 8), Zał. nr 3 (oceny cząstkowe ZOPZ i UOPZ 2–5), ocena sprawozdania 2–5. Eksport do CSV/XLSX z kolumnami nr albumu, nazwisko, imię, ocena końcowa, data.

```mermaid
sequenceDiagram
    actor S as Student
    actor UOPZ as Opiekun_Uczeln
    actor Adm as Admin
    participant FE as Frontend
    participant FB as Flask_Backend
    participant DB as Database
    participant PDF as Generator_PDF

    Adm->>FE: Ustawia termin egzaminu i skład komisji
    FE->>FB: POST /egzamin {praktyka_id, data_termin, komisja_sklad[]}
    FB->>DB: INSERT egzamin {status: "Draft"}
    FB->>S: Powiadomienie e-mail: termin egzaminu
    FB->>UOPZ: Powiadomienie: termin egzaminu

    S->>FE: Sprawdza termin
    FE->>FB: GET /egzamin/{id}
    FB->>DB: SELECT egzamin + dokumentacja_studenta
    DB-->>FB: dane
    FB-->>FE: karta egzaminu ze statusem dokumentacji

    Adm->>FE: Otwiera protokół egzaminacyjny (Zał. nr 8)
    FE->>FB: GET /egzamin/{id}/protokol
    FB->>DB: SELECT oceny cząstkowe (ZOPZ 2-5, UOPZ 2-5, sprawozdanie 2-5)
    DB-->>FB: oceny cząstkowe
    FB-->>FE: formularz protokołu z ocenami cząstkowymi

    Adm->>FE: Wpisuje ocenę z egzaminu ustnego (2–5) i ocenę końcową
    FE->>FB: POST /egzamin/{id}/wynik {ocena_ustna, ocena_koncowa}
    FB->>DB: Walidacja: ocena w zakresie 2–5
    DB-->>FB: OK / błąd zakresu

    alt Ocena niedostateczna (2)
        FB->>DB: UPDATE egzamin {status: "Rejected"}
        FB->>DB: INSERT egzamin {praktyka_id, status: "Draft", typ: "poprawkowy"}
        FB->>S: Powiadomienie: egzamin niezdany, wyznaczono poprawkę
    else Ocena pozytywna (3–5)
        FB->>DB: UPDATE egzamin {ocena_ustna, ocena_koncowa, status: "Approved"}
        FB->>DB: UPDATE praktyka {status: "Closed", ocena_koncowa}
        DB-->>FB: OK

        FB->>DB: SELECT student, komisja, oceny_cząstkowe, ocena_koncowa, data
        DB-->>FB: komplet danych
        FB->>PDF: render_protokol_egzaminu(dane)
        PDF-->>FB: protokol_zal8.pdf
        FB->>DB: INSERT dokument {typ: "protokol_zal8", status: "Closed"}
        DB-->>FB: OK
        FB-->>FE: Protokół gotowy
        FE-->>Adm: Pobierz protokół (Zał. nr 8)
        FE-->>S: Powiadomienie: praktyka zaliczona

        Note over Adm,DB: Eksport ocen do CSV/XLSX
        Adm->>FE: Kliknij "Eksportuj oceny" (filtr: semestr, rok akademicki)
        FE->>FB: GET /eksport/oceny?rok_ak=2024/2025&format=xlsx
        FB->>DB: SELECT nr_albumu, nazwisko, imie, ocena_koncowa, data_zaliczenia FROM praktyki WHERE rok_ak=? AND status="Closed"
        DB-->>FB: lista ocen
        FB->>FB: Generuj plik XLSX (openpyxl) lub CSV
        FB-->>FE: oceny_praktyki_2024_2025.xlsx
        FE-->>Adm: Pobierz plik do ręcznego wpisu w USOS
    end
```
