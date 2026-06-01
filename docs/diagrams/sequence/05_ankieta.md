### Proces 5 — Kwestionariusz ankiety
> Dane: Zał. nr 5 (14 pytań w skali 5-stopniowej, pole na uwagi, metryczka: rok ak., kierunek, forma studiów, semestr, liczba godzin; formularz anonimowy).

```mermaid
sequenceDiagram
    actor S as Student
    participant FE as Frontend
    participant FB as Flask_Backend
    participant DB as Database
    participant PDF as Generator_PDF

    Note over S,DB: Ankieta jest anonimowa – brak powiązania z student_id
    S->>FE: Otwiera formularz ankiety (Zał. nr 5)
    FE->>FB: GET /ankieta/szablon
    FB-->>FE: 14 pytań + metryczka (bez danych osobowych)

    S->>FE: Zaznacza odpowiedzi 1–14 (skala 5-stopniowa)
    S->>FE: Wypełnia metryczkę (rok ak., kierunek, forma, semestr, liczba godzin)
    S->>FE: Opcjonalnie dodaje uwagi tekstowe
    FE->>FB: POST /ankieta {odpowiedzi[14], metryczka, uwagi}
    FB->>DB: Walidacja: czy wszystkie 14 pytań udzielono odpowiedzi
    DB-->>FB: OK / lista brakujących odpowiedzi

    alt Brakujące odpowiedzi
        FB-->>FE: 400 + lista pytań bez odpowiedzi
        FE-->>S: Podświetl brakujące pytania
    else Ankieta kompletna
        FB->>DB: INSERT ankieta {odpowiedzi, metryczka, uwagi, timestamp, student_id: null}
        DB-->>FB: ankieta_id
        FB->>DB: UPDATE praktyka SET ankieta_wypelniona = 1 WHERE student_id = (session)
        FB->>DB: SELECT ankieta WHERE id=ankieta_id
        DB-->>FB: dane ankiety
        FB->>PDF: render_ankieta(dane)
        PDF-->>FB: ankieta_zal5.pdf
        FB->>DB: INSERT dokument {typ: "zal_nr5", student_id: null, status: "Closed"}
        FB-->>FE: 201 Created + URL do pobrania
        FE-->>S: Ankieta wysłana, pobierz swój egzemplarz
    end
```

> **Uwaga:** Ankieta jest anonimowa (brak FK do studenta), ale flaga ankieta_wypelniona w tabeli PRAKTYKA pozwala zweryfikować kompletność dokumentacji.
