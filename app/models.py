from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Many-to-many helper table for wpis_dziennika <-> efekt_uczenia
wpis_efekt = db.Table('wpis_efekt',
    db.Column('id', db.Integer, primary_key=True, autoincrement=True),
    db.Column('wpis_id', db.Integer, db.ForeignKey('wpis_dziennika.id'), nullable=False),
    db.Column('efekt_id', db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False),
    db.UniqueConstraint('wpis_id', 'efekt_id')
)

class EfektUczenia(db.Model):
    __tablename__ = 'efekt_uczenia'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nr = db.Column(db.Integer, nullable=False, unique=True)
    opis = db.Column(db.Text, nullable=False)

    __table_args__ = (
        db.CheckConstraint('nr BETWEEN 1 AND 13', name='check_efekt_nr_range'),
    )

class Uzytkownik(UserMixin, db.Model):
    __tablename__ = 'uzytkownik'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    haslo_hash = db.Column(db.String(255), nullable=False)
    rola = db.Column(db.String(50), nullable=True) # Set nullable=True for first OAuth login
    microsoft_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        db.CheckConstraint(
            "rola IN ('student', 'zopz', 'uopz', 'administrator', 'dyrektor') OR rola IS NULL",
            name='check_uzytkownik_rola'
        ),
    )

    def set_password(self, password):
        self.haslo_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.haslo_hash, password)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False, unique=True)
    nr_albumu = db.Column(db.String(20), nullable=False, unique=True)
    kierunek = db.Column(db.String(100), nullable=False)
    specjalnosc = db.Column(db.String(100), nullable=True)
    semestr = db.Column(db.Integer, nullable=False)
    forma_studiow = db.Column(db.String(50), nullable=False)
    rok_akademicki = db.Column(db.String(20), nullable=False)

    uzytkownik = db.relationship('Uzytkownik', backref=db.backref('student', uselist=False))

    __table_args__ = (
        db.CheckConstraint('semestr IN (6, 7)', name='check_student_semestr'),
        db.CheckConstraint("forma_studiow IN ('stacjonarne', 'niestacjonarne')", name='check_student_forma_studiow'),
    )

class ZakladPracy(db.Model):
    __tablename__ = 'zaklad_pracy'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nazwa = db.Column(db.String(255), nullable=False)
    adres = db.Column(db.String(255), nullable=False)
    nip = db.Column(db.String(20), nullable=False, unique=True)
    zopz_imie = db.Column(db.String(100), nullable=False)
    zopz_nazwisko = db.Column(db.String(100), nullable=False)
    zopz_stanowisko = db.Column(db.String(100), nullable=False)
    zopz_wyksztalcenie = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Approved')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    zopz_uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=True)
    
    zopz_uzytkownik = db.relationship('Uzytkownik', foreign_keys=[zopz_uzytkownik_id], backref='zaklady_opiekun')

    def is_opiekun(self, user):
        if not user or user.rola != 'zopz':
            return False
        if self.zopz_uzytkownik_id is not None:
            return self.zopz_uzytkownik_id == user.id
        return self.zopz_imie == user.imie and self.zopz_nazwisko == user.nazwisko

    __table_args__ = (
        db.CheckConstraint("status IN ('Approved', 'Rejected')", name='check_zaklad_pracy_status'),
    )

class Praktyka(db.Model):
    __tablename__ = 'praktyka'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    zaklad_id = db.Column(db.Integer, db.ForeignKey('zaklad_pracy.id'), nullable=False)
    uopz_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    termin_od = db.Column(db.Date, nullable=False)
    termin_do = db.Column(db.Date, nullable=False)
    rok_akademicki = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    ocena_koncowa = db.Column(db.Float, nullable=True)
    ankieta_wypelniona = db.Column(db.Integer, nullable=False, default=0)
    dziennik_status = db.Column(db.String(50), nullable=False, default='Draft')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    student = db.relationship('Student', backref='praktyki')
    zaklad_pracy = db.relationship('ZakladPracy', backref='praktyki')
    uopz = db.relationship('Uzytkownik', backref='praktyki_uopz')

    __table_args__ = (
        db.CheckConstraint("status IN ('Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected', 'Closed')", name='check_praktyka_status'),
        db.CheckConstraint('ocena_koncowa BETWEEN 2.0 AND 5.0', name='check_praktyka_ocena_range'),
        db.CheckConstraint('ankieta_wypelniona IN (0, 1)', name='check_praktyka_ankieta_flag'),
        db.CheckConstraint("dziennik_status IN ('Draft', 'Under_Review', 'Closed', 'Rejected')", name='check_praktyka_dziennik_status'),
    )

class Harmonogram(db.Model):
    __tablename__ = 'harmonogram'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False, unique=True)
    podpis_student = db.Column(db.Integer, nullable=False, default=0)
    podpis_zopz = db.Column(db.Integer, nullable=False, default=0)
    podpis_uopz = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    komentarz_odrzucenia = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    praktyka = db.relationship('Praktyka', backref=db.backref('harmonogram', uselist=False))

    __table_args__ = (
        db.CheckConstraint('podpis_student IN (0, 1)', name='check_harmonogram_podpis_student'),
        db.CheckConstraint('podpis_zopz IN (0, 1)', name='check_harmonogram_podpis_zopz'),
        db.CheckConstraint('podpis_uopz IN (0, 1)', name='check_harmonogram_podpis_uopz'),
        db.CheckConstraint("status IN ('Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected')", name='check_harmonogram_status'),
    )

    def validate_total_days(self):
        total_days = sum(dzial.planowane_dni for dzial in self.dzialy)
        return total_days == 120

class HarmonogramDzial(db.Model):
    __tablename__ = 'harmonogram_dzial'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    harmonogram_id = db.Column(db.Integer, db.ForeignKey('harmonogram.id'), nullable=False)
    nazwa_dzialu = db.Column(db.String(255), nullable=False)
    planowane_dni = db.Column(db.Integer, nullable=False)

    harmonogram = db.relationship('Harmonogram', backref=db.backref('dzialy', cascade='all, delete-orphan'))

    __table_args__ = (
        db.CheckConstraint('planowane_dni > 0', name='check_harmonogram_dzial_planowane_dni'),
    )

class ProgramPraktykiPozycja(db.Model):
    """Pozycja programu praktyki (Zał. 2a) - mapowanie efektu kształcenia na
    dział/przykładowe prace wykonywane przez praktykanta. Wypełnia opiekun (ZOPZ)."""
    __tablename__ = 'program_praktyki_pozycja'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    harmonogram_id = db.Column(db.Integer, db.ForeignKey('harmonogram.id'), nullable=False)
    efekt_id = db.Column(db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False)
    opis_realizacji = db.Column(db.Text, nullable=True)

    harmonogram = db.relationship('Harmonogram', backref=db.backref('program_pozycje', cascade='all, delete-orphan'))
    efekt = db.relationship('EfektUczenia')

    __table_args__ = (
        db.UniqueConstraint('harmonogram_id', 'efekt_id', name='uq_program_harmonogram_efekt'),
    )

class WpisDziennika(db.Model):
    __tablename__ = 'wpis_dziennika'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False)
    dzien_nr = db.Column(db.Integer, nullable=False)
    data_wpisu = db.Column(db.Date, nullable=False)
    opis_prac = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    komentarz_zopz = db.Column(db.Text, nullable=True)
    podpis_zopz = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    praktyka = db.relationship('Praktyka', backref='wpisy_dziennika')
    efekty = db.relationship('EfektUczenia', secondary=wpis_efekt, backref='wpisy_dziennika')

    __table_args__ = (
        db.CheckConstraint('dzien_nr BETWEEN 1 AND 120', name='check_wpis_dzien_nr_range'),
        db.CheckConstraint("status IN ('Draft', 'Submitted', 'Approved', 'Rejected')", name='check_wpis_status'),
        db.CheckConstraint('podpis_zopz IN (0, 1)', name='check_wpis_podpis_zopz'),
        db.UniqueConstraint('praktyka_id', 'dzien_nr', name='uq_praktyka_dzien_nr'),
    )

class PotwierdzenieEfektow(db.Model):
    __tablename__ = 'potwierdzenie_efektow'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False, unique=True)
    godziny_zrealizowane = db.Column(db.Integer, nullable=False)
    opinia_uopz = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    komentarz_odrzucenia = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    praktyka = db.relationship('Praktyka', backref=db.backref('potwierdzenie_efektow', uselist=False))

    __table_args__ = (
        db.CheckConstraint('godziny_zrealizowane > 0', name='check_potwierdzenie_godziny'),
        db.CheckConstraint("status IN ('Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected')", name='check_potwierdzenie_status'),
    )

class PotwierdzenieEfektOcena(db.Model):
    __tablename__ = 'potwierdzenie_efekt_ocena'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    potwierdzenie_id = db.Column(db.Integer, db.ForeignKey('potwierdzenie_efektow.id'), nullable=False)
    efekt_id = db.Column(db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False)
    uzyskano = db.Column(db.Integer, nullable=False)

    potwierdzenie = db.relationship('PotwierdzenieEfektow', backref=db.backref('oceny', cascade='all, delete-orphan'))
    efekt = db.relationship('EfektUczenia')

    __table_args__ = (
        db.CheckConstraint('uzyskano IN (0, 1)', name='check_ocena_uzyskano_flag'),
        db.UniqueConstraint('potwierdzenie_id', 'efekt_id', name='uq_potwierdzenie_efekt'),
    )

class Sprawozdanie(db.Model):
    __tablename__ = 'sprawozdanie'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False)
    sekcja_I = db.Column(db.Text, nullable=False)
    sekcja_II = db.Column(db.Text, nullable=False)
    sekcja_III = db.Column(db.Text, nullable=False)
    wersja = db.Column(db.Integer, nullable=False, default=1)
    ocena = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    praktyka = db.relationship('Praktyka', backref='sprawozdania')

    __table_args__ = (
        db.CheckConstraint('ocena BETWEEN 2.0 AND 5.0', name='check_sprawozdanie_ocena_range'),
        db.CheckConstraint("status IN ('Draft', 'Submitted', 'Under_Review', 'Approved', 'Rejected')", name='check_sprawozdanie_status'),
    )

    def validate_sections_length(self):
        return len(self.sekcja_I or '') >= 100 and len(self.sekcja_II or '') >= 100 and len(self.sekcja_III or '') >= 100

class KartaPraktyki(db.Model):
    __tablename__ = 'karta_praktyki'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False, unique=True)
    ocena_param_zopz = db.Column(db.Float, nullable=True)
    ocena_opisowa_zopz = db.Column(db.Text, nullable=True)
    ocena_param_uopz = db.Column(db.Float, nullable=True)
    ocena_opisowa_uopz = db.Column(db.Text, nullable=True)
    ocena_sprawozdania = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    komentarz_odrzucenia = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    praktyka = db.relationship('Praktyka', backref=db.backref('karta_praktyki', uselist=False))

    __table_args__ = (
        db.CheckConstraint('ocena_param_zopz BETWEEN 2.0 AND 5.0', name='check_karta_ocena_zopz'),
        db.CheckConstraint('ocena_param_uopz BETWEEN 2.0 AND 5.0', name='check_karta_ocena_uopz'),
        db.CheckConstraint('ocena_sprawozdania BETWEEN 2.0 AND 5.0', name='check_karta_ocena_sprawozdania'),
        db.CheckConstraint("status IN ('Draft', 'Under_Review', 'Approved', 'Rejected', 'Closed')", name='check_karta_status'),
    )

class Ankieta(db.Model):
    __tablename__ = 'ankieta'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rok_akademicki = db.Column(db.String(20), nullable=False)
    kierunek = db.Column(db.String(100), nullable=False)
    forma_studiow = db.Column(db.String(50), nullable=False)
    semestr = db.Column(db.Integer, nullable=False)
    godziny = db.Column(db.Integer, nullable=False)
    uwagi = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

class AnkietaOdpowiedz(db.Model):
    __tablename__ = 'ankieta_odpowiedz'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ankieta_id = db.Column(db.Integer, db.ForeignKey('ankieta.id'), nullable=False)
    pytanie_nr = db.Column(db.Integer, nullable=False)
    odpowiedz = db.Column(db.Integer, nullable=False)

    ankieta = db.relationship('Ankieta', backref=db.backref('odpowiedzi', cascade='all, delete-orphan'))

    __table_args__ = (
        db.CheckConstraint('pytanie_nr BETWEEN 1 AND 14', name='check_ankieta_pytanie_nr'),
        db.CheckConstraint('odpowiedz BETWEEN 1 AND 5', name='check_ankieta_odpowiedz_range'),
        db.UniqueConstraint('ankieta_id', 'pytanie_nr', name='uq_ankieta_pytanie'),
    )

class WniosekAlternatywny(db.Model):
    __tablename__ = 'wniosek_alternatywny'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    typ = db.Column(db.String(50), nullable=False)
    uzasadnienie = db.Column(db.Text, nullable=False)
    opinia_komisji = db.Column(db.Text, nullable=True)
    decyzja = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Submitted')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    student = db.relationship('Student', backref='wnioski_alternatywne')

    __table_args__ = (
        db.CheckConstraint("typ IN ('praca_zawodowa', 'staz', 'dzialalnosc_gospodarcza')", name='check_wniosek_typ'),
        db.CheckConstraint("decyzja IN ('zgoda_pelna', 'zgoda_czesciowa', 'odmowa') OR decyzja IS NULL", name='check_wniosek_decyzja'),
        db.CheckConstraint("status IN ('Submitted', 'Under_Review', 'Approved', 'Rejected')", name='check_wniosek_status'),
    )

class ZalacznikSkan(db.Model):
    __tablename__ = 'zalacznik_skan'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    wniosek_id = db.Column(db.Integer, db.ForeignKey('wniosek_alternatywny.id'), nullable=False)
    nazwa_pliku = db.Column(db.String(255), nullable=False)
    sciezka_pliku = db.Column(db.String(255), nullable=False)
    typ_dokumentu = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    wniosek = db.relationship('WniosekAlternatywny', backref=db.backref('skany', cascade='all, delete-orphan'))

    __table_args__ = (
        db.CheckConstraint(
            "typ_dokumentu IN ('umowa_o_prace', 'zakres_obowiazkow', 'ceidg', 'krs', 'inny')",
            name='check_zalacznik_typ'
        ),
    )

class Egzamin(db.Model):
    __tablename__ = 'egzamin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=False)
    termin = db.Column(db.DateTime, nullable=False)
    ocena_ustna = db.Column(db.Float, nullable=True)
    ocena_koncowa = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Draft')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    praktyka = db.relationship('Praktyka', backref='egzaminy')

    __table_args__ = (
        db.CheckConstraint('ocena_ustna BETWEEN 2.0 AND 5.0', name='check_egzamin_ocena_ustna'),
        db.CheckConstraint('ocena_koncowa BETWEEN 2.0 AND 5.0', name='check_egzamin_ocena_koncowa'),
        db.CheckConstraint("status IN ('Draft', 'Approved', 'Rejected')", name='check_egzamin_status'),
    )

class KomisjaCzlonek(db.Model):
    __tablename__ = 'komisja_czlonek'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    egzamin_id = db.Column(db.Integer, db.ForeignKey('egzamin.id'), nullable=False)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    rola_w_komisji = db.Column(db.String(50), nullable=False)

    egzamin = db.relationship('Egzamin', backref=db.backref('komisja', cascade='all, delete-orphan'))
    uzytkownik = db.relationship('Uzytkownik')

    __table_args__ = (
        db.CheckConstraint("rola_w_komisji IN ('przewodniczacy', 'czlonek')", name='check_rola_w_komisji'),
        db.UniqueConstraint('egzamin_id', 'uzytkownik_id', name='uq_egzamin_uzytkownik'),
    )

class Dokument(db.Model):
    __tablename__ = 'dokument'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    praktyka_id = db.Column(db.Integer, db.ForeignKey('praktyka.id'), nullable=True)
    typ = db.Column(db.String(50), nullable=False)
    sciezka_pliku = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Closed')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    praktyka = db.relationship('Praktyka', backref='dokumenty')

    __table_args__ = (
        db.CheckConstraint(
            "typ IN ('zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr4b', 'zal_nr5', 'zal_nr6', 'zal_nr7', 'zal_nr8', 'signed_karta_sprawozdanie')",
            name='check_dokument_typ'
        ),
    )

    def get_download_url(self):
        return f"/api/v1/documents/{self.id}/download"
