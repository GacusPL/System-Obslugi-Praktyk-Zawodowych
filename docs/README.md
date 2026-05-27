# Dokumentacja Projektu: System Obsługi Praktyk Zawodowych

W tym katalogu znajduje się dokumentacja systemu.

## Spis treści

- [Wymagania Systemowe](requirements.md)

### Baza Danych i Diagram ERD
Specyfikacja techniczna oraz model struktury danych:
- [Diagram ERD](diagrams/erd/erd.md)
- [Wybór i konfiguracja bazy danych](database.md)

### Diagramy Sekwencji (Procesy)
Diagramy przedstawiające przepływ sterowania i interakcje między aktorami a systemem dla poszczególnych procesów:
1. [Rejestracja i konfiguracja praktyki](diagrams/sequence/01_rejestracja.md)
2. [Codzienny dziennik praktyki](diagrams/sequence/02_dziennik.md)
3. [Potwierdzenie efektów uczenia się](diagrams/sequence/03_efekty.md)
4. [Sprawozdanie końcowe studenta](diagrams/sequence/04_sprawozdanie.md)
5. [Kwestionariusz ankiety](diagrams/sequence/05_ankieta.md)
6. [Kompletacja i złożenie pełnej dokumentacji](diagrams/sequence/06_kompletacja.md)
7. [Ścieżka alternatywna](diagrams/sequence/07_sciezka_alternatywna.md)
8. [Egzamin ustny i eksport ocen](diagrams/sequence/08_egzamin.md)
9. [Administracja systemu](diagrams/sequence/09_administracja.md)

### Schematy Blokowe i Diagramy Stanów (Flowcharts)
Diagramy modelujące logikę biznesową i cykl życia obiektów:
- [State Diagram: Cykl życia dokumentu](diagrams/flowcharts/state_diagram.md)
- [Flowchart: Logika uprawnień do edycji dokumentu](diagrams/flowcharts/logika_uprawnien.md)
- [Flowchart: Logika biznesowa kompletacji dokumentacji](diagrams/flowcharts/logika_kompletacji.md)


