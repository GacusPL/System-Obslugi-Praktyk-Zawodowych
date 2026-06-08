import os

def search():
    terms = ['static/generated', 'static\\generated', 'generated/']
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root or '.pytest_cache' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith(('.py', '.html', '.js', '.css', '.md')):
                path = os.path.join(root, f)
                try:
                    content = open(path, 'r', encoding='utf-8').read()
                    for term in terms:
                        if term in content:
                            print(f"Found '{term}' in {path}")
                except Exception as e:
                    pass

if __name__ == '__main__':
    search()
