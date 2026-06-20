from flask import Blueprint, render_template, redirect, url_for, request, abort, flash
from flask_login import login_required, current_user
from app.models import Student, Praktyka, ZakladPracy, WpisDziennika, WniosekAlternatywny, Egzamin, Uzytkownik, Sprawozdanie, EfektUczenia, KartaPraktyki, ZalacznikSkan, db
from app.decorators import role_required

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.rola is None:
        return redirect(url_for('auth.waiting'))
        
    template_map = {
        'student': 'dashboard/student.html',
        'zopz': 'dashboard/zopz.html',
        'uopz': 'dashboard/uopz.html',
        'administrator': 'dashboard/admin.html',
        'dyrektor': 'dashboard/dyrektor.html'
    }
    
    template_name = template_map.get(current_user.rola)
    if not template_name:
        return redirect(url_for('auth.waiting'))
        
    context = {}
    
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
        wpisy_zatwierdzone = WpisDziennika.query.filter_by(praktyka_id=praktyka.id, status='Approved').count() if praktyka else 0
        wnioski = WniosekAlternatywny.query.filter_by(student_id=student.id).all() if student else []
        
        context.update({
            'student': student,
            'praktyka': praktyka,
            'wpisy_zatwierdzone': wpisy_zatwierdzone,
            'wnioski': wnioski
        })
        
    elif current_user.rola == 'zopz':
        zaklady = ZakladPracy.query.filter((ZakladPracy.zopz_uzytkownik_id == current_user.id) | ((ZakladPracy.zopz_uzytkownik_id.is_(None)) & (ZakladPracy.zopz_imie == current_user.imie) & (ZakladPracy.zopz_nazwisko == current_user.nazwisko))).all()
        zaklad_ids = [z.id for z in zaklady]
        praktyki = Praktyka.query.filter(Praktyka.zaklad_id.in_(zaklad_ids)).all() if zaklad_ids else []
        oczekujace_wpisy = WpisDziennika.query.join(Praktyka).filter(Praktyka.zaklad_id.in_(zaklad_ids), WpisDziennika.status == 'Submitted').all() if zaklad_ids else []

        context.update({
            'zaklady': zaklady,
            'praktyki': praktyki,
            'oczekujace_wpisy': oczekujace_wpisy
        })
        
    elif current_user.rola == 'uopz':
        praktyki = Praktyka.query.filter_by(uopz_id=current_user.id).all()
        oczekujace_dzienniki = Praktyka.query.filter_by(uopz_id=current_user.id, dziennik_status='Under_Review').all()
        oczekujace_sprawozdania = Sprawozdanie.query.join(Praktyka).filter(Praktyka.uopz_id == current_user.id, Sprawozdanie.status == 'Submitted').all()
        
        context.update({
            'praktyki': praktyki,
            'oczekujace_dzienniki': oczekujace_dzienniki,
            'oczekujace_sprawozdania': oczekujace_sprawozdania
        })
        
    elif current_user.rola == 'dyrektor':
        wnioski = WniosekAlternatywny.query.filter(WniosekAlternatywny.status.in_(['Submitted', 'Under_Review'])).all()
        
        context.update({
            'wnioski_alternatywne': wnioski
        })
        
    elif current_user.rola == 'administrator':
        context.update({
            'stats': {
                'users': Uzytkownik.query.count(),
                'praktyki': Praktyka.query.count(),
                'zaklady': ZakladPracy.query.count(),
            },
            'bez_roli': Uzytkownik.query.filter_by(rola=None).all()
        })
        
    return render_template(template_name, **context)

def _zopz_praktyki(user):
    zaklady = ZakladPracy.query.filter(
        (ZakladPracy.zopz_uzytkownik_id == user.id) |
        ((ZakladPracy.zopz_uzytkownik_id.is_(None)) &
         (ZakladPracy.zopz_imie == user.imie) &
         (ZakladPracy.zopz_nazwisko == user.nazwisko))
    ).all()
    zaklad_ids = [z.id for z in zaklady]
    return Praktyka.query.filter(Praktyka.zaklad_id.in_(zaklad_ids)).all() if zaklad_ids else []

@main_bp.route('/zopz/moja-grupa')
@login_required
@role_required('zopz')
def zopz_moja_grupa():
    praktyki = _zopz_praktyki(current_user)
    return render_template('dashboard/zopz_grupa.html', praktyki=praktyki)

@main_bp.route('/uopz/praktyki')
@login_required
@role_required('uopz', 'administrator')
def uopz_praktyki():
    if current_user.rola == 'uopz':
        praktyki = Praktyka.query.filter_by(uopz_id=current_user.id).all()
    else:
        praktyki = Praktyka.query.all()
    return render_template('dashboard/uopz_praktyki.html', praktyki=praktyki)

@main_bp.route('/praktyka/<int:praktyka_id>/przeglad')
@login_required
@role_required('uopz', 'zopz', 'administrator')
def praktyka_przeglad(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    wpisy_approved = WpisDziennika.query.filter_by(praktyka_id=praktyka.id, status='Approved').count()
    sprawozdanie = Sprawozdanie.query.filter_by(praktyka_id=praktyka.id).order_by(Sprawozdanie.wersja.desc()).first()
    egzamin = Egzamin.query.filter_by(praktyka_id=praktyka.id).first()
    return render_template('dashboard/praktyka_przeglad.html', praktyka=praktyka,
                           wpisy_approved=wpisy_approved, sprawozdanie=sprawozdanie, egzamin=egzamin)

@main_bp.route('/praktyka/zgloszenie')
@login_required
def zgloszenie_praktyki():
    if current_user.rola != 'student':
        abort(403)
    from app.models import Student, ZakladPracy, Uzytkownik, Praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
    zaklady = ZakladPracy.query.filter_by(archived=False).all()
    uopz_list = Uzytkownik.query.filter_by(rola='uopz', archived=False).all()
    return render_template('praktyka/zgloszenie.html', zaklady=zaklady, uopz_list=uopz_list, praktyka=praktyka)

@main_bp.route('/wniosek/alternatywny')
@login_required
def zgloszenie_alternatywne():
    if current_user.rola != 'student':
        return redirect(url_for('main.dashboard'))
    from app.models import Student, Praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
    if praktyka and praktyka.status in ['Approved', 'Closed']:
        flash("Twoje zgłoszenie praktyki zostało już zaakceptowane. Nie możesz złożyć wniosku alternatywnego.", "warning")
        return redirect(url_for('main.dashboard'))
    return render_template('praktyka/wniosek_alternatywny.html')

def check_praktyka_ownership(praktyka):
    if current_user.rola == 'administrator':
        return
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if student and praktyka.student_id == student.id:
            return
    elif current_user.rola == 'uopz':
        if praktyka.uopz_id == current_user.id:
            return
    elif current_user.rola == 'zopz':
        if praktyka.zaklad_pracy.is_opiekun(current_user):
            return
    abort(403)

@main_bp.route('/harmonogram/edycja')
@login_required
def harmonogram_edit():
    from app.models import Student, Praktyka, Harmonogram
    praktyka_id = request.args.get('praktyka_id', type=int)
    
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
        if not praktyka:
            return redirect(url_for('main.dashboard'))
    else:
        if not praktyka_id:
            abort(400, "Brak parametru praktyka_id")
        praktyka = Praktyka.query.get_or_404(praktyka_id)
        # Access checks
        if current_user.rola == 'uopz':
            if praktyka.uopz_id != current_user.id:
                abort(403)
        elif current_user.rola == 'zopz':
            if not praktyka.zaklad_pracy.is_opiekun(current_user):
                abort(403)
        elif current_user.rola != 'administrator':
            abort(403)
            
    harmonogram = praktyka.harmonogram
    if not harmonogram:
        harmonogram = Harmonogram(praktyka_id=praktyka.id)
        db.session.add(harmonogram)
        db.session.commit()

    from app.models import EfektUczenia
    efekty = EfektUczenia.query.order_by(EfektUczenia.nr.asc()).all()
    program_map = {p.efekt_id: p.opis_realizacji for p in harmonogram.program_pozycje}
    return render_template('harmonogram/edit.html', praktyka=praktyka, harmonogram=harmonogram,
                           efekty=efekty, program_map=program_map)

@main_bp.route('/dziennik')
@login_required
def dziennik_list():
    praktyka_id = request.args.get('praktyka_id', type=int)
    
    if praktyka_id:
        praktyka = Praktyka.query.get_or_404(praktyka_id)
        # Access check
        if current_user.rola == 'student':
            student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
            if not student or praktyka.student_id != student.id:
                abort(403)
        elif current_user.rola == 'uopz':
            if praktyka.uopz_id != current_user.id:
                abort(403)
        elif current_user.rola == 'zopz':
            if not praktyka.zaklad_pracy.is_opiekun(current_user):
                abort(403)
    else:
        if current_user.rola == 'student':
            student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
            praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
        else:
            praktyka = None

    if not praktyka:
        return redirect(url_for('main.dashboard'))

    efekty = EfektUczenia.query.order_by(EfektUczenia.nr).all()
    from datetime import date
    return render_template('dziennik/list.html', praktyka=praktyka, efekty=efekty, today=date.today().isoformat())

@main_bp.route('/ankieta/formularz')
@login_required
def ankieta_form():
    if current_user.rola != 'student':
        abort(403)
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
    if not praktyka:
        return redirect(url_for('main.dashboard'))
    return render_template('ankieta/form.html', praktyka=praktyka)

@main_bp.route('/praktyka/<int:praktyka_id>/efekty')
@login_required
def efekty_potwierdzenie(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    efekty = EfektUczenia.query.order_by(EfektUczenia.nr).all()
    potwierdzenie = praktyka.potwierdzenie_efektow
    if not potwierdzenie:
        from app.models import PotwierdzenieEfektow
        potwierdzenie = PotwierdzenieEfektow(praktyka_id=praktyka.id, godziny_zrealizowane=960)
        db.session.add(potwierdzenie)
        db.session.commit()
    return render_template('efekty/potwierdzenie.html', praktyka=praktyka, efekty=efekty, potwierdzenie=potwierdzenie)

@main_bp.route('/praktyka/<int:praktyka_id>/sprawozdanie')
@login_required
def sprawozdanie_form(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    sprawozdanie = Sprawozdanie.query.filter_by(praktyka_id=praktyka.id).order_by(Sprawozdanie.wersja.desc()).first()
    return render_template('sprawozdanie/form.html', praktyka=praktyka, sprawozdanie=sprawozdanie)

@main_bp.route('/praktyka/<int:praktyka_id>/karta')
@login_required
def karta_praktyki_view(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    karta = praktyka.karta_praktyki
    if not karta:
        from app.models import KartaPraktyki
        karta = KartaPraktyki(praktyka_id=praktyka.id)
        db.session.add(karta)
        db.session.commit()
    return render_template('karta_praktyki/view.html', praktyka=praktyka, karta=karta)

@main_bp.route('/praktyka/<int:praktyka_id>/dokumentacja/checklist')
@login_required
def dokumentacja_checklist(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    return render_template('dokumentacja/checklist.html', praktyka=praktyka)

@main_bp.route('/praktyka/<int:praktyka_id>/weryfikacja-zgloszenia')
@login_required
@role_required('uopz', 'administrator')
def weryfikacja_zgloszenia(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    if current_user.rola == 'uopz' and praktyka.uopz_id != current_user.id:
        abort(403)
    return render_template('praktyka/weryfikacja_zgloszenia.html', praktyka=praktyka)

@main_bp.route('/praktyka/<int:praktyka_id>/dokumentacja/weryfikacja')
@login_required
def dokumentacja_weryfikacja(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    from app.routes.api.dokumentacja import check_checklist
    checklist = check_checklist(praktyka)
    all_approved = all(checklist.values())
    return render_template('dokumentacja/review.html', praktyka=praktyka,
                           checklist=checklist, all_approved=all_approved)

@main_bp.route('/profile')
@login_required
def profile_view():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    return render_template('profile/view.html', student=student)

@main_bp.route('/praktyka/<int:praktyka_id>/karta/ocena-zopz')
@login_required
@role_required('zopz', 'administrator')
def ocena_zopz_form(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka_id).first()
    return render_template('karta_praktyki/ocena_zopz.html', praktyka=praktyka, karta=karta)

@main_bp.route('/praktyka/<int:praktyka_id>/karta/ocena-uopz')
@login_required
@role_required('uopz', 'administrator')
def ocena_uopz_form(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    karta = KartaPraktyki.query.filter_by(praktyka_id=praktyka_id).first()
    return render_template('karta_praktyki/ocena_uopz.html', praktyka=praktyka, karta=karta)

@main_bp.route('/wniosek/<int:wniosek_id>/komisja')
@login_required
@role_required('dyrektor', 'administrator')
def komisja_ocena_form(wniosek_id):
    wniosek = WniosekAlternatywny.query.get_or_404(wniosek_id)
    efekty = EfektUczenia.query.order_by(EfektUczenia.nr).all()
    return render_template('wniosek/komisja_ocena.html', wniosek=wniosek, efekty=efekty)

@main_bp.route('/wniosek/<int:wniosek_id>')
@login_required
def wniosek_detail(wniosek_id):
    wniosek = WniosekAlternatywny.query.get_or_404(wniosek_id)
    # Access checks
    if current_user.rola == 'student':
        student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
        if not student or wniosek.student_id != student.id:
            abort(403)
    skany = ZalacznikSkan.query.filter_by(wniosek_id=wniosek_id).all()
    return render_template('wniosek/detail.html', wniosek=wniosek, skany=skany)

@main_bp.route('/praktyka/<int:praktyka_id>/dziennik/pelny')
@login_required
@role_required('uopz', 'administrator')
def dziennik_pelny(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    check_praktyka_ownership(praktyka)
    wpisy = WpisDziennika.query.filter_by(praktyka_id=praktyka_id).order_by(WpisDziennika.dzien_nr.asc()).all()
    return render_template('dziennik/pelny.html', praktyka=praktyka, wpisy=wpisy)

@main_bp.route('/dziennik/wpisy/<int:wpis_id>/edycja')
@login_required
@role_required('student')
def wpis_edit_form(wpis_id):
    wpis = WpisDziennika.query.get_or_404(wpis_id)
    praktyka = wpis.praktyka
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    if not student or praktyka.student_id != student.id:
        abort(403)
    if wpis.status not in ['Draft', 'Rejected']:
        abort(400)
    efekty = EfektUczenia.query.order_by(EfektUczenia.nr).all()
    return render_template('dziennik/wpis_edit.html', wpis=wpis, efekty=efekty)
