### Bonus — Flowchart: Logika biznesowa kompletacji dokumentacji

> Ten diagram pokrywa kluczowy mechanizm checklisty przed złożeniem e-teczki (Proces 6), który jest najtrudniejszy do wyrażenia samym diagramem sekwencji.

```mermaid
flowchart TD
    A([Student inicjuje złożenie dokumentacji]) --> B[Backend pobiera\nchecklistę dokumentów]

    B --> C{Zał. nr 3\nKarta Praktyki\nstatus = Approved?}
    C -- Nie --> ERR[/Zwróć listę braków\nHTTP 422/]
    ERR --> A

    C -- Tak --> D{Zał. nr 4\nEfekty uczenia się\nstatus = Approved?}
    D -- Nie --> ERR

    D -- Tak --> E{Zał. nr 5\nAnkieta\nstatus = Closed?}
    E -- Nie --> ERR

    E -- Tak --> F{Zał. nr 6\nDziennik\nstatus = Closed\noraz 120 wpisów?}
    F -- Nie --> ERR

    F -- Tak --> G{Zał. nr 7\nSprawozdanie\nstatus = Approved?}
    G -- Nie --> ERR

    G -- Tak --> H[Backend zmienia status\npraktyki na Submitted]
    H --> I[Powiadomienie e-mail\ndo UOPZ]
    I --> J{UOPZ weryfikuje\nkompletność e-teczki}

    J -- Odrzuca --> K[Status: Rejected\nPowiadomienie do Studenta\nz wykazem braków]
    K --> A

    J -- Zatwierdza --> L[Backend generuje\narchiwum PDF\nZał. 3 + 4 + 6 + 7]
    L --> M[Status praktyki\nustawiony na Closed]
    M --> N([Dokumentacja\nzarchiwizowana])
```
