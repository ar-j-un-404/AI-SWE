import ast


def parse_python_file(file_data):
    content = file_data["content"]

    try:
        tree = ast.parse(content)

    except SyntaxError as error:
        return {
            "path": file_data["path"],
            "imports": [],
            "functions": [],
            "classes": [],
            "syntax_error": str(error)
        }

    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            module = node.module or ""

            imports.append(module)

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef
            )
        ):

            functions.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno
                    )
                }
            )

        elif isinstance(node, ast.ClassDef):

            classes.append(
                {
                    "name": node.name,
                    "start_line": node.lineno,
                    "end_line": getattr(
                        node,
                        "end_lineno",
                        node.lineno
                    )
                }
            )

    return {
        "path": file_data["path"],
        "imports": imports,
        "functions": functions,
        "classes": classes,
        "syntax_error": None
    }


def build_symbol_index(files):
    index = []

    for file_data in files:
        parsed = parse_python_file(
            file_data
        )

        index.append(parsed)

    return index