# runs pyflakes. for code evaluation

import os

exclude_dirs = ['.venv', '.vscode', 'images', '__pycache__']

for root, dirs, files in os.walk(os.getcwd()):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file.endswith('.py'):
            py_path = os.path.join(root, file)
            os.system(f'pyflakes {py_path}')