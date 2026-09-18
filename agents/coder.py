import re

from llm import ask_llm


MAX_GENERATION_ATTEMPTS = 3


def get_file_content(repo_files, path):
    normalized_path = path.replace("\\", "/")

    for file_data in repo_files:
        file_path = file_data.get(
            "path",
            ""
        ).replace(
            "\\",
            "/"
        )

        if file_path == normalized_path:
            return file_data.get(
                "content",
                ""
            )

    return ""


def file_exists(repo_files, path):
    normalized_path = path.replace(
        "\\",
        "/"
    )

    for file_data in repo_files:
        file_path = file_data.get(
            "path",
            ""
        ).replace(
            "\\",
            "/"
        )

        if file_path == normalized_path:
            return True

    return False


def clean_response(response):
    if not response:
        return ""

    response = response.strip()

    response = response.replace(
        "```python",
        ""
    )

    response = response.replace(
        "```xml",
        ""
    )

    response = response.replace(
        "```text",
        ""
    )

    response = response.replace(
        "```",
        ""
    )

    response = response.replace(
        "<FND>",
        "<FIND>"
    )

    response = response.replace(
        "</FND>",
        "</FIND>"
    )

    response = response.replace(
        "<REPLCE>",
        "<REPLACE>"
    )

    response = response.replace(
        "</REPLCE>",
        "</REPLACE>"
    )

    response = response.replace(
        "<CONTENTS>",
        "<CONTENT>"
    )

    response = response.replace(
        "</CONTENTS>",
        "</CONTENT>"
    )

    return response.strip()


def extract_patch_blocks(response):
    return re.findall(
        r"<PATCH>\s*(.*?)\s*</PATCH>",
        response,
        flags=(
            re.DOTALL
            | re.IGNORECASE
        )
    )


def extract_tag(block, tag):
    match = re.search(
        rf"<{tag}>\s*(.*?)\s*</{tag}>",
        block,
        flags=(
            re.DOTALL
            | re.IGNORECASE
        )
    )

    if not match:
        return None

    return match.group(1)


def parse_patches(response):
    response = clean_response(
        response
    )

    if not response:
        return []

    patches = []

    patch_blocks = extract_patch_blocks(
        response
    )

    for block in patch_blocks:
        path = extract_tag(
            block,
            "PATH"
        )

        if path is None:
            continue

        path = path.strip()

        if not path:
            continue

        content = extract_tag(
            block,
            "CONTENT"
        )

        if content is not None:
            content = content.strip(
                "\r\n"
            )

            if not content:
                continue

            patches.append(
                {
                    "path": path,
                    "action": "create",
                    "content": content,
                }
            )

            continue

        find_text = extract_tag(
            block,
            "FIND"
        )

        replace_text = extract_tag(
            block,
            "REPLACE"
        )

        if (
            find_text is None
            or replace_text is None
        ):
            continue

        find_text = find_text.strip(
            "\r\n"
        )

        replace_text = replace_text.strip(
            "\r\n"
        )

        if not find_text:
            continue

        if find_text == replace_text:
            continue

        patches.append(
            {
                "path": path,
                "action": "modify",
                "find": find_text,
                "replace": replace_text,
            }
        )

    return patches


def tokenize(text):
    return re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        text or ""
    )


def normalize_for_match(text):
    lines = text.splitlines()

    normalized_lines = []

    for line in lines:
        normalized_lines.append(
            line.rstrip()
        )

    return "\n".join(
        normalized_lines
    ).strip()


def find_flexible_match(
    content,
    find_text
):
    if find_text in content:
        return find_text

    normalized_content = normalize_for_match(
        content
    )

    normalized_find = normalize_for_match(
        find_text
    )

    if normalized_find not in normalized_content:
        return None

    content_lines = content.splitlines(
        keepends=True
    )

    find_lines = find_text.splitlines()

    if not find_lines:
        return None

    target_lines = [
        line.rstrip()
        for line in find_lines
    ]

    for start in range(
        len(content_lines)
    ):
        end = start + len(
            target_lines
        )

        if end > len(
            content_lines
        ):
            break

        candidate_lines = [
            line.rstrip(
                "\r\n"
            ).rstrip()
            for line in content_lines[
                start:end
            ]
        ]

        if candidate_lines == target_lines:
            return "".join(
                content_lines[
                    start:end
                ]
            ).rstrip(
                "\r\n"
            )

    return None


def validate_patches(
    patches,
    repo_files
):
    valid_patches = []

    for patch in patches:
        action = patch.get(
            "action"
        )

        path = patch.get(
            "path",
            ""
        ).strip()

        if not path:
            print(
                "[REJECTED] Missing file path."
            )
            continue

        if action == "create":
            if file_exists(
                repo_files,
                path
            ):
                print(
                    f"[REJECTED] {path}: "
                    "CREATE requested but file already exists."
                )
                continue

            content = patch.get(
                "content",
                ""
            )

            if not content.strip():
                print(
                    f"[REJECTED] {path}: "
                    "new file content is empty."
                )
                continue

            valid_patches.append(
                patch
            )

            continue

        if action != "modify":
            print(
                f"[REJECTED] {path}: "
                f"unknown action {action}."
            )
            continue

        if not file_exists(
            repo_files,
            path
        ):
            print(
                f"[REJECTED] {path}: "
                "MODIFY requested but file does not exist."
            )
            continue

        existing_content = get_file_content(
            repo_files,
            path
        )

        find_text = patch.get(
            "find",
            ""
        )

        replace_text = patch.get(
            "replace",
            ""
        )

        if not find_text:
            print(
                f"[REJECTED] {path}: "
                "FIND text is empty."
            )
            continue

        if find_text == replace_text:
            print(
                f"[REJECTED] {path}: "
                "patch does not change anything."
            )
            continue

        exact_count = existing_content.count(
            find_text
        )

        if exact_count == 1:
            valid_patches.append(
                patch
            )
            continue

        if exact_count > 1:
            print(
                f"[REJECTED] {path}: "
                f"FIND matched {exact_count} times."
            )
            continue

        flexible_match = find_flexible_match(
            existing_content,
            find_text
        )

        if flexible_match is not None:
            flexible_count = (
                existing_content.count(
                    flexible_match
                )
            )

            if flexible_count == 1:
                repaired_patch = dict(
                    patch
                )

                repaired_patch[
                    "find"
                ] = flexible_match

                valid_patches.append(
                    repaired_patch
                )

                print(
                    f"[REPAIRED] {path}: "
                    "whitespace mismatch corrected."
                )

                continue

        print(
            f"[REJECTED] {path}: "
            "FIND text does not exactly match the file."
        )

        print(
            "FIND:"
        )

        print(
            find_text[:1500]
        )

    return valid_patches


def build_files_context(
    task,
    plan,
    repo_files
):
    target_files = []

    for path in plan.get(
        "files_to_modify",
        []
    ):
        if path not in target_files:
            target_files.append(
                path
            )

    for path in plan.get(
        "files_to_create",
        []
    ):
        if path not in target_files:
            target_files.append(
                path
            )

    context = ""

    for path in target_files:
        context += "\n"
        context += "=" * 70
        context += "\n"

        context += (
            f"FILE: {path}\n"
        )

        context += "=" * 70
        context += "\n"

        if file_exists(
            repo_files,
            path
        ):
            context += get_file_content(
                repo_files,
                path
            )

        else:
            context += (
                "[FILE DOES NOT EXIST]"
            )

        context += "\n"

    if not target_files:
        for file_data in repo_files:
            context += "\n"
            context += "=" * 70
            context += "\n"

            context += (
                f"FILE: "
                f"{file_data.get('path', '')}\n"
            )

            context += "=" * 70
            context += "\n"

            context += file_data.get(
                "content",
                ""
            )

            context += "\n"

    return context


def build_prompt(
    task,
    plan,
    files_context
):
    return f"""
You are the coding agent of an AI Software Engineer.

Your job is to implement the requested repository change.

USER TASK:

{task}

IMPLEMENTATION PLAN:

{plan}

CURRENT FILE CONTENT:

{files_context}

You must return file patches only.

To modify an existing file:

<PATCH>
<PATH>relative/path.py</PATH>
<FIND>
exact text copied from the existing file
</FIND>
<REPLACE>
replacement text
</REPLACE>
</PATCH>

To create a new file:

<PATCH>
<PATH>relative/new_file.py</PATH>
<CONTENT>
complete new file content
</CONTENT>
</PATCH>

Rules:

1. Return only PATCH blocks.
2. Do not return Markdown.
3. Do not return JSON.
4. Do not use code fences.
5. Do not explain the changes.
6. Do not output tool-call syntax.
7. Do not output tags such as arg_value.
8. Every patch must contain PATH.
9. Existing files must use FIND and REPLACE.
10. New files must use CONTENT.
11. FIND must be copied exactly from the provided file.
12. Preserve indentation exactly.
13. Keep FIND blocks small.
14. FIND blocks must uniquely identify one location.
15. Do not rewrite a large file when a small patch is enough.
16. Preserve unrelated behavior.
17. Do not create unnecessary dependencies.
18. Do not generate no-op patches.
19. Do not modify files outside the repository.
20. Generated Python must be syntactically valid.
21. If multiple locations need modification, generate multiple PATCH blocks.
22. If a file already exists, never use CONTENT for it.
23. If a file does not exist, never use FIND and REPLACE for it.
24. Carefully verify all XML-style tags before responding.
25. Use exactly FIND, REPLACE, CONTENT, PATH and PATCH tags.

Return the patches now.
"""


def build_repair_prompt(
    task,
    plan,
    files_context,
    invalid_response,
):
    return f"""
You are repairing an invalid response produced by a coding agent.

The previous response could not be safely applied.

Generate the implementation again from scratch.

USER TASK:

{task}

IMPLEMENTATION PLAN:

{plan}

CURRENT FILE CONTENT:

{files_context}

INVALID PREVIOUS RESPONSE:

{invalid_response}

Return only valid PATCH blocks.

For an existing file:

<PATCH>
<PATH>file.py</PATH>
<FIND>
exact existing code copied from CURRENT FILE CONTENT
</FIND>
<REPLACE>
replacement code
</REPLACE>
</PATCH>

For a new file:

<PATCH>
<PATH>new_file.py</PATH>
<CONTENT>
complete file content
</CONTENT>
</PATCH>

Rules:

1. Return only PATCH blocks.
2. Do not use Markdown.
3. Do not use JSON.
4. Do not use code fences.
5. Do not output explanations.
6. Do not output arg_value tags.
7. FIND must exist exactly in CURRENT FILE CONTENT.
8. Keep FIND small and unique.
9. Preserve indentation.
10. Do not create unnecessary dependencies.
11. Do not generate identical FIND and REPLACE blocks.
12. Do not rewrite entire existing files unnecessarily.
13. Validate every opening and closing tag before responding.
"""


def print_parsed_patches(
    patches
):
    if not patches:
        print(
            "No parsable patches found."
        )
        return

    print(
        f"Parsed patches: {len(patches)}"
    )

    for patch in patches:
        print(
            f"- {patch.get('action')} "
            f"-> {patch.get('path')}"
        )


def generate_changes(
    task,
    plan,
    repo_files,
):
    files_context = build_files_context(
        task,
        plan,
        repo_files,
    )

    prompt = build_prompt(
        task,
        plan,
        files_context,
    )

    last_response = None

    for attempt in range(
        1,
        MAX_GENERATION_ATTEMPTS + 1,
    ):
        print(
            f"Coder generation attempt "
            f"{attempt}/"
            f"{MAX_GENERATION_ATTEMPTS}"
        )

        response = ask_llm(
            prompt
        )

        last_response = response

        patches = parse_patches(
            response
        )

        print_parsed_patches(
            patches
        )

        if patches:
            valid_patches = (
                validate_patches(
                    patches,
                    repo_files,
                )
            )

            if valid_patches:
                print(
                    f"Valid patches generated: "
                    f"{len(valid_patches)}"
                )

                return {
                    "patches": (
                        valid_patches
                    )
                }

            print(
                "All parsed patches "
                "failed validation."
            )

        else:
            print(
                "Model response contained "
                "no valid PATCH blocks."
            )

        if attempt < MAX_GENERATION_ATTEMPTS:
            print(
                "Requesting corrected patches..."
            )

            prompt = build_repair_prompt(
                task,
                plan,
                files_context,
                response,
            )

    print()
    print(
        "=" * 70
    )

    print(
        "LAST CODER RESPONSE"
    )

    print(
        "=" * 70
    )

    if last_response:
        print(
            last_response
        )

    else:
        print(
            "[EMPTY RESPONSE]"
        )

    print(
        "=" * 70
    )

    raise ValueError(
        "Coder failed to generate valid patches "
        f"after {MAX_GENERATION_ATTEMPTS} attempts."
    )