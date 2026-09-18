import ast


def get_source_segment(
    lines,
    start,
    end
):
    return "\n".join(
        lines[start - 1:end]
    )


def chunk_python_file(file_data):
    content = file_data["content"]
    lines = content.splitlines()

    chunks = []

    try:
        tree = ast.parse(content)

    except SyntaxError:
        return [
            {
                "path": file_data["path"],
                "symbol": "FILE",
                "type": "file",
                "content": content
            }
        ]

    module_level_lines = []

    for node in tree.body:

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef
            )
        ):
            start = node.lineno
            end = getattr(
                node,
                "end_lineno",
                start
            )

            chunks.append(
                {
                    "path": file_data["path"],
                    "symbol": node.name,
                    "type": "function",
                    "content": get_source_segment(
                        lines,
                        start,
                        end
                    )
                }
            )

        elif isinstance(node, ast.ClassDef):
            start = node.lineno
            end = getattr(
                node,
                "end_lineno",
                start
            )

            chunks.append(
                {
                    "path": file_data["path"],
                    "symbol": node.name,
                    "type": "class",
                    "content": get_source_segment(
                        lines,
                        start,
                        end
                    )
                }
            )

        else:
            start = getattr(
                node,
                "lineno",
                None
            )

            end = getattr(
                node,
                "end_lineno",
                start
            )

            if start and end:
                module_level_lines.append(
                    get_source_segment(
                        lines,
                        start,
                        end
                    )
                )

    if module_level_lines:
        chunks.append(
            {
                "path": file_data["path"],
                "symbol": "MODULE_LEVEL",
                "type": "module",
                "content": "\n\n".join(
                    module_level_lines
                )
            }
        )

    if not chunks:
        chunks.append(
            {
                "path": file_data["path"],
                "symbol": "FILE",
                "type": "file",
                "content": content
            }
        )

    return chunks


def create_chunks(files):
    chunks = []

    for file_data in files:
        chunks.extend(
            chunk_python_file(
                file_data
            )
        )

    return chunks