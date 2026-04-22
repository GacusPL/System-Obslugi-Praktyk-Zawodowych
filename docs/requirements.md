# Inżynieria Wymagań – System Obsługi Praktyk Zawodowych (IIS)

Dokumentacja wymagań dla systemu cyfryzacji i obiegu dokumentacji praktyk zawodowych w Instytucie Informatyki Stosowanej (IIS).

## 1. Aktorzy Systemu (Interesariusze) i ich cele

* **Student**: Główny użytkownik systemu. Jego celem jest cyfrowe zgłoszenie miejsca praktyki, systematyczne prowadzenie dziennika (rejestracja 120 dni roboczych), wypełnianie formularzy samooceny oraz skompletowanie e-teczki.
* **Zakładowy Opiekun Praktyki Zawodowej (ZOPZ)**: Przedstawiciel pracodawcy. Odpowiada za nadzór merytoryczny, akceptację wpisów w Dzienniku oraz potwierdzenie 13 efektów uczenia się.
* **Uczelniany Opiekun Praktyk Zawodowych (UOPZ)**: Pracownik akademicki. Weryfikuje zgłoszenia, współtworzy harmonogram (Zał. nr 2a), ocenia sprawozdania i zatwierdza kompletną dokumentację przed egzaminem.
* **Administrator / Dziekanat**: Zarządza danymi systemowymi, monitoruje statusy praktyk i eksportuje oceny do systemu USOS.
* **Dyrektor Instytutu**: Rozpatruje wnioski o zaliczenie praktyk na podstawie pracy zawodowej (ścieżka alternatywna) oraz podejmuje ostateczne decyzje w sprawach spornych.

---

## 2. Wymagania Funkcjonalne

| ID | Nazwa | Opis | Priorytet MoSCoW |
| :--- | :--- | :--- | :--- |
| **REQ-01** | Dynamiczny Dziennik Praktyk | System umożliwia Studentowi wprowadzanie codziennych wpisów do tabeli (Zał. nr 6), zawierających opis prac i powiązane efekty uczenia się. | Must Have |
| **REQ-02** | Blokada edycji | System automatycznie blokuje edycję dokumentu przez studenta po jego przesłaniu do weryfikacji przez ZOPZ/UOPZ. | Must Have |
| **REQ-03** | Komentarze merytoryczne | System umożliwia Opiekunom dodawanie uwag tekstowych przy odrzucaniu wpisów lub cofaniu dokumentacji do poprawy. | Must Have |
| **REQ-04** | Ocena i generowanie PDF | System umożliwia UOPZ wpisanie ocen cząstkowych i wygenerowanie sformatowanego dokumentu PDF (np. Zał. nr 3). | Must Have |
| **REQ-05** | Potwierdzenie efektów | System umożliwia ZOPZ odznaczanie statusu ("uzyskał/a") przy każdym z 13 narzuconych efektów uczenia się (Zał. nr 4). | Must Have |
| **REQ-06** | Ścieżka alternatywna | System umożliwia Studentowi złożenie wniosku (Zał. nr 4b) o zaliczenie praktyki na podstawie pracy zawodowej/stażu wraz z załącznikami. | Should Have |
| **REQ-07** | Generowanie skierowania | System umożliwia wygenerowanie skierowania na praktykę (część Zał. nr 3) po akceptacji miejsca praktyki przez UOPZ. | Must Have |
| **REQ-08** | Eksport do USOS | System umożliwia Administratorowi wygenerowanie zbiorczego zestawienia ocen końcowych w formacie CSV/XLSX. | Should Have |
| **REQ-09** | Anonimowa ankieta | System umożliwia Studentowi wypełnienie anonimowej ankiety ewaluacyjnej (Zał. nr 5). | Could Have |

---

## 3. Scenariusze User Stories

* **US-01 (Student)**: Jako Student, chcę sprawnie uzupełniać codzienne wpisy w Dzienniku, aby na bieżąco dokumentować 120 dni roboczych praktyki zgodnie z regulaminem.
* **US-02 (Opiekun)**: Jako ZOPZ, chcę mieć możliwość odrzucenia wpisu z komentarzem, aby precyzyjnie wskazać studentowi błędy merytoryczne przed ostatecznym podpisem.
* **US-03 (Dyrektor)**: Jako Dyrektor Instytutu, chcę przeglądać wnioski o uznanie efektów uczenia się z pracy zawodowej, aby na podstawie opinii Komisji podjąć wiążącą decyzję o zaliczeniu (Zał. 4b).
* **US-04 (Administrator)**: Jako Administrator, chcę wyeksportować listę ocen wszystkich studentów z danego semestru, aby bezbłędnie i szybko przenieść je do systemu USOS.

---

## 4. Wymagania Niefunkcjonalne

* **Bezpieczeństwo i RBAC**: Dostęp do dokumentacji studenta mają wyłącznie przypisani do niego opiekunowie. Ankieta ewaluacyjna musi być technicznie oddzielona od tożsamości studenta.
* **Użyteczność (UX/UI)**: Interfejs, w tym dynamiczne tabele Dziennika Praktyk, musi być responsywny (RWD) i zoptymalizowany pod urządzenia mobilne.
* **Wydajność**: System musi wygenerować sformatowany dokument PDF (łączący wiele załączników) w czasie **≤ 5 sekund przy założeniu do 30 jednoczesnych sesji generowania dokumentów**.
* **Archiwizacja**: System musi zapewniać trwałość danych w formacie JSON oraz regularne kopie zapasowe wygenerowanych plików PDF dla celów audytowych.

---

## 5. Przepływ Dokumentacji (Workflow) - Dziennik Praktyk

1.  **Inicjacja i wpis (Student)**: Student tworzy wpis dla konkretnego dnia roboczego (1-120), dodając opis prac i numery efektów. Status: `Draft` lub `Submitted`.
2.  **Weryfikacja merytoryczna (ZOPZ)**: Zakładowy Opiekun analizuje treść wpisu pod kątem merytorycznym oraz zgodności z faktycznie wykonanymi pracami. Sprawdza, czy przypisane efekty uczenia się odpowiadają opisowi czynności.
    * *Odrzucenie*: ZOPZ cofa wpis do statusu `Rejected`, załączając komentarz. Student nanosi poprawki i wysyła ponownie.
    * *Akceptacja*: ZOPZ zatwierdza wpis. Status zmienia się na `Approved`. Wpis zostaje zablokowany do edycji.
3.  **Kompletacja (System)**: Po zatwierdzeniu 120 wpisów, system zmienia status Dziennika na `Closed`.
4.  **Zatwierdzenie końcowe (UOPZ)**: UOPZ ocenia merytorycznie cały Dziennik w ramach agregacji e-teczki. Pozytywna weryfikacja umożliwia dopuszczenie studenta do egzaminu ustnego.

---
