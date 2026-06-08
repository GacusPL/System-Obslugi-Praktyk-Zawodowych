import os

def search():
    terms = ['dokumenty', 'download', 'documents']
    for root, dirs, files in os.walk('app/templates'):
        for f in files:
            if f.endswith('.html'):
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
