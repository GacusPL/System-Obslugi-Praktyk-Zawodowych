from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.models import Student, Praktyka, ZakladPracy, WpisDziennika, WniosekAlternatywny, Egzamin, Uzytkownik, Sprawozdanie, EfektUczenia, db

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
        zaklady = ZakladPracy.query.filter_by(zopz_imie=current_user.imie, zopz_nazwisko=current_user.nazwisko).all()
        zaklad_ids = [z.id for z in zaklady]
        praktyki = Praktyka.query.filter(Praktyka.zaklad_id.in_(zaklad_ids)).all() if zaklad_ids else []
        oczekujace_wpisy = WpisDziennika.query.join(Praktyka).filter(Praktyka.zaklad_id.in_(zaklad_ids), WpisDziennika.status == 'Submitted').all() if zaklad_ids else []
        
        context.update({
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
        wnioski = WniosekAlternatywny.query.filter_by(status='Submitted').all()
        
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

@main_bp.route('/praktyka/zgloszenie')
@login_required
def zgloszenie_praktyki():
    if current_user.rola != 'student':
        return redirect(url_for('main.dashboard'))
    
    zaklady = ZakladPracy.query.filter_by(status='Approved').all()
    uopz_list = Uzytkownik.query.filter_by(rola='uopz').all()
    return render_template('praktyka/zgloszenie.html', zaklady=zaklady, uopz_list=uopz_list)

@main_bp.route('/wniosek/alternatywny')
@login_required
def zgloszenie_alternatywne():
    if current_user.rola != 'student':
        return redirect(url_for('main.dashboard'))
    return render_template('praktyka/wniosek_alternatywny.html')

@main_bp.route('/harmonogram/edycja')
@login_required
def harmonogram_edit():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
    if not praktyka:
        return redirect(url_for('main.dashboard'))
    harmonogram = praktyka.harmonogram
    if not harmonogram:
        from app.models import Harmonogram
        harmonogram = Harmonogram(praktyka_id=praktyka.id)
        db.session.add(harmonogram)
        db.session.commit()
    return render_template('harmonogram/edit.html', praktyka=praktyka, harmonogram=harmonogram)

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
            if praktyka.zaklad_pracy.zopz_imie != current_user.imie or praktyka.zaklad_pracy.zopz_nazwisko != current_user.nazwisko:
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
    return render_template('dziennik/list.html', praktyka=praktyka, efekty=efekty)

@main_bp.route('/ankieta/formularz')
@login_required
def ankieta_form():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    praktyka = Praktyka.query.filter_by(student_id=student.id).first() if student else None
    if not praktyka:
        return redirect(url_for('main.dashboard'))
    return render_template('ankieta/form.html', praktyka=praktyka)

@main_bp.route('/praktyka/<int:praktyka_id>/efekty')
@login_required
def efekty_potwierdzenie(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
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
    sprawozdanie = Sprawozdanie.query.filter_by(praktyka_id=praktyka.id).order_by(Sprawozdanie.wersja.desc()).first()
    return render_template('sprawozdanie/form.html', praktyka=praktyka, sprawozdanie=sprawozdanie)

@main_bp.route('/praktyka/<int:praktyka_id>/karta')
@login_required
def karta_praktyki_view(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
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
    return render_template('dokumentacja/checklist.html', praktyka=praktyka)

@main_bp.route('/praktyka/<int:praktyka_id>/dokumentacja/weryfikacja')
@login_required
def dokumentacja_weryfikacja(praktyka_id):
    praktyka = Praktyka.query.get_or_404(praktyka_id)
    return render_template('dokumentacja/review.html', praktyka=praktyka)

@main_bp.route('/profile')
@login_required
def profile_view():
    student = Student.query.filter_by(uzytkownik_id=current_user.id).first()
    return render_template('profile/view.html', student=student)
