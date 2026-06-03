import pytest
from app import db
from app.models import EfektUczenia, Uzytkownik
from app.seed import seed_db

def test_seed_db(db_session):
    # Run seed the first time
    seed_db()
    
    assert EfektUczenia.query.count() == 13
    assert Uzytkownik.query.filter_by(email="admin@ans-elblag.pl").count() == 1
    
    # Run seed the second time (idempotency check)
    seed_db()
    
    assert EfektUczenia.query.count() == 13
    assert Uzytkownik.query.filter_by(email="admin@ans-elblag.pl").count() == 1
