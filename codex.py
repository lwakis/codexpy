import os
import ast
import chardet
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


def detect_encoding(file_path):
    """Определяет кодировку файла."""
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']


def extract_docstring(node):
    """Извлекает docstring из AST узла."""
    if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return None
    docstring = ast.get_docstring(node)
    if docstring:
        return docstring.strip()
    return None


def parse_file(file_path):
    """Парсит файл и извлекает все docstring и исходный код функций."""
    try:
        encoding = detect_encoding(file_path)  # Определяем кодировку файла
        print(f"\nОбработка файла: {file_path} (кодировка: {encoding})")
        with open(file_path, 'r', encoding=encoding) as file:
            content = file.read()
            tree = ast.parse(content, filename=file_path)

        docstrings = []
        for node in ast.walk(tree):
            node_type = type(node).__name__
            node_name = getattr(node, 'name', 'Module')
            docstring = extract_docstring(node)
            if docstring:
                print(f"Найден docstring в узле: {node_type} {node_name}")
                # Извлекаем исходный код функции
                start_line = node.lineno - 1  # Нумерация строк с 0
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                function_code = '\n'.join(content.splitlines()[start_line:end_line])

                docstrings.append({
                    'type': node_type,
                    'name': node_name,
                    'docstring': docstring,
                    'file': file_path,
                    'fileName': os.path.basename(file_path).replace('.py', ''),
                    'code': function_code
                })
            else:
                print(f"Узел без docstring: {node_type} {node_name}")
        return docstrings
    except SyntaxError as e:
        print(f"Синтаксическая ошибка в файле {file_path}: {e}")
        return []
    except UnicodeDecodeError as e:
        print(f"Ошибка декодирования файла {file_path}: {e}")
        return []
    except Exception as e:
        print(f"Неизвестная ошибка при обработке файла {file_path}: {e}")
        return []


def generate_html(docstrings, output_file):
    """Генерирует HTML-документацию с раскрывающимися блоками кода."""
    # Подключаем стили Pygments для подсветки синтаксиса
    pygments_css = HtmlFormatter().get_style_defs('.highlight')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>tg-poster</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                display: flex;
            }}
            .sidebar {{
                width: 250px;
                background-color: #f4f4f4;
                padding: 20px;
                height: 100vh;
                overflow-y: auto;
                box-shadow: 2px 0 5px rgba(0, 0, 0, 0.1);
            }}
            .sidebar h2 {{
                margin-top: 0;
            }}
            .sidebar ul {{
                list-style: none;
                padding: 0;
            }}
            .sidebar ul li {{
                margin: 10px 0;
            }}
            .sidebar ul li a {{
                text-decoration: none;
                color: #333;
                font-weight: bold;
            }}
            .sidebar ul li a:hover {{
                color: #007BFF;
            }}
            .sidebar .file {{
                cursor: pointer;
                font-weight: bold;
            }}
            .sidebar .file ul {{
                display: none;
                margin-left: 15px;
            }}
            .content {{
                flex: 1;
                padding: 20px;
                overflow-y: auto;
            }}
            .docstring {{
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #fff;
            }}
            .docstring .file {{
                font-size: 0.9em;
                color: #888;
                margin-bottom: 5px;
            }}
            .docstring .name {{
                color: #333;
                font-size: 1.2em;
                margin-bottom: 10px;
            }}
            .docstring .name .keyword {{
                color: green;
            }}
            .docstring .name .function-name {{
                color: blue;
            }}
            .docstring .doc {{
                color: #666;
                white-space: pre-wrap;
            }}
            .toggle-code {{
                margin-top: 10px;
                color: #007BFF;
                cursor: pointer;
                text-decoration: underline;
            }}
            .code-block {{
                display: none;
                margin-top: 10px;
            }}
            {pygments_css}
        </style>
    </head>
    <body>
        <div class="sidebar">
            <h2>tg-poster</h2>
            <ul>
    """

    # Группируем docstrings по файлам
    files = {}
    for doc in docstrings:
        file_name = doc['fileName']
        if file_name not in files:
            files[file_name] = []
        files[file_name].append(doc)

    # Добавляем выпадающие списки для файлов
    for file_name, docs in files.items():
        html_content += f"""
            <li class="file" onclick="toggleFile('{file_name}')">
                {file_name}
                <ul id="{file_name}">
        """
        for doc in docs:
            html_content += f"""
                    <li><a href="#{doc['name']}">{doc['name']}</a></li>
            """
        html_content += """
                </ul>
            </li>
        """

    html_content += """
            </ul>
        </div>
        <div class="content">
    """

    # Добавляем контент документации
    for doc in docstrings:
        # Подсветка имени функции
        function_keyword = "async def" if doc['type'] == "AsyncFunctionDef" else "def"
        function_name = doc['name']
        function_header = f"""
            <span class="keyword">{function_keyword}</span>
            <span class="function-name">{function_name}</span>
        """

        # Подсветка кода функции
        highlighted_code = highlight(doc['code'], PythonLexer(), HtmlFormatter())

        html_content += f"""
            <div class="docstring" id="{doc['name']}">
                <div class="file">File: {doc['file']}</div>
                <div class="name">{function_header}</div>
                <div class="doc">{doc['docstring']}</div>
                <div class="toggle-code" onclick="toggleCode('{doc['name']}-code')">Показать код</div>
                <div class="code-block" id="{doc['name']}-code">
                    {highlighted_code}
                </div>
            </div>
        """

    html_content += """
        </div>
        <script>
            function toggleCode(id) {
                const codeBlock = document.getElementById(id);
                if (codeBlock.style.display === "none") {
                    codeBlock.style.display = "block";
                } else {
                    codeBlock.style.display = "none";
                }
            }

            function toggleFile(id) {
                const fileList = document.getElementById(id);
                if (fileList.style.display === "none") {
                    fileList.style.display = "block";
                } else {
                    fileList.style.display = "none";
                }
            }
        </script>
    </body>
    </html>
    """

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)


def process_project(project_path, output_file):
    """Обрабатывает весь проект, извлекая docstring и генерируя HTML."""
    all_docstrings = []
    skipped_files = []

    for root, dirs, files in os.walk(project_path):
        # Пропускаем директорию venv и другие ненужные папки
        if 'venv' in dirs:
            dirs.remove('venv')
        if '.git' in dirs:
            dirs.remove('.git')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                docstrings = parse_file(file_path)
                if docstrings:
                    all_docstrings.extend(docstrings)
                else:
                    skipped_files.append(file_path)

    generate_html(all_docstrings, output_file)

    # Логируем пропущенные файлы
    if skipped_files:
        print("\nПропущенные файлы:")
        for file in skipped_files:
            print(f"- {file}")

if __name__ == "__main__":
    project_path = '.'  # Текущая директория
    output_file = "documentation.html"  # Имя выходного HTML-файла
    process_project(project_path, output_file)
    print(f"Документация успешно создана: {output_file}")