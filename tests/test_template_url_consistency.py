"""S-06: Wykrywanie rozbieżności URL między szablonami a trasami API.

Testy API wołają endpointy bezpośrednio, więc literówki w URL-ach fetch/action
w szablonach (np. /api/v1/efekty/potwierdzenia zamiast /potwierdzenie) przechodzą
niezauważone. Ten test skanuje szablony i sprawdza, czy każdy literalny URL
/api/v1/... da się dopasować do zarejestrowanej trasy.
"""
import os
import re
import pytest

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', 'app', 'templates')


def _iter_template_files():
    for root, _, files in os.walk(TEMPLATES_DIR):
        for f in files:
            if f.endswith('.html'):
                yield os.path.join(root, f)


def _normalize(text):
    # Zastap wyrazenia Jinja i interpolacje JS pojedynczym segmentem 'X'
    text = re.sub(r'\{\{.*?\}\}', 'X', text)
    text = re.sub(r'\{%.*?%\}', '', text)
    text = re.sub(r'\$\{.*?\}', 'X', text)
    return text


def _extract_api_urls(text):
    text = _normalize(text)
    urls = set()
    for m in re.findall(r"/api/v1/[^\s\"'`)>]*", text):
        url = m.split('?')[0].rstrip('/')
        # Pomijaj fragmenty bez sensu (samo /api/v1)
        if url and url != '/api/v1':
            urls.add(url)
    return urls


def _rule_regexes(app):
    regexes = []
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/api/v1/'):
            continue
        pattern = re.sub(r'<[^>]+>', '[^/]+', rule.rule).rstrip('/')
        regexes.append(re.compile('^' + pattern + '$'))
    return regexes


def test_template_api_urls_match_routes(app):
    regexes = _rule_regexes(app)
    unmatched = {}
    for path in _iter_template_files():
        with open(path, encoding='utf-8') as fh:
            content = fh.read()
        for url in _extract_api_urls(content):
            norm = re.sub(r'/X(?=/|$)', '/[^/]+', url)
            # Buduj kandydata do dopasowania: zamien segmenty 'X' na placeholder
            candidate = url.replace('/X', '/PLACEHOLDER')
            test_url = candidate.replace('/PLACEHOLDER', '/1')
            if not any(rx.match(test_url) for rx in regexes):
                unmatched.setdefault(os.path.basename(path), set()).add(url)

    assert not unmatched, f"URL-e w szablonach bez pasujacej trasy API: {unmatched}"
