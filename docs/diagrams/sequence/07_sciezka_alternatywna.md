### Proces 7 — Ścieżka alternatywna: zaliczenie przez pracę zawodową
> Dane: Zał. nr 4b (uzasadnienie, typ: praca/staż/działalność, lista skanów: umowa / zakres obowiązków / CEIDG lub KRS; opinia komisji; decyzja Dyrektora: zgoda pełna / częściowa / odmowa). Podstawa: §4 regulaminu.

```mermaid
sequenceDiagram
    actor S as Student
    actor UOPZ as Opiekun_Uczeln
    actor Dyr as Dyrektor_IIS
    participant FE as Frontend
    participant FB as Flask_Backend
    participant DB as Database
    participant PDF as Generator_PDF

    S->>FE: Wypełnia Wniosek o zaliczenie efektów (Zał. nr 4b)
    S->>FE: Wgrywa skany dokumentów (umowa, zakres obowiązków, CEIDG/KRS)
    FE->>FB: POST /wniosek-zaliczenia {student_id, uzasadnienie, typ, dokumenty_skan[]}
    FB->>DB: INSERT wniosek {status: "Submitted"}
    FB->>DB: INSERT zalacznik_skan {wniosek_id, pliki[]}
    FB->>UOPZ: Powiadomienie e-mail: nowy wniosek

    UOPZ->>FE: Weryfikuje wniosek wstępnie
    FE->>FB: GET /wniosek/{id}
    FB->>DB: SELECT wniosek + skany
    DB-->>FB: dane
    FB-->>FE: wyświetl wniosek

    alt UOPZ odrzuca wstępnie (braki formalne)
        UOPZ->>FE: Odrzuć + opis braków
        FE->>FB: PATCH /wniosek/{id} {status: "Rejected", komentarz}
        FB->>DB: UPDATE status
        FB->>S: Powiadomienie: uzupełnij dokumenty
    else UOPZ kieruje do Komisji
        FE->>FB: PATCH /wniosek/{id} {status: "Under_Review"}
        FB->>DB: UPDATE status
        FB->>Dyr: Powiadomienie: wniosek do rozpatrzenia

        Dyr->>FE: Otwiera formularz oceny merytorycznej (Zał. nr 4)
        FE->>FB: GET /wniosek/{id}/pelny
        FB->>DB: SELECT wniosek + dokumenty + efekty_uczenia_sie
        DB-->>FB: dane do oceny
        FB-->>FE: formularz z 13 efektami

        Dyr->>FE: Ocenia każdy efekt 01–13, wpisuje opinię Komisji
        FE->>FB: POST /komisja/ocena {wniosek_id, oceny_efektow[13], opinia}
        FB->>DB: INSERT ocena_komisji
        DB-->>FB: OK

        alt Decyzja Dyrektora: Zgoda pełna
            Dyr->>FE: Zatwierdź: zgoda pełna
            FE->>FB: PATCH /wniosek/{id} {decyzja: "zgoda_pelna", status: "Approved"}
            FB->>DB: UPDATE wniosek + INSERT zaliczenie_praktyki
            FB->>PDF: render_wniosek_4b(dane, decyzja: "zgoda_pelna")
            PDF-->>FB: wniosek_zal4b.pdf
            FB->>DB: INSERT dokument {status: "Closed"}
            FB->>S: Powiadomienie: praktyka zaliczona
            FE-->>S: Pobierz decyzję (Zał. nr 4b)
        else Decyzja Dyrektora: Zgoda częściowa
            Dyr->>FE: Wskaż efekty do uzupełnienia
            FE->>FB: PATCH /wniosek/{id} {decyzja: "zgoda_czesciowa", efekty_do_uzup[], status: "Rejected"}
            FB->>DB: UPDATE wniosek
            FB->>S: Powiadomienie: uzupełnij wskazane efekty standardową ścieżką
        else Decyzja Dyrektora: Odmowa
            Dyr->>FE: Odmów + uzasadnienie
            FE->>FB: PATCH /wniosek/{id} {decyzja: "odmowa", status: "Rejected"}
            FB->>DB: UPDATE status
            FB->>S: Powiadomienie: odmowa, student odbywa praktykę standardowo
        end
    end
```
