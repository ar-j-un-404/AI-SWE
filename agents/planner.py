import json
import re

from llm import ask_llm


REQUIRED_PLAN_FIELDS = {
    "summary",
    "reasoning",
    "files_to_modify",
    "files_to_create",
    "steps",
    "risks",
    "tests_to_run",
}


def extract_json(response):
    if response is None:
        raise ValueError(
            "Planner returned no response."
        )

    if not isinstance(response, str):
        response = str(response)

    text = response.strip()

    if not text:
        raise ValueError(
            "Planner returned an empty response."
        )

    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```\s*",
        "",
        text,
    )

    text = text.strip()

    try:
        parsed = json.loads(
            text
        )

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if (
        start != -1
        and end != -1
        and end > start
    ):
        candidate = text[
            start:end + 1
        ]

        try:
            parsed = json.loads(
                candidate
            )

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError as error:
            print(
                "Planner JSON parsing error:"
            )

            print(
                error
            )

    print(
        "\n"
        "========== RAW PLANNER RESPONSE =========="
    )

    print(
        text
    )

    print(
        "=========================================="
        "\n"
    )

    raise ValueError(
        "Planner did not return valid JSON."
    )


def build_relevant_context(
    relevant_chunks,
):
    if not relevant_chunks:
        return (
            "No relevant repository chunks "
            "were retrieved."
        )

    sections = []

    for index, chunk in enumerate(
        relevant_chunks,
        start=1,
    ):
        path = chunk.get(
            "path",
            "unknown",
        )

        symbol = chunk.get(
            "symbol",
            "MODULE_LEVEL",
        )

        content = chunk.get(
            "content",
            "",
        )

        score = chunk.get(
            "retrieval_score",
            chunk.get(
                "similarity",
                0,
            ),
        )

        section = (
            f"CHUNK {index}\n"
            f"FILE: {path}\n"
            f"SYMBOL: {symbol}\n"
            f"SCORE: {score}\n"
            "CONTENT:\n"
            f"{content}"
        )

        sections.append(
            section
        )

    return "\n\n".join(
        sections
    )


def build_symbol_context(
    symbols,
):
    if not symbols:
        return (
            "No repository symbol "
            "information is available."
        )

    lines = []

    if isinstance(
        symbols,
        dict,
    ):
        for path, value in symbols.items():
            if isinstance(
                value,
                dict,
            ):
                imports = value.get(
                    "imports",
                    [],
                )

                functions = value.get(
                    "functions",
                    [],
                )

                classes = value.get(
                    "classes",
                    [],
                )

                lines.append(
                    f"FILE: {path}"
                )

                if imports:
                    lines.append(
                        "  Imports: "
                        + ", ".join(
                            str(item)
                            for item in imports
                        )
                    )

                if functions:
                    lines.append(
                        "  Functions: "
                        + ", ".join(
                            _symbol_name(item)
                            for item in functions
                        )
                    )

                if classes:
                    lines.append(
                        "  Classes: "
                        + ", ".join(
                            _symbol_name(item)
                            for item in classes
                        )
                    )

            elif isinstance(
                value,
                list,
            ):
                lines.append(
                    f"FILE: {path}"
                )

                for item in value:
                    lines.append(
                        "  "
                        + _symbol_description(
                            item
                        )
                    )

            else:
                lines.append(
                    f"{path}: {value}"
                )

        return "\n".join(
            lines
        )

    if isinstance(
        symbols,
        list,
    ):
        for item in symbols:
            if isinstance(
                item,
                dict,
            ):
                path = (
                    item.get("path")
                    or item.get("file")
                    or item.get("file_path")
                    or "unknown"
                )

                name = (
                    item.get("name")
                    or item.get("symbol")
                    or item.get("function")
                    or item.get("class")
                    or "unknown"
                )

                symbol_type = (
                    item.get("type")
                    or item.get("symbol_type")
                    or item.get("kind")
                    or "symbol"
                )

                start_line = (
                    item.get("start_line")
                    or item.get("lineno")
                )

                end_line = (
                    item.get("end_line")
                    or item.get("end_lineno")
                )

                line_info = ""

                if start_line is not None:
                    line_info = (
                        f" line {start_line}"
                    )

                    if end_line is not None:
                        line_info += (
                            f"-{end_line}"
                        )

                lines.append(
                    f"{path}: "
                    f"{symbol_type} "
                    f"{name}"
                    f"{line_info}"
                )

            else:
                lines.append(
                    str(item)
                )

        return "\n".join(
            lines
        )

    return str(
        symbols
    )


def _symbol_name(
    item,
):
    if isinstance(
        item,
        str,
    ):
        return item

    if isinstance(
        item,
        dict,
    ):
        return str(
            item.get("name")
            or item.get("symbol")
            or item.get("function")
            or item.get("class")
            or item
        )

    return str(
        item
    )


def _symbol_description(
    item,
):
    if not isinstance(
        item,
        dict,
    ):
        return str(
            item
        )

    name = (
        item.get("name")
        or item.get("symbol")
        or "unknown"
    )

    symbol_type = (
        item.get("type")
        or item.get("kind")
        or "symbol"
    )

    return (
        f"{symbol_type}: {name}"
    )


def normalize_string_list(
    value,
):
    if value is None:
        return []

    if isinstance(
        value,
        str,
    ):
        value = value.strip()

        if not value:
            return []

        return [
            value
        ]

    if not isinstance(
        value,
        list,
    ):
        return [
            str(value)
        ]

    result = []

    for item in value:
        if item is None:
            continue

        if isinstance(
            item,
            str,
        ):
            cleaned = item.strip()

            if cleaned:
                result.append(
                    cleaned
                )

        else:
            result.append(
                str(item)
            )

    return result


def normalize_file_list(
    value,
):
    files = normalize_string_list(
        value
    )

    normalized = []

    seen = set()

    for path in files:
        path = path.replace(
            "\\",
            "/",
        ).strip()

        while path.startswith(
            "./"
        ):
            path = path[2:]

        if not path:
            continue

        if path not in seen:
            normalized.append(
                path
            )

            seen.add(
                path
            )

    return normalized


def sanitize_test_commands(
    commands,
):
    commands = normalize_string_list(
        commands
    )

    safe_commands = []

    for command in commands:
        cleaned = command.strip()

        lower = cleaned.lower()

        if not cleaned:
            continue

        if (
            "streamlit run" in lower
            or "flask run" in lower
            or "uvicorn " in lower
            or "gunicorn " in lower
            or "npm start" in lower
            or "npm run dev" in lower
        ):
            print(
                "Planner removed persistent "
                f"test command: {cleaned}"
            )

            continue

        if (
            "pip install" in lower
            or "python -m pip install"
            in lower
            or "npm install" in lower
        ):
            print(
                "Planner removed installation "
                f"command from tests: {cleaned}"
            )

            continue

        safe_commands.append(
            cleaned
        )

    if not safe_commands:
        safe_commands = [
            "python -m compileall ."
        ]

    return safe_commands


def validate_plan(
    plan,
):
    if not isinstance(
        plan,
        dict,
    ):
        raise ValueError(
            "Planner output must be a JSON object."
        )

    missing = (
        REQUIRED_PLAN_FIELDS
        - set(
            plan.keys()
        )
    )

    if missing:
        print(
            "Planner response missing fields:",
            ", ".join(
                sorted(
                    missing
                )
            ),
        )

    summary = plan.get(
        "summary",
        "",
    )

    reasoning = plan.get(
        "reasoning",
        "",
    )

    if summary is None:
        summary = ""

    if reasoning is None:
        reasoning = ""

    if not isinstance(
        summary,
        str,
    ):
        summary = str(
            summary
        )

    if not isinstance(
        reasoning,
        str,
    ):
        reasoning = str(
            reasoning
        )

    normalized = {
        "summary": (
            summary.strip()
            or "Engineering task analysis"
        ),
        "reasoning": (
            reasoning.strip()
            or (
                "The planner did not provide "
                "additional reasoning."
            )
        ),
        "files_to_modify": (
            normalize_file_list(
                plan.get(
                    "files_to_modify",
                    [],
                )
            )
        ),
        "files_to_create": (
            normalize_file_list(
                plan.get(
                    "files_to_create",
                    [],
                )
            )
        ),
        "steps": (
            normalize_string_list(
                plan.get(
                    "steps",
                    [],
                )
            )
        ),
        "risks": (
            normalize_string_list(
                plan.get(
                    "risks",
                    [],
                )
            )
        ),
        "tests_to_run": (
            sanitize_test_commands(
                plan.get(
                    "tests_to_run",
                    [],
                )
            )
        ),
    }

    overlap = set(
        normalized[
            "files_to_modify"
        ]
    ) & set(
        normalized[
            "files_to_create"
        ]
    )

    if overlap:
        raise ValueError(
            "The same file cannot appear in both "
            "files_to_modify and files_to_create: "
            + ", ".join(
                sorted(
                    overlap
                )
            )
        )

    return normalized


def build_planner_prompt(
    task,
    relevant_context,
    symbol_context,
):
    return f"""
You are the planning agent for an AI Software Engineer.

Your responsibility is to inspect the engineering task and repository context and create a precise implementation plan.

You are NOT the coding agent.
Do not write implementation code.
Do not generate patches.

Return ONLY one valid JSON object.

STRICT OUTPUT RULES:

1. Return valid JSON only.
2. Do not use markdown.
3. Do not use code fences.
4. Do not write ```json.
5. Do not include text before the JSON.
6. Do not include text after the JSON.
7. Do not include comments.
8. Do not use trailing commas.
9. Use double quotes for JSON strings and keys.
10. Always include every required field.
11. files_to_modify must be a JSON array of repository-relative file paths.
12. files_to_create must be a JSON array of repository-relative file paths.
13. steps must be a JSON array of strings.
14. risks must be a JSON array of strings.
15. tests_to_run must be a JSON array of terminating commands.
16. Do not include commands that start a persistent development server.
17. Do not use "streamlit run" as a test.
18. Do not use installation commands as tests.
19. Prefer existing repository tests when clearly relevant.
20. Otherwise use safe syntax validation such as "python -m compileall .".
21. Do not add unrelated files.
22. Prefer the smallest safe implementation.
23. Preserve existing behavior unless the task explicitly requires changing it.
24. Only list files that actually need modification.
25. Only list files_to_create when a new file is genuinely required.
26. If the task is inspection-only and no changes are required, return empty arrays for files_to_modify and files_to_create.
27. Do not invent repository files that are not supported by the provided context.
28. Git operations such as git status, git remote, git commit, and git push are actions, not test commands. Do not put Git commands in tests_to_run.

Required JSON structure:

{{
  "summary": "short summary of the engineering task",
  "reasoning": "why this plan is appropriate",
  "files_to_modify": [],
  "files_to_create": [],
  "steps": [],
  "risks": [],
  "tests_to_run": []
}}

ENGINEERING TASK:

{task}

RELEVANT REPOSITORY CODE:

{relevant_context}

REPOSITORY SYMBOL INFORMATION:

{symbol_context}

Return only the JSON object.
""".strip()


def build_repair_prompt(
    original_prompt,
    bad_response,
    error,
):
    return f"""
Your previous planning response was invalid.

You MUST regenerate the complete response from scratch.

ERROR:

{error}

INVALID RESPONSE:

{bad_response}

ORIGINAL REQUEST:

{original_prompt}

Return ONLY one valid JSON object.

Do not use markdown.
Do not use code fences.
Do not explain the correction.
Do not include any text outside the JSON.
Use valid JSON syntax with double quotes.
Include every required field.
""".strip()


def create_plan(
    task,
    relevant_chunks,
    symbols,
):
    if not task:
        raise ValueError(
            "Engineering task cannot be empty."
        )

    task = str(
        task
    ).strip()

    if not task:
        raise ValueError(
            "Engineering task cannot be empty."
        )

    relevant_context = (
        build_relevant_context(
            relevant_chunks
        )
    )

    symbol_context = (
        build_symbol_context(
            symbols
        )
    )

    original_prompt = (
        build_planner_prompt(
            task,
            relevant_context,
            symbol_context,
        )
    )

    prompt = original_prompt

    last_error = None
    last_response = None

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        print()
        print(
            "=" * 60
        )

        print(
            f"PLANNER ATTEMPT "
            f"{attempt}/{max_attempts}"
        )

        print(
            "=" * 60
        )

        try:
            response = ask_llm(
                prompt
            )

            last_response = response

            print()
            print(
                "========== RAW PLANNER RESPONSE =========="
            )

            print(
                response
            )

            print(
                "=========================================="
            )

            print()

            plan = extract_json(
                response
            )

            validated_plan = (
                validate_plan(
                    plan
                )
            )

            print(
                "Planner response validated successfully."
            )

            print(
                "Files to modify:",
                validated_plan[
                    "files_to_modify"
                ],
            )

            print(
                "Files to create:",
                validated_plan[
                    "files_to_create"
                ],
            )

            print(
                "Tests:",
                validated_plan[
                    "tests_to_run"
                ],
            )

            return validated_plan

        except Exception as error:
            last_error = error

            print(
                f"Planner attempt "
                f"{attempt} failed:"
            )

            print(
                error
            )

            if attempt < max_attempts:
                prompt = (
                    build_repair_prompt(
                        original_prompt,
                        last_response
                        or "(no response)",
                        error,
                    )
                )

    print()
    print(
        "========== FINAL PLANNER FAILURE =========="
    )

    if last_response:
        print(
            "Last model response:"
        )

        print(
            last_response
        )

    print(
        "Last error:"
    )

    print(
        last_error
    )

    print(
        "==========================================="
    )

    raise ValueError(
        "Planner failed after "
        f"{max_attempts} attempts. "
        f"Last error: {last_error}"
    )


if __name__ == "__main__":
    sample_task = (
        "Add a small message to the "
        "Streamlit sidebar."
    )

    sample_chunks = [
        {
            "path": "app.py",
            "symbol": "MODULE_LEVEL",
            "content": (
                "import streamlit as st\n"
                "st.title('Example')"
            ),
            "retrieval_score": 0.95,
        }
    ]

    sample_symbols = [
        {
            "path": "app.py",
            "name": "MODULE_LEVEL",
            "type": "module",
        }
    ]

    try:
        result = create_plan(
            sample_task,
            sample_chunks,
            sample_symbols,
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    except Exception as error:
        print(
            "Planner test failed:"
        )

        print(
            error
        )