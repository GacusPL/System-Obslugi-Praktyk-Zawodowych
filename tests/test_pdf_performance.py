import time
import pytest
import os
from app.pdf import generate_pdf

def test_pdf_generation_performance(db_session):
    data = {
        'praktyka_id': 9999,
        'student_name': 'Zażółć Gęślą Jaźń',
        'nr_albumu': '67890',
        'kierunek': 'Informatyka Stosowana',
        'specjalnosc': 'Inżynieria Danych',
        'semestr': 6,
        'forma_studiow': 'stacjonarne',
        'zaklad_nazwa': 'Polskie Przedsiębiorstwo Testowe Sp. z o.o.',
        'uopz_name': 'Prof. Janusz Kowalski',
        'termin_od': '2026-07-01',
        'termin_do': '2026-09-30',
        'rok_akademicki': '2025/2026',
        
        # for zal_nr2a
        'dzialy': [
            {'nazwa_dzialu': 'Dział Programowania i Testów', 'planowane_dni': 60},
            {'nazwa_dzialu': 'Dział Wdrożeń Systemów IT', 'planowane_dni': 60}
        ],
        'podpis_student': True,
        'podpis_zopz': True,
        'podpis_uopz': False,
        
        # for zal_nr3
        'ocena_zopz_1': 4.5,
        'ocena_zopz_2': 5.0,
        'ocena_zopz_3': 4.0,
        'ocena_zopz_4': 5.0,
        'ocena_zopz_5': 4.5,
        'ocena_zopz_ogolna': 4.5,
        'opinia_zopz_opis': 'Bardzo zaangażowany i samodzielny student.',
        'opinia_uopz_opis': 'Weryfikacja pozytywna.',
        'ocena_sprawozdania': 4.5,
        'ocena_koncowa': 4.5,
        
        # for zal_nr4
        'godziny_zrealizowane': 960,
        'opinia_uopz': 'Wszystkie efekty osiągnięte na poziomie bardzo dobrym.',
        'efekty': [
            {'nr': i, 'opis': f'Opis efektu numer {i}', 'uzyskano': True} for i in range(1, 14)
        ],
        
        # for zal_nr4b
        'typ': 'praca_zawodowa',
        'uzasadnienie': 'Pracuję jako software developer od 2 lat w pełnym wymiarze godzin.',
        'decyzja': 'zgoda_pelna',
        'opinia_komisji': 'Wniosek w pełni uzasadniony.',
        'zalaczniki': ['Umowa o pracę', 'Karta stanowiska'],
        
        # for zal_nr5
        'godziny': '960',
        'uwagi': 'Brak uwag, praktyka była świetnie zorganizowana.',
        'odpowiedzi': [
            {'pytanie_nr': i, 'odpowiedz': 5} for i in range(1, 15)
        ],
        
        # for zal_nr6
        'wpisy': [
            {
                'dzien_nr': i,
                'data_wpisu': '2026-07-01',
                'opis_prac': f'Prace programistyczne w dniu {i}',
                'status': 'Approved',
                'efekty': [1, 2, 3]
            } for i in range(1, 121)
        ],
        
        # for zal_nr7
        'sekcja_I': 'Opis struktury organizacyjnej firmy...' * 10,
        'sekcja_II': 'Opis stanowiska pracy oraz wykonywanych zadań...' * 10,
        'sekcja_III': 'Wnioski końcowe oraz ocena własna studenta...' * 10,
        
        # for zal_nr8
        'data_egzaminu': '2026-10-05',
        'ocena_ustna': 4.5,
        'komisja': [
            {'imie': 'Jan', 'nazwisko': 'Przewodniczący', 'rola_w_komisji': 'przewodniczacy'},
            {'imie': 'Anna', 'nazwisko': 'Członek', 'rola_w_komisji': 'czlonek'}
        ]
    }

    document_types = ['zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr4b', 'zal_nr5', 'zal_nr6', 'zal_nr7', 'zal_nr8']
    
    for typ in document_types:
        start_time = time.perf_counter()
        filepath = generate_pdf(typ, data)
        duration = time.perf_counter() - start_time
        
        # Assert generation time is <= 5 seconds
        assert duration <= 5.0, f"Generation of {typ} took {duration:.2f} seconds, exceeding the 5s limit"
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0
        
        # Cleanup
        os.remove(filepath)
