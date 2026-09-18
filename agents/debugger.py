import re

from llm import ask_llm


def clean_response(response):
    if not response:
        raise ValueError(
            "Debugger returned an empty response."
        )

    response = response.strip()

    response = response.replace(
        "```python",
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

    return response.strip()


def parse_debug_response(
    response
):
    response = clean_response(
        response
    )

    root_cause = "Unknown"

    root_match = re.search(
        r"<ROOT_CAUSE>\s*(.*?)\s*</ROOT_CAUSE>",
        response,
        flags=(
            re.DOTALL
            | re.IGNORECASE
        )
    )

    if root_match:
        root_cause = (
            root_match
            .group(1)
            .strip()
        )

    patches = []

    patch_blocks = re.findall(
        r"<PATCH>(.*?)</PATCH>",
        response,
        flags=(
            re.DOTALL
            | re.IGNORECASE
        )
    )

    for block in patch_blocks:

        path_match = re.search(
            r"<PATH>\s*(.*?)\s*</PATH>",
            block,
            flags=(
                re.DOTALL
                | re.IGNORECASE
            )
        )

        if not path_match:
            continue

        path = (
            path_match
            .group(1)
            .strip()
        )

        content_match = re.search(
            r"<CONTENT>\s*(.*?)\s*</CONTENT>",
            block,
            flags=(
                re.DOTALL
                | re.IGNORECASE
            )
        )

        if content_match:

            patches.append(
                {
                    "path": path,
                    "action": "create",
                    "content": (
                        content_match
                        .group(1)
                        .strip("\r\n")
                    )
                }
            )

            continue

        find_match = re.search(
            r"<FIND>\s*(.*?)\s*</FIND>",
            block,
            flags=(
                re.DOTALL
                | re.IGNORECASE
            )
        )

        replace_match = re.search(
            r"<REPLACE>\s*(.*?)\s*</REPLACE>",
            block,
            flags=(
                re.DOTALL
                | re.IGNORECASE
            )
        )

        if (
            find_match
            and replace_match
        ):

            find_text = (
                find_match
                .group(1)
                .strip("\r\n")
            )

            replace_text = (
                replace_match
                .group(1)
                .strip("\r\n")
            )

            if (
                find_text
                and find_text
                != replace_text
            ):

                patches.append(
                    {
                        "path": path,
                        "action": "modify",
                        "find": find_text,
                        "replace": replace_text
                    }
                )

    return {
        "root_cause": root_cause,
        "patches": patches
    }


def debug_failure(
    task,
    test_results,
    repo_files
):
    failures = ""

    for result in test_results:

        if (
            result.get(
                "returncode"
            ) == 0
        ):
            continue

        failures += (
            "\nCOMMAND:\n"
            f"{result.get('command')}\n"
        )

        failures += (
            "\nSTDOUT:\n"
            f"{result.get('stdout', '')}\n"
        )

        failures += (
            "\nSTDERR:\n"
            f"{result.get('stderr', '')}\n"
        )

    repository_context = ""

    for file_data in repo_files:

        repository_context += (
            "\n"
            + "=" * 60
            + "\n"
        )

        repository_context += (
            f"FILE: "
            f"{file_data['path']}\n"
        )

        repository_context += (
            "=" * 60
            + "\n"
        )

        repository_context += (
            file_data[
                "content"
            ]
        )

        repository_context += "\n"

    prompt = f"""
You are the debugging agent of an AI Software Engineer.

ORIGINAL TASK:

{task}

TEST OR RUNTIME FAILURE:

{failures}

CURRENT REPOSITORY:

{repository_context}

Your job:

1. Identify the actual root cause.
2. Find the responsible file.
3. Produce the smallest safe repair.
4. Do not rewrite unrelated code.
5. Do not introduce unnecessary dependencies.

Return this format:

<ROOT_CAUSE>
brief technical explanation
</ROOT_CAUSE>

<PATCH>
<PATH>file.py</PATH>
<FIND>
exact code currently in file
</FIND>
<REPLACE>
corrected code
</REPLACE>
</PATCH>

For new files:

<PATCH>
<PATH>new_file.py</PATH>
<CONTENT>
complete new file
</CONTENT>
</PATCH>

Rules:

- Return only ROOT_CAUSE and PATCH blocks.
- No markdown.
- No JSON.
- FIND must exactly match the repository.
- Keep patches small.
- Preserve existing functionality.
"""

    response = ask_llm(
        prompt
    )

    return parse_debug_response(
        response
    )